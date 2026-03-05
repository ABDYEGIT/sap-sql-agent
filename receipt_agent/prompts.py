"""
Fis Okuyucu Agent - GPT-4o-mini Vision OCR Prompt.

Kompakt prompt: Token tasarrufu icin kisaltilmis versiyon.
"""

RECEIPT_OCR_PROMPT = """Turkiye fis okuma. Gorseli oku, SADECE JSON dondur.

tutar = GENEL TOPLAM (en buyuk sayi, KDV DAHIL). KDV tutari DEGIL!
kdv_orani = KDV yuzde orani (sayi: 1, 10, 20). Birden fazlaysa en yuksek.
fis_turu: yemek/market/akaryakit/giyim/konaklama/ulasim/alkol/sigara/saglik/egitim/teknoloji/diger
alkol_sigara_pisin: Alkol veya sigara/tutun urunu varsa true, yoksa false.

Okunamayan alan icin "OKUNAMADI". Sayilarda nokta kullan (1234.50).

{"isletme_adi":"","adres":"","vergi_no":"","vergi_dairesi":"","tarih":"GG.AA.YYYY","saat":"SS:DD","fis_no":"","tutar":0.0,"kdv_orani":0,"fis_turu":"","alkol_sigara_pisin":false}"""
