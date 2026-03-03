"""
Ornek SAP BAPI metadata Excel dosyasi olusturma scripti.
Bir kere calistirilir, bapi_sample_metadata.xlsx dosyasini uretir.
"""
import pandas as pd
from pathlib import Path

# Sheet 1: BAPIler
bapiler_data = [
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "ACIKLAMA": "Malzeme ana verisi olusturma ve guncelleme", "ISLEM_TIPI": "CREATE/UPDATE"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "ACIKLAMA": "Satin alma siparisi olusturma", "ISLEM_TIPI": "CREATE"},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "ACIKLAMA": "Tedarikci detay bilgilerini okuma", "ISLEM_TIPI": "READ"},
    {"BAPI_ADI": "BAPI_MATERIAL_GET_DETAIL", "ACIKLAMA": "Malzeme detay bilgilerini okuma", "ISLEM_TIPI": "READ"},
    {"BAPI_ADI": "BAPI_MATERIAL_STOCK_REQ_LIST", "ACIKLAMA": "Malzeme stok ve ihtiyac listesi sorgulama", "ISLEM_TIPI": "READ"},
]

# Sheet 2: Parametreler
parametreler_data = [
    # BAPI_MATERIAL_SAVEDATA
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "HEADDATA", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "X", "ACIKLAMA": "Malzeme basi bilgileri (malzeme no, sanayi kolu, malzeme tipi)"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATA", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "X", "ACIKLAMA": "Genel istemci verileri (malzeme grubu, olcu birimi)"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATAX", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "X", "ACIKLAMA": "Genel istemci verileri degisiklik bayraklari"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "PLANTDATA", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Tesis duzeyi veriler (MRP, uretim bilgileri)"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "PLANTDATAX", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Tesis verileri degisiklik bayraklari"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "RETURN", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Islem sonuc mesaji (basari/hata)"},

    # BAPI_PO_CREATE1
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADER", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "X", "ACIKLAMA": "Siparis basi bilgileri (belge tipi, satin alma org., tedarikci)"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADERX", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "X", "ACIKLAMA": "Siparis basi degisiklik bayraklari"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "EXPPURCHASEORDER", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "", "ACIKLAMA": "Olusturulan siparis numarasi"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "RETURN", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "TABLE", "ZORUNLU": "", "ACIKLAMA": "Islem sonuc mesajlari"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "PARAMETRE_YONU": "TABLES", "VERI_TIPI": "TABLE", "ZORUNLU": "X", "ACIKLAMA": "Siparis kalem bilgileri"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEMX", "PARAMETRE_YONU": "TABLES", "VERI_TIPI": "TABLE", "ZORUNLU": "X", "ACIKLAMA": "Siparis kalem degisiklik bayraklari"},

    # BAPI_VENDOR_GETDETAIL
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "VENDORNO", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "X", "ACIKLAMA": "Tedarikci numarasi"},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "COMPANYCODE", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "", "ACIKLAMA": "Sirket kodu"},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "GENERALDETAIL", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Tedarikci genel bilgileri"},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "RETURN", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Islem sonuc mesaji"},

    # BAPI_MATERIAL_GET_DETAIL
    {"BAPI_ADI": "BAPI_MATERIAL_GET_DETAIL", "PARAMETRE_ADI": "MATERIAL", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "X", "ACIKLAMA": "Malzeme numarasi"},
    {"BAPI_ADI": "BAPI_MATERIAL_GET_DETAIL", "PARAMETRE_ADI": "PLANT", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "", "ACIKLAMA": "Tesis kodu"},
    {"BAPI_ADI": "BAPI_MATERIAL_GET_DETAIL", "PARAMETRE_ADI": "MATERIAL_GENERAL_DATA", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Malzeme genel verileri"},
    {"BAPI_ADI": "BAPI_MATERIAL_GET_DETAIL", "PARAMETRE_ADI": "RETURN", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Islem sonuc mesaji"},

    # BAPI_MATERIAL_STOCK_REQ_LIST
    {"BAPI_ADI": "BAPI_MATERIAL_STOCK_REQ_LIST", "PARAMETRE_ADI": "MATERIAL", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "X", "ACIKLAMA": "Malzeme numarasi"},
    {"BAPI_ADI": "BAPI_MATERIAL_STOCK_REQ_LIST", "PARAMETRE_ADI": "PLANT", "PARAMETRE_YONU": "IMPORT", "VERI_TIPI": "CHAR", "ZORUNLU": "X", "ACIKLAMA": "Tesis kodu"},
    {"BAPI_ADI": "BAPI_MATERIAL_STOCK_REQ_LIST", "PARAMETRE_ADI": "MRP_LIST", "PARAMETRE_YONU": "TABLES", "VERI_TIPI": "TABLE", "ZORUNLU": "", "ACIKLAMA": "MRP listesi sonuclari"},
    {"BAPI_ADI": "BAPI_MATERIAL_STOCK_REQ_LIST", "PARAMETRE_ADI": "RETURN", "PARAMETRE_YONU": "EXPORT", "VERI_TIPI": "STRUCTURE", "ZORUNLU": "", "ACIKLAMA": "Islem sonuc mesaji"},
]

# Sheet 3: Parametre Alanlari
parametre_alanlari_data = [
    # BAPI_MATERIAL_SAVEDATA - HEADDATA
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "HEADDATA", "ALAN_ADI": "MATERIAL", "VERI_TIPI": "CHAR(18)", "ZORUNLU": "X", "ACIKLAMA": "Malzeme numarasi", "ORNEK_DEGER": "000000001312312"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "HEADDATA", "ALAN_ADI": "IND_SECTOR", "VERI_TIPI": "CHAR(1)", "ZORUNLU": "X", "ACIKLAMA": "Sanayi kolu (M=Makine, C=Kimya)", "ORNEK_DEGER": "M"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "HEADDATA", "ALAN_ADI": "MATL_TYPE", "VERI_TIPI": "CHAR(4)", "ZORUNLU": "X", "ACIKLAMA": "Malzeme tipi", "ORNEK_DEGER": "FERT"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "HEADDATA", "ALAN_ADI": "BASIC_VIEW", "VERI_TIPI": "CHAR(1)", "ZORUNLU": "", "ACIKLAMA": "Temel veri gorunumu aktif", "ORNEK_DEGER": "X"},

    # BAPI_MATERIAL_SAVEDATA - CLIENTDATA
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATA", "ALAN_ADI": "MATL_GROUP", "VERI_TIPI": "CHAR(9)", "ZORUNLU": "X", "ACIKLAMA": "Malzeme grubu", "ORNEK_DEGER": "001"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATA", "ALAN_ADI": "BASE_UOM", "VERI_TIPI": "UNIT(3)", "ZORUNLU": "X", "ACIKLAMA": "Temel olcu birimi", "ORNEK_DEGER": "ST"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATA", "ALAN_ADI": "NET_WEIGHT", "VERI_TIPI": "QUAN(13)", "ZORUNLU": "", "ACIKLAMA": "Net agirlik", "ORNEK_DEGER": "1.500"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "CLIENTDATA", "ALAN_ADI": "UNIT_OF_WT", "VERI_TIPI": "UNIT(3)", "ZORUNLU": "", "ACIKLAMA": "Agirlik birimi", "ORNEK_DEGER": "KG"},

    # BAPI_MATERIAL_SAVEDATA - PLANTDATA
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "PLANTDATA", "ALAN_ADI": "PLANT", "VERI_TIPI": "CHAR(4)", "ZORUNLU": "X", "ACIKLAMA": "Tesis kodu", "ORNEK_DEGER": "1000"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "PLANTDATA", "ALAN_ADI": "MRP_TYPE", "VERI_TIPI": "CHAR(2)", "ZORUNLU": "", "ACIKLAMA": "MRP tipi", "ORNEK_DEGER": "PD"},
    {"BAPI_ADI": "BAPI_MATERIAL_SAVEDATA", "PARAMETRE_ADI": "PLANTDATA", "ALAN_ADI": "MRP_CTRLER", "VERI_TIPI": "CHAR(3)", "ZORUNLU": "", "ACIKLAMA": "MRP kontroloru", "ORNEK_DEGER": "001"},

    # BAPI_PO_CREATE1 - POHEADER
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADER", "ALAN_ADI": "DOC_TYPE", "VERI_TIPI": "CHAR(4)", "ZORUNLU": "X", "ACIKLAMA": "Belge tipi", "ORNEK_DEGER": "NB"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADER", "ALAN_ADI": "PURCH_ORG", "VERI_TIPI": "CHAR(4)", "ZORUNLU": "X", "ACIKLAMA": "Satin alma organizasyonu", "ORNEK_DEGER": "1000"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADER", "ALAN_ADI": "PUR_GROUP", "VERI_TIPI": "CHAR(3)", "ZORUNLU": "X", "ACIKLAMA": "Satin alma grubu", "ORNEK_DEGER": "001"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POHEADER", "ALAN_ADI": "VENDOR", "VERI_TIPI": "CHAR(10)", "ZORUNLU": "X", "ACIKLAMA": "Tedarikci numarasi", "ORNEK_DEGER": "0000012345"},

    # BAPI_PO_CREATE1 - POITEM
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "ALAN_ADI": "PO_ITEM", "VERI_TIPI": "NUMC(5)", "ZORUNLU": "X", "ACIKLAMA": "Kalem numarasi", "ORNEK_DEGER": "00010"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "ALAN_ADI": "MATERIAL", "VERI_TIPI": "CHAR(18)", "ZORUNLU": "X", "ACIKLAMA": "Malzeme numarasi", "ORNEK_DEGER": "000000001312312"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "ALAN_ADI": "PLANT", "VERI_TIPI": "CHAR(4)", "ZORUNLU": "X", "ACIKLAMA": "Tesis", "ORNEK_DEGER": "1000"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "ALAN_ADI": "QUANTITY", "VERI_TIPI": "QUAN(13)", "ZORUNLU": "X", "ACIKLAMA": "Siparis miktari", "ORNEK_DEGER": "100"},
    {"BAPI_ADI": "BAPI_PO_CREATE1", "PARAMETRE_ADI": "POITEM", "ALAN_ADI": "NET_PRICE", "VERI_TIPI": "CURR(11)", "ZORUNLU": "", "ACIKLAMA": "Net fiyat", "ORNEK_DEGER": "25.50"},

    # BAPI_VENDOR_GETDETAIL - GENERALDETAIL
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "GENERALDETAIL", "ALAN_ADI": "NAME", "VERI_TIPI": "CHAR(35)", "ZORUNLU": "", "ACIKLAMA": "Tedarikci adi", "ORNEK_DEGER": ""},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "GENERALDETAIL", "ALAN_ADI": "CITY", "VERI_TIPI": "CHAR(35)", "ZORUNLU": "", "ACIKLAMA": "Sehir", "ORNEK_DEGER": ""},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "GENERALDETAIL", "ALAN_ADI": "COUNTRY", "VERI_TIPI": "CHAR(3)", "ZORUNLU": "", "ACIKLAMA": "Ulke kodu", "ORNEK_DEGER": ""},
    {"BAPI_ADI": "BAPI_VENDOR_GETDETAIL", "PARAMETRE_ADI": "GENERALDETAIL", "ALAN_ADI": "TELEPHONE", "VERI_TIPI": "CHAR(16)", "ZORUNLU": "", "ACIKLAMA": "Telefon numarasi", "ORNEK_DEGER": ""},
]

# Excel olustur
output_path = Path(__file__).resolve().parent / "bapi_sample_metadata.xlsx"

df_bapiler = pd.DataFrame(bapiler_data)
df_parametreler = pd.DataFrame(parametreler_data)
df_alanlar = pd.DataFrame(parametre_alanlari_data)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df_bapiler.to_excel(writer, sheet_name="BAPIler", index=False)
    df_parametreler.to_excel(writer, sheet_name="Parametreler", index=False)
    df_alanlar.to_excel(writer, sheet_name="Parametre_Alanlari", index=False)

print(f"bapi_sample_metadata.xlsx olusturuldu: {output_path}")
print(f"  BAPI'ler: {df_bapiler['BAPI_ADI'].nunique()} BAPI")
print(f"  Parametreler: {len(df_parametreler)} parametre")
print(f"  Parametre Alanlari: {len(df_alanlar)} alan")
