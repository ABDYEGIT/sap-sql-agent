"""
SQL Agent - Excel Metadata Parser ve RAG Entegrasyonu.

Excel dosyasindan SAP tablo metadata'sini okur, yapilandirir,
RAG motoru ile indexler ve vektor arama yapar.

RAG ENTEGRASYONU:
- Excel yuklendiginde tablolar RAGEngine ile indexlenir (embedding olusturulur)
- Kullanici sorusunda find_relevant_tables() artik VECTOR SEARCH kullanir
- Keyword arama yerine anlamsal (semantic) arama yapilir
"""
import pandas as pd


def load_metadata_from_excel(uploaded_file):
    """
    Excel dosyasini parse ederek tablo ve iliski metadata'si olusturur.

    Args:
        uploaded_file: Streamlit file_uploader'dan gelen dosya

    Returns:
        (tables_dict, relationships_list, error_message_or_None)
    """
    try:
        # Sheet 1: Tablolar
        df_tables = pd.read_excel(
            uploaded_file, sheet_name="Tablolar", engine="openpyxl"
        )
        required_cols_tables = {"TABLO_ADI", "ALAN_ADI", "ALAN_ACIKLAMASI", "VERI_TIPI", "ANAHTAR"}
        missing = required_cols_tables - set(df_tables.columns)
        if missing:
            return None, None, f"Tablolar sayfasinda eksik sutunlar: {', '.join(missing)}"

        # Sheet 2: Iliskiler
        df_rels = pd.read_excel(
            uploaded_file, sheet_name="Iliskiler", engine="openpyxl"
        )
        required_cols_rels = {"KAYNAK_TABLO", "KAYNAK_ALAN", "HEDEF_TABLO", "HEDEF_ALAN", "ILISKI_TIPI"}
        missing_rels = required_cols_rels - set(df_rels.columns)
        if missing_rels:
            return None, None, f"Iliskiler sayfasinda eksik sutunlar: {', '.join(missing_rels)}"

        # Tablolari dict'e cevir
        tables = {}
        for _, row in df_tables.iterrows():
            table_name = str(row["TABLO_ADI"]).strip().upper()
            if table_name not in tables:
                tables[table_name] = {"fields": []}

            key_val = str(row.get("ANAHTAR", "")).strip().upper()
            if key_val in ("NAN", "NONE", ""):
                key_val = ""

            tables[table_name]["fields"].append({
                "name": str(row["ALAN_ADI"]).strip().upper(),
                "description": str(row["ALAN_ACIKLAMASI"]).strip(),
                "data_type": str(row["VERI_TIPI"]).strip().upper(),
                "key": key_val,
            })

        # Iliskileri list'e cevir
        relationships = []
        for _, row in df_rels.iterrows():
            source_fields_raw = str(row["KAYNAK_ALAN"]).strip().upper()
            target_fields_raw = str(row["HEDEF_ALAN"]).strip().upper()

            source_fields = [f.strip() for f in source_fields_raw.split("+")]
            target_fields = [f.strip() for f in target_fields_raw.split("+")]

            relationships.append({
                "source_table": str(row["KAYNAK_TABLO"]).strip().upper(),
                "source_fields": source_fields,
                "target_table": str(row["HEDEF_TABLO"]).strip().upper(),
                "target_fields": target_fields,
                "relationship_type": str(row["ILISKI_TIPI"]).strip(),
            })

        return tables, relationships, None

    except Exception as e:
        return None, None, f"Excel okuma hatasi: {str(e)}"


def get_table_summary(tables: dict) -> str:
    """Sidebar icin tablo ozeti HTML'i olusturur."""
    html_parts = []
    for table_name, table_data in sorted(tables.items()):
        fields = table_data["fields"]
        pk_fields = [f["name"] for f in fields if f["key"] == "PK"]
        pk_text = ", ".join(pk_fields) if pk_fields else "-"
        html_parts.append(
            f'<div class="metadata-card">'
            f'<span class="table-name">{table_name}</span> '
            f'<span class="field-count">({len(fields)} alan)</span><br>'
            f'<small>PK: {pk_text}</small>'
            f'</div>'
        )
    return "\n".join(html_parts)


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 1: INDEXLEME - Tablo Metadata'sini Vektor Veritabanina Kaydet
# ══════════════════════════════════════════════════════════════════════
# Excel yuklendiginde bu fonksiyon cagirilir.
# Her tablo icin bir "dokuman" metni olusturulur ve RAGEngine'e gonderilir.
# RAGEngine bu metni embedding'e cevirip ChromaDB'ye kaydeder.
#
# Dokuman metni ornegi:
#   "MARA - Malzeme Ana Verileri | Alanlar: MATNR (Malzeme Numarasi),
#    MTART (Malzeme Tipi), MATKL (Malzeme Grubu), MEINS (Temel Olcu Birimi)"
# ══════════════════════════════════════════════════════════════════════

def index_tables_for_rag(tables: dict, rag_engine):
    """
    Tablo metadata'sini RAG motoru ile indexler.

    ── RAG INDEXLEME: Her tablo icin aranabilir metin olustur ve vektorlestir ──

    Bu fonksiyon Excel yuklendiginde bir kez cagirilir.
    Sonrasinda kullanici soru sordugunda bu index uzerinden
    vector search yapilir (find_relevant_tables_with_rag).

    Args:
        tables: Tablo metadata dict'i ({TABLO_ADI: {fields: [...]}})
        rag_engine: RAGEngine instance'i
    """
    # Onceki indexi temizle (yeni Excel yuklendiyse)
    rag_engine.clear()

    documents = []
    for table_name, table_data in tables.items():
        # Her tablo icin aranabilir bir metin olustur
        # Bu metin embedding'e cevrilecek, bu yuzden detayli olmali
        field_descriptions = []
        for field in table_data["fields"]:
            key_info = f" [{field['key']}]" if field["key"] else ""
            field_descriptions.append(
                f"{field['name']} ({field['description']}){key_info}"
            )

        # Tablo dokuman metni: tablo adi + tum alan aciklamalari
        doc_text = (
            f"Tablo: {table_name} | "
            f"Alanlar: {', '.join(field_descriptions)}"
        )

        documents.append({
            "id": table_name,
            "text": doc_text,
            "metadata": {
                "type": "table",
                "field_count": str(len(table_data["fields"])),
            }
        })

    # ── RAGEngine'e gonder: metin → embedding → ChromaDB ──
    rag_engine.index_documents(documents)


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 2: RETRIEVAL - Vector Search ile Ilgili Tablolari Bul
# ══════════════════════════════════════════════════════════════════════
# Kullanici soru sordugunda bu fonksiyon cagirilir.
# Soru metni embedding'e cevrilir ve ChromaDB'de en yakin
# tablo dokumanlarini bulur (cosine similarity).
#
# Eski yontem (keyword arama): "urun kodu" → sadece "urun" kelimesini arar
# Yeni yontem (vector search): "urun kodu" → "Malzeme Numarasi" da bulur!
#   Cunku embedding modeli anlamsal benzerligi yakalayabilir.
# ══════════════════════════════════════════════════════════════════════

def find_relevant_tables_with_rag(tables: dict, relationships: list, query: str, rag_engine, top_k: int = 5):
    """
    Vector search ile kullanici sorusuna en uygun tablolari bulur.

    ── RAG RETRIEVAL: Sorguyu vektore cevir → ChromaDB'de ara → En yakin tablolari getir ──

    Eski keyword-based find_relevant_tables() yerine bu fonksiyon kullanilir.
    Anlamsal arama sayesinde daha dogru sonuclar verir.

    Args:
        tables: Tum tablo metadata'si
        relationships: Tum iliskiler
        query: Kullanicinin Turkce sorusu
        rag_engine: RAGEngine instance'i
        top_k: En fazla kac tablo getirilecek

    Returns:
        (filtered_tables_dict, filtered_relationships_list)
    """
    # ── Vector search ile en yakin tablolari bul ──
    results = rag_engine.search(query, top_k=top_k)

    if not results:
        # Vector search sonuc bulamazsa tum tablolari dondur
        return tables, relationships

    # ── Bulunan tablo adlarini cikar ──
    # Benzerlik skoru 0.3'ten yuksek olan tablolari al
    matched_tables = set()
    for result in results:
        if result["score"] >= 0.3:  # Minimum benzerlik esigi
            matched_tables.add(result["id"])

    if not matched_tables:
        # Esik alti sonuclar varsa en yuksek skorlu 3 tanesini al
        for result in results[:3]:
            matched_tables.add(result["id"])

    # ── Iliski grafi ile komsu tablolari da ekle ──
    # Bulunan tablolarin dogrudan iliskili oldugu tablolari da dahil et
    graph = _build_relationship_graph(relationships)
    expanded = _expand_tables_via_relationships(matched_tables, graph, max_hops=1)

    # Filtrele
    filtered_tables = {k: v for k, v in tables.items() if k in expanded}
    filtered_rels = [
        r for r in relationships
        if r["source_table"] in expanded and r["target_table"] in expanded
    ]

    if len(filtered_tables) < 1:
        return tables, relationships

    return filtered_tables, filtered_rels


# ── Yardimci fonksiyonlar (iliski grafi islemleri) ──

def _build_relationship_graph(relationships: list) -> dict:
    """Iliskilerden komsusluk grafi olusturur."""
    graph = {}
    for rel in relationships:
        src = rel["source_table"]
        tgt = rel["target_table"]
        graph.setdefault(src, set()).add(tgt)
        graph.setdefault(tgt, set()).add(src)
    return graph


def _expand_tables_via_relationships(matched_tables: set, graph: dict, max_hops: int = 2) -> set:
    """Eslesen tablolardan max_hops mesafedeki tablolari da ekler."""
    expanded = set(matched_tables)
    frontier = set(matched_tables)
    for _ in range(max_hops):
        next_frontier = set()
        for table in frontier:
            for neighbor in graph.get(table, set()):
                if neighbor not in expanded:
                    expanded.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
    return expanded


# ══════════════════════════════════════════════════════════════════════
# RAG ADIM 3: AUGMENTATION - Bulunan Tablolari Prompt'a Ekle
# ══════════════════════════════════════════════════════════════════════
# Vector search sonucu bulunan tablolarin metadata'si
# LLM'e gonderilecek prompt'a eklenir.
# Bu sayede LLM sadece ilgili tablolari gorur (token tasarrufu + odaklanma).
# ══════════════════════════════════════════════════════════════════════

def format_metadata_for_prompt(tables: dict, relationships: list) -> str:
    """
    Tablo ve iliski metadata'sini LLM prompt'ina uygun string formatina cevirir.

    ── RAG AUGMENTATION: Bulunan metadata'yi prompt'a gomme ──
    Vector search ile bulunan tablolarin detayli bilgisi
    system prompt'a eklenir. LLM bu bilgiyi kullanarak SQL uretir.

    Args:
        tables: Filtrelenmis tablo metadata'si (vector search sonucu)
        relationships: Filtrelenmis iliskiler

    Returns:
        LLM icin yapilandirilmis metin
    """
    lines = ["=== TABLOLAR ===\n"]

    for table_name in sorted(tables.keys()):
        table_data = tables[table_name]
        lines.append(f"TABLO: {table_name}")
        lines.append("Alanlar:")
        for field in table_data["fields"]:
            key_str = f", {field['key']}" if field["key"] else ""
            lines.append(
                f"  - {field['name']} ({field['data_type']}{key_str}): {field['description']}"
            )
        lines.append("")

    lines.append("=== ILISKILER ===\n")
    for rel in relationships:
        src_fields = "+".join(rel["source_fields"])
        tgt_fields = "+".join(rel["target_fields"])
        lines.append(
            f"{rel['source_table']}.{src_fields} -> "
            f"{rel['target_table']}.{tgt_fields} ({rel['relationship_type']})"
        )

    return "\n".join(lines)
