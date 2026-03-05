"""
Fis Okuyucu Agent - GPT-4o-mini Vision ile Fis Okuma.

Fis gorselini OpenAI Vision API'ye gonderir ve
yapilandirilmis JSON verisi olarak geri alir.
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
        # ADIM 1: base64 encoding
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        mime_map = {"jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png"}
        mime_type = mime_map.get(file_type.lower(), "image/jpeg")
        data_url = f"data:{mime_type};base64,{base64_image}"

        # ADIM 2: Vision API cagirisi
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
                                "detail": "low",  # Hizli mod: fis icin yeterli
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
            temperature=0.1,
        )

        # ADIM 3: JSON parse
        raw_content = response.choices[0].message.content.strip()

        json_str = raw_content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        parsed = json.loads(json_str)

        # ADIM 4: Eksik alanlari tamamla
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
