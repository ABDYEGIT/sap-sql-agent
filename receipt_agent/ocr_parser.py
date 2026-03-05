"""
Fis Okuyucu Agent - GPT-4o-mini Vision ile Fis Okuma.

Fis gorselini OpenAI Vision API'ye gonderir ve
yapilandirilmis JSON verisi olarak geri alir.

Token Optimizasyonu:
  - Gorsel API'ye gonderilmeden once max 1024px'e kucultulur
  - detail="low" ile sabit 85 token gorsel maliyeti
  - Bu sayede ~2000+ token yerine ~85 token gorsel maliyeti
"""
import base64
import io
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from receipt_agent.prompts import RECEIPT_OCR_PROMPT
from token_tracker import log_token_usage

# ── Gorsel boyut limiti (piksel) ──
# Uzun kenar bu degeri asmayacak sekilde kucultulur
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


EMPTY_RECEIPT = {
    "isletme_adi": "OKUNAMADI",
    "adres": "OKUNAMADI",
    "vergi_no": "OKUNAMADI",
    "vergi_dairesi": "OKUNAMADI",
    "tarih": "OKUNAMADI",
    "saat": "OKUNAMADI",
    "fis_no": "OKUNAMADI",
    "tutar": 0.0,
    "kdv_orani": 0.0,
    "fis_turu": "diger",
    "alkol_sigara_pisin": False,
}


def parse_receipt_image(image_bytes: bytes, file_type: str = "jpeg") -> dict:
    """
    Fis gorselini Vision API ile okur ve yapilandirilmis veri dondurur.

    Pipeline: Gorsel → base64 → Vision API → JSON parse → dict
    """
    api_key = _get_api_key()
    if not api_key:
        return {**EMPTY_RECEIPT, "_error": "API anahtari bulunamadi"}

    try:
        # ADIM 1: Gorseli kucult (token tasarrufu)
        # Telefon kameralari 3000-4000+ px gorsel uretir.
        # Bunu 1024px'e kucultmek tile sayisini dusurur.
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            if max(w, h) > MAX_IMAGE_DIMENSION:
                ratio = MAX_IMAGE_DIMENSION / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # JPEG olarak compress et (kalite 85, boyut kuculsun)
            buf = io.BytesIO()
            img_format = "JPEG"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(buf, format=img_format, quality=85)
            image_bytes = buf.getvalue()
            file_type = "jpeg"
        except Exception:
            pass  # Kucultme basarisiz olursa orijinal gorsel kullanilir

        # ADIM 2: base64 encoding
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{base64_image}"

        # ADIM 3: Vision API cagirisi
        # detail="low" → sabit 85 token gorsel maliyeti (vs auto/high: 1000-2000+ token)
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": RECEIPT_OCR_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "low",
                            },
                        },
                    ],
                }
            ],
            max_tokens=400,
            temperature=0.1,
        )

        # Token kullanimi kaydet
        try:
            usage = response.usage
            if usage:
                log_token_usage(
                    agent_adi="Fis Okuyucu",
                    model=VISION_MODEL,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="OCR",
                )
        except Exception:
            pass  # Token loglama hatasi fis okumayı bozmasin

        # ADIM 4: JSON parse
        raw_content = response.choices[0].message.content.strip()

        json_str = raw_content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)

        # ADIM 5: Eksik alanlari tamamla
        result = {**EMPTY_RECEIPT}
        for key in EMPTY_RECEIPT:
            if key in parsed and parsed[key] is not None:
                result[key] = parsed[key]

        # Tutar ve KDV oranini sayiya cevir
        try:
            result["tutar"] = float(str(result["tutar"]).replace(",", ".").replace("TL", "").strip())
        except (ValueError, TypeError):
            result["tutar"] = 0.0

        try:
            result["kdv_orani"] = float(str(result["kdv_orani"]).replace("%", "").replace(",", ".").strip())
        except (ValueError, TypeError):
            result["kdv_orani"] = 0.0

        # alkol_sigara_pisin boolean kontrol
        result["alkol_sigara_pisin"] = bool(parsed.get("alkol_sigara_pisin", False))

        return result

    except json.JSONDecodeError as e:
        return {**EMPTY_RECEIPT, "_error": f"JSON parse hatasi: {str(e)}"}
    except Exception as e:
        return {**EMPTY_RECEIPT, "_error": f"OCR hatasi: {str(e)}"}
