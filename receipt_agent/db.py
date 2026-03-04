"""
Fis Okuyucu Agent - SQLite Veritabani Yonetimi.

Okunan fis verilerini kalici olarak SQLite dosyasinda saklar.
SD/MM Agent'in mock DB'sinden farkli olarak bu DB dosya-tabanlidir
cunku fis kayitlari kalici olmalidir.

Tablo: FISLER
  - id (otomatik artan)
  - isletme_adi, adres, vergi_no, vergi_dairesi
  - tarih, saat, fis_no
  - tutar, kdv_orani
  - fis_turu
  - olusturma_zamani (otomatik)
  - durum (AKTIF/PASIF)

DB Konumu: receipt_agent/receipts.db
"""
import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ── DB dosya yolu ──
# Streamlit Cloud'da yazma izni olan tek yer /tmp veya cwd'dir
# Lokalde receipt_agent/ klasorunde saklanir
DB_PATH = Path(__file__).resolve().parent / "receipts.db"


# ══════════════════════════════════════════════════════════════════════
# VERITABANI BASLAT - Tablo olustur (yoksa)
# ══════════════════════════════════════════════════════════════════════


def init_receipt_db() -> sqlite3.Connection:
    """
    Fis veritabanini baslatir. Yoksa olusturur.

    ── KALICI SQLITE DB ──
    In-memory degil, dosya-tabanli. Fis kayitlari oturum
    kapandiktan sonra da saklanir.

    Returns:
        sqlite3.Connection
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS FISLER (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isletme_adi TEXT,
            adres TEXT,
            vergi_no TEXT,
            vergi_dairesi TEXT,
            tarih TEXT,
            saat TEXT,
            fis_no TEXT,
            tutar REAL,
            kdv_orani REAL,
            fis_turu TEXT,
            kalemler TEXT DEFAULT '[]',
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            durum TEXT DEFAULT 'AKTIF'
        )
    """)

    # Mevcut tabloya kalemler sutunu ekle (eski DB uyumlulugu)
    try:
        cursor.execute("ALTER TABLE FISLER ADD COLUMN kalemler TEXT DEFAULT '[]'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Sutun zaten var

    conn.commit()
    return conn


def get_receipt_db() -> sqlite3.Connection:
    """
    Fis DB baglantisini dondurur (session state'te cache'lenir).

    ── SESSION STATE PATTERN ──
    Ilk cagirida init_receipt_db() cagirilir,
    sonraki cagrilarda mevcut baglanti dondurulur.
    """
    if "receipt_db_conn" not in st.session_state or st.session_state["receipt_db_conn"] is None:
        st.session_state["receipt_db_conn"] = init_receipt_db()
    return st.session_state["receipt_db_conn"]


# ══════════════════════════════════════════════════════════════════════
# CRUD ISLEMLERI
# ══════════════════════════════════════════════════════════════════════


def save_receipt(conn: sqlite3.Connection, data: dict) -> int:
    """
    Fis verisini veritabanina kaydeder.

    Args:
        conn: SQLite baglantisi
        data: Fis verisi dict'i:
            {
                "isletme_adi": "STARBUCKS COFFEE",
                "adres": "...",
                "vergi_no": "7690310116",
                "vergi_dairesi": "Bogazici Kurumlar VD",
                "tarih": "18.01.2025",
                "saat": "11:58",
                "fis_no": "0030",
                "tutar": 95.00,
                "kdv_orani": 10,
                "fis_turu": "yemek"
            }

    Returns:
        int: Kaydedilen fisin ID'si
    """
    cursor = conn.cursor()

    # Kalemler listesini JSON string'e cevir
    kalemler = data.get("kalemler", [])
    if isinstance(kalemler, list):
        kalemler_json = json.dumps(kalemler, ensure_ascii=False)
    else:
        kalemler_json = "[]"

    cursor.execute("""
        INSERT INTO FISLER (
            isletme_adi, adres, vergi_no, vergi_dairesi,
            tarih, saat, fis_no, tutar, kdv_orani, fis_turu, kalemler
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("isletme_adi", ""),
        data.get("adres", ""),
        data.get("vergi_no", ""),
        data.get("vergi_dairesi", ""),
        data.get("tarih", ""),
        data.get("saat", ""),
        data.get("fis_no", ""),
        float(data.get("tutar", 0)),
        float(data.get("kdv_orani", 0)),
        data.get("fis_turu", "diger"),
        kalemler_json,
    ))

    conn.commit()
    return cursor.lastrowid


def get_all_receipts(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Tum kayitli fisleri DataFrame olarak dondurur.

    Returns:
        pd.DataFrame: Tum fis kayitlari (id, isletme_adi, tarih, tutar, fis_turu, ...)
    """
    try:
        df = pd.read_sql_query(
            "SELECT * FROM FISLER WHERE durum = 'AKTIF' ORDER BY olusturma_zamani DESC",
            conn
        )
        return df
    except Exception:
        return pd.DataFrame()


def get_receipt_count(conn: sqlite3.Connection) -> int:
    """Aktif fis sayisini dondurur."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM FISLER WHERE durum = 'AKTIF'")
        return cursor.fetchone()[0]
    except Exception:
        return 0
