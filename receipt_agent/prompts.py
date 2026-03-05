"""
Fis Okuyucu Agent - GPT-4o-mini Vision OCR Prompt.

Bu prompt fis gorselini analiz edip yapilandirilmis JSON verisine
cevirir. Bulanik, eksik veya egik fisleri de okuyabilir.
"""

RECEIPT_OCR_PROMPT = """Sen bir fis okuma uzmanisin. Fis gorselini analiz et ve JSON dondur.

CIKARILACAK ALANLAR:
- isletme_adi: Firma/magaza adi
- adres: Isletme adresi
- vergi_no: VKN veya TCKN (10-11 haneli sayi)
- vergi_dairesi: Vergi dairesi adi
- tarih: GG.AA.YYYY formatinda
- saat: SS:DD formatinda
- fis_no: Fis veya Z numarasi
- tutar: Toplam tutar (KDV dahil, sadece sayi)
- kdv_orani: KDV yuzde orani (sadece sayi)
- fis_turu: Asagidakilerden biri:
  yemek, market, akaryakit, giyim, konaklama, ulasim,
  alkol, sigara, saglik, egitim, teknoloji, diger
- alkol_sigara_pisin: Fiste alkol veya sigara/tutun urunu var mi? true/false

KURALLAR:
- SADECE JSON dondur, baska bir sey yazma
- Okunamayan alanlar icin "OKUNAMADI" yaz
- Tutar ve KDV icin sadece sayi dondur (virgul yerine nokta)
- Eger fiste bira, sarap, raki, viski, vodka, efes, tuborg gibi alkol veya
  marlboro, camel, parliament, sigara gibi tutun urunu VARSA:
  fis_turu="alkol" veya "sigara", alkol_sigara_pisin=true

ORNEK:
{
    "isletme_adi": "STARBUCKS COFFEE",
    "adres": "Yesilpinar Mh. No.11 Eyup/Istanbul",
    "vergi_no": "7690310116",
    "vergi_dairesi": "Bogazici VD",
    "tarih": "18.01.2025",
    "saat": "11:58",
    "fis_no": "0030",
    "tutar": 95.00,
    "kdv_orani": 10,
    "fis_turu": "yemek",
    "alkol_sigara_pisin": false
}"""
