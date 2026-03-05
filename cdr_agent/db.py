"""
Teknik Resim (CDR) Agent - SQLite Veritabani Yonetimi.

Analiz edilen cam teknik resim verilerini kalici SQLite dosyasinda saklar.

Tablo: TEKNIK_RESIMLER
  - id (otomatik artan)
  - musteri_adi, siparis_no, parca_adi
  - en_mm, boy_mm, kalinlik_mm
  - cam_tipi, adet
  - kenar_isleme, delik_sayisi
  - notlar
  - olusturma_zamani (otomatik)
  - durum (AKTIF/PASIF)

DB Konumu: cdr_agent/designs.db
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ── DB dosya yolu ──
DB_PATH = Path(__file__).resolve().parent / "designs.db"


# ══════════════════════════════════════════════════════════════════════
# VERITABANI BASLAT
# ══════════════════════════════════════════════════════════════════════


def init_cdr_db() -> sqlite3.Connection:
    """
    Teknik resim veritabanini baslatir. Yoksa olusturur.

    Returns:
        sqlite3.Connection
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TEKNIK_RESIMLER (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_adi TEXT,
            siparis_no TEXT,
            parca_adi TEXT,
            en_mm INTEGER,
            boy_mm INTEGER,
            kalinlik_mm INTEGER,
            cam_tipi TEXT,
            adet INTEGER DEFAULT 1,
            kenar_isleme TEXT DEFAULT 'belirtilmemis',
            delik_sayisi INTEGER DEFAULT 0,
            notlar TEXT DEFAULT '',
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            durum TEXT DEFAULT 'AKTIF'
        )
    """)

    conn.commit()
    return conn


def get_cdr_db() -> sqlite3.Connection:
    """
    CDR DB baglantisini dondurur (session state'te cache'lenir).
    """
    if "cdr_db_conn" not in st.session_state or st.session_state["cdr_db_conn"] is None:
        st.session_state["cdr_db_conn"] = init_cdr_db()
    return st.session_state["cdr_db_conn"]


# ══════════════════════════════════════════════════════════════════════
# CRUD ISLEMLERI
# ══════════════════════════════════════════════════════════════════════


def save_design(conn: sqlite3.Connection, data: dict) -> int:
    """
    Teknik resim verisini veritabanina kaydeder.

    Args:
        conn: SQLite baglantisi
        data: Parsed teknik resim verisi dict'i

    Returns:
        int: Kaydedilen kaydin ID'si
    """
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO TEKNIK_RESIMLER (
            musteri_adi, siparis_no, parca_adi,
            en_mm, boy_mm, kalinlik_mm,
            cam_tipi, adet, kenar_isleme, delik_sayisi, notlar
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("musteri_adi", ""),
        data.get("siparis_no", ""),
        data.get("parca_adi", ""),
        int(data.get("en_mm", 0)),
        int(data.get("boy_mm", 0)),
        int(data.get("kalinlik_mm", 0)),
        data.get("cam_tipi", "diger"),
        int(data.get("adet", 1)),
        data.get("kenar_isleme", "belirtilmemis"),
        int(data.get("delik_sayisi", 0)),
        data.get("notlar", ""),
    ))

    conn.commit()
    return cursor.lastrowid


def get_all_designs(conn: sqlite3.Connection) -> pd.DataFrame:
    """Tum aktif teknik resim kayitlarini DataFrame olarak dondurur."""
    try:
        df = pd.read_sql_query(
            "SELECT * FROM TEKNIK_RESIMLER WHERE durum = 'AKTIF' ORDER BY olusturma_zamani DESC",
            conn
        )
        return df
    except Exception:
        return pd.DataFrame()


def get_design_count(conn: sqlite3.Connection) -> int:
    """Aktif teknik resim sayisini dondurur."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM TEKNIK_RESIMLER WHERE durum = 'AKTIF'")
        return cursor.fetchone()[0]
    except Exception:
        return 0
