"""
Teknik Resim (CDR) Agent - CDR Dosya Isleyici + Vision API Analizi.

CDR dosyasindan onizleme gorseli cikarir veya dogrudan gorsel alir,
GPT-4o-mini Vision API ile analiz eder, yapilandirilmis JSON verisine cevirir.

CDR Dosya Yapisi:
  - CDR X4+ (versiyon 14+): ZIP konteyner → preview bitmap/PNG icinde
  - CDR eski versiyon: RIFF binary → BMP imzasi aramasiyla cikarim
  - Preview bulunamazsa: Kullaniciya PNG/JPG export tavsiyesi

Token Optimizasyonu:
  - Gorsel max 1024px'e kucultulur
  - JPEG %85 kalitede sikistirilir
"""
import base64
import io
import json
import os
import struct
import zipfile
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from cdr_agent.prompts import CDR_VISION_PROMPT
from token_tracker import log_token_usage


# ── Gorsel boyut limiti (piksel) ──
MAX_IMAGE_DIMENSION = 1024


# ── Config'den VISION_MODEL'i al ──
try:
    from config import VISION_MODEL
except ImportError:
    VISION_MODEL = "gpt-4o-mini"


def _get_api_key() -> str:
    """API anahtarini taze okur (st.secrets veya .env)."""
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    try:
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_env_path, override=True)
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


# ── Varsayilan bos sonuc ──
EMPTY_CDR_RESULT = {
    "musteri_adi": "OKUNAMADI",
    "siparis_no": "OKUNAMADI",
    "parca_adi": "OKUNAMADI",
    "en_mm": 0,
    "boy_mm": 0,
    "kalinlik_mm": 0,
    "cam_tipi": "diger",
    "adet": 1,
    "kenar_isleme": "belirtilmemis",
    "delik_sayisi": 0,
    "notlar": "",
}


# ══════════════════════════════════════════════════════════════════════
# CDR PREVIEW CIKARMA
# ══════════════════════════════════════════════════════════════════════


def extract_preview_from_cdr(cdr_bytes: bytes) -> bytes | None:
    """
    CDR dosyasindan onizleme gorselini cikarir.

    Strateji 1: ZIP container (CDR X4+, versiyon 14+)
      - ZIP olarak ac, preview/thumbnail dosyalarini ara
      - Bulunan ilk gecerli gorseli dondur

    Strateji 2: RIFF binary (eski CDR)
      - BMP imzasi (0x42 0x4D) arayarak embed bitmap cikart
      - BMP header'dan boyut oku ve veriyi cikart

    Returns:
        Gorsel bytes (BMP/PNG) veya None (bulunamazsa).
    """
    # ── Strateji 1: ZIP container ──
    try:
        with zipfile.ZipFile(io.BytesIO(cdr_bytes), "r") as zf:
            names = zf.namelist()

            # Oncelik sirasina gore aday dosyalari bul
            preview_candidates = []
            for name in names:
                name_lower = name.lower()
                if "preview" in name_lower or "thumbnail" in name_lower:
                    preview_candidates.insert(0, name)  # en yuksek oncelik
                elif name_lower.endswith((".bmp", ".png", ".jpg", ".jpeg")):
                    preview_candidates.append(name)

            for candidate in preview_candidates:
                try:
                    data = zf.read(candidate)
                    # Gecerli gorsel mi kontrol et
                    Image.open(io.BytesIO(data))
                    return data
                except Exception:
                    continue
    except zipfile.BadZipFile:
        pass  # ZIP degil, RIFF dene

    # ── Strateji 2: RIFF binary - BMP imzasi ara ──
    bmp_sig = b"\x42\x4D"  # "BM"
    offset = 0
    while True:
        idx = cdr_bytes.find(bmp_sig, offset)
        if idx == -1:
            break
        try:
            # BMP dosya boyutu: offset +2'de 4 byte little-endian
            bmp_size = struct.unpack("<I", cdr_bytes[idx + 2 : idx + 6])[0]
            if 1000 < bmp_size < len(cdr_bytes) - idx + 1:
                bmp_data = cdr_bytes[idx : idx + bmp_size]
                # Gecerli gorsel mi kontrol et
                Image.open(io.BytesIO(bmp_data))
                return bmp_data
        except Exception:
            pass
        offset = idx + 2

    return None  # Preview bulunamadi


# ══════════════════════════════════════════════════════════════════════
# GORSEL KUCULTME + SIKISTIRMA
# ══════════════════════════════════════════════════════════════════════


def _resize_and_compress(image_bytes: bytes) -> bytes:
    """
    Gorseli max 1024px'e kucultup JPEG %85 olarak sikistirir.

    Returns:
        Sikistirilmis gorsel bytes.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        if max(w, h) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception:
        return image_bytes


# ══════════════════════════════════════════════════════════════════════
# VISION API ANALIZ
# ══════════════════════════════════════════════════════════════════════


def parse_cdr_image(image_bytes: bytes, file_type: str = "jpeg") -> dict:
    """
    Teknik resim gorselini Vision API ile okur ve yapilandirilmis veri dondurur.

    Pipeline: Gorsel → resize/compress → base64 → Vision API → JSON parse → dict

    Args:
        image_bytes: Ham gorsel verisi (PNG, JPG veya CDR'den cikarilmis BMP)
        file_type: "jpeg", "jpg", "png" veya "bmp"

    Returns:
        dict: Parse edilmis teknik resim verileri.
              Hata durumunda '_error' anahtari eklenir.
    """
    api_key = _get_api_key()
    if not api_key:
        return {**EMPTY_CDR_RESULT, "_error": "API anahtari bulunamadi"}

    try:
        # ADIM 1: Gorseli kucult ve sikistir
        image_bytes = _resize_and_compress(image_bytes)

        # ADIM 2: base64 encoding
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_image}"

        # ADIM 3: Vision API cagirisi
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CDR_VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "auto",
                            },
                        },
                    ],
                }
            ],
            max_tokens=600,
            temperature=0.1,
        )

        # ADIM 4: Token kullanimi kaydet
        try:
            usage = response.usage
            if usage:
                log_token_usage(
                    agent_adi="Teknik Resim",
                    model=VISION_MODEL,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="CDR Analiz",
                )
        except Exception:
            pass  # Token loglama hatasi analizi bozmasin

        # ADIM 5: JSON parse
        raw_content = response.choices[0].message.content.strip()

        json_str = raw_content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)

        # ADIM 6: Eksik alanlari varsayilanlarla tamamla
        result = {**EMPTY_CDR_RESULT}
        for key in EMPTY_CDR_RESULT:
            if key in parsed and parsed[key] is not None:
                result[key] = parsed[key]

        # Sayisal alanlari int'e cevir
        for num_field in ("en_mm", "boy_mm", "kalinlik_mm", "adet", "delik_sayisi"):
            try:
                result[num_field] = int(
                    float(str(result[num_field]).replace(",", "."))
                )
            except (ValueError, TypeError):
                result[num_field] = EMPTY_CDR_RESULT[num_field]

        return result

    except json.JSONDecodeError as e:
        return {**EMPTY_CDR_RESULT, "_error": f"JSON parse hatasi: {str(e)}"}
    except Exception as e:
        return {**EMPTY_CDR_RESULT, "_error": f"Analiz hatasi: {str(e)}"}
