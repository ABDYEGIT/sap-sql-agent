"""
Yorglass IK Chatbot - FastAPI Web Servisi.

Intranet portalindaki chatbot icin REST API.
RAG (ChromaDB + OpenAI Embedding) ile IK dokumanlarinda arama yapar,
Azure OpenAI ile yanitlar uretir.

Kullanim:
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

Swagger UI:
    http://localhost:8000/docs

Akis:
    Portal Chatbot → POST /api/chat → RAG Search → Azure OpenAI → JSON Response
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AzureOpenAI
from pydantic import BaseModel, Field

from ik_agent.document_loader import load_and_chunk_docx, get_default_document_path
from ik_agent.prompts import IK_SYSTEM_PROMPT
from rag_engine import RAGEngine
from token_tracker import log_token_usage


# ══════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("ik-chatbot-api")


# ══════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════
ik_rag: Optional[RAGEngine] = None
azure_client: Optional[AzureOpenAI] = None
azure_deployment: str = ""


# ══════════════════════════════════════════════════════════════════════
# ENV YAPILANDIRMA
# ══════════════════════════════════════════════════════════════════════
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

# Embedding icin standard OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM icin Azure OpenAI
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# CORS
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# LLM parametreleri
TEMPERATURE = 0.2
MAX_TOKENS = 2000


# ══════════════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN (Lifespan)
# ══════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Sunucu basladiginda RAG index'ini ve Azure client'i hazirlar.
    Sunucu kapandiginda temizlik yapar.
    """
    global ik_rag, azure_client, azure_deployment

    logger.info("=== IK Chatbot API baslatiliyor ===")

    # ── 1. OpenAI API Key kontrol (embedding icin) ──
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY bulunamadi! Embedding calismayacak.")
    else:
        logger.info("OpenAI API key yuklendi (embedding icin).")

    # ── 2. Azure OpenAI kontrol (LLM icin) ──
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        logger.error(
            "Azure OpenAI yapilandirmasi eksik! "
            "AZURE_OPENAI_ENDPOINT ve AZURE_OPENAI_API_KEY gerekli."
        )
    else:
        azure_client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            api_version=AZURE_API_VERSION,
        )
        azure_deployment = AZURE_DEPLOYMENT
        logger.info(
            f"Azure OpenAI baglandi: {AZURE_ENDPOINT} "
            f"(deployment: {azure_deployment})"
        )

    # ── 3. IK Dokumani yukle + RAG index olustur ──
    ik_doc_path = get_default_document_path()
    if Path(ik_doc_path).exists():
        chunks = load_and_chunk_docx(ik_doc_path)
        ik_rag = RAGEngine("api_ik_documents", OPENAI_API_KEY)
        ik_rag.index_documents(chunks)
        logger.info(
            f"IK RAG index hazir: {len(chunks)} chunk, "
            f"{ik_rag.get_document_count()} dokuman"
        )
    else:
        logger.error(f"IK dokumani bulunamadi: {ik_doc_path}")

    logger.info("=== IK Chatbot API hazir ===")
    logger.info(f"CORS izinli origin'ler: {CORS_ORIGINS}")

    yield  # Sunucu calisiyor

    # ── Shutdown ──
    logger.info("IK Chatbot API kapaniyor...")


# ══════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════════════════════════════════
app = FastAPI(
    title="Yorglass IK Chatbot API",
    description=(
        "Yorglass Insan Kaynaklari asistani. "
        "IK prosedur dokumanlari uzerinde RAG tabanli soru-cevap servisi."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
# PYDANTIC MODELLER
# ══════════════════════════════════════════════════════════════════════


class ChatMessage(BaseModel):
    """Tek bir sohbet mesaji."""

    role: str = Field(..., description="Mesaj rolu: 'user' veya 'assistant'")
    content: str = Field(..., description="Mesaj icerigi")


class ChatRequest(BaseModel):
    """Chatbot'tan gelen istek."""

    message: str = Field(
        ...,
        description="Kullanicinin sorusu",
        min_length=1,
        examples=["Yillik izin hakkim kac gun?"],
    )
    chat_history: list[ChatMessage] = Field(
        default=[],
        description="Onceki sohbet gecmisi (opsiyonel)",
    )


class SourceInfo(BaseModel):
    """RAG'den bulunan kaynak bilgisi."""

    section_title: str
    source_file: str
    score: float


class TokenInfo(BaseModel):
    """Token kullanim bilgisi."""

    input: int
    output: int
    total: int


class ChatResponse(BaseModel):
    """API'nin dondurdugu yanitlar."""

    response: str = Field(..., description="IK asistaninin yaniti")
    sources: list[SourceInfo] = Field(
        default=[], description="Kullanilan kaynak dokumanlar"
    )
    tokens: Optional[TokenInfo] = Field(
        default=None, description="Token kullanim bilgisi"
    )


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/chat
# ══════════════════════════════════════════════════════════════════════


@app.post(
    "/api/chat",
    response_model=ChatResponse,
    summary="IK sorusu sor",
    description="IK dokumanlarina dayali RAG tabanli soru-cevap.",
)
async def chat(request: ChatRequest):
    """
    IK sorusunu alir, RAG ile ilgili dokumanlari bulur,
    Azure OpenAI ile yanit uretir.
    """
    # ── Kontroller ──
    if not ik_rag:
        raise HTTPException(
            status_code=503,
            detail="IK RAG index'i henuz hazir degil. Sunucu baslatilirken hata olustu.",
        )

    if not azure_client:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI baglantisi yapilandirilmamis. .env dosyasini kontrol edin.",
        )

    try:
        # ═══════════════════════════════════════
        # RAG ADIM 1: RETRIEVAL - Vektor Arama
        # ═══════════════════════════════════════
        search_results = ik_rag.search(request.message, top_k=5)

        sources = []
        context_parts = []

        for i, result in enumerate(search_results):
            # Kaynak bilgisi
            sources.append(
                SourceInfo(
                    section_title=result.get("metadata", {}).get(
                        "section_title", "Bilinmiyor"
                    ),
                    source_file=result.get("metadata", {}).get(
                        "source_file", "Bilinmiyor"
                    ),
                    score=round(result.get("score", 0), 4),
                )
            )

            # Context metni
            section = result.get("metadata", {}).get("section_title", "")
            text = result.get("text", "")
            context_parts.append(f"--- Kaynak {i + 1} [{section}] ---\n{text}")

        context_text = "\n\n".join(context_parts) if context_parts else "(Dokumanda ilgili bilgi bulunamadi)"

        # ═══════════════════════════════════════
        # RAG ADIM 2: AUGMENTATION - Prompt Olustur
        # ═══════════════════════════════════════
        system_prompt = IK_SYSTEM_PROMPT.format(context=context_text)

        messages = [{"role": "system", "content": system_prompt}]

        # Chat gecmisini ekle (son 6 mesaj)
        if request.chat_history:
            for msg in request.chat_history[-6:]:
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": request.message})

        # ═══════════════════════════════════════
        # RAG ADIM 3: GENERATION - Azure OpenAI
        # ═══════════════════════════════════════
        response = azure_client.chat.completions.create(
            model=azure_deployment,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        response_text = response.choices[0].message.content.strip()

        # ═══════════════════════════════════════
        # Token Kullanimi Kaydet
        # ═══════════════════════════════════════
        token_info = None
        usage = response.usage
        if usage:
            token_info = TokenInfo(
                input=usage.prompt_tokens,
                output=usage.completion_tokens,
                total=usage.total_tokens,
            )

            # SQLite'a logla
            try:
                log_token_usage(
                    agent_adi="IK Chatbot API",
                    model=f"azure/{azure_deployment}",
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="Chatbot Soru-Cevap",
                )
            except Exception as e:
                logger.warning(f"Token loglama hatasi: {e}")

        logger.info(
            f"Chat yaniti uretildi: "
            f"{len(response_text)} karakter, "
            f"{usage.total_tokens if usage else '?'} token"
        )

        return ChatResponse(
            response=response_text,
            sources=sources,
            tokens=token_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat hatasi: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Yanit uretilemedi: {str(e)}",
        )


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT: GET /health
# ══════════════════════════════════════════════════════════════════════


@app.get(
    "/health",
    summary="Servis saglik kontrolu",
    description="RAG index ve Azure baglanti durumunu kontrol eder.",
)
async def health():
    """Sunucu ve bagimliliklarin durumunu dondurur."""
    rag_ready = ik_rag is not None and ik_rag.get_document_count() > 0
    azure_ready = azure_client is not None

    status = "healthy" if (rag_ready and azure_ready) else "degraded"

    return {
        "status": status,
        "components": {
            "rag_index": {
                "ready": rag_ready,
                "document_count": ik_rag.get_document_count() if ik_rag else 0,
            },
            "azure_openai": {
                "ready": azure_ready,
                "endpoint": AZURE_ENDPOINT[:40] + "..." if AZURE_ENDPOINT else "N/A",
                "deployment": azure_deployment or "N/A",
            },
            "embedding": {
                "ready": bool(OPENAI_API_KEY),
                "model": "text-embedding-3-small",
            },
        },
    }


# ══════════════════════════════════════════════════════════════════════
# DOGRUDAN CALISTIRMA
# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
