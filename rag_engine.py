"""
RAG (Retrieval-Augmented Generation) Motoru.

Bu modul, vektor tabanli arama (vector search) ve
bilgi getirme (retrieval) islemlerini yonetir.

RAG Pipeline Ozeti:
===================
1. INDEXLEME  : Excel'den okunan metadata → metin parcalari → embedding vektorleri → ChromaDB'ye kaydet
2. RETRIEVAL  : Kullanici sorusu → embedding → ChromaDB'de cosine similarity ile ara → en yakin sonuclar
3. AUGMENTATION: Bulunan sonuclari LLM prompt'una ekleyerek zenginlestir
4. GENERATION : LLM zenginlestirilmis prompt ile cevap uretir

Teknik Detaylar:
- Embedding Modeli: OpenAI text-embedding-3-small (1536 boyutlu vektor)
- Vektor Veritabani: ChromaDB (in-memory, cosine similarity)
- Her tablo/BAPI icin bir "dokuman" olusturulur ve vektorlestirilir
"""

import chromadb
from openai import OpenAI


class RAGEngine:
    """
    RAG Motoru - Tum agent'larin ortak kullandigi vektor arama motoru.

    Kullanim:
        engine = RAGEngine("sql_tables", api_key="sk-...")
        engine.index_documents([...])           # Excel'den gelen metadata'yi indexle
        results = engine.search("malzeme rengi") # Kullanici sorusuyla ara
    """

    def __init__(self, collection_name: str, api_key: str):
        """
        RAG motorunu baslatir.

        Args:
            collection_name: ChromaDB koleksiyon adi (ornek: "sql_tables", "bapi_functions")
            api_key: OpenAI API anahtari (embedding olusturmak icin gerekli)
        """
        # ══════════════════════════════════════════════════════════════
        # CHROMADB BASLAT - Vektor veritabanini olustur
        # ChromaDB, embedding vektorlerini saklayan ve cosine similarity
        # ile arama yapabilen bir vektor veritabanidir.
        # In-memory modda calisir (Streamlit Cloud uyumlu).
        # ══════════════════════════════════════════════════════════════
        self.client = chromadb.Client()  # In-memory ChromaDB istemcisi

        # Koleksiyonu olustur veya mevcut olani al
        # hnsw:space = "cosine" → cosine similarity kullanarak arama yapar
        # Cosine similarity: iki vektor arasindaki aciyi olcer (1.0 = ayni yon, 0.0 = dik)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # OpenAI istemcisi - embedding olusturmak icin kullanilacak
        self.openai_client = OpenAI(api_key=api_key)
        self.api_key = api_key

    # ══════════════════════════════════════════════════════════════════
    # VECTOR SEARCH - ADIM 1: EMBEDDING OLUSTURMA
    # ══════════════════════════════════════════════════════════════════
    # Embedding nedir?
    # Bir metni sabit uzunlukta bir sayisal vektore (1536 sayi dizisi) cevirir.
    # Benzer anlamli metinler birbirine yakin vektorler uretir.
    #
    # Ornek:
    #   "malzeme numarasi" → [0.023, -0.156, 0.891, ...]  (1536 sayi)
    #   "urun kodu"        → [0.021, -0.148, 0.887, ...]  (yakin vektor!)
    #   "tedarikci adresi"  → [0.512, 0.334, -0.221, ...]  (uzak vektor)
    # ══════════════════════════════════════════════════════════════════

    def create_embeddings(self, texts: list) -> list:
        """
        Metin listesini embedding vektorlerine cevirir.

        ── VECTOR SEARCH'UN TEMEL ADIMI ──
        Her metin 1536 boyutlu bir sayisal vektore donusturulur.
        Bu vektorler daha sonra ChromaDB'de saklanir ve aranir.

        Args:
            texts: Vektorlestirilecek metin listesi
                   Ornek: ["MARA - Malzeme Numarasi, Malzeme Tipi, Malzeme Grubu",
                           "EKKO - Satin Alma Belge Numarasi, Sirket Kodu"]

        Returns:
            Her metin icin 1536 boyutlu vektor listesi
            Ornek: [[0.023, -0.156, ...], [0.512, 0.334, ...]]
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",   # OpenAI'nin kucuk ve hizli embedding modeli
            input=texts                        # Vektorlestirilecek metinler
        )
        # API'den gelen her embedding objesinden vektor dizisini cikar
        return [item.embedding for item in response.data]

    # ══════════════════════════════════════════════════════════════════
    # RAG ADIM 1: INDEXLEME (Bilgi Deposu Olusturma)
    # ══════════════════════════════════════════════════════════════════
    # Excel'den okunan metadata'yi vektor veritabanina kaydeder.
    # Her tablo veya BAPI icin bir "dokuman" olusturulur:
    #   - id: Benzersiz kimlik (tablo/BAPI adi)
    #   - text: Aranabilir metin (tablo adi + alan aciklamalari)
    #   - metadata: Ek bilgiler (tablo_adi, alan_sayisi vs.)
    #
    # Bu adim sadece Excel yuklendiginde bir kez calisir.
    # Sonrasinda tum aramalar bu index uzerinden yapilir.
    # ══════════════════════════════════════════════════════════════════

    def index_documents(self, documents: list):
        """
        Metadata dokumanlarini vektorlestirip ChromaDB'ye kaydeder.

        ── RAG'IN ILKE ADIMI: BILGI DEPOSU OLUSTURMA ──
        Excel'den okunan her tablo/BAPI icin:
        1. Aciklama metnini al
        2. OpenAI Embedding API ile vektore cevir
        3. ChromaDB'ye vektor + metin + metadata olarak kaydet

        Args:
            documents: Dokuman listesi. Her eleman bir dict:
                {
                    "id": "MARA",                          # Benzersiz kimlik
                    "text": "MARA - Malzeme Ana Verileri...", # Aranabilir metin
                    "metadata": {"type": "table", ...}     # Ek bilgiler (opsiyonel)
                }
        """
        if not documents:
            return

        # Dokuman bilgilerini ayristir
        texts = [doc["text"] for doc in documents]
        ids = [doc["id"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        # ── Metinleri vektorlere cevir (Embedding) ──
        embeddings = self.create_embeddings(texts)

        # ── Vektorleri ChromaDB'ye kaydet ──
        # Her dokuman icin: id + vektor + orijinal metin + metadata saklanir
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    # ══════════════════════════════════════════════════════════════════
    # RAG ADIM 2: RETRIEVAL - Bilgi Getirme (VECTOR SEARCH)
    # ══════════════════════════════════════════════════════════════════
    # Kullanici bir soru sorduğunda:
    # 1. Soru metni embedding'e cevrilir (ayni model ile)
    # 2. Bu embedding ChromaDB'deki tum vektorlerle karsilastirilir
    # 3. Cosine similarity ile en yakin N sonuc bulunur
    # 4. Bu sonuclar LLM'e gonderilecek prompt'a eklenir
    #
    # NEDEN VECTOR SEARCH?
    # Keyword arama: "urun kodu" → sadece "urun" ve "kodu" kelimelerini arar
    # Vector search: "urun kodu" → "malzeme numarasi" da bulur! (anlamsal benzerlik)
    # ══════════════════════════════════════════════════════════════════

    def search(self, query: str, top_k: int = 5) -> list:
        """
        Kullanici sorusuna en yakin dokumanlari getirir.

        ── VECTOR SEARCH BURADA GERCEKLESIR ──
        1. Kullanici sorusunu ayni embedding modeli ile vektore cevir
        2. ChromaDB'de cosine similarity ile en yakin top_k sonucu bul
        3. Sonuclari skor sirali olarak dondur

        Args:
            query: Kullanicinin dogal dil sorusu
                   Ornek: "malzeme genisletmek istiyorum"
            top_k: Dondurulecek maksimum sonuc sayisi (varsayilan: 5)

        Returns:
            Sonuc listesi. Her eleman bir dict:
            {
                "id": "MARA",                              # Dokuman kimligi
                "text": "MARA - Malzeme Ana Verileri...",  # Orijinal metin
                "score": 0.89,                              # Benzerlik skoru (0-1)
                "metadata": {"type": "table", ...}         # Ek bilgiler
            }
        """
        # Koleksiyonda dokuman yoksa bos dondur
        if self.collection.count() == 0:
            return []

        # ── Sorguyu vektore cevir ──
        query_embedding = self.create_embeddings([query])[0]

        # ── ChromaDB'de cosine similarity ile ara ──
        # query_embeddings: Aranacak vektoru verir
        # n_results: En yakin kac sonuc getirilecek
        # ChromaDB otomatik olarak cosine similarity hesaplar ve siralar
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        # ── Sonuclari duzenlenmis formatta dondur ──
        output = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB cosine distance dondurur (0 = ayni, 2 = tam zit)
                # Bunu benzerlik skoruna ceviriyoruz: score = 1 - (distance / 2)
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - (distance / 2)  # 0-1 arasi skor (1 = en benzer)

                output.append({
                    "id": doc_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "score": round(score, 4),
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                })

        return output

    def clear(self):
        """
        Koleksiyondaki tum dokumanlari siler.
        Yeni Excel yuklendiginde onceki index temizlenir.
        """
        # Mevcut koleksiyonu sil ve yeniden olustur
        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def get_document_count(self) -> int:
        """Koleksiyondaki toplam dokuman sayisini dondurur."""
        return self.collection.count()
