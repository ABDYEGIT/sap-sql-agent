"""
Fis Okuyucu Agent - Yasal Kontrol Modulu.

Masraf olarak girilemeyecek fis turlerini kontrol eder.
Turk vergi mevzuatina gore bazi harcamalar masraf olarak
gosterilemez (alkol, sigara/tutun urunleri vb.)

Engellenen Turler:
  - alkol: Alkolu icecek fisleri (bira, sarap, raki, viski vb.)
  - sigara: Tutun urunleri fisleri (sigara, puro, tutun vb.)
"""


# ══════════════════════════════════════════════════════════════════════
# YASAL OLARAK MASRAF GIRILEMEYECEK FIS TURLERI
# ══════════════════════════════════════════════════════════════════════
# Turk Vergi Mevzuati'na gore bu kategorilerdeki harcamalar
# sirket masrafi olarak gosterilemez.
# ══════════════════════════════════════════════════════════════════════

ENGELLENEN_TURLER = {
    "alkol": "Alkolu icecek fisleri yasal olarak masraf olarak girilemez. "
             "(193 sayili MOATUK - Alkol ve Tutun Kontrol Kanunu)",
    "sigara": "Sigara ve tutun urunleri fisleri yasal olarak masraf olarak girilemez. "
              "(193 sayili MOATUK - Alkol ve Tutun Kontrol Kanunu)",
}


def check_legal(fis_turu: str) -> tuple:
    """
    Fis turunun masraf olarak girilebilir olup olmadigini kontrol eder.

    ── YASAL KONTROL ──
    Alkol ve sigara/tutun urunleri masraf olarak girilemez.

    Args:
        fis_turu: Fis kategorisi (ornek: "yemek", "market", "alkol", "sigara")

    Returns:
        (True, "") → Masraf olarak girilebilir
        (False, "Aciklama mesaji") → ENGELLENDI, masraf girilemez
    """
    fis_turu_lower = fis_turu.strip().lower()

    if fis_turu_lower in ENGELLENEN_TURLER:
        return False, ENGELLENEN_TURLER[fis_turu_lower]

    return True, ""
