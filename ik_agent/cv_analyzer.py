"""
IK Agent - CV Uygunluk Analiz Modulu.

PDF formatindaki CV dosyalarini okur, LLM ile kriterlere gore
degerlendirir ve uygunluk skoru hesaplar.

Akis:
1. PDF → metin cikarma (PyMuPDF / fitz)
2. Kriterler + CV metni → LLM (OpenAI)
3. JSON formatinda skor + analiz
4. Toplu sonuclari siralama
"""
import json
import logging
import os
from pathlib import Path

import fitz  # PyMuPDF
from openai import OpenAI

from ik_agent.cv_prompts import CV_ANALYSIS_PROMPT
from config import OPENAI_MODEL, TEMPERATURE, MAX_TOKENS_RESPONSE
from token_tracker import log_token_usage

logger = logging.getLogger("cv-analyzer")


# ══════════════════════════════════════════════════════════════════════
# PDF METIN CIKARMA
# ══════════════════════════════════════════════════════════════════════


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    PDF dosyasindan metin cikarir.

    PyMuPDF (fitz) kullanarak her sayfadaki metni okur
    ve tek bir string olarak dondurur.

    Args:
        pdf_bytes: PDF dosyasinin byte verisi

    Returns:
        PDF'den cikarilan duz metin
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()

        full_text = "\n".join(text_parts).strip()

        if not full_text:
            return "(PDF'den metin cikarilamadi. Gorsel tabanli bir CV olabilir.)"

        return full_text

    except Exception as e:
        logger.error(f"PDF metin cikarma hatasi: {e}")
        return f"(PDF okuma hatasi: {str(e)})"


# ══════════════════════════════════════════════════════════════════════
# KRITER FORMATLAMA
# ══════════════════════════════════════════════════════════════════════


def format_criteria(
    position: str = "",
    experience_years: int = 0,
    education: str = "",
    languages: str = "",
    skills: str = "",
    extra_criteria: str = "",
) -> str:
    """
    Form alanlari ve serbest metni birlestirerek
    LLM'e gonderilecek kriter metnini olusturur.

    Args:
        position: Pozisyon adi
        experience_years: Minimum deneyim yili
        education: Egitim seviyesi
        languages: Dil gereksinimleri
        skills: Teknik beceriler (virgul ile ayrilmis)
        extra_criteria: Ek kriterler (serbest metin)

    Returns:
        Formatlanmis kriter metni
    """
    parts = []

    if position:
        parts.append(f"Pozisyon: {position}")
    if experience_years > 0:
        parts.append(f"Minimum Deneyim: {experience_years} yil")
    if education:
        parts.append(f"Egitim Seviyesi: {education}")
    if languages:
        parts.append(f"Dil Gereksinimleri: {languages}")
    if skills:
        parts.append(f"Teknik Beceriler: {skills}")
    if extra_criteria:
        parts.append(f"Ek Kriterler: {extra_criteria}")

    return "\n".join(parts) if parts else "Genel degerlendirme yapiniz."


# ══════════════════════════════════════════════════════════════════════
# TEK CV ANALIZI
# ══════════════════════════════════════════════════════════════════════


def analyze_single_cv(
    cv_text: str,
    criteria_text: str,
    api_key: str,
) -> dict:
    """
    Tek bir CV'yi belirtilen kriterlere gore analiz eder.

    Args:
        cv_text: CV'den cikarilan metin
        criteria_text: Formatlanmis kriter metni
        api_key: OpenAI API anahtari

    Returns:
        LLM'den gelen JSON analiz sonucu (dict)
        Hata durumunda hata bilgisi iceren dict
    """
    try:
        # Prompt olustur
        prompt = CV_ANALYSIS_PROMPT.format(
            criteria=criteria_text,
            cv_text=cv_text[:6000],  # Token limiti icin kes
        )

        # LLM cagir
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Sen bir CV degerlendirme uzmanisin. SADECE JSON formatinda yanit ver."},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_RESPONSE,
            response_format={"type": "json_object"},
        )

        # Token loglama
        usage = response.usage
        if usage:
            log_token_usage(
                agent_adi="CV Analiz",
                model=OPENAI_MODEL,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                islem_turu="CV Degerlendirme",
            )

        # JSON parse
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        # Zorunlu alanlar kontrolu
        if "uygunluk_skoru" not in result:
            result["uygunluk_skoru"] = 0
        if "aday_adi" not in result:
            result["aday_adi"] = "Bilinmiyor"
        if "ozet" not in result:
            result["ozet"] = "Degerlendirme yapildi."
        if "guclu_yonler" not in result:
            result["guclu_yonler"] = []
        if "zayif_yonler" not in result:
            result["zayif_yonler"] = []
        if "kriter_detay" not in result:
            result["kriter_detay"] = {}

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse hatasi: {e}")
        return {
            "aday_adi": "Bilinmiyor",
            "uygunluk_skoru": 0,
            "ozet": f"CV analiz edilemedi: JSON parse hatasi.",
            "guclu_yonler": [],
            "zayif_yonler": [],
            "kriter_detay": {},
            "hata": str(e),
        }

    except Exception as e:
        logger.error(f"CV analiz hatasi: {e}")
        return {
            "aday_adi": "Bilinmiyor",
            "uygunluk_skoru": 0,
            "ozet": f"CV analiz edilemedi: {str(e)}",
            "guclu_yonler": [],
            "zayif_yonler": [],
            "kriter_detay": {},
            "hata": str(e),
        }


# ══════════════════════════════════════════════════════════════════════
# TOPLU CV ANALIZI
# ══════════════════════════════════════════════════════════════════════


def analyze_multiple_cvs(
    cv_files: list,
    criteria_text: str,
    api_key: str,
    progress_callback=None,
) -> list:
    """
    Birden fazla CV dosyasini toplu analiz eder.

    Args:
        cv_files: Streamlit UploadedFile listesi (PDF)
        criteria_text: Formatlanmis kriter metni
        api_key: OpenAI API anahtari
        progress_callback: İlerleme guncelleme fonksiyonu (i, total, filename)

    Returns:
        Uygunluk skoruna gore sirali analiz sonuclari listesi
        Her eleman: {filename, ...analiz_sonucu}
    """
    results = []

    for i, cv_file in enumerate(cv_files):
        filename = cv_file.name

        # Ilerleme bildirimi
        if progress_callback:
            progress_callback(i, len(cv_files), filename)

        # PDF'den metin cikar
        pdf_bytes = cv_file.read()
        cv_file.seek(0)  # Dosyayi basa sar (tekrar okunabilir olmasi icin)

        cv_text = extract_text_from_pdf(pdf_bytes)

        # LLM ile analiz
        result = analyze_single_cv(cv_text, criteria_text, api_key)
        result["dosya_adi"] = filename

        results.append(result)

    # Uygunluk skoruna gore sirala (yuksekten dusuge)
    results.sort(key=lambda x: x.get("uygunluk_skoru", 0), reverse=True)

    return results
