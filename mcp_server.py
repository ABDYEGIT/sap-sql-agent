"""
Yorglass SAP AI Platform - MCP Server.

5 SAP AI tool'unu MCP (Model Context Protocol) uzerinden sunar.
Claude Desktop veya herhangi bir MCP client bu tool'lari kullanabilir.

Mevcut Streamlit uygulamasini ETKILEMEZ - ayri bir giris noktasidir.

Calistirma:
    python mcp_server.py

Claude Desktop config (claude_desktop_config.json):
    {
        "mcpServers": {
            "yorglass-sap": {
                "command": "python",
                "args": ["C:/.../sap_sql_agent/mcp_server.py"]
            }
        }
    }
"""
import sys
import base64
import logging
from pathlib import Path

# Proje kokunu sys.path'e ekle (agent import'lari icin)
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

# ── Agent import'lari ──
from config import _resolve_api_key
from rag_engine import RAGEngine

from sql_agent.generator import generate_sql, extract_sql_block
from sql_agent.metadata_loader import (
    load_metadata_from_excel,
    index_tables_for_rag,
)

from bapi_agent.generator import generate_bapi_response
from bapi_agent.metadata_loader import (
    load_bapi_metadata_from_excel,
    index_bapis_for_rag,
)

from sd_mm_agent.mock_db import init_mock_db
from sd_mm_agent.sql_executor import convert_sap_to_sqlite, execute_query

from ik_agent.generator import generate_ik_response
from ik_agent.document_loader import load_and_chunk_docx, get_default_document_path

from receipt_agent.ocr_parser import parse_receipt_image
from receipt_agent.legal_check import check_legal
from receipt_agent.db import init_receipt_db, save_receipt, get_all_receipts, get_receipt_count


# ══════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("yorglass-mcp")


# ══════════════════════════════════════════════════════════════════════
# GLOBAL STATE - startup() ile doldurulur
# ══════════════════════════════════════════════════════════════════════
api_key = ""
sql_tables = {}
sql_relationships = []
bapi_metadata = {}
sql_rag = None
bapi_rag = None
ik_rag = None
mock_db_conn = None
receipt_db_conn = None


# ══════════════════════════════════════════════════════════════════════
# MCP SERVER
# ══════════════════════════════════════════════════════════════════════
mcp = FastMCP("yorglass-sap")


def startup():
    """Tum kaynaklari yukler: API key, RAG motorlari, metadata, veritabanlari."""
    global api_key, sql_tables, sql_relationships, bapi_metadata
    global sql_rag, bapi_rag, ik_rag, mock_db_conn, receipt_db_conn

    # ── API Key ──
    api_key = _resolve_api_key()
    if not api_key:
        logger.error("OPENAI_API_KEY bulunamadi. .env dosyasini kontrol edin.")
        return
    logger.info("API key basariyla yuklendi.")

    # ── SQL Metadata + RAG ──
    sql_excel = PROJECT_ROOT / "sql_agent" / "sample_metadata.xlsx"
    if sql_excel.exists():
        tables, rels, error = load_metadata_from_excel(str(sql_excel))
        if error:
            logger.error(f"SQL metadata hatasi: {error}")
        else:
            sql_tables = tables
            sql_relationships = rels
            sql_rag = RAGEngine("mcp_sql_tables", api_key)
            index_tables_for_rag(sql_tables, sql_rag)
            logger.info(f"SQL: {len(sql_tables)} tablo, RAG: {sql_rag.get_document_count()} doc")
    else:
        logger.warning(f"SQL metadata bulunamadi: {sql_excel}")

    # ── BAPI Metadata + RAG ──
    bapi_excel = PROJECT_ROOT / "bapi_agent" / "bapi_sample_metadata.xlsx"
    if bapi_excel.exists():
        bapis, error = load_bapi_metadata_from_excel(str(bapi_excel))
        if error:
            logger.error(f"BAPI metadata hatasi: {error}")
        else:
            bapi_metadata = bapis
            bapi_rag = RAGEngine("mcp_bapi_functions", api_key)
            index_bapis_for_rag(bapi_metadata, bapi_rag)
            logger.info(f"BAPI: {len(bapi_metadata)} BAPI, RAG: {bapi_rag.get_document_count()} doc")
    else:
        logger.warning(f"BAPI metadata bulunamadi: {bapi_excel}")

    # ── IK Dokuman + RAG ──
    ik_doc_path = get_default_document_path()
    if Path(ik_doc_path).exists():
        chunks = load_and_chunk_docx(ik_doc_path)
        ik_rag = RAGEngine("mcp_ik_documents", api_key)
        ik_rag.index_documents(chunks)
        logger.info(f"IK: {len(chunks)} chunk, RAG: {ik_rag.get_document_count()} doc")
    else:
        logger.warning(f"IK dokumani bulunamadi: {ik_doc_path}")

    # ── Mock DB (SD/MM) ──
    mock_db_conn = init_mock_db()
    logger.info("Mock SQLite DB baslatildi (9 tablo, 237 kayit)")

    # ── Receipt DB ──
    receipt_db_conn = init_receipt_db()
    logger.info("Fis veritabani baslatildi.")

    logger.info("=== Yorglass MCP Server hazir ===")


# ══════════════════════════════════════════════════════════════════════
# TOOL 1: SAP SQL QUERY
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
def sap_sql_query(question: str, execute: bool = True) -> str:
    """
    Dogal dilden SAP Open SQL sorgusu uretir ve mock veritabaninda calistirir.

    RAG tabanli vektor arama ile ilgili SAP tablolarini bulur,
    ABAP 7.40+ Open SQL syntax'inda sorgu uretir.
    execute=True ise sorguyu Yorglass mock DB'de (9 tablo, 237 kayit) calistirir.

    Args:
        question: Turkce dogal dil sorusu.
                  Ornekler: "Tum malzemeleri listele",
                  "Stoku 100'den fazla olan malzemeler",
                  "Hangi tedarikci hangi malzemeyi sagliyor?"
        execute: True ise sorguyu mock DB'de calistirip sonuclari dondurur.
    """
    if not sql_tables:
        return "Hata: SQL metadata yuklenemedi."

    response_text, used_tables = generate_sql(
        question, sql_tables, sql_relationships,
        chat_history=[], rag_engine=sql_rag,
    )

    parts = [response_text]

    if execute:
        sap_sql = extract_sql_block(response_text)
        if sap_sql:
            sqlite_sql = convert_sap_to_sqlite(sap_sql)
            parts.append(f"\n--- SQLite Cevirisi ---\n{sqlite_sql}")

            if sqlite_sql and mock_db_conn:
                df, error = execute_query(sqlite_sql, mock_db_conn)
                if error:
                    parts.append(f"\nSorgu Hatasi: {error}")
                elif df is not None and not df.empty:
                    parts.append(f"\n--- Sonuclar ({len(df)} kayit) ---")
                    try:
                        parts.append(df.to_markdown(index=False))
                    except ImportError:
                        parts.append(df.to_string(index=False))
                elif df is not None:
                    parts.append("\nSorgu basarili, 0 kayit dondurdu.")
        else:
            parts.append("\n(Yanit icinde SQL blogu bulunamadi)")

    if used_tables:
        parts.append(f"\nKullanilan tablolar: {', '.join(used_tables)}")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# TOOL 2: BAPI LOOKUP
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
def bapi_lookup(question: str) -> str:
    """
    SAP BAPI onerisi ve parametre doldurma rehberi.

    Yapilmak istenen isleme gore uygun BAPI'yi bulur,
    parametrelerini ve ABAP kod ornegini gosterir.

    Args:
        question: Yapilmak istenen islem aciklamasi.
                  Ornekler: "Malzeme olusturmak istiyorum",
                  "Satin alma siparisi acmak istiyorum",
                  "Tedarikci bilgilerini okumak istiyorum"
    """
    if not bapi_metadata:
        return "Hata: BAPI metadata yuklenemedi."

    response_text, used_bapis = generate_bapi_response(
        question, bapi_metadata,
        chat_history=[], rag_engine=bapi_rag,
    )

    parts = [response_text]

    if used_bapis:
        parts.append(f"\nKullanilan BAPI'ler: {', '.join(used_bapis)}")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# TOOL 3: HR POLICY SEARCH
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
def hr_policy_search(question: str) -> str:
    """
    Yorglass IK prosedur dokumani uzerinde RAG tabanli soru-cevap.

    Yillik izin, saglik raporu, fazla mesai, disiplin proseduru,
    performans degerlendirme, uzaktan calisma, is guvenligi,
    kidem tazminati gibi konularda sirket politikalarini arar.

    Args:
        question: IK ile ilgili Turkce soru.
                  Ornekler: "Yillik izin hakki kac gun?",
                  "Fazla mesai ucreti nasil hesaplanir?",
                  "Evlilik izni kac gun?"
    """
    if not ik_rag:
        return "Hata: IK dokumani yuklenemedi."

    response_text, sources = generate_ik_response(
        question, rag_engine=ik_rag, chat_history=[],
    )

    parts = [response_text]

    if sources:
        parts.append("\n--- Kaynaklar ---")
        for i, src in enumerate(sources, 1):
            score_pct = int(src.get("score", 0) * 100)
            parts.append(
                f"{i}. [{src['section_title']}] "
                f"(benzerlik: %{score_pct}) "
                f"- {src['source_file']}"
            )

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# TOOL 4: RECEIPT SCAN
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
def receipt_scan(image_path: str = "", image_base64: str = "", file_type: str = "jpeg", save: bool = True) -> str:
    """
    Fis gorselini GPT-4o Vision ile okuyup yapilandirilmis veri cikarir.

    Dosya yolu VEYA base64 kodlanmis gorsel kabul eder.
    OCR ile isletme adi, vergi no, tarih, tutar, KDV orani ve
    kalem kalem urun detaylarini cikarir.
    Alkol/sigara fisleri yasal olarak masraf kaydedilemez.

    Args:
        image_path: Fis gorselinin dosya yolu (ornek: "C:/Users/foto/fis.jpg").
                    Bu parametre tercih edilir - dosyayi dogrudan okur.
        image_base64: Alternatif: Base64 kodlanmis gorsel verisi.
        file_type: Gorsel formati - "jpeg", "jpg" veya "png".
        save: True ise okunan fisi veritabanina kaydeder.
    """
    # Gorsel verisini al: dosya yolu veya base64
    if image_path:
        img_path = Path(image_path)
        if not img_path.exists():
            return f"Hata: Dosya bulunamadi: {image_path}"
        try:
            image_bytes = img_path.read_bytes()
            # Dosya uzantisindan file_type belirle
            ext = img_path.suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg", "png"):
                file_type = ext
        except Exception as e:
            return f"Dosya okuma hatasi: {e}"
    elif image_base64:
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return f"Base64 cozme hatasi: {e}"
    else:
        return "Hata: image_path veya image_base64 parametrelerinden biri gerekli."

    result = parse_receipt_image(image_bytes, file_type)

    if "_error" in result:
        error_msg = result.pop("_error")
        parts = [f"OCR Uyarisi: {error_msg}"]
    else:
        parts = ["Fis basariyla okundu."]

    # Fis verilerini formatla
    parts.append("\n--- Fis Verileri ---")
    field_labels = {
        "isletme_adi": "Isletme Adi",
        "adres": "Adres",
        "vergi_no": "VKN/TCKN",
        "vergi_dairesi": "Vergi Dairesi",
        "tarih": "Tarih",
        "saat": "Saat",
        "fis_no": "Fis No",
        "tutar": "Tutar (TL)",
        "kdv_orani": "KDV Orani (%)",
        "fis_turu": "Fis Turu",
    }
    for key, label in field_labels.items():
        parts.append(f"  {label}: {result.get(key, 'N/A')}")

    # Kalem detaylari
    kalemler = result.get("kalemler", [])
    if kalemler:
        parts.append("\n--- Kalem Detaylari ---")
        parts.append(f"  {'Urun':<30} {'Adet':>5} {'Birim':>10} {'Toplam':>10}")
        parts.append(f"  {'-'*30} {'-'*5} {'-'*10} {'-'*10}")
        for item in kalemler:
            parts.append(
                f"  {item['urun']:<30} {item['adet']:>5.0f} "
                f"{item['birim_fiyat']:>9.2f} {item['toplam']:>9.2f}"
            )

    # Yasal kontrol
    is_legal, legal_reason = check_legal(result.get("fis_turu", "diger"))
    if not is_legal:
        parts.append(f"\n*** YASAL UYARI: {legal_reason}")
        parts.append("Bu fis masraf olarak KAYDEDILEMEZ.")
        save = False

    # DB'ye kaydet
    if save and receipt_db_conn:
        try:
            record_id = save_receipt(receipt_db_conn, result)
            parts.append(f"\nVeritabanina kaydedildi (ID: {record_id})")
        except Exception as e:
            parts.append(f"\nKayit hatasi: {e}")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# TOOL 5: RECEIPT HISTORY
# ══════════════════════════════════════════════════════════════════════


@mcp.tool()
def receipt_history(limit: int = 50) -> str:
    """
    Daha once okutulan ve kaydedilen fisleri listeler.

    Veritabanindaki tum aktif fisleri isletme adi, tarih,
    tutar, tur ve kayit zamani bilgileriyle dondurur.

    Args:
        limit: Maksimum fis sayisi (varsayilan: 50).
    """
    if not receipt_db_conn:
        return "Hata: Fis veritabani baslatilmadi."

    count = get_receipt_count(receipt_db_conn)

    if count == 0:
        return "Veritabaninda kayitli fis bulunmuyor."

    df = get_all_receipts(receipt_db_conn)

    if df.empty:
        return "Aktif fis bulunamadi."

    if len(df) > limit:
        df = df.head(limit)

    parts = [
        f"Toplam aktif fis: {count}",
        f"Gosterilen: {len(df)} fis",
        "",
    ]

    try:
        parts.append(df.to_markdown(index=False))
    except ImportError:
        parts.append(df.to_string(index=False))

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    startup()
    mcp.run(transport="stdio")
