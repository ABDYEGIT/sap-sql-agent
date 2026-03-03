"""
BAPI Agent - Excel Metadata Parser ve RAG Entegrasyonu.

Excel dosyasindan SAP BAPI metadata'sini okur, yapilandirir,
RAG motoru ile indexler ve vektor arama yapar.

Excel Format (3 sayfa):
- BAPIler: BAPI adi, aciklama, islem tipi
- Parametreler: BAPI parametreleri (IMPORT/EXPORT/TABLES yonu)
- Parametre_Alanlari: Her parametrenin alt alanlari ve ornek degerler

RAG ENTEGRASYONU:
- Excel yuklendiginde BAPI'ler RAGEngine ile indexlenir
- Kullanici "malzeme genisletmek istiyorum" dediginde vector search
  ile en uygun BAPI bulunur
"""
import pandas as pd


def load_bapi_metadata_from_excel(uploaded_file):
    """
    Excel dosyasini parse ederek BAPI metadata'si olusturur.

    Args:
        uploaded_file: Streamlit file_uploader'dan gelen dosya

    Returns:
        (bapis_dict, error_message_or_None)

    bapis_dict yapisi:
    {
        "BAPI_MATERIAL_SAVEDATA": {
            "description": "Malzeme ana verisi olusturma/guncelleme",
            "operation_type": "CREATE/UPDATE",
            "parameters": [
                {
                    "name": "HEADDATA",
                    "direction": "IMPORT",
                    "data_type": "STRUCTURE",
                    "required": True,
                    "description": "Malzeme basi bilgileri",
                    "fields": [
                        {"name": "MATERIAL", "data_type": "CHAR(18)", "required": True,
                         "description": "Malzeme numarasi", "example": "000000001312312"}
                    ]
                }
            ]
        }
    }
    """
    try:
        # Sheet 1: BAPIler
        df_bapis = pd.read_excel(
            uploaded_file, sheet_name="BAPIler", engine="openpyxl"
        )
        required_cols = {"BAPI_ADI", "ACIKLAMA", "ISLEM_TIPI"}
        missing = required_cols - set(df_bapis.columns)
        if missing:
            return None, f"BAPIler sayfasinda eksik sutunlar: {', '.join(missing)}"

        # Sheet 2: Parametreler
        df_params = pd.read_excel(
            uploaded_file, sheet_name="Parametreler", engine="openpyxl"
        )
        required_param_cols = {"BAPI_ADI", "PARAMETRE_ADI", "PARAMETRE_YONU", "VERI_TIPI", "ZORUNLU", "ACIKLAMA"}
        missing_p = required_param_cols - set(df_params.columns)
        if missing_p:
            return None, f"Parametreler sayfasinda eksik sutunlar: {', '.join(missing_p)}"

        # Sheet 3: Parametre_Alanlari (opsiyonel ama onerilir)
        try:
            df_fields = pd.read_excel(
                uploaded_file, sheet_name="Parametre_Alanlari", engine="openpyxl"
            )
        except Exception:
            df_fields = pd.DataFrame()

        # BAPI'leri dict'e cevir
        bapis = {}
        for _, row in df_bapis.iterrows():
            bapi_name = str(row["BAPI_ADI"]).strip().upper()
            bapis[bapi_name] = {
                "description": str(row["ACIKLAMA"]).strip(),
                "operation_type": str(row["ISLEM_TIPI"]).strip().upper(),
                "parameters": [],
            }

        # Parametreleri ekle
        for _, row in df_params.iterrows():
            bapi_name = str(row["BAPI_ADI"]).strip().upper()
            if bapi_name not in bapis:
                continue

            required_val = str(row.get("ZORUNLU", "")).strip().upper()
            is_required = required_val in ("X", "EVET", "TRUE", "1")

            param = {
                "name": str(row["PARAMETRE_ADI"]).strip().upper(),
                "direction": str(row["PARAMETRE_YONU"]).strip().upper(),
                "data_type": str(row["VERI_TIPI"]).strip().upper(),
                "required": is_required,
                "description": str(row["ACIKLAMA"]).strip(),
                "fields": [],
            }
            bapis[bapi_name]["parameters"].append(param)

        # Parametre alt alanlarini ekle (eger Sheet 3 varsa)
        if not df_fields.empty:
            for _, row in df_fields.iterrows():
                bapi_name = str(row["BAPI_ADI"]).strip().upper()
                param_name = str(row["PARAMETRE_ADI"]).strip().upper()

                if bapi_name not in bapis:
                    continue

                # Ilgili parametreyi bul
                for param in bapis[bapi_name]["parameters"]:
                    if param["name"] == param_name:
                        required_val = str(row.get("ZORUNLU", "")).strip().upper()
                        is_required = required_val in ("X", "EVET", "TRUE", "1")

                        example_val = str(row.get("ORNEK_DEGER", "")).strip()
                        if example_val in ("nan", "None", ""):
                            example_val = ""

                        param["fields"].append({
                            "name": str(row["ALAN_ADI"]).strip().upper(),
                            "data_type": str(row["VERI_TIPI"]).strip(),
                            "required": is_required,
                            "description": str(row["ACIKLAMA"]).strip(),
                            "example": example_val,
                        })
                        break

        return bapis, None

    except Exception as e:
        return None, f"Excel okuma hatasi: {str(e)}"


def get_bapi_summary(bapis: dict) -> str:
    """Sidebar icin BAPI ozeti HTML'i olusturur."""
    html_parts = []
    for bapi_name, bapi_data in sorted(bapis.items()):
        param_count = len(bapi_data["parameters"])
        op_type = bapi_data["operation_type"]

        # Islem tipine gore renk
        if "CREATE" in op_type:
            badge_color = "#4CAF50"
        elif "READ" in op_type:
            badge_color = "#2196F3"
        elif "UPDATE" in op_type:
            badge_color = "#FF9800"
        elif "DELETE" in op_type:
            badge_color = "#f44336"
        else:
            badge_color = "#9E9E9E"

        html_parts.append(
            f'<div class="metadata-card">'
            f'<span class="table-name">{bapi_name}</span> '
            f'<span style="color:{badge_color};font-size:0.7rem;font-weight:600;">[{op_type}]</span><br>'
            f'<small>{bapi_data["description"]}</small><br>'
            f'<span class="field-count">({param_count} parametre)</span>'
            f'</div>'
        )
    return "\n".join(html_parts)


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 1: INDEXLEME - BAPI Metadata'sini Vektor Veritabanina Kaydet
# ══════════════════════════════════════════════════════════════════════
# Excel yuklendiginde bu fonksiyon cagirilir.
# Her BAPI icin bir "dokuman" metni olusturulur:
#   - BAPI adi ve aciklamasi
#   - Islem tipi (CREATE, READ, UPDATE, DELETE)
#   - Parametre isimleri ve aciklamalari
#
# Bu metin embedding'e cevrilip ChromaDB'ye kaydedilir.
# Kullanici "malzeme olusturmak istiyorum" dediginde vector search
# ile BAPI_MATERIAL_SAVEDATA bulunur.
# ══════════════════════════════════════════════════════════════════════

def index_bapis_for_rag(bapis: dict, rag_engine):
    """
    BAPI metadata'sini RAG motoru ile indexler.

    ── RAG INDEXLEME: Her BAPI icin aranabilir metin olustur ve vektorlestir ──

    Args:
        bapis: BAPI metadata dict'i
        rag_engine: RAGEngine instance'i
    """
    rag_engine.clear()

    documents = []
    for bapi_name, bapi_data in bapis.items():
        # Her BAPI icin detayli aranabilir metin olustur
        param_descriptions = []
        for param in bapi_data["parameters"]:
            req_mark = " [ZORUNLU]" if param["required"] else ""
            param_descriptions.append(
                f"{param['name']} ({param['direction']}, {param['data_type']}): "
                f"{param['description']}{req_mark}"
            )

        doc_text = (
            f"BAPI: {bapi_name} | "
            f"Aciklama: {bapi_data['description']} | "
            f"Islem: {bapi_data['operation_type']} | "
            f"Parametreler: {'; '.join(param_descriptions)}"
        )

        documents.append({
            "id": bapi_name,
            "text": doc_text,
            "metadata": {
                "type": "bapi",
                "operation": bapi_data["operation_type"],
                "param_count": str(len(bapi_data["parameters"])),
            }
        })

    # ── RAGEngine'e gonder: metin → embedding → ChromaDB ──
    rag_engine.index_documents(documents)


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 2: RETRIEVAL - Vector Search ile Ilgili BAPI'leri Bul
# ══════════════════════════════════════════════════════════════════════

def find_relevant_bapis_with_rag(bapis: dict, query: str, rag_engine, top_k: int = 3):
    """
    Vector search ile kullanici sorusuna en uygun BAPI'leri bulur.

    ── RAG RETRIEVAL: Sorguyu vektore cevir → ChromaDB'de ara → En yakin BAPI'leri getir ──

    Args:
        bapis: Tum BAPI metadata'si
        query: Kullanicinin Turkce sorusu (ornek: "malzeme genisletmek istiyorum")
        rag_engine: RAGEngine instance'i
        top_k: En fazla kac BAPI getirilecek

    Returns:
        filtered_bapis_dict
    """
    results = rag_engine.search(query, top_k=top_k)

    if not results:
        return bapis

    # Benzerlik skoru 0.3'ten yuksek olanlari al
    matched_bapis = set()
    for result in results:
        if result["score"] >= 0.3:
            matched_bapis.add(result["id"])

    if not matched_bapis:
        # En yuksek skorlu ilk sonucu al
        if results:
            matched_bapis.add(results[0]["id"])

    filtered = {k: v for k, v in bapis.items() if k in matched_bapis}
    return filtered if filtered else bapis


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 3: AUGMENTATION - Bulunan BAPI'leri Prompt'a Ekle
# ══════════════════════════════════════════════════════════════════════

def format_bapi_metadata_for_prompt(bapis: dict) -> str:
    """
    BAPI metadata'sini LLM prompt'ina uygun string formatina cevirir.

    ── RAG AUGMENTATION: Bulunan BAPI bilgisini prompt'a gom ──

    Args:
        bapis: Filtrelenmis BAPI metadata'si (vector search sonucu)

    Returns:
        LLM icin yapilandirilmis metin
    """
    lines = ["=== BAPI'LER ===\n"]

    for bapi_name in sorted(bapis.keys()):
        bapi_data = bapis[bapi_name]
        lines.append(f"BAPI: {bapi_name}")
        lines.append(f"Aciklama: {bapi_data['description']}")
        lines.append(f"Islem Tipi: {bapi_data['operation_type']}")
        lines.append("Parametreler:")

        for param in bapi_data["parameters"]:
            req = " [ZORUNLU]" if param["required"] else ""
            lines.append(
                f"  - {param['name']} ({param['direction']}, {param['data_type']}){req}: "
                f"{param['description']}"
            )

            # Alt alanlar
            if param["fields"]:
                for field in param["fields"]:
                    freq = " *" if field["required"] else ""
                    example = f" | Ornek: {field['example']}" if field["example"] else ""
                    lines.append(
                        f"      . {field['name']} ({field['data_type']}){freq}: "
                        f"{field['description']}{example}"
                    )

        lines.append("")

    return "\n".join(lines)
