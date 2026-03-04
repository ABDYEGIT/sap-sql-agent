"""
Yorglass SAP AI Platform - Mimari ve Akis Diyagrami Sayfasi.

Projenin genel mimarisini, her agent'in calisma akisini
ve teknoloji yigitini gorsel olarak sunar.
"""
import streamlit as st


def render_architecture_page():
    """Proje mimarisi ve akis diyagramini gorsel olarak render eder."""

    # ── Ozel CSS ──
    st.markdown("""
    <style>
    .arch-hero {
        text-align: center;
        padding: 30px 0 20px 0;
    }
    .arch-hero h1 {
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 4px;
    }
    .arch-hero .subtitle {
        color: rgba(250,250,250,0.5);
        font-size: 0.95rem;
        letter-spacing: 1px;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FF8A65;
        border-bottom: 2px solid rgba(255,87,34,0.3);
        padding-bottom: 8px;
        margin: 30px 0 16px 0;
        letter-spacing: 1px;
    }

    .agent-card {
        background: linear-gradient(135deg, rgba(255,87,34,0.08) 0%, rgba(255,87,34,0.02) 100%);
        border: 1px solid rgba(255,87,34,0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        min-height: 220px;
        transition: transform 0.2s, border-color 0.2s;
    }
    .agent-card:hover {
        border-color: rgba(255,87,34,0.5);
        transform: translateY(-2px);
    }
    .agent-card .agent-icon {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .agent-card .agent-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FF8A65;
        margin-bottom: 6px;
    }
    .agent-card .agent-desc {
        font-size: 0.85rem;
        color: rgba(250,250,250,0.7);
        margin-bottom: 12px;
        line-height: 1.4;
    }
    .agent-card .agent-tech {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }
    .tech-badge {
        background: rgba(255,87,34,0.15);
        border: 1px solid rgba(255,87,34,0.25);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.72rem;
        color: #FFB74D;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .flow-container {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 24px;
        margin: 12px 0;
    }

    .flow-step {
        display: flex;
        align-items: center;
        margin: 10px 0;
    }
    .flow-step-num {
        background: #FF5722;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.8rem;
        flex-shrink: 0;
        margin-right: 12px;
    }
    .flow-step-text {
        font-size: 0.9rem;
        color: rgba(250,250,250,0.85);
    }
    .flow-step-text strong {
        color: #FF8A65;
    }
    .flow-arrow {
        text-align: center;
        color: rgba(255,87,34,0.5);
        font-size: 1.2rem;
        margin: 4px 0;
        letter-spacing: 4px;
    }

    .tech-layer {
        background: linear-gradient(135deg, rgba(33,150,243,0.08) 0%, rgba(33,150,243,0.02) 100%);
        border: 1px solid rgba(33,150,243,0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .tech-layer .layer-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #64B5F6;
        margin-bottom: 8px;
    }
    .tech-layer .layer-items {
        font-size: 0.85rem;
        color: rgba(250,250,250,0.7);
        line-height: 1.6;
    }

    .overview-box {
        background: rgba(76,175,80,0.06);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        text-align: center;
    }
    .overview-box .box-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #81C784;
        margin-bottom: 6px;
    }
    .overview-box .box-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #4CAF50;
    }
    .overview-box .box-desc {
        font-size: 0.75rem;
        color: rgba(250,250,250,0.4);
        margin-top: 4px;
    }

    .entry-box {
        background: rgba(156,39,176,0.08);
        border: 1px solid rgba(156,39,176,0.25);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .entry-box .entry-icon { font-size: 1.8rem; margin-bottom: 6px; }
    .entry-box .entry-title {
        font-weight: 700;
        color: #CE93D8;
        font-size: 0.95rem;
    }
    .entry-box .entry-desc {
        font-size: 0.78rem;
        color: rgba(250,250,250,0.5);
        margin-top: 4px;
    }

    .connector-arrow {
        text-align: center;
        font-size: 1.5rem;
        color: rgba(255,87,34,0.4);
        padding: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # HERO
    # ══════════════════════════════════════════
    st.markdown("""
    <div class="arch-hero">
        <h1>Yorglass SAP AI Platform</h1>
        <div class="subtitle">Mimari ve Akis Diyagrami</div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # GENEL BAKIS METRIKLERI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Genel Bakis</div>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown("""
        <div class="overview-box">
            <div class="box-value">5</div>
            <div class="box-title">AI Agent</div>
            <div class="box-desc">SQL, BAPI, SD/MM, Fis, IK</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="overview-box">
            <div class="box-value">3</div>
            <div class="box-title">RAG Motoru</div>
            <div class="box-desc">ChromaDB + Cosine</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="overview-box">
            <div class="box-value">2</div>
            <div class="box-title">LLM Model</div>
            <div class="box-desc">gpt-4o-mini + gpt-4o</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown("""
        <div class="overview-box">
            <div class="box-value">9</div>
            <div class="box-title">SAP Tablo</div>
            <div class="box-desc">Mock DB - 237 Kayit</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown("""
        <div class="overview-box">
            <div class="box-value">2</div>
            <div class="box-title">Giris Noktasi</div>
            <div class="box-desc">Streamlit + MCP</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # GIRIS NOKTALARI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Giris Noktalari</div>', unsafe_allow_html=True)

    e1, e_arrow, e2 = st.columns([2, 1, 2])
    with e1:
        st.markdown("""
        <div class="entry-box">
            <div class="entry-icon">🌐</div>
            <div class="entry-title">Streamlit Web UI</div>
            <div class="entry-desc">app.py - Tarayici uzerinden erisim<br>
            Kullanicilar sidebar'dan agent secer</div>
        </div>
        """, unsafe_allow_html=True)
    with e_arrow:
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:rgba(255,87,34,0.4);">
            <div style="font-size:0.8rem; margin-bottom:4px;">Her iki giris noktasi da</div>
            <div style="font-size:1.5rem;">⟶ 5 Agent ⟵</div>
            <div style="font-size:0.8rem; margin-top:4px;">ayni agent'lari kullanir</div>
        </div>
        """, unsafe_allow_html=True)
    with e2:
        st.markdown("""
        <div class="entry-box">
            <div class="entry-icon">🤖</div>
            <div class="entry-title">MCP Server (Claude Desktop)</div>
            <div class="entry-desc">mcp_server.py - stdio JSON-RPC<br>
            5 tool olarak disariya acilir</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # 5 AGENT KARTLARI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">5 AI Agent</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">🗃️</div>
            <div class="agent-name">1. SQL Generator Agent</div>
            <div class="agent-desc">
                Dogal dil sorusunu SAP Open SQL sorgusuna cevirir.
                RAG ile ilgili tablolari bulur, iliski grafi ile genisletir.
            </div>
            <div class="agent-tech">
                <span class="tech-badge">RAG</span>
                <span class="tech-badge">gpt-4o-mini</span>
                <span class="tech-badge">11 SAP Tablo</span>
                <span class="tech-badge">ABAP 7.40+</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with a2:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">⚙️</div>
            <div class="agent-name">2. BAPI Asistani Agent</div>
            <div class="agent-desc">
                Yapilmak istenen isleme gore uygun BAPI'yi bulur.
                Parametre detaylari ve ABAP kod ornegi sunar.
            </div>
            <div class="agent-tech">
                <span class="tech-badge">RAG</span>
                <span class="tech-badge">gpt-4o-mini</span>
                <span class="tech-badge">5 BAPI</span>
                <span class="tech-badge">Parametre Rehber</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with a3:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">🔀</div>
            <div class="agent-name">3. SD/MM Agent (Orkestrator)</div>
            <div class="agent-desc">
                Intent detection ile sorguyu analiz eder.
                Listeleme ise SQL, olusturma ise BAPI pipeline'a yonlendirir.
            </div>
            <div class="agent-tech">
                <span class="tech-badge">Intent Detection</span>
                <span class="tech-badge">SQL + BAPI</span>
                <span class="tech-badge">Mock DB</span>
                <span class="tech-badge">Orkestrasyon</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    a4, a5 = st.columns(2)
    with a4:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">🧾</div>
            <div class="agent-name">4. Fis Okuyucu Agent</div>
            <div class="agent-desc">
                Fis gorselini GPT-4o Vision ile okur. Kalem kalem urun detayi cikarir.
                Alkol/sigara kalemleri otomatik engellenir, tutardan dusulur.
            </div>
            <div class="agent-tech">
                <span class="tech-badge">GPT-4o Vision</span>
                <span class="tech-badge">OCR</span>
                <span class="tech-badge">SQLite DB</span>
                <span class="tech-badge">Yasal Kontrol</span>
                <span class="tech-badge">Kalem Analiz</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with a5:
        st.markdown("""
        <div class="agent-card">
            <div class="agent-icon">👥</div>
            <div class="agent-name">5. IK Asistani Agent</div>
            <div class="agent-desc">
                Yorglass IK prosedur dokumani uzerinde RAG tabanli soru-cevap.
                Izin, mesai, disiplin, performans gibi konularda cevap verir.
            </div>
            <div class="agent-tech">
                <span class="tech-badge">RAG</span>
                <span class="tech-badge">gpt-4o-mini</span>
                <span class="tech-badge">Word Dokuman</span>
                <span class="tech-badge">48 Chunk</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # DETAYLI AKIS DIYAGRAMLARI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Agent Akis Detaylari</div>', unsafe_allow_html=True)

    # ── SQL Generator Akisi ──
    with st.expander("🗃️ SQL Generator Agent Akisi", expanded=False):
        st.markdown("""
        <div class="flow-container">
            <div class="flow-step">
                <div class="flow-step-num">1</div>
                <div class="flow-step-text"><strong>Kullanici Sorusu</strong> → "Stoku 100'den fazla olan malzemeleri listele"</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">2</div>
                <div class="flow-step-text"><strong>RAG Vektor Arama</strong> → ChromaDB'de sql_tables koleksiyonunda top_k=5 arama</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">3</div>
                <div class="flow-step-text"><strong>Iliski Grafi Genisletme</strong> → Bulunan tablolarin iliskili tablolarini ekle (max_hops=1)</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">4</div>
                <div class="flow-step-text"><strong>Prompt Olustur</strong> → System prompt + Tablo metadata + Chat history birlestir</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">5</div>
                <div class="flow-step-text"><strong>LLM (gpt-4o-mini)</strong> → ABAP 7.40+ SAP Open SQL sorgusu uret</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">6</div>
                <div class="flow-step-text"><strong>SQL Blogu Cikar</strong> → extract_sql_block() ile yanit icinden SQL kodunu ayikla</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── BAPI Asistani Akisi ──
    with st.expander("⚙️ BAPI Asistani Agent Akisi", expanded=False):
        st.markdown("""
        <div class="flow-container">
            <div class="flow-step">
                <div class="flow-step-num">1</div>
                <div class="flow-step-text"><strong>Kullanici Sorusu</strong> → "Malzeme olusturmak istiyorum"</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">2</div>
                <div class="flow-step-text"><strong>RAG Vektor Arama</strong> → ChromaDB'de bapi_functions koleksiyonunda top_k=3 arama</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">3</div>
                <div class="flow-step-text"><strong>En Yakin BAPI Bul</strong> → BAPI_MATERIAL_SAVEDATA (cosine similarity)</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">4</div>
                <div class="flow-step-text"><strong>Prompt + BAPI Metadata</strong> → Parametreler, alanlar, veri tipleri prompt'a eklenir</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">5</div>
                <div class="flow-step-text"><strong>LLM (gpt-4o-mini)</strong> → Parametre rehberi + ABAP kod ornegi uret</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── SD/MM Agent Akisi ──
    with st.expander("🔀 SD/MM Agent Akisi (Orkestrator)", expanded=False):
        st.markdown("""
        <div class="flow-container">
            <div class="flow-step">
                <div class="flow-step-num">1</div>
                <div class="flow-step-text"><strong>Kullanici Sorusu</strong> → Herhangi bir SAP islemi</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">2</div>
                <div class="flow-step-text"><strong>Intent Detection (gpt-4o-mini, temp=0.0)</strong> → Sorunun amacini belirle</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">3</div>
                <div class="flow-step-text">
                    <strong>Yonlendirme:</strong><br>
                    &nbsp;&nbsp;📊 Listeleme / Sorgulama → <strong>SQL Pipeline</strong> (RAG → SQL Uret → SAP-to-SQLite → Mock DB → Sonuc)<br>
                    &nbsp;&nbsp;📝 Olusturma / Guncelleme → <strong>BAPI Pipeline</strong> (RAG → BAPI Bul → Parametre Rehberi)
                </div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">4</div>
                <div class="flow-step-text"><strong>SQL Pipeline ise:</strong> SAP SQL → SQLite cevirisi → Mock DB'de calistir → Sonuc tablosu</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Fis Okuyucu Akisi ──
    with st.expander("🧾 Fis Okuyucu Agent Akisi", expanded=False):
        st.markdown("""
        <div class="flow-container">
            <div class="flow-step">
                <div class="flow-step-num">1</div>
                <div class="flow-step-text"><strong>Fis Gorseli</strong> → JPG/PNG formatinda yuklenir</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">2</div>
                <div class="flow-step-text"><strong>Base64 Encoding</strong> → Gorsel binary → base64 string cevirisi</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">3</div>
                <div class="flow-step-text"><strong>GPT-4o Vision API</strong> → OCR prompt + gorsel gonderilir (detail: high)</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">4</div>
                <div class="flow-step-text"><strong>JSON Parse</strong> → Isletme adi, vergi no, tarih, tutar, KDV, kalemler cikarilir</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">5</div>
                <div class="flow-step-text"><strong>Kalem Isleme</strong> → Her urun: ad, adet, birim fiyat, toplam, kategori (alkol/sigara/normal)</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">6</div>
                <div class="flow-step-text">
                    <strong>Yasal Kontrol (2 Katman):</strong><br>
                    &nbsp;&nbsp;Katman 1: Fis turu kontrolu (tamamen alkol/sigara fisi → ENGELLE)<br>
                    &nbsp;&nbsp;Katman 2: Kalem seviyesi kontrol (GPT kategori + anahtar kelime tarama)
                </div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">7</div>
                <div class="flow-step-text">
                    <strong>Sonuc:</strong><br>
                    &nbsp;&nbsp;✅ Normal kalemler → Masraf olarak kaydedilir<br>
                    &nbsp;&nbsp;🚫 Alkol/Sigara kalemler → Toplam tutardan dusulur, kaydedilmez
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── IK Asistani Akisi ──
    with st.expander("👥 IK Asistani Agent Akisi", expanded=False):
        st.markdown("""
        <div class="flow-container">
            <div class="flow-step">
                <div class="flow-step-num">1</div>
                <div class="flow-step-text"><strong>Dokuman Indexleme</strong> → yorglass_ik_prosedur.docx → 500 char chunk, 100 overlap → 48 chunk</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">2</div>
                <div class="flow-step-text"><strong>Kullanici Sorusu</strong> → "Yillik izin hakki kac gun?"</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">3</div>
                <div class="flow-step-text"><strong>RAG Vektor Arama</strong> → ChromaDB'de ik_documents koleksiyonunda top_k=5 chunk ara</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">4</div>
                <div class="flow-step-text"><strong>Context Olustur</strong> → En ilgili chunk'lari prompt'a ekle + kaynak referanslari</div>
            </div>
            <div class="flow-arrow">▼</div>
            <div class="flow-step">
                <div class="flow-step-num">5</div>
                <div class="flow-step-text"><strong>LLM (gpt-4o-mini)</strong> → Cevap uret + kaynak bolum basliklarini goster</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # RAG PIPELINE
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">RAG (Retrieval-Augmented Generation) Pipeline</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(255,87,34,0.1) 0%, rgba(255,87,34,0.03) 100%); border-color: rgba(255,87,34,0.25);">
            <div class="layer-title" style="color: #FF8A65;">1. Indexing</div>
            <div class="layer-items">
                📄 Veri kaynagi yukle<br>
                (Excel / Word)<br><br>
                🔢 Embedding olustur<br>
                text-embedding-3-small<br>
                1536 boyut vektor<br><br>
                💾 ChromaDB'ye kaydet
            </div>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(33,150,243,0.1) 0%, rgba(33,150,243,0.03) 100%); border-color: rgba(33,150,243,0.25);">
            <div class="layer-title" style="color: #64B5F6;">2. Retrieval</div>
            <div class="layer-items">
                ❓ Kullanici sorusu<br><br>
                🔍 Soru embedding olustur<br><br>
                📊 ChromaDB'de ara<br>
                top_k = 5<br>
                Cosine Similarity<br><br>
                🎯 Skor filtreleme (esik: 0.3)
            </div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(76,175,80,0.1) 0%, rgba(76,175,80,0.03) 100%); border-color: rgba(76,175,80,0.25);">
            <div class="layer-title" style="color: #81C784;">3. Augmentation</div>
            <div class="layer-items">
                📋 Ilgili dokumanlari<br>
                prompt'a ekle<br><br>
                🧩 System Prompt<br>
                + Context (RAG sonuc)<br>
                + Chat History<br><br>
                ➡️ Zenginlestirilmis prompt
            </div>
        </div>
        """, unsafe_allow_html=True)
    with r4:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(156,39,176,0.1) 0%, rgba(156,39,176,0.03) 100%); border-color: rgba(156,39,176,0.25);">
            <div class="layer-title" style="color: #CE93D8;">4. Generation</div>
            <div class="layer-items">
                🤖 gpt-4o-mini<br>
                temperature = 0.2<br><br>
                📝 Yapilandirilmis yanit<br>
                (SQL / BAPI / Cevap)<br><br>
                ✅ Kullaniciya sun
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # MCP SERVER YAPISI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">MCP Server Yapisi</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="flow-container">
        <div style="text-align:center; margin-bottom:16px;">
            <span style="font-size:1.1rem; color:#CE93D8; font-weight:700;">Claude Desktop / Claude Code</span>
            <span style="color:rgba(250,250,250,0.3);"> ──── stdio JSON-RPC ────</span>
            <span style="font-size:1.1rem; color:#FF8A65; font-weight:700;"> FastMCP Server (yorglass-sap)</span>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:center;">
            <div style="background:rgba(255,87,34,0.1); border:1px solid rgba(255,87,34,0.25); border-radius:8px; padding:12px 16px; min-width:160px; text-align:center;">
                <div style="font-weight:700; color:#FF8A65; margin-bottom:4px;">sap_sql_query</div>
                <div style="font-size:0.75rem; color:rgba(250,250,250,0.5);">Dogal dil → SQL</div>
            </div>
            <div style="background:rgba(255,87,34,0.1); border:1px solid rgba(255,87,34,0.25); border-radius:8px; padding:12px 16px; min-width:160px; text-align:center;">
                <div style="font-weight:700; color:#FF8A65; margin-bottom:4px;">bapi_lookup</div>
                <div style="font-size:0.75rem; color:rgba(250,250,250,0.5);">Islem → BAPI rehberi</div>
            </div>
            <div style="background:rgba(255,87,34,0.1); border:1px solid rgba(255,87,34,0.25); border-radius:8px; padding:12px 16px; min-width:160px; text-align:center;">
                <div style="font-weight:700; color:#FF8A65; margin-bottom:4px;">hr_policy_search</div>
                <div style="font-size:0.75rem; color:rgba(250,250,250,0.5);">IK soru-cevap</div>
            </div>
            <div style="background:rgba(255,87,34,0.1); border:1px solid rgba(255,87,34,0.25); border-radius:8px; padding:12px 16px; min-width:160px; text-align:center;">
                <div style="font-weight:700; color:#FF8A65; margin-bottom:4px;">receipt_scan</div>
                <div style="font-size:0.75rem; color:rgba(250,250,250,0.5);">Fis gorseli → OCR</div>
            </div>
            <div style="background:rgba(255,87,34,0.1); border:1px solid rgba(255,87,34,0.25); border-radius:8px; padding:12px 16px; min-width:160px; text-align:center;">
                <div style="font-weight:700; color:#FF8A65; margin-bottom:4px;">receipt_history</div>
                <div style="font-size:0.75rem; color:rgba(250,250,250,0.5);">Kayitli fisler</div>
            </div>
        </div>
        <div style="text-align:center; margin-top:16px;">
            <div style="font-size:0.8rem; color:rgba(250,250,250,0.35);">
                startup() → API Key + 3 RAG Engine + Mock DB + Receipt DB yuklenir
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # TEKNOLOJI KATMANLARI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Teknoloji Katmanlari</div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(156,39,176,0.1) 0%, rgba(156,39,176,0.03) 100%); border-color: rgba(156,39,176,0.25);">
            <div class="layer-title" style="color: #CE93D8;">UI Katmani</div>
            <div class="layer-items">
                🌐 <strong>Streamlit</strong><br>
                &nbsp;&nbsp;&nbsp;Web arayuzu<br><br>
                🤖 <strong>Claude Desktop</strong><br>
                &nbsp;&nbsp;&nbsp;MCP Client<br><br>
                🔧 <strong>FastMCP</strong><br>
                &nbsp;&nbsp;&nbsp;stdio transport
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t2:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(255,87,34,0.1) 0%, rgba(255,87,34,0.03) 100%); border-color: rgba(255,87,34,0.25);">
            <div class="layer-title" style="color: #FF8A65;">Agent Katmani</div>
            <div class="layer-items">
                🗃️ <strong>SQL Agent</strong><br>
                &nbsp;&nbsp;&nbsp;generator.py<br><br>
                ⚙️ <strong>BAPI Agent</strong><br>
                &nbsp;&nbsp;&nbsp;generator.py<br><br>
                🔀 <strong>SD/MM Agent</strong><br>
                &nbsp;&nbsp;&nbsp;orchestrator.py<br><br>
                🧾 <strong>Receipt Agent</strong><br>
                &nbsp;&nbsp;&nbsp;ocr_parser.py<br><br>
                👥 <strong>IK Agent</strong><br>
                &nbsp;&nbsp;&nbsp;generator.py
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t3:
        st.markdown("""
        <div class="tech-layer">
            <div class="layer-title">AI Katmani</div>
            <div class="layer-items">
                💬 <strong>gpt-4o-mini</strong><br>
                &nbsp;&nbsp;&nbsp;Metin uretimi<br>
                &nbsp;&nbsp;&nbsp;SQL, BAPI, IK<br><br>
                👁️ <strong>gpt-4o</strong><br>
                &nbsp;&nbsp;&nbsp;Vision OCR<br>
                &nbsp;&nbsp;&nbsp;Fis okuma<br><br>
                📐 <strong>text-embedding-3-small</strong><br>
                &nbsp;&nbsp;&nbsp;Vektorlestirme<br>
                &nbsp;&nbsp;&nbsp;1536 boyut
            </div>
        </div>
        """, unsafe_allow_html=True)
    with t4:
        st.markdown("""
        <div class="tech-layer" style="background: linear-gradient(135deg, rgba(76,175,80,0.1) 0%, rgba(76,175,80,0.03) 100%); border-color: rgba(76,175,80,0.25);">
            <div class="layer-title" style="color: #81C784;">Veri Katmani</div>
            <div class="layer-items">
                🔮 <strong>ChromaDB</strong><br>
                &nbsp;&nbsp;&nbsp;Vektor veritabani<br>
                &nbsp;&nbsp;&nbsp;3 koleksiyon<br><br>
                🗄️ <strong>SQLite</strong><br>
                &nbsp;&nbsp;&nbsp;Mock DB (9 tablo)<br>
                &nbsp;&nbsp;&nbsp;Receipt DB<br><br>
                📊 <strong>Excel + Word</strong><br>
                &nbsp;&nbsp;&nbsp;SAP metadata<br>
                &nbsp;&nbsp;&nbsp;IK dokumanlari
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # GENEL SISTEM AKIS DIYAGRAMI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Genel Sistem Akis Diyagrami</div>', unsafe_allow_html=True)

    # Flowchart CSS
    st.markdown("""
    <style>
    .fc { position: relative; padding: 20px 0; }
    .fc-row { display: flex; justify-content: center; align-items: center; gap: 16px; margin: 0; flex-wrap: wrap; }
    .fc-box { border-radius: 10px; padding: 14px 20px; text-align: center; min-width: 140px; max-width: 200px; position: relative; }
    .fc-user { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); border: 2px solid #5c6bc0; color: #fff; }
    .fc-entry { background: linear-gradient(135deg, #4a148c 0%, #6a1b9a 100%); border: 2px solid #ab47bc; color: #fff; }
    .fc-agent { background: linear-gradient(135deg, #bf360c 0%, #e65100 100%); border: 2px solid #ff8a65; color: #fff; }
    .fc-infra { background: linear-gradient(135deg, #004d40 0%, #00695c 100%); border: 2px solid #4db6ac; color: #fff; }
    .fc-data { background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); border: 2px solid #66bb6a; color: #fff; }
    .fc-result { background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%); border: 2px solid #42a5f5; color: #fff; }
    .fc-box .fc-icon { font-size: 1.4rem; margin-bottom: 4px; }
    .fc-box .fc-label { font-weight: 700; font-size: 0.85rem; line-height: 1.3; }
    .fc-box .fc-sub { font-size: 0.7rem; opacity: 0.7; margin-top: 3px; }
    .fc-arrows { display: flex; justify-content: center; align-items: center; padding: 6px 0; gap: 8px; }
    .fc-arrow-down { display: flex; flex-direction: column; align-items: center; color: #ff8a65; }
    .fc-arrow-down .fc-line { width: 3px; height: 20px; background: linear-gradient(to bottom, #ff8a65, #ff5722); border-radius: 2px; }
    .fc-arrow-down .fc-head { width: 0; height: 0; border-left: 8px solid transparent; border-right: 8px solid transparent; border-top: 10px solid #ff5722; }
    .fc-arrow-down .fc-text { font-size: 0.65rem; color: rgba(255,138,101,0.8); margin-top: 2px; white-space: nowrap; }
    .fc-branch { display: flex; justify-content: center; align-items: stretch; gap: 20px; margin: 0; flex-wrap: wrap; }
    .fc-branch-item { display: flex; flex-direction: column; align-items: center; gap: 6px; }
    .fc-diamond { width: 120px; height: 60px; background: linear-gradient(135deg, #f57f17, #ff8f00); border: 2px solid #ffc107; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; font-size: 0.8rem; }
    .fc-divider { border: none; height: 1px; background: linear-gradient(to right, transparent, rgba(255,87,34,0.3), transparent); margin: 24px 0; }
    .fc-section-label { text-align: center; font-size: 0.75rem; color: rgba(250,250,250,0.3); letter-spacing: 3px; text-transform: uppercase; margin: 8px 0 12px 0; }
    </style>
    """, unsafe_allow_html=True)

    # Part 1: User → Entry Points → 5 Agents
    st.markdown("""
    <div class="fc">
        <div class="fc-section-label">Kullanici</div>
        <div class="fc-row">
            <div class="fc-box fc-user">
                <div class="fc-icon">👤</div>
                <div class="fc-label">Kullanici</div>
                <div class="fc-sub">Dogal dil sorusu<br>veya fis gorseli</div>
            </div>
        </div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div></div>
        <div class="fc-section-label">Giris Noktalari</div>
        <div class="fc-row">
            <div class="fc-box fc-entry">
                <div class="fc-icon">🌐</div>
                <div class="fc-label">Streamlit UI</div>
                <div class="fc-sub">app.py<br>Web tarayici</div>
            </div>
            <div style="color:rgba(250,250,250,0.3); font-size:0.9rem; padding:0 8px;">veya</div>
            <div class="fc-box fc-entry">
                <div class="fc-icon">🤖</div>
                <div class="fc-label">MCP Server</div>
                <div class="fc-sub">mcp_server.py<br>Claude Desktop</div>
            </div>
        </div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">agent secimi / tool cagirisi</div></div></div>
        <div class="fc-section-label">5 AI Agent</div>
        <div class="fc-row">
            <div class="fc-box fc-agent"><div class="fc-icon">🗃️</div><div class="fc-label">SQL Generator</div><div class="fc-sub">Dogal dil → SQL</div></div>
            <div class="fc-box fc-agent"><div class="fc-icon">⚙️</div><div class="fc-label">BAPI Asistani</div><div class="fc-sub">Islem → BAPI</div></div>
            <div class="fc-box fc-agent"><div class="fc-icon">🔀</div><div class="fc-label">SD/MM Agent</div><div class="fc-sub">Orkestrator</div></div>
            <div class="fc-box fc-agent"><div class="fc-icon">🧾</div><div class="fc-label">Fis Okuyucu</div><div class="fc-sub">Vision OCR</div></div>
            <div class="fc-box fc-agent"><div class="fc-icon">👥</div><div class="fc-label">IK Asistani</div><div class="fc-sub">RAG Soru-Cevap</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Part 2: AI Infrastructure → Data Layer
    st.markdown("""
    <div class="fc">
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">RAG arama + LLM cagirisi</div></div></div>
        <div class="fc-section-label">AI Altyapisi</div>
        <div class="fc-row">
            <div class="fc-box fc-infra"><div class="fc-icon">🔮</div><div class="fc-label">RAG Engine</div><div class="fc-sub">ChromaDB<br>Cosine Similarity<br>top_k = 5</div></div>
            <div class="fc-box fc-infra"><div class="fc-icon">📐</div><div class="fc-label">Embedding</div><div class="fc-sub">text-embedding<br>-3-small<br>1536 boyut</div></div>
            <div class="fc-box fc-infra"><div class="fc-icon">💬</div><div class="fc-label">gpt-4o-mini</div><div class="fc-sub">Metin uretimi<br>SQL / BAPI / IK<br>temp: 0.2</div></div>
            <div class="fc-box fc-infra"><div class="fc-icon">👁️</div><div class="fc-label">gpt-4o Vision</div><div class="fc-sub">Gorsel analiz<br>Fis OCR<br>detail: high</div></div>
        </div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">veri okuma / yazma</div></div></div>
        <div class="fc-section-label">Veri Katmani</div>
        <div class="fc-row">
            <div class="fc-box fc-data"><div class="fc-icon">📊</div><div class="fc-label">Excel Metadata</div><div class="fc-sub">11 SAP Tablo<br>5 BAPI</div></div>
            <div class="fc-box fc-data"><div class="fc-icon">📄</div><div class="fc-label">Word Dokuman</div><div class="fc-sub">IK Prosedur<br>17 Bolum, 48 Chunk</div></div>
            <div class="fc-box fc-data"><div class="fc-icon">🗄️</div><div class="fc-label">Mock SQLite DB</div><div class="fc-sub">9 Tablo<br>237 Kayit</div></div>
            <div class="fc-box fc-data"><div class="fc-icon">🧾</div><div class="fc-label">Receipt DB</div><div class="fc-sub">Fis veritabani<br>SQLite</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Part 3: Output → User
    st.markdown("""
    <div class="fc">
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">sonuc uret</div></div></div>
        <div class="fc-section-label">Cikti</div>
        <div class="fc-row">
            <div class="fc-box fc-result"><div class="fc-icon">📋</div><div class="fc-label">SAP Open SQL</div><div class="fc-sub">ABAP 7.40+ sorgu</div></div>
            <div class="fc-box fc-result"><div class="fc-icon">📦</div><div class="fc-label">BAPI Rehberi</div><div class="fc-sub">Parametre + ABAP kod</div></div>
            <div class="fc-box fc-result"><div class="fc-icon">📊</div><div class="fc-label">Sorgu Sonucu</div><div class="fc-sub">DataFrame tablo</div></div>
            <div class="fc-box fc-result"><div class="fc-icon">🧾</div><div class="fc-label">Fis Verisi</div><div class="fc-sub">JSON + Kalemler<br>Yasal kontrol</div></div>
            <div class="fc-box fc-result"><div class="fc-icon">💬</div><div class="fc-label">IK Cevabi</div><div class="fc-sub">Kaynak referansli</div></div>
        </div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">kullaniciya goster</div></div></div>
        <div class="fc-row">
            <div class="fc-box fc-user"><div class="fc-icon">✅</div><div class="fc-label">Kullaniciya Sunulur</div><div class="fc-sub">Chat / Tablo / Form</div></div>
        </div>
    </div>
    <hr class="fc-divider">
    """, unsafe_allow_html=True)

    # Part 4: SD/MM Orchestration Detail
    st.markdown("""
    <div class="fc-section-label" style="margin-top:20px;">SD/MM Agent - Orkestrasyon Akisi (Detay)</div>
    <div class="fc">
        <div class="fc-row"><div class="fc-box fc-user"><div class="fc-icon">❓</div><div class="fc-label">Kullanici Sorusu</div></div></div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div></div>
        <div class="fc-row"><div class="fc-diamond">Intent Detection<br>gpt-4o-mini</div></div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">intent nedir?</div></div></div>
        <div class="fc-branch">
            <div class="fc-branch-item">
                <div style="color:#64B5F6; font-weight:700; font-size:0.8rem;">Listeleme / Sorgulama</div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-box fc-infra" style="min-width:180px;"><div class="fc-label">SQL Pipeline</div><div class="fc-sub">RAG → SQL Uret<br>→ SAP-to-SQLite<br>→ Mock DB Calistir</div></div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-box fc-result" style="min-width:180px;"><div class="fc-icon">📊</div><div class="fc-label">Sonuc Tablosu</div></div>
            </div>
            <div class="fc-branch-item">
                <div style="color:#FF8A65; font-weight:700; font-size:0.8rem;">Olusturma / Guncelleme</div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-box fc-infra" style="min-width:180px;"><div class="fc-label">BAPI Pipeline</div><div class="fc-sub">RAG → BAPI Bul<br>→ Parametre Rehberi<br>→ ABAP Kod Ornegi</div></div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-box fc-result" style="min-width:180px;"><div class="fc-icon">📦</div><div class="fc-label">BAPI Onerisi</div></div>
            </div>
        </div>
    </div>
    <hr class="fc-divider">
    """, unsafe_allow_html=True)

    # Part 5: Receipt Agent Legal Control Detail
    st.markdown("""
    <div class="fc-section-label" style="margin-top:20px;">Fis Okuyucu Agent - Yasal Kontrol Akisi (Detay)</div>
    <div class="fc">
        <div class="fc-row"><div class="fc-box fc-user" style="min-width:160px;"><div class="fc-icon">📸</div><div class="fc-label">Fis Gorseli</div><div class="fc-sub">JPG / PNG</div></div></div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">base64 encoding</div></div></div>
        <div class="fc-row"><div class="fc-box fc-infra" style="min-width:200px;"><div class="fc-icon">👁️</div><div class="fc-label">GPT-4o Vision OCR</div><div class="fc-sub">Tum alanlari cikar<br>+ Kalem kategorileri<br>(alkol/sigara/normal)</div></div></div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">JSON parse</div></div></div>
        <div class="fc-row"><div class="fc-diamond" style="width:160px;">Fis Turu Kontrolu</div></div>
        <div class="fc-arrows"><div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">fis_turu = alkol/sigara?</div></div></div>
        <div class="fc-branch">
            <div class="fc-branch-item">
                <div style="color:#f44336; font-weight:700; font-size:0.8rem;">Evet → Tamamen Engelle</div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-box" style="background:#b71c1c; border:2px solid #f44336; color:#fff; min-width:160px;"><div class="fc-icon">🚫</div><div class="fc-label">REDDEDILDI</div><div class="fc-sub">Masraf kaydedilemez</div></div>
            </div>
            <div class="fc-branch-item">
                <div style="color:#4CAF50; font-weight:700; font-size:0.8rem;">Hayir → Kalem Kontrolu</div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div></div>
                <div class="fc-diamond" style="width:180px;">Kalem Kalem Kontrol</div>
                <div class="fc-arrow-down"><div class="fc-line"></div><div class="fc-head"></div><div class="fc-text">her kalem: GPT kategori + anahtar kelime</div></div>
                <div style="display:flex; gap:12px;">
                    <div class="fc-box" style="background:#b71c1c; border:2px solid #f44336; color:#fff; min-width:130px;"><div class="fc-icon">🍺</div><div class="fc-label">Engellenen</div><div class="fc-sub">Tutardan dusulur</div></div>
                    <div class="fc-box" style="background:#1b5e20; border:2px solid #4CAF50; color:#fff; min-width:130px;"><div class="fc-icon">✅</div><div class="fc-label">Izinli</div><div class="fc-sub">DB'ye kaydedilir</div></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # DOSYA YAPISI
    # ══════════════════════════════════════════
    st.markdown('<div class="section-title">Proje Dosya Yapisi</div>', unsafe_allow_html=True)

    st.code("""
sap_sql_agent/
├── app.py                          # Ana Streamlit uygulamasi
├── mcp_server.py                   # MCP Server (5 tool)
├── config.py                       # API key, model ayarlari
├── styles.py                       # Platform CSS
├── rag_engine.py                   # RAG motoru (ChromaDB + OpenAI)
├── architecture_page.py            # Bu sayfa
│
├── sql_agent/                      # Agent 1: SQL Generator
│   ├── page.py                     #   Streamlit arayuzu
│   ├── generator.py                #   SQL uretim motoru
│   ├── metadata_loader.py          #   Excel → tablo metadata
│   ├── prompts.py                  #   System prompt
│   └── sample_metadata.xlsx        #   11 SAP tablo metadata
│
├── bapi_agent/                     # Agent 2: BAPI Asistani
│   ├── page.py                     #   Streamlit arayuzu
│   ├── generator.py                #   BAPI cevap motoru
│   ├── metadata_loader.py          #   Excel → BAPI metadata
│   ├── prompts.py                  #   System prompt
│   └── bapi_sample_metadata.xlsx   #   5 BAPI metadata
│
├── sd_mm_agent/                    # Agent 3: SD/MM Orkestrator
│   ├── page.py                     #   Streamlit arayuzu
│   ├── orchestrator.py             #   Intent detection + yonlendirme
│   ├── mock_db.py                  #   SQLite mock veritabani (9 tablo)
│   └── sql_executor.py             #   SAP SQL → SQLite cevirici
│
├── receipt_agent/                  # Agent 4: Fis Okuyucu
│   ├── page.py                     #   Streamlit arayuzu (form + kalem)
│   ├── ocr_parser.py               #   GPT-4o Vision OCR
│   ├── prompts.py                  #   OCR prompt (kalem + kategori)
│   ├── legal_check.py              #   Yasal kontrol (fis + kalem)
│   └── db.py                       #   SQLite fis veritabani
│
└── ik_agent/                       # Agent 5: IK Asistani
    ├── page.py                     #   Streamlit arayuzu
    ├── generator.py                #   IK cevap motoru
    ├── prompts.py                  #   System prompt
    ├── document_loader.py          #   Word → chunk isleyici
    └── data/
        └── yorglass_ik_prosedur.docx  # IK prosedur dokumani
    """, language="text")
