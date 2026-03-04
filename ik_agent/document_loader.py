"""
IK Agent - Dokuman Yukleyici ve Chunking Modulu.

Word (.docx) dokumanlarini okur, paragraflari bolumlerine gore
chunklara ayirir ve RAG indexleme icin hazirlar.

Chunk Stratejisi:
- Heading'ler section basligi olarak takip edilir
- Paragraflar birlestirilerek ~500 karakter chunk'lar olusturulur
- Her chunk'a source_file, section_title metadata'si eklenir
"""
from pathlib import Path
from docx import Document


# ── Chunk Parametreleri ──
CHUNK_SIZE = 500        # Hedef chunk boyutu (karakter)
CHUNK_OVERLAP = 100     # Chunk'lar arasi overlap (karakter)


def load_and_chunk_docx(file_path: str) -> list:
    """
    Word dokumanini okuyup RAG icin chunk'lara ayirir.

    Args:
        file_path: .docx dosyasinin yolu

    Returns:
        Chunk listesi. Her eleman:
        {
            "id": "dosya_adi_chunk_0",
            "text": "Chunk icerigi...",
            "metadata": {
                "source_file": "yorglass_ik_prosedur.docx",
                "section_title": "Yillik Izin",
                "chunk_index": 0
            }
        }
    """
    doc = Document(file_path)
    file_name = Path(file_path).name
    base_id = Path(file_path).stem

    # ── Paragraf + Section Eslestirmesi ──
    current_section = "Genel"
    sections = []  # (section_title, text)

    buffer = ""

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Heading → yeni section basligi
        if para.style.name.startswith("Heading"):
            # Onceki buffer'i kaydet
            if buffer:
                sections.append((current_section, buffer))
                buffer = ""
            current_section = text
        else:
            # Normal paragraf → buffer'a ekle
            if buffer:
                buffer += "\n" + text
            else:
                buffer = text

    # Son buffer'i kaydet
    if buffer:
        sections.append((current_section, buffer))

    # ── Chunk Olusturma ──
    chunks = []
    chunk_index = 0

    for section_title, section_text in sections:
        # Section metni CHUNK_SIZE'dan kucukse tek chunk
        if len(section_text) <= CHUNK_SIZE:
            chunks.append({
                "id": f"{base_id}_chunk_{chunk_index}",
                "text": f"{section_title}: {section_text}",
                "metadata": {
                    "source_file": file_name,
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                }
            })
            chunk_index += 1
        else:
            # Buyuk section'i overlap ile bol
            start = 0
            while start < len(section_text):
                end = start + CHUNK_SIZE
                chunk_text = section_text[start:end]

                chunks.append({
                    "id": f"{base_id}_chunk_{chunk_index}",
                    "text": f"{section_title}: {chunk_text}",
                    "metadata": {
                        "source_file": file_name,
                        "section_title": section_title,
                        "chunk_index": chunk_index,
                    }
                })
                chunk_index += 1

                # Sonraki baslangic: overlap kadar geri
                start = end - CHUNK_OVERLAP
                if start >= len(section_text):
                    break

    return chunks


def get_default_document_path() -> str:
    """Varsayilan IK prosedur dokumani yolunu dondurur."""
    return str(Path(__file__).resolve().parent / "data" / "yorglass_ik_prosedur.docx")
