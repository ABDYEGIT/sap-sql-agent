"""
Fis Okuyucu Agent - GPT-4o Vision ile Fis Okuma.

Fis gorselini OpenAI GPT-4o Vision API'ye gonderir ve
yapilandirilmis JSON verisi olarak geri alir.

Desteklenen Gorseller:
  - JPEG, JPG, PNG
  - Bulanik, egik, karanlik fis gorselleri de islenebilir

Teknik:
  - Gorsel base64 formatina cevrilir
  - GPT-4o'ya image_url olarak gonderilir
  - JSON yaniti parse edilir ve dict olarak dondurulur
"""
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from receipt_agent.prompts import RECEIPT_OCR_PROMPT


# ── Config'den VISION_MODEL'i al ──
try:
    from config import VISION_MODEL
except ImportError:
    VISION_MODEL = "gpt-4o"


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


# ══════════════════════════════════════════════════════════════════════
# BOS FIS SABLONU
# ══════════════════════════════════════════════════════════════════════
# OCR basarisiz olursa veya hata durumunda dondurulecek bos sablon.
# Tum alanlar "OKUNAMADI" veya 0 olarak ayarlanir.
# ══════════════════════════════════════════════════════════════════════

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
    "kalemler": [],
}


# ══════════════════════════════════════════════════════════════════════
# ANA OCR FONKSIYONU - GPT-4o Vision ile Fis Okuma
# ══════════════════════════════════════════════════════════════════════
# Bu fonksiyon fis gorselini alir, base64'e cevirir,
# GPT-4o Vision API'ye gonderir ve JSON yaniti parse eder.
#
# GPT-4o NEDEN?
# - gpt-4o-mini gorsel desteklemiyor
# - gpt-4o hem metin hem gorsel anlayabilen multimodal bir model
# - Bulanik, egik, dusuk kaliteli gorsellerde bile iyi sonuc verir
# ══════════════════════════════════════════════════════════════════════


def parse_receipt_image(image_bytes: bytes, file_type: str = "jpeg") -> dict:
    """
    Fis gorselini GPT-4o Vision API ile okur ve yapilandirilmis veri dondurur.

    ── VISION OCR PIPELINE ──
    1. Gorsel → base64 encoding
    2. base64 → GPT-4o Vision API'ye gonder
    3. GPT-4o yaniti → JSON parse
    4. JSON → dict olarak dondur

    Args:
        image_bytes: Gorsel dosyasinin binary icerigi
        file_type: Gorsel formati ("jpeg", "png" vs.)

    Returns:
        dict: Parse edilmis fis verileri
        {
            "isletme_adi": "STARBUCKS COFFEE",
            "adres": "Yesilpinar Mh. ...",
            "vergi_no": "7690310116",
            "vergi_dairesi": "Bogazici Kurumlar VD",
            "tarih": "18.01.2025",
            "saat": "11:58",
            "fis_no": "0030",
            "tutar": 95.00,
            "kdv_orani": 10,
            "fis_turu": "yemek"
        }
    """
    api_key = _get_api_key()
    if not api_key:
        return {**EMPTY_RECEIPT, "_error": "API anahtari bulunamadi"}

    try:
        # ── ADIM 1: Gorseli base64'e cevir ──
        # OpenAI Vision API, gorselleri base64 data URL formatinda kabul eder
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # MIME type belirle
        mime_map = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
        }
        mime_type = mime_map.get(file_type.lower(), "image/jpeg")
        data_url = f"data:{mime_type};base64,{base64_image}"

        # ── ADIM 2: GPT-4o Vision API'ye gonder ──
        # Mesaj icerigi: metin prompt + gorsel URL
        # GPT-4o hem metni hem gorseli ayni anda isler
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=VISION_MODEL,  # "gpt-4o" - gorsel destekli model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": RECEIPT_OCR_PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "high",  # Yuksek detay: fis yazilari icin onemli
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
            temperature=0.1,  # Dusuk yaraticilik: OCR icin deterministik olmali
        )

        # ── ADIM 3: Yaniti parse et ──
        raw_content = response.choices[0].message.content.strip()

        # JSON blogunu cikar (bazen ``` ile sarili gelebilir)
        json_str = raw_content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)

        # ── ADIM 4: Eksik alanlari tamamla ──
        # API'den gelmeyen alanlari "OKUNAMADI" ile doldur
        result = {**EMPTY_RECEIPT}
        for key in EMPTY_RECEIPT:
            if key == "kalemler":
                continue  # kalemler ayri islenir
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

        # ── ADIM 5: Kalem (line item) verilerini isle ──
        raw_kalemler = parsed.get("kalemler", [])
        kalemler = []
        if isinstance(raw_kalemler, list):
            for item in raw_kalemler:
                if isinstance(item, dict) and item.get("urun"):
                    try:
                        adet = float(str(item.get("adet", 1)).replace(",", "."))
                    except (ValueError, TypeError):
                        adet = 1
                    try:
                        birim_fiyat = float(str(item.get("birim_fiyat", 0)).replace(",", ".").replace("TL", "").strip())
                    except (ValueError, TypeError):
                        birim_fiyat = 0.0
                    try:
                        toplam = float(str(item.get("toplam", 0)).replace(",", ".").replace("TL", "").strip())
                    except (ValueError, TypeError):
                        toplam = birim_fiyat * adet
                    kategori = str(item.get("kategori", "normal")).lower()
                    if kategori not in ("alkol", "sigara", "normal"):
                        kategori = "normal"
                    kalemler.append({
                        "urun": str(item["urun"]),
                        "adet": adet,
                        "birim_fiyat": birim_fiyat,
                        "toplam": toplam,
                        "kategori": kategori,
                    })
        result["kalemler"] = kalemler

        return result

    except json.JSONDecodeError as e:
        return {**EMPTY_RECEIPT, "_error": f"JSON parse hatasi: {str(e)}"}
    except Exception as e:
        return {**EMPTY_RECEIPT, "_error": f"OCR hatasi: {str(e)}"}
