"""
Token Kullanim Takip Modulu.

Her LLM cagrisinin token tuketimini SQLite veritabaninda saklar.
Agent bazinda input/output token, model, maliyet gibi bilgileri tutar.

Tablo: TOKEN_USAGE
  - id, agent_adi, model, input_tokens, output_tokens,
    total_tokens, islem_turu, olusturma_zamani
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "token_usage.db"


def _get_conn() -> sqlite3.Connection:
    """Token DB baglantisi olusturur."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS TOKEN_USAGE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_adi TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            islem_turu TEXT DEFAULT '',
            olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def log_token_usage(
    agent_adi: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    islem_turu: str = "",
):
    """
    Bir LLM cagrisinin token kulanimini DB'ye kaydeder.

    Args:
        agent_adi: "Fis Okuyucu" veya "IK Asistani" gibi
        model: "gpt-4o-mini", "gpt-4o" gibi
        input_tokens: Girdi token sayisi (prompt)
        output_tokens: Cikti token sayisi (completion)
        total_tokens: Toplam token
        islem_turu: "OCR", "Soru-Cevap" gibi (opsiyonel)
    """
    conn = _get_conn()
    conn.execute(
        """INSERT INTO TOKEN_USAGE
           (agent_adi, model, input_tokens, output_tokens, total_tokens, islem_turu)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (agent_adi, model, input_tokens, output_tokens, total_tokens, islem_turu),
    )
    conn.commit()
    conn.close()


def get_token_summary() -> pd.DataFrame:
    """
    Agent bazinda token ozet tablosu dondurur.

    Returns:
        DataFrame: agent_adi, model, toplam_islem, toplam_input,
                   toplam_output, toplam_token
    """
    conn = _get_conn()
    df = pd.read_sql_query("""
        SELECT
            agent_adi AS "Agent",
            model AS "Model",
            COUNT(*) AS "Toplam Islem",
            SUM(input_tokens) AS "Input Token",
            SUM(output_tokens) AS "Output Token",
            SUM(total_tokens) AS "Toplam Token"
        FROM TOKEN_USAGE
        GROUP BY agent_adi, model
        ORDER BY SUM(total_tokens) DESC
    """, conn)
    conn.close()
    return df


def get_token_history(limit: int = 50) -> pd.DataFrame:
    """Son token kullanim kayitlarini dondurur."""
    conn = _get_conn()
    df = pd.read_sql_query(f"""
        SELECT
            agent_adi AS "Agent",
            model AS "Model",
            input_tokens AS "Input",
            output_tokens AS "Output",
            total_tokens AS "Toplam",
            islem_turu AS "Islem",
            olusturma_zamani AS "Zaman"
        FROM TOKEN_USAGE
        ORDER BY olusturma_zamani DESC
        LIMIT {limit}
    """, conn)
    conn.close()
    return df


def get_total_stats() -> dict:
    """Genel toplam istatistikleri dondurur."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COALESCE(SUM(input_tokens), 0),
            COALESCE(SUM(output_tokens), 0),
            COALESCE(SUM(total_tokens), 0),
            COUNT(*)
        FROM TOKEN_USAGE
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "total_input": row[0],
        "total_output": row[1],
        "total_tokens": row[2],
        "total_requests": row[3],
    }
