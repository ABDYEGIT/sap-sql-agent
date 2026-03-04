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


# ══════════════════════════════════════════════════════════════════════
# KALEM SEVIYESINDE YASAL KONTROL
# ══════════════════════════════════════════════════════════════════════
# Fis turu "market" olsa bile icindeki kalemlerde alkol/sigara olabilir.
# Bu durumda fis tamamen engellenmez, sadece yasadisi kalemler dusulur.
# ══════════════════════════════════════════════════════════════════════

ALKOL_ANAHTAR_KELIMELER = [
    "bira", "sarap", "raki", "viski", "vodka", "cin", "tekila",
    "likör", "likor", "kokteyl", "efes", "tuborg", "carlsberg",
    "bomonti", "miller", "beck", "heineken", "corona", "amstel",
    "guinness", "jack daniel", "johnnie walker", "chivas",
    "absolut", "smirnoff", "bacardi", "jagermeister", "jaegermeister",
    "baileys", "malibu", "campari", "martini", "aperol",
    "wine", "beer", "whiskey", "whisky", "brandy", "cognac",
    "champagne", "prosecco", "sangria", "mojito",
    "şarap", "bira", "rakı",
]

SIGARA_ANAHTAR_KELIMELER = [
    "sigara", "tutun", "tütün", "puro", "pipo",
    "marlboro", "camel", "parliament", "kent", "winston",
    "lucky strike", "chesterfield", "lm", "l&m",
    "muratti", "tekel", "samsun", "maltepe", "yeni harman",
    "tobacco", "cigarette",
]


def check_kalemler_legal(kalemler: list) -> dict:
    """
    Kalem listesindeki her urunu alkol/sigara acisindan kontrol eder.

    ── KALEM SEVIYESI YASAL KONTROL ──
    Her kalemin 'kategori' alanina (GPT tarafindan atanmis) veya
    urun adina bakarak engellenen kalemleri tespit eder.
    Engellenen kalemlerin tutarlari toplam tutardan dusulur.

    Args:
        kalemler: Kalem listesi [{"urun": "...", "adet": 1, "toplam": 10.0, "kategori": "normal"}, ...]

    Returns:
        {
            "engellenen_kalemler": [{"urun": "...", "toplam": 10.0, "sebep": "alkol"}, ...],
            "izinli_kalemler": [{"urun": "...", ...}, ...],
            "engellenen_toplam": 25.0,
            "has_engellenen": True/False,
        }
    """
    engellenen = []
    izinli = []

    for kalem in kalemler:
        urun = str(kalem.get("urun", "")).lower()
        kategori = str(kalem.get("kategori", "normal")).lower()
        toplam = float(kalem.get("toplam", 0))

        # Oncelik 1: GPT'nin atadigi kategori
        if kategori in ("alkol", "sigara"):
            engellenen.append({
                "urun": kalem.get("urun", ""),
                "toplam": toplam,
                "sebep": kategori,
            })
            continue

        # Oncelik 2: Urun adinda anahtar kelime kontrolu (fallback)
        blocked = False
        for kelime in ALKOL_ANAHTAR_KELIMELER:
            if kelime in urun:
                engellenen.append({
                    "urun": kalem.get("urun", ""),
                    "toplam": toplam,
                    "sebep": "alkol",
                })
                blocked = True
                break

        if not blocked:
            for kelime in SIGARA_ANAHTAR_KELIMELER:
                if kelime in urun:
                    engellenen.append({
                        "urun": kalem.get("urun", ""),
                        "toplam": toplam,
                        "sebep": "sigara",
                    })
                    blocked = True
                    break

        if not blocked:
            izinli.append(kalem)

    engellenen_toplam = sum(item["toplam"] for item in engellenen)

    return {
        "engellenen_kalemler": engellenen,
        "izinli_kalemler": izinli,
        "engellenen_toplam": engellenen_toplam,
        "has_engellenen": len(engellenen) > 0,
    }
