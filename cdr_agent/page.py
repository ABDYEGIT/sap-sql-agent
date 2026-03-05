"""
Teknik Resim (CDR) Agent - Ana Sayfa Modulu.

Teknik resim dosyasi/gorseli yukleme, Vision analizi, form duzenleme
ve kaydetme islemlerini yoneten Streamlit arayuzu.

3 MOD:
  Mod 1 - Dosya Yukleme: CDR/gorsel yukle + "Analiz Et" butonu
  Mod 2 - Form Duzenleme: Analiz sonuclarini duzelt + "Kaydet"
  Mod 3 - Gecmis Kayitlar: Daha once kaydedilen teknik resimlerin listesi
"""
import os
from pathlib import Path

import streamlit as st

from cdr_agent.cdr_parser import extract_preview_from_cdr, extract_image_from_pdf, parse_cdr_image
from cdr_agent.db import get_cdr_db, save_design, get_all_designs, get_design_count


# ── Cam tipi secenekleri ──
CAM_TIPI_OPTIONS = [
    "temperli",
    "lamine",
    "lamine_temperli",
    "duz",
    "buzlu",
    "low_e",
    "diger",
]

# ── Kenar isleme secenekleri ──
KENAR_ISLEME_OPTIONS = [
    "belirtilmemis",
    "rodaj",
    "bizote",
    "makinali",
    "parlak rodaj",
    "mat rodaj",
    "diger",
]


def _get_api_key() -> str:
    """API key cozumle."""
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        _env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_env_path, override=True)
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


# ══════════════════════════════════════════════════════════════════════
# ANA RENDER FONKSIYONU
# ══════════════════════════════════════════════════════════════════════


def render_cdr_agent():
    """Teknik Resim Agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "cdr_mode" not in st.session_state:
        st.session_state["cdr_mode"] = "upload"
    if "cdr_parsed_data" not in st.session_state:
        st.session_state["cdr_parsed_data"] = None
    if "cdr_uploaded_image" not in st.session_state:
        st.session_state["cdr_uploaded_image"] = None  # Orijinal gorsel (yuksek cozunurluk)
    if "cdr_preview_image" not in st.session_state:
        st.session_state["cdr_preview_image"] = None  # Vision API icin kullanilan gorsel

    # ── DB baslat ──
    db_conn = get_cdr_db()

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("Teknik Resim Veritabani")

        design_count = get_design_count(db_conn)
        st.markdown(f"**Kayitli Tasarim:** {design_count} adet")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yeni Analiz", use_container_width=True, key="btn_cdr_new"):
                st.session_state["cdr_mode"] = "upload"
                st.session_state["cdr_parsed_data"] = None
                st.session_state["cdr_uploaded_image"] = None
                st.session_state["cdr_preview_image"] = None
                st.rerun()
        with col2:
            if st.button("Gecmis", use_container_width=True, key="btn_cdr_history"):
                st.session_state["cdr_mode"] = "history"
                st.rerun()

        st.divider()

        # API durumu
        api_key = _get_api_key()
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:]
            st.caption(f"API Bagli ({masked})")
        else:
            st.caption("API anahtari bulunamadi")

        st.divider()

        st.caption(
            "**Desteklenen Formatlar:** .cdr (CorelDRAW X4+), "
            ".png, .jpg, .jpeg, .pdf"
        )

    # ══════════════════════════════════════════
    # ANA ICERIK - Mod'a gore render
    # ══════════════════════════════════════════
    current_mode = st.session_state["cdr_mode"]

    if current_mode == "upload":
        _render_upload_mode()
    elif current_mode == "form":
        _render_form_mode()
    elif current_mode == "history":
        _render_history_mode()


# ══════════════════════════════════════════════════════════════════════
# MOD 1: DOSYA YUKLEME
# ══════════════════════════════════════════════════════════════════════


def _render_upload_mode():
    """Teknik resim dosyasi yukleme ekrani."""

    st.title("Teknik Resim Okuyucu")
    st.markdown(
        "Cam teknik resminizi (CDR veya gorsel) yukleyin, "
        "**GPT-4o Vision** ile otomatik analiz edilecek."
    )

    uploaded_file = st.file_uploader(
        "Teknik resim dosyasini yukleyin",
        type=["cdr", "jpg", "jpeg", "png", "pdf"],
        key="cdr_uploader",
        help="CorelDRAW (.cdr), gorsel (JPG/PNG) veya PDF formatinda teknik resim yukleyin",
    )

    if uploaded_file is not None:
        file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
        is_cdr = file_ext == "cdr"
        is_pdf = file_ext == "pdf"
        raw_bytes = uploaded_file.getvalue()

        col_img, col_info = st.columns([1, 1])

        with col_info:
            st.markdown("**Dosya Bilgileri:**")
            st.markdown(f"- **Ad:** {uploaded_file.name}")
            st.markdown(f"- **Boyut:** {uploaded_file.size / 1024:.1f} KB")
            fmt_map = {"cdr": "CorelDRAW (.cdr)", "pdf": "PDF"}
            fmt_label = fmt_map.get(file_ext, file_ext.upper())
            st.markdown(f"- **Format:** {fmt_label}")

        # ── Gorsel preview ──
        preview_image_bytes = None

        if is_cdr:
            with col_img:
                with st.spinner("CDR onizleme cikariliyor..."):
                    preview_image_bytes = extract_preview_from_cdr(raw_bytes)
                if preview_image_bytes:
                    st.image(preview_image_bytes, caption="CDR Onizleme Gorseli")
                else:
                    st.warning(
                        "CDR dosyasindan onizleme gorseli cikarilamadi. "
                        "Lutfen dosyayi CorelDRAW'dan PNG/JPG olarak export edin."
                    )
        elif is_pdf:
            with col_img:
                with st.spinner("PDF gorsele cevriliyor..."):
                    preview_image_bytes = extract_image_from_pdf(raw_bytes)
                if preview_image_bytes:
                    st.image(preview_image_bytes, caption="PDF Onizleme (Sayfa 1)")
                else:
                    st.warning(
                        "PDF gorsele cevrilemedi. PyMuPDF yuklenmis olabilir. "
                        "Lutfen PDF'i PNG/JPG olarak export edin."
                    )
        else:
            preview_image_bytes = raw_bytes
            with col_img:
                st.image(raw_bytes, caption="Yuklenen Teknik Resim")

        st.divider()

        # ── "Analiz Et" butonu ──
        can_analyze = preview_image_bytes is not None
        if st.button(
            "Analiz Et",
            type="primary",
            use_container_width=True,
            key="btn_cdr_analyze",
            disabled=not can_analyze,
        ):
            api_key = _get_api_key()
            if not api_key:
                st.error("OpenAI API anahtari bulunamadi. `.env` dosyanizi kontrol edin.")
                return

            with st.spinner("Teknik resim analiz ediliyor... (GPT-4o Vision)"):
                parsed = parse_cdr_image(preview_image_bytes, "jpeg")

            if "_error" in parsed:
                st.error(f"Analiz hatasi: {parsed['_error']}")
                return

            st.session_state["cdr_parsed_data"] = parsed
            st.session_state["cdr_uploaded_image"] = raw_bytes  # Orijinal dosya (tam cozunurluk)
            st.session_state["cdr_preview_image"] = preview_image_bytes  # Vision icin kullanilan
            st.session_state["cdr_mode"] = "form"
            st.rerun()
    else:
        st.info(
            "Henuz dosya yuklenmedi. Yukaridaki alandan bir teknik resim "
            "dosyasi yukleyin. Desteklenen formatlar: **CDR, JPG, JPEG, PNG, PDF**"
        )


# ══════════════════════════════════════════════════════════════════════
# MOD 2: FORM DUZENLEME
# ══════════════════════════════════════════════════════════════════════


def _render_form_mode():
    """Analiz sonuclarini duzenlenebilir formda gosterir."""

    st.title("Teknik Resim Bilgilerini Dogrulayin")
    st.markdown(
        "Vision API ile okunan bilgileri kontrol edin. "
        "Hatali alanlari duzelterek **Kaydet** butonuna basin."
    )

    parsed = st.session_state.get("cdr_parsed_data", {})
    if not parsed:
        st.warning("Okunan veri bulunamadi. Lutfen yeni analiz baslatin.")
        return

    # ── Gorsel onizleme (orijinal cozunurluk) ──
    image_bytes = st.session_state.get("cdr_uploaded_image")
    if image_bytes:
        with st.expander("Teknik Resim Gorseli", expanded=False):
            st.image(image_bytes, caption="Analiz Edilen Resim")

    # ── OKUNAMADI uyarisi ──
    okunamadi_alanlar = [
        k for k, v in parsed.items()
        if v == "OKUNAMADI" and k != "_error"
    ]
    if okunamadi_alanlar:
        st.warning(
            f"**{len(okunamadi_alanlar)} alan okunamadi:** "
            f"{', '.join(okunamadi_alanlar)}. "
            f"Lutfen bu alanlari manuel doldurun."
        )

    # ── Form ──
    with st.form("cdr_edit_form"):
        col1, col2 = st.columns(2)

        with col1:
            musteri_adi = st.text_input(
                "Musteri Adi",
                value=parsed.get("musteri_adi", ""),
                key="f_cdr_musteri",
            )
            siparis_no = st.text_input(
                "Siparis No",
                value=parsed.get("siparis_no", ""),
                key="f_cdr_siparis",
            )
            parca_adi = st.text_input(
                "Parca Adi",
                value=parsed.get("parca_adi", ""),
                key="f_cdr_parca",
            )

            # Cam tipi selectbox
            cam_tipi_val = parsed.get("cam_tipi", "diger")
            if cam_tipi_val not in CAM_TIPI_OPTIONS:
                cam_tipi_val = "diger"
            cam_tipi = st.selectbox(
                "Cam Tipi",
                options=CAM_TIPI_OPTIONS,
                index=CAM_TIPI_OPTIONS.index(cam_tipi_val),
                key="f_cdr_cam_tipi",
            )

            # Kenar isleme selectbox
            kenar_val = parsed.get("kenar_isleme", "belirtilmemis")
            if kenar_val not in KENAR_ISLEME_OPTIONS:
                kenar_val = "diger"
            kenar_isleme = st.selectbox(
                "Kenar Isleme",
                options=KENAR_ISLEME_OPTIONS,
                index=KENAR_ISLEME_OPTIONS.index(kenar_val),
                key="f_cdr_kenar",
            )

        with col2:
            en_mm = st.number_input(
                "En (mm)",
                value=int(parsed.get("en_mm", 0)),
                min_value=0,
                step=1,
                key="f_cdr_en",
            )
            boy_mm = st.number_input(
                "Boy (mm)",
                value=int(parsed.get("boy_mm", 0)),
                min_value=0,
                step=1,
                key="f_cdr_boy",
            )
            kalinlik_mm = st.number_input(
                "Kalinlik (mm)",
                value=int(parsed.get("kalinlik_mm", 0)),
                min_value=0,
                step=1,
                key="f_cdr_kalinlik",
            )
            adet = st.number_input(
                "Adet",
                value=int(parsed.get("adet", 1)),
                min_value=1,
                step=1,
                key="f_cdr_adet",
            )
            delik_sayisi = st.number_input(
                "Delik Sayisi",
                value=int(parsed.get("delik_sayisi", 0)),
                min_value=0,
                step=1,
                key="f_cdr_delik",
            )

        notlar = st.text_area(
            "Notlar",
            value=parsed.get("notlar", ""),
            height=100,
            key="f_cdr_notlar",
        )

        st.divider()

        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            submitted = st.form_submit_button(
                "Kaydet",
                type="primary",
                use_container_width=True,
            )
        with btn_col2:
            cancelled = st.form_submit_button(
                "Iptal",
                use_container_width=True,
            )

    if submitted:
        design_data = {
            "musteri_adi": musteri_adi,
            "siparis_no": siparis_no,
            "parca_adi": parca_adi,
            "en_mm": en_mm,
            "boy_mm": boy_mm,
            "kalinlik_mm": kalinlik_mm,
            "cam_tipi": cam_tipi,
            "adet": adet,
            "kenar_isleme": kenar_isleme,
            "delik_sayisi": delik_sayisi,
            "notlar": notlar,
        }
        db_conn = get_cdr_db()
        design_id = save_design(db_conn, design_data)
        st.success(f"Teknik resim basariyla kaydedildi! (ID: {design_id})")
        st.balloons()

        # State temizle
        st.session_state["cdr_mode"] = "upload"
        st.session_state["cdr_parsed_data"] = None
        st.session_state["cdr_uploaded_image"] = None
        st.session_state["cdr_preview_image"] = None

    if cancelled:
        st.session_state["cdr_mode"] = "upload"
        st.session_state["cdr_parsed_data"] = None
        st.session_state["cdr_uploaded_image"] = None
        st.session_state["cdr_preview_image"] = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# MOD 3: GECMIS KAYITLAR
# ══════════════════════════════════════════════════════════════════════


def _render_history_mode():
    """Gecmis teknik resim kayitlarini listeler."""

    st.title("Gecmis Teknik Resimler")
    st.markdown("Daha once analiz edilip kaydedilen teknik resimlerin listesi.")

    db_conn = get_cdr_db()
    df = get_all_designs(db_conn)

    if df.empty:
        st.info(
            "Henuz kaydedilmis teknik resim bulunmuyor. "
            "Yeni analiz icin sidebar'daki butonu kullanin."
        )
        return

    # ── Ozet istatistikler ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Kayit", len(df))
    with col2:
        toplam_adet = df["adet"].sum() if "adet" in df.columns else 0
        st.metric("Toplam Parca", int(toplam_adet))
    with col3:
        if not df["cam_tipi"].mode().empty:
            en_cok_tip = df["cam_tipi"].mode().iloc[0]
        else:
            en_cok_tip = "-"
        st.metric("En Cok Cam Tipi", en_cok_tip)
    with col4:
        unique_customers = df["musteri_adi"].nunique() if "musteri_adi" in df.columns else 0
        st.metric("Farkli Musteri", unique_customers)

    st.divider()

    # ── Tablo ──
    display_cols = [
        "id", "musteri_adi", "siparis_no", "parca_adi",
        "en_mm", "boy_mm", "kalinlik_mm", "cam_tipi",
        "adet", "olusturma_zamani",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    df_display = df[available_cols].copy()

    column_rename = {
        "id": "ID",
        "musteri_adi": "Musteri",
        "siparis_no": "Siparis No",
        "parca_adi": "Parca",
        "en_mm": "En (mm)",
        "boy_mm": "Boy (mm)",
        "kalinlik_mm": "Kalinlik",
        "cam_tipi": "Cam Tipi",
        "adet": "Adet",
        "olusturma_zamani": "Kayit Zamani",
    }
    df_display = df_display.rename(columns=column_rename)

    st.dataframe(df_display, use_container_width=True, hide_index=True)
