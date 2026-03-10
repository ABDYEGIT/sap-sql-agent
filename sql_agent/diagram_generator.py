"""
SQL Agent - Mermaid Diagram Generator.

SQL sorgusundan Mermaid diagram syntax'i uretir.
LLM cagrisi yapmaz — deterministik olarak parse eder.

Iki tip diagram uretir:
1. Flow Diagram: Soru → Intent → Tablolar → SQL akisi
2. ER Diagram: Kullanilan tablolar arasi iliskiler
"""
import re


def generate_flow_diagram(
    question: str,
    intent: dict,
    used_tables: list,
    sql: str | None,
) -> str:
    """
    Sorgu akis diagrami uretir (Mermaid graph TD formati).

    Args:
        question: Kullanicinin sorusu
        intent: Intent sonucu {"db": "BW"|"SAP", "confidence": 0.9}
        used_tables: Kullanilan tablo isimleri
        sql: Uretilen SQL sorgusu

    Returns:
        Mermaid graph TD string
    """
    db = intent.get("db", "SAP")
    confidence = intent.get("confidence", 0)
    conf_pct = int(confidence * 100)

    # Soruyu kisalt (Mermaid'de uzun text sorun cikarir)
    q_short = question[:50] + "..." if len(question) > 50 else question
    # Mermaid ozel karakterlerini temizle
    q_short = _sanitize_mermaid(q_short)

    lines = [
        "graph TD",
        f'    A["Kullanici Sorusu<br/>{q_short}"]',
        '    A --> B["Intent Classifier"]',
        f'    B -->|"{db} %{conf_pct}"| C["{db} RAG Engine"]',
        '    C -->|"Vector Search"| D["Ilgili Tablolar"]',
    ]

    # Tablo kutularini ekle
    if used_tables:
        table_list = "<br/>".join(used_tables[:5])
        lines.append(f'    D --> E["{table_list}"]')
        lines.append('    E --> F["SQL Generator<br/>LLM"]')
    else:
        lines.append('    D --> F["SQL Generator<br/>LLM"]')

    # SQL ozeti
    if sql:
        sql_type = "SELECT + JOIN" if "JOIN" in sql.upper() else "SELECT"
        lines.append(f'    F --> G["Sonuc<br/>{sql_type} sorgusu"]')
    else:
        lines.append('    F --> G["Sonuc<br/>SQL Sorgusu"]')

    # Stillendirme
    lines.extend([
        "",
        "    style A fill:#4f46e5,stroke:#3730a3,color:#fff",
        "    style B fill:#f59e0b,stroke:#d97706,color:#fff",
        f"    style C fill:{'#0891b2' if db == 'BW' else '#16a34a'},stroke:#134e4a,color:#fff",
        "    style D fill:#6366f1,stroke:#4f46e5,color:#fff",
        "    style F fill:#ec4899,stroke:#be185d,color:#fff",
        "    style G fill:#10b981,stroke:#059669,color:#fff",
    ])

    return "\n".join(lines)


def generate_er_diagram(
    used_tables: list,
    tables_metadata: dict,
    relationships: list,
) -> str:
    """
    Kullanilan tablolarin ER diagramini uretir (Mermaid erDiagram formati).

    Args:
        used_tables: Sorgu icinde kullanilan tablo isimleri
        tables_metadata: Tum tablo metadata dict'i
        relationships: Tum iliskiler listesi

    Returns:
        Mermaid erDiagram string
    """
    if not used_tables:
        return ""

    lines = ["erDiagram"]

    # Her tablo icin entity tanimla
    for table_name in used_tables:
        table_data = tables_metadata.get(table_name)
        if not table_data:
            continue

        lines.append(f"    {table_name} {{")
        for field in table_data.get("fields", [])[:8]:  # Max 8 alan goster
            ftype = _simplify_type(field.get("data_type", "string"))
            fname = field["name"]
            key_mark = "PK" if field.get("key") == "PK" else ""
            key_mark = "FK" if field.get("key") == "FK" else key_mark
            desc = field.get("description", "").replace('"', "'")[:30]
            lines.append(f'        {ftype} {fname} {key_mark} "{desc}"')
        lines.append("    }")

    # Kullanilan tablolar arasi iliskileri ekle
    used_set = set(t.upper() for t in used_tables)
    for rel in relationships:
        src = rel["source_table"].upper()
        tgt = rel["target_table"].upper()
        if src in used_set and tgt in used_set:
            rel_type = rel.get("relationship_type", "1:N")
            src_fields = "+".join(rel["source_fields"])
            tgt_fields = "+".join(rel["target_fields"])

            if rel_type == "1:N":
                lines.append(f'    {src} ||--o{{ {tgt} : "{src_fields}"')
            elif rel_type == "N:1":
                lines.append(f'    {src} }}o--|| {tgt} : "{src_fields}"')
            else:
                lines.append(f'    {src} ||--|| {tgt} : "{src_fields}"')

    return "\n".join(lines)


def _sanitize_mermaid(text: str) -> str:
    """Mermaid syntax icin guvenli text olusturur."""
    # Mermaid'de sorun cikaran karakterleri temizle
    text = text.replace('"', "'")
    text = text.replace("(", "")
    text = text.replace(")", "")
    text = text.replace("?", "")
    text = text.replace("#", "")
    text = text.replace("&", "ve")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("{", "")
    text = text.replace("}", "")
    return text.strip()


def _simplify_type(data_type: str) -> str:
    """SAP veri tipini Mermaid-uyumlu basit tipe cevirir."""
    dt = data_type.upper()
    if "CHAR" in dt or "STRING" in dt or "LANG" in dt:
        return "string"
    if "NUMC" in dt or "INT" in dt or "DEC" in dt:
        return "number"
    if "DATS" in dt or "DATE" in dt:
        return "date"
    if "CURR" in dt or "QUAN" in dt:
        return "number"
    if "UNIT" in dt:
        return "string"
    return "string"
