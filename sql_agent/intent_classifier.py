"""
SQL Agent - Intent Classifier.

Kullanicinin sorusunu analiz ederek BW mi SAP mi olduguna karar verir.
LLM-based siniflandirma ile yuksek dogruluk saglar.
"""
import json

from openai import OpenAI

from token_tracker import log_token_usage


INTENT_SYSTEM_PROMPT = """Sen bir SAP soru siniflandirici yapay zekasin.
Kullanicinin Turkce sorusunu analiz ederek sorgunun SAP (transactional) mi yoksa
BW (Business Warehouse / raporlama) mi olduguna karar veriyorsun.

SINIFLANDIRMA KURALLARI:

BW (Business Warehouse) sinyalleri:
- Rapor, trend, analiz, KPI, karsilastirma, istatistik
- Aylik/yillik/donemsel toplam, ozet, ortalama
- "Son 6 ay", "gecen yil", "bu ceyrek" gibi donemsel ifadeler
- Gelir, ciro, kar, maliyet TRENDI
- Fire orani, uretim verimi, kalite istatistigi
- InfoCube, DSO, ADSO, InfoProvider referanslari
- Dashbord, grafik, chart icin veri talebi
- "Karsilastir", "trend goster", "analiz et" gibi fiiller

SAP (Transactional) sinyalleri:
- Belirli bir malzeme, siparis, musteri, tedarikci sorgulama
- Stok durumu, fatura, teslimat, sevkiyat
- Master data: malzeme adi, musteri adresi, tedarikci bilgisi
- "Getir", "listele", "goster", "bul" gibi fiiller
- Belirli bir belge numarasi (siparis no, malzeme no)
- Guncel/anlik veri talebi (stok, acik siparisler)
- MARA, EKKO, VBAK, LFA1 gibi standart tablo referanslari

KARISIK DURUMLAR:
- "Malzeme bazli toplam satis" → BW (aggregation var)
- "Malzeme 1234'un stoku" → SAP (belirli kayit sorgusu)
- "Aylik fire raporu" → BW (donemsel rapor)
- "Tedarikci listesi" → SAP (master data)

CIKTINI MUTLAKA ASAGIDAKI JSON FORMATINDA VER:
{"db": "BW" veya "SAP", "confidence": 0.0-1.0 arasi, "reason": "kisa aciklama"}
"""


def classify_intent(question: str, api_key: str, model: str = "gpt-4o-mini") -> dict:
    """
    Sorunun BW mi SAP mi olduguna karar verir.

    Args:
        question: Kullanicinin Turkce sorusu
        api_key: OpenAI API anahtari
        model: Kullanilacak LLM modeli

    Returns:
        {"db": "BW" | "SAP", "confidence": float, "reason": str}
    """
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"},
        )

        # Token kullanimi kaydet
        try:
            usage = response.usage
            if usage:
                log_token_usage(
                    agent_adi="Intent Classifier",
                    model=model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    islem_turu="Intent Siniflandirma",
                )
        except Exception:
            pass

        content = response.choices[0].message.content
        result = json.loads(content)

        # Varsayilan degerler
        return {
            "db": result.get("db", "SAP").upper(),
            "confidence": float(result.get("confidence", 0.5)),
            "reason": result.get("reason", ""),
        }

    except Exception as e:
        # Hata durumunda SAP'ye varsayilan olarak don
        return {
            "db": "SAP",
            "confidence": 0.0,
            "reason": f"Intent siniflandirma hatasi: {e}",
        }
