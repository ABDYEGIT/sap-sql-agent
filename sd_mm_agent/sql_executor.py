"""
SD/MM Agent - SAP Open SQL → SQLite Cevirici ve Calistirici.

SAP Open SQL (ABAP 7.40+ syntax) sorgusunu SQLite'a uyumlu
hale cevirir ve mock veritabaninda calistirir.

CEVIRME KURALLARI:
1. tablo~alan         → tablo.alan       (SAP field notation)
2. INTO TABLE @DATA() → kaldirilir       (SAP internal table)
3. Sondaki nokta (.)  → kaldirilir       (ABAP statement sonu)
4. ASCENDING          → ASC              (siralama)
5. DESCENDING         → DESC             (siralama)
6. UP TO N ROWS       → LIMIT N          (satir siniri)
7. INNER JOIN ON      → ayni kalir       (SQLite destekler)
"""
import re
import sqlite3

import pandas as pd


# ══════════════════════════════════════════════════════════════════════
# SAP OPEN SQL → SQLITE SQL CEVIRICI
# ══════════════════════════════════════════════════════════════════════
# SAP Open SQL, standart SQL'den farkli bazi syntax kurallarina sahiptir.
# Ornegin: tablo~alan (tablo.alan yerine), INTO TABLE @DATA(...) ifadesi,
# ve satir sonunda nokta (.) karakteri.
# Bu fonksiyon bu farkliliklari SQLite'a uyumlu hale cevirir.
# ══════════════════════════════════════════════════════════════════════


def convert_sap_to_sqlite(sap_sql: str) -> str:
    """
    SAP Open SQL sorgusunu SQLite SQL'e cevirir.

    ── SAP → SQLITE CEVIRME ADIMLARI ──
    Her adim sirayla uygulanir.

    Args:
        sap_sql: SAP Open SQL sorgusu
            Ornek: "SELECT mara~matnr mara~maktx
                    FROM mara
                    INTO TABLE @DATA(lt_result)."

    Returns:
        SQLite uyumlu SQL sorgusu
            Ornek: "SELECT mara.matnr, mara.maktx
                    FROM mara"
    """
    if not sap_sql or not sap_sql.strip():
        return ""

    sql = sap_sql.strip()

    # ── ADIM 1: Sondaki noktayi kaldir (ABAP statement sonu) ──
    # ABAP'ta her ifade noktayla biter: SELECT ... FROM ... .
    if sql.endswith("."):
        sql = sql[:-1].strip()

    # ── ADIM 2: INTO TABLE @DATA(...) ifadesini kaldir ──
    # SAP Open SQL'de sonuc ic tabloya atanir, SQLite'da buna gerek yok
    # Ornek: "INTO TABLE @DATA(lt_mara)" → kaldirilir
    sql = re.sub(
        r"\s+INTO\s+TABLE\s+@DATA\s*\([^)]*\)",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # ── ADIM 2b: INTO @DATA(...) ifadesini de kaldir (tek satir) ──
    sql = re.sub(
        r"\s+INTO\s+@DATA\s*\([^)]*\)",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # ── ADIM 2c: INTO (...) basit formunu da kaldir ──
    sql = re.sub(
        r"\s+INTO\s+\([^)]*\)",
        "",
        sql,
        flags=re.IGNORECASE
    )

    # ── ADIM 3: tablo~alan → tablo.alan (SAP field notation) ──
    # SAP'ta tablo ve alan arasinda ~ kullanilir
    # Ornek: mara~matnr → mara.matnr
    sql = sql.replace("~", ".")

    # ── ADIM 4: ASCENDING → ASC, DESCENDING → DESC ──
    sql = re.sub(r"\bASCENDING\b", "ASC", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\bDESCENDING\b", "DESC", sql, flags=re.IGNORECASE)

    # ── ADIM 5: UP TO N ROWS → LIMIT N ──
    # SAP: SELECT ... UP TO 10 ROWS
    # SQLite: SELECT ... LIMIT 10
    up_to_match = re.search(r"\bUP\s+TO\s+(\d+)\s+ROWS\b", sql, re.IGNORECASE)
    if up_to_match:
        limit_n = up_to_match.group(1)
        sql = re.sub(r"\bUP\s+TO\s+\d+\s+ROWS\b", "", sql, flags=re.IGNORECASE)
        # LIMIT'i sorgu sonuna ekle
        sql = sql.strip() + f" LIMIT {limit_n}"

    # ── ADIM 6: SELECT sonrasi virgul ekleme ──
    # SAP Open SQL'de alan listesinde virgul olmayabilir
    # Ornek: SELECT matnr maktx FROM mara → SELECT matnr, maktx FROM mara
    sql = _fix_select_commas(sql)

    # ── ADIM 7: Fazla bosluklari temizle ──
    sql = re.sub(r"\s+", " ", sql).strip()

    return sql


def _fix_select_commas(sql: str) -> str:
    """
    SELECT ile FROM arasindaki alan listesine virgul ekler.

    SAP Open SQL'de alan listesinde virgul kullanilmaz:
        SELECT matnr maktx meins FROM mara
    SQLite'da virgul gerekir:
        SELECT matnr, maktx, meins FROM mara

    Ancak dikkat: tablo.alan alias gibi ifadeler korunmali.
    """
    # SELECT ... FROM ... kismini bul
    select_match = re.match(
        r"(SELECT\s+(?:DISTINCT\s+)?)(.*?)(\s+FROM\s+)",
        sql,
        re.IGNORECASE | re.DOTALL
    )

    if not select_match:
        return sql

    prefix = select_match.group(1)    # "SELECT " veya "SELECT DISTINCT "
    fields_part = select_match.group(2)  # Alan listesi
    from_part = select_match.group(3)  # " FROM "
    rest = sql[select_match.end():]     # FROM sonrasi

    # Zaten virgul varsa dokunma
    if "," in fields_part:
        return sql

    # * varsa dokunma
    if fields_part.strip() == "*":
        return sql

    # COUNT, SUM, AVG gibi fonksiyonlar varsa dikkatli ol
    if re.search(r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(", fields_part, re.IGNORECASE):
        return sql

    # Alanlari boslukla ayir (tablo.alan veya alan olabilir)
    # Ancak "AS alias" gibi ifadeleri korumaliyiz
    tokens = fields_part.split()

    if len(tokens) <= 1:
        return sql

    # Token'lari analiz et: alan AS alias veya sadece alan
    fixed_fields = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Sonraki token AS mi?
        if i + 1 < len(tokens) and tokens[i + 1].upper() == "AS":
            if i + 2 < len(tokens):
                fixed_fields.append(f"{token} AS {tokens[i + 2]}")
                i += 3
            else:
                fixed_fields.append(token)
                i += 1
        else:
            fixed_fields.append(token)
            i += 1

    return prefix + ", ".join(fixed_fields) + from_part + rest


# ══════════════════════════════════════════════════════════════════════
# SQLITE SORGU CALISTIRICI
# ══════════════════════════════════════════════════════════════════════
# Cevrilen SQL sorgusunu SQLite veritabaninda calistirir
# ve sonuclari pandas DataFrame olarak dondurur.
# ══════════════════════════════════════════════════════════════════════


def execute_query(sqlite_sql: str, db_conn: sqlite3.Connection):
    """
    SQLite SQL sorgusunu calistirir ve sonuclari DataFrame olarak dondurur.

    ── MOCK DB UZERINDE SORGU CALISTIRMA ──
    SAP Open SQL → SQLite'a cevrilen sorgu burada calistirilir.
    Sonuclar pandas DataFrame formatinda dondurulur
    ve Streamlit'te st.dataframe() ile gosterilir.

    Args:
        sqlite_sql: SQLite uyumlu SQL sorgusu
        db_conn: SQLite veritabani baglantisi

    Returns:
        (pandas.DataFrame, None) - Basarili ise
        (None, str) - Hata mesaji ise
    """
    if not sqlite_sql or not sqlite_sql.strip():
        return None, "Bos SQL sorgusu"

    try:
        # Sorguyu calistir ve DataFrame olarak oku
        df = pd.read_sql_query(sqlite_sql, db_conn)
        return df, None
    except Exception as e:
        return None, f"SQLite sorgu hatasi: {str(e)}"
