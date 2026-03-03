"""
SD/MM Agent - SQLite Mock Veritabani.

Yorglass cam uretim firmasina ait gercekci SAP verilerini
SQLite veritabaninda olusturur ve yonetir.

Tablolar mevcut sql_agent/create_sample.py'deki SAP tablo
yapisina birebir uyumludur:
  MARA, MARC, MARD, MAKT, ZMM_T_RENK, ZMM_T_KALITE, EKKO, EKPO, LFA1

Mock veriler Yorglass baglami ile olusturulmustur:
  - Cam levha, temperli cam, lamine cam, ayna, aksesuar urunleri
  - Cam hammadde tedarikcileri
  - Gercekci stok ve siparis verileri
"""
import sqlite3

import streamlit as st


# ══════════════════════════════════════════════════════════════════════
# MOCK VERITABANI OLUSTURMA
# ══════════════════════════════════════════════════════════════════════
# Bu fonksiyon SD/MM Agent acildiginda bir kez calisir.
# SQLite in-memory veritabaninda 9 SAP tablosu olusturur ve
# Yorglass'a ozgu gercekci veriler ekler.
# ══════════════════════════════════════════════════════════════════════


def _pad_matnr(n: int) -> str:
    """Malzeme numarasini SAP formatina cevirir (18 karakter, basa sifir)."""
    return str(n).zfill(18)


def _pad_lifnr(n: int) -> str:
    """Tedarikci numarasini SAP formatina cevirir (10 karakter, basa sifir)."""
    return str(n).zfill(10)


def _pad_ebeln(n: int) -> str:
    """Satin alma belge numarasini SAP formatina cevirir (10 karakter)."""
    return str(n).zfill(10)


def init_mock_db() -> sqlite3.Connection:
    """
    SQLite mock veritabanini olusturur ve Yorglass verileriyle doldurur.

    Returns:
        sqlite3.Connection - Veritabani baglantisi

    ── MOCK DB: Gercek SAP tablolariyla ayni yapida SQLite tabloları ──
    Bu sayede SAP Open SQL sorgulari (SQLite'a cevrildikten sonra)
    dogrudan bu DB uzerinde calistirilabilir.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()

    # ────────────────────────────────────────
    # TABLO 1: MARA - Malzeme Ana Verileri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MARA (
            MATNR TEXT PRIMARY KEY,
            MTART TEXT,
            MATKL TEXT,
            MEINS TEXT,
            MAKTX TEXT
        )
    """)

    # Yorglass cam urunleri - 25 malzeme
    mara_data = [
        (_pad_matnr(1), "FERT", "CAM01", "AD", "Duz Cam 4mm Seffaf"),
        (_pad_matnr(2), "FERT", "CAM01", "AD", "Duz Cam 6mm Seffaf"),
        (_pad_matnr(3), "FERT", "CAM01", "AD", "Duz Cam 8mm Seffaf"),
        (_pad_matnr(4), "FERT", "CAM02", "AD", "Temperli Cam 6mm Seffaf"),
        (_pad_matnr(5), "FERT", "CAM02", "AD", "Temperli Cam 8mm Seffaf"),
        (_pad_matnr(6), "FERT", "CAM02", "AD", "Temperli Cam 10mm Seffaf"),
        (_pad_matnr(7), "FERT", "CAM03", "AD", "Lamine Cam 6+6mm Seffaf"),
        (_pad_matnr(8), "FERT", "CAM03", "AD", "Lamine Cam 8+8mm Seffaf"),
        (_pad_matnr(9), "FERT", "CAM04", "AD", "Ayna 4mm Standart"),
        (_pad_matnr(10), "FERT", "CAM04", "AD", "Ayna 6mm Standart"),
        (_pad_matnr(11), "FERT", "CAM05", "AD", "Buzlu Cam 6mm"),
        (_pad_matnr(12), "FERT", "CAM05", "AD", "Desenli Cam 4mm"),
        (_pad_matnr(13), "FERT", "CAM01", "AD", "Duz Cam 4mm Bronz"),
        (_pad_matnr(14), "FERT", "CAM01", "AD", "Duz Cam 6mm Bronz"),
        (_pad_matnr(15), "FERT", "CAM02", "AD", "Temperli Cam 6mm Bronz"),
        (_pad_matnr(16), "FERT", "CAM06", "AD", "Isicam 4+16+4 Seffaf"),
        (_pad_matnr(17), "FERT", "CAM06", "AD", "Isicam 6+16+6 Seffaf"),
        (_pad_matnr(18), "ROH", "HAM01", "KG", "Float Cam Hammadde"),
        (_pad_matnr(19), "ROH", "HAM01", "KG", "PVB Film (Lamine icin)"),
        (_pad_matnr(20), "ROH", "HAM02", "LT", "Cam Boyasi Seffaf"),
        (_pad_matnr(21), "ROH", "HAM02", "LT", "Cam Boyasi Bronz"),
        (_pad_matnr(22), "HALB", "AKS01", "AD", "Cam Kenar Profili"),
        (_pad_matnr(23), "HALB", "AKS01", "AD", "Cam Tutamak Aksesuar"),
        (_pad_matnr(24), "HALB", "AKS02", "AD", "Spacer (Isicam Aralayici)"),
        (_pad_matnr(25), "FERT", "CAM02", "AD", "Temperli Cam 12mm Seffaf"),
    ]
    cursor.executemany("INSERT INTO MARA VALUES (?, ?, ?, ?, ?)", mara_data)

    # ────────────────────────────────────────
    # TABLO 2: MARC - Malzeme Tesis Verileri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MARC (
            MATNR TEXT,
            WERKS TEXT,
            LGORT TEXT,
            DISMM TEXT,
            DISPO TEXT,
            PRIMARY KEY (MATNR, WERKS)
        )
    """)

    marc_data = []
    for i in range(1, 26):
        # Tesis 1000: Yorglass Merkez Fabrika
        lgort = "0001" if i >= 18 else "0002"  # Hammadde → 0001, Mamul → 0002
        dismm = "PD" if i >= 18 else "VB"  # Hammadde → MRP, Mamul → Tuketim bazli
        marc_data.append((_pad_matnr(i), "1000", lgort, dismm, "001"))
    cursor.executemany("INSERT INTO MARC VALUES (?, ?, ?, ?, ?)", marc_data)

    # ────────────────────────────────────────
    # TABLO 3: MARD - Malzeme Depo Verileri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MARD (
            MATNR TEXT,
            WERKS TEXT,
            LGORT TEXT,
            LABST REAL,
            INSME REAL,
            SPEME REAL,
            PRIMARY KEY (MATNR, WERKS, LGORT)
        )
    """)

    # Her malzeme icin 2 depo: 0001 (Hammadde Deposu), 0002 (Mamul Deposu)
    import random
    random.seed(42)  # Tekrarlanabilir sonuclar

    mard_data = []
    for i in range(1, 26):
        # Depo 0001 - Hammadde Deposu
        labst1 = round(random.uniform(50, 500), 2) if i >= 18 else round(random.uniform(0, 50), 2)
        insme1 = round(random.uniform(0, 20), 2)
        speme1 = round(random.uniform(0, 10), 2)
        mard_data.append((_pad_matnr(i), "1000", "0001", labst1, insme1, speme1))

        # Depo 0002 - Mamul Deposu
        labst2 = round(random.uniform(100, 1000), 2) if i < 18 else round(random.uniform(0, 30), 2)
        insme2 = round(random.uniform(0, 30), 2)
        speme2 = round(random.uniform(0, 5), 2)
        mard_data.append((_pad_matnr(i), "1000", "0002", labst2, insme2, speme2))

    cursor.executemany("INSERT INTO MARD VALUES (?, ?, ?, ?, ?, ?)", mard_data)

    # ────────────────────────────────────────
    # TABLO 4: MAKT - Malzeme Kisa Metinleri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MAKT (
            MATNR TEXT,
            SPRAS TEXT,
            MAKTX TEXT,
            PRIMARY KEY (MATNR, SPRAS)
        )
    """)

    # Turkce (T) ve Ingilizce (E) aciklamalar
    makt_tr_en = [
        (1, "Duz Cam 4mm Seffaf", "Flat Glass 4mm Clear"),
        (2, "Duz Cam 6mm Seffaf", "Flat Glass 6mm Clear"),
        (3, "Duz Cam 8mm Seffaf", "Flat Glass 8mm Clear"),
        (4, "Temperli Cam 6mm Seffaf", "Tempered Glass 6mm Clear"),
        (5, "Temperli Cam 8mm Seffaf", "Tempered Glass 8mm Clear"),
        (6, "Temperli Cam 10mm Seffaf", "Tempered Glass 10mm Clear"),
        (7, "Lamine Cam 6+6mm Seffaf", "Laminated Glass 6+6mm Clear"),
        (8, "Lamine Cam 8+8mm Seffaf", "Laminated Glass 8+8mm Clear"),
        (9, "Ayna 4mm Standart", "Mirror 4mm Standard"),
        (10, "Ayna 6mm Standart", "Mirror 6mm Standard"),
        (11, "Buzlu Cam 6mm", "Frosted Glass 6mm"),
        (12, "Desenli Cam 4mm", "Patterned Glass 4mm"),
        (13, "Duz Cam 4mm Bronz", "Flat Glass 4mm Bronze"),
        (14, "Duz Cam 6mm Bronz", "Flat Glass 6mm Bronze"),
        (15, "Temperli Cam 6mm Bronz", "Tempered Glass 6mm Bronze"),
        (16, "Isicam 4+16+4 Seffaf", "Insulated Glass 4+16+4 Clear"),
        (17, "Isicam 6+16+6 Seffaf", "Insulated Glass 6+16+6 Clear"),
        (18, "Float Cam Hammadde", "Float Glass Raw Material"),
        (19, "PVB Film (Lamine icin)", "PVB Film (For Lamination)"),
        (20, "Cam Boyasi Seffaf", "Glass Paint Clear"),
        (21, "Cam Boyasi Bronz", "Glass Paint Bronze"),
        (22, "Cam Kenar Profili", "Glass Edge Profile"),
        (23, "Cam Tutamak Aksesuar", "Glass Handle Accessory"),
        (24, "Spacer (Isicam Aralayici)", "Spacer (Insulated Glass)"),
        (25, "Temperli Cam 12mm Seffaf", "Tempered Glass 12mm Clear"),
    ]

    makt_data = []
    for num, tr_text, en_text in makt_tr_en:
        makt_data.append((_pad_matnr(num), "T", tr_text))
        makt_data.append((_pad_matnr(num), "E", en_text))
    cursor.executemany("INSERT INTO MAKT VALUES (?, ?, ?)", makt_data)

    # ────────────────────────────────────────
    # TABLO 5: ZMM_T_RENK - Malzeme Renkleri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ZMM_T_RENK (
            MATNR TEXT PRIMARY KEY,
            RENK TEXT,
            RENK_TANIMI TEXT
        )
    """)

    renk_data = [
        (_pad_matnr(1), "SF", "Seffaf"),
        (_pad_matnr(2), "SF", "Seffaf"),
        (_pad_matnr(3), "SF", "Seffaf"),
        (_pad_matnr(4), "SF", "Seffaf"),
        (_pad_matnr(5), "SF", "Seffaf"),
        (_pad_matnr(6), "SF", "Seffaf"),
        (_pad_matnr(7), "SF", "Seffaf"),
        (_pad_matnr(8), "SF", "Seffaf"),
        (_pad_matnr(9), "GU", "Gumus"),
        (_pad_matnr(10), "GU", "Gumus"),
        (_pad_matnr(11), "BZ", "Buzlu"),
        (_pad_matnr(13), "BR", "Bronz"),
        (_pad_matnr(14), "BR", "Bronz"),
        (_pad_matnr(15), "BR", "Bronz"),
        (_pad_matnr(16), "SF", "Seffaf"),
    ]
    cursor.executemany("INSERT INTO ZMM_T_RENK VALUES (?, ?, ?)", renk_data)

    # ────────────────────────────────────────
    # TABLO 6: ZMM_T_KALITE - Malzeme Kalite Siniflari
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ZMM_T_KALITE (
            MATNR TEXT PRIMARY KEY,
            KALITE_SINIFI TEXT,
            SON_KONTROL_TARIHI TEXT
        )
    """)

    kalite_data = []
    kalite_siniflari = ["A", "A", "A", "B", "A"]  # Cogunluk A sinifi
    for i in range(1, 26):
        sinif = kalite_siniflari[i % len(kalite_siniflari)]
        # Tarih formati: YYYYMMDD (SAP DATS formati)
        ay = str(((i * 3) % 12) + 1).zfill(2)
        gun = str(((i * 7) % 28) + 1).zfill(2)
        tarih = f"2025{ay}{gun}"
        kalite_data.append((_pad_matnr(i), sinif, tarih))
    cursor.executemany("INSERT INTO ZMM_T_KALITE VALUES (?, ?, ?)", kalite_data)

    # ────────────────────────────────────────
    # TABLO 7: LFA1 - Tedarikci Ana Verileri
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LFA1 (
            LIFNR TEXT PRIMARY KEY,
            NAME1 TEXT,
            ORT01 TEXT,
            LAND1 TEXT
        )
    """)

    lfa1_data = [
        (_pad_lifnr(1), "Sisecam A.S.", "Istanbul", "TR"),
        (_pad_lifnr(2), "Turkiye Sise ve Cam Fab.", "Mersin", "TR"),
        (_pad_lifnr(3), "Guardian Glass TR", "Kocaeli", "TR"),
        (_pad_lifnr(4), "AGC Flat Glass", "Ankara", "TR"),
        (_pad_lifnr(5), "Saint-Gobain Turkiye", "Istanbul", "TR"),
        (_pad_lifnr(6), "Pilkington TR", "Bursa", "TR"),
        (_pad_lifnr(7), "Kuraray PVB Film", "Izmir", "TR"),
    ]
    cursor.executemany("INSERT INTO LFA1 VALUES (?, ?, ?, ?)", lfa1_data)

    # ────────────────────────────────────────
    # TABLO 8: EKKO - Satin Alma Belge Basi
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EKKO (
            EBELN TEXT PRIMARY KEY,
            BUKRS TEXT,
            BSART TEXT,
            LIFNR TEXT,
            AEDAT TEXT
        )
    """)

    ekko_data = [
        (_pad_ebeln(4500000001), "1000", "NB", _pad_lifnr(1), "20250115"),
        (_pad_ebeln(4500000002), "1000", "NB", _pad_lifnr(1), "20250120"),
        (_pad_ebeln(4500000003), "1000", "NB", _pad_lifnr(2), "20250201"),
        (_pad_ebeln(4500000004), "1000", "NB", _pad_lifnr(3), "20250210"),
        (_pad_ebeln(4500000005), "1000", "NB", _pad_lifnr(4), "20250215"),
        (_pad_ebeln(4500000006), "1000", "NB", _pad_lifnr(5), "20250220"),
        (_pad_ebeln(4500000007), "1000", "NB", _pad_lifnr(6), "20250301"),
        (_pad_ebeln(4500000008), "1000", "NB", _pad_lifnr(7), "20250305"),
        (_pad_ebeln(4500000009), "1000", "NB", _pad_lifnr(1), "20250310"),
        (_pad_ebeln(4500000010), "1000", "NB", _pad_lifnr(2), "20250315"),
        (_pad_ebeln(4500000011), "1000", "NB", _pad_lifnr(3), "20250320"),
        (_pad_ebeln(4500000012), "1000", "NB", _pad_lifnr(5), "20250325"),
    ]
    cursor.executemany("INSERT INTO EKKO VALUES (?, ?, ?, ?, ?)", ekko_data)

    # ────────────────────────────────────────
    # TABLO 9: EKPO - Satin Alma Belge Kalemi
    # ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS EKPO (
            EBELN TEXT,
            EBELP TEXT,
            MATNR TEXT,
            MENGE REAL,
            MEINS TEXT,
            NETPR REAL,
            WERKS TEXT,
            PRIMARY KEY (EBELN, EBELP)
        )
    """)

    ekpo_data = [
        # Siparis 1 - Sisecam'dan float cam
        (_pad_ebeln(4500000001), "00010", _pad_matnr(18), 5000.0, "KG", 12.50, "1000"),
        (_pad_ebeln(4500000001), "00020", _pad_matnr(20), 200.0, "LT", 45.00, "1000"),
        (_pad_ebeln(4500000001), "00030", _pad_matnr(22), 500.0, "AD", 8.75, "1000"),
        # Siparis 2 - Sisecam'dan duz cam
        (_pad_ebeln(4500000002), "00010", _pad_matnr(1), 1000.0, "AD", 35.00, "1000"),
        (_pad_ebeln(4500000002), "00020", _pad_matnr(2), 800.0, "AD", 52.00, "1000"),
        # Siparis 3 - Turkiye Sise'den temperli cam
        (_pad_ebeln(4500000003), "00010", _pad_matnr(4), 300.0, "AD", 85.00, "1000"),
        (_pad_ebeln(4500000003), "00020", _pad_matnr(5), 200.0, "AD", 110.00, "1000"),
        (_pad_ebeln(4500000003), "00030", _pad_matnr(6), 150.0, "AD", 145.00, "1000"),
        # Siparis 4 - Guardian'dan lamine cam
        (_pad_ebeln(4500000004), "00010", _pad_matnr(7), 400.0, "AD", 175.00, "1000"),
        (_pad_ebeln(4500000004), "00020", _pad_matnr(8), 250.0, "AD", 220.00, "1000"),
        # Siparis 5 - AGC'den ayna
        (_pad_ebeln(4500000005), "00010", _pad_matnr(9), 600.0, "AD", 65.00, "1000"),
        (_pad_ebeln(4500000005), "00020", _pad_matnr(10), 400.0, "AD", 95.00, "1000"),
        # Siparis 6 - Saint-Gobain'den isicam
        (_pad_ebeln(4500000006), "00010", _pad_matnr(16), 200.0, "AD", 195.00, "1000"),
        (_pad_ebeln(4500000006), "00020", _pad_matnr(17), 150.0, "AD", 245.00, "1000"),
        (_pad_ebeln(4500000006), "00030", _pad_matnr(24), 1000.0, "AD", 3.50, "1000"),
        # Siparis 7 - Pilkington'dan buzlu cam
        (_pad_ebeln(4500000007), "00010", _pad_matnr(11), 500.0, "AD", 78.00, "1000"),
        (_pad_ebeln(4500000007), "00020", _pad_matnr(12), 300.0, "AD", 55.00, "1000"),
        # Siparis 8 - Kuraray'dan PVB film
        (_pad_ebeln(4500000008), "00010", _pad_matnr(19), 2000.0, "KG", 28.00, "1000"),
        # Siparis 9 - Sisecam'dan bronz cam
        (_pad_ebeln(4500000009), "00010", _pad_matnr(13), 700.0, "AD", 38.00, "1000"),
        (_pad_ebeln(4500000009), "00020", _pad_matnr(14), 500.0, "AD", 55.00, "1000"),
        (_pad_ebeln(4500000009), "00030", _pad_matnr(15), 300.0, "AD", 92.00, "1000"),
        # Siparis 10 - Turkiye Sise'den duz cam
        (_pad_ebeln(4500000010), "00010", _pad_matnr(3), 600.0, "AD", 68.00, "1000"),
        (_pad_ebeln(4500000010), "00020", _pad_matnr(25), 200.0, "AD", 180.00, "1000"),
        # Siparis 11 - Guardian'dan hammadde
        (_pad_ebeln(4500000011), "00010", _pad_matnr(18), 8000.0, "KG", 11.80, "1000"),
        (_pad_ebeln(4500000011), "00020", _pad_matnr(21), 150.0, "LT", 52.00, "1000"),
        # Siparis 12 - Saint-Gobain'den aksesuar
        (_pad_ebeln(4500000012), "00010", _pad_matnr(22), 1000.0, "AD", 7.90, "1000"),
        (_pad_ebeln(4500000012), "00020", _pad_matnr(23), 500.0, "AD", 15.50, "1000"),
        (_pad_ebeln(4500000012), "00030", _pad_matnr(24), 2000.0, "AD", 3.20, "1000"),
    ]
    cursor.executemany("INSERT INTO EKPO VALUES (?, ?, ?, ?, ?, ?, ?)", ekpo_data)

    conn.commit()
    return conn


def get_db_connection() -> sqlite3.Connection:
    """
    Mock veritabani baglantisini dondurur.

    ── SESSION STATE: Baglanti Streamlit oturumu boyunca saklanir ──
    Ilk cagirida init_mock_db() ile olusturulur,
    sonraki cagrilarda mevcut baglanti dondurulur.
    """
    if "sdmm_db_conn" not in st.session_state or st.session_state["sdmm_db_conn"] is None:
        st.session_state["sdmm_db_conn"] = init_mock_db()
    return st.session_state["sdmm_db_conn"]


def get_table_counts(conn: sqlite3.Connection) -> dict:
    """
    Her tablodaki kayit sayisini dondurur (sidebar'da gostermek icin).

    Returns:
        {"MARA": 25, "MARC": 25, "MARD": 50, ...}
    """
    tables = ["MARA", "MARC", "MARD", "MAKT", "ZMM_T_RENK", "ZMM_T_KALITE", "EKKO", "EKPO", "LFA1"]
    counts = {}
    cursor = conn.cursor()
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except Exception:
            counts[table] = 0
    return counts
