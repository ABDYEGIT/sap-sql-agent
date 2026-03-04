"""
Fis Okuyucu Agent - Ana Sayfa Modulu.

Fis gorseli yukleme, OCR okuma, form duzenleme ve kaydetme
islemlerini yoneten Streamlit arayuzu.

3 MOD:
  Mod 1 - Fis Yukleme: Gorsel yukle + "Fisi Oku" butonu
  Mod 2 - Form Duzenleme: OCR sonuclarini duzelt + "Kaydet"
  Mod 3 - Gecmis Fisler: Daha once kaydedilen fislerin listesi
"""
import streamlit as st

from receipt_agent.ocr_parser import parse_receipt_image
from receipt_agent.legal_check import check_legal
from receipt_agent.db import get_receipt_db, save_receipt, get_all_receipts, get_receipt_count


# ── Fis turu secenekleri ──
FIS_TURU_OPTIONS = [
    "yemek",
    "market",
    "akaryakit",
    "giyim",
    "konaklama",
    "ulasim",
    "alkol",
    "sigara",
    "saglik",
    "egitim",
    "teknoloji",
    "diger",
]


def _get_api_key() -> str:
    """API key cozumle."""
    import os
    from pathlib import Path
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


def render_receipt_agent():
    """Fis Okuyucu Agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "receipt_mode" not in st.session_state:
        st.session_state["receipt_mode"] = "upload"  # upload / form / history
    if "receipt_parsed_data" not in st.session_state:
        st.session_state["receipt_parsed_data"] = None
    if "receipt_uploaded_image" not in st.session_state:
        st.session_state["receipt_uploaded_image"] = None

    # ── DB baslat ──
    db_conn = get_receipt_db()

    # ══════════════════════════════════════════
    # SIDEBAR ICERIGI
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("Fis Veritabani")

        receipt_count = get_receipt_count(db_conn)
        st.markdown(f"**Kayitli Fis:** {receipt_count} adet")

        st.divider()

        # Mod degistirme butonlari
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yeni Fis Okut", use_container_width=True, key="btn_new"):
                st.session_state["receipt_mode"] = "upload"
                st.session_state["receipt_parsed_data"] = None
                st.session_state["receipt_uploaded_image"] = None
                st.rerun()
        with col2:
            if st.button("Okuttuğum Fisler", use_container_width=True, key="btn_history"):
                st.session_state["receipt_mode"] = "history"
                st.rerun()

        st.divider()

        # API durumu
        api_key = _get_api_key()
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:]
            st.markdown(f'<span class="status-ok">API Bagli</span> ({masked})', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">API anahtari bulunamadi</span>', unsafe_allow_html=True)

        st.divider()

        # Yasal uyari
        st.caption(
            "**Yasal Uyari:** Alkol ve sigara/tutun "
            "urunleri fisleri masraf olarak kaydedilemez."
        )

    # ══════════════════════════════════════════
    # ANA ICERIK - Mod'a Gore Render
    # ══════════════════════════════════════════
    current_mode = st.session_state["receipt_mode"]

    if current_mode == "upload":
        _render_upload_mode()
    elif current_mode == "form":
        _render_form_mode()
    elif current_mode == "history":
        _render_history_mode()


# ══════════════════════════════════════════════════════════════════════
# MOD 1: FIS YUKLEME
# ══════════════════════════════════════════════════════════════════════


def _render_upload_mode():
    """Fis gorseli yukleme ekrani."""

    st.title("Fis Okuyucu")
    st.markdown(
        "Fis gorselinizi yukleyin, **GPT-4o Vision** ile otomatik okunacak. "
        "Bulanik veya egik fis gorselleri de desteklenir."
    )

    # ── Gorsel yukleme ──
    uploaded_file = st.file_uploader(
        "Fis gorselini yukleyin",
        type=["jpg", "jpeg", "png"],
        key="receipt_uploader",
        help="JPEG veya PNG formatinda fis gorseli yukleyin",
    )

    if uploaded_file is not None:
        # Gorseli goster
        col_img, col_info = st.columns([1, 1])

        with col_img:
            st.image(uploaded_file, caption="Yuklenen Fis Gorseli", use_container_width=True)

        with col_info:
            st.markdown("**Dosya Bilgileri:**")
            st.markdown(f"- **Ad:** {uploaded_file.name}")
            st.markdown(f"- **Boyut:** {uploaded_file.size / 1024:.1f} KB")
            st.markdown(f"- **Tur:** {uploaded_file.type}")

        st.divider()

        # ── "Fisi Oku" butonu ──
        if st.button("Fisi Oku", type="primary", use_container_width=True, key="btn_read"):
            api_key = _get_api_key()
            if not api_key:
                st.error("OpenAI API anahtari bulunamadi. `.env` dosyanizi kontrol edin.")
                return

            with st.spinner("Fis okunuyor... (GPT-4o Vision)"):
                # Dosya turunu belirle
                file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else "jpeg"

                # OCR ile fisi oku
                image_bytes = uploaded_file.getvalue()
                parsed = parse_receipt_image(image_bytes, file_ext)

            # Hata kontrolu
            if "_error" in parsed:
                st.error(f"Fis okuma hatasi: {parsed['_error']}")
                return

            # Basarili → Form moduna gec
            st.session_state["receipt_parsed_data"] = parsed
            st.session_state["receipt_uploaded_image"] = image_bytes
            st.session_state["receipt_mode"] = "form"
            st.rerun()
    else:
        # Ornek gorsel ipucu
        st.info(
            "Henuz fis gorseli yuklenmedi. Yukaridaki alandan bir fis "
            "fotografi yukleyin. Desteklenen formatlar: **JPG, JPEG, PNG**"
        )


# ══════════════════════════════════════════════════════════════════════
# MOD 2: FORM DUZENLEME
# ══════════════════════════════════════════════════════════════════════
# OCR sonuclari otomatik doldurulmus form gosterilir.
# Kullanici hatalari duzeltebilir.
# "Kaydet" butonu yasal kontrol + DB kayit yapar.
# ══════════════════════════════════════════════════════════════════════


def _render_form_mode():
    """OCR sonuclarini duzenlenebilir formda gosterir."""

    st.title("Fis Bilgilerini Dogrulayin")
    st.markdown("OCR ile okunan bilgileri kontrol edin. Hatali alanlari duzelterek **Kaydet** butonuna basin.")

    parsed = st.session_state.get("receipt_parsed_data", {})
    if not parsed:
        st.warning("Okunan fis verisi bulunamadi. Lutfen yeni fis okutun.")
        return

    # Gorsel onizleme (varsa)
    image_bytes = st.session_state.get("receipt_uploaded_image")
    if image_bytes:
        with st.expander("Fis Gorseli", expanded=False):
            st.image(image_bytes, caption="Okunan Fis", use_container_width=True)

    # OKUNAMADI uyarisi
    okunamadi_alanlar = [k for k, v in parsed.items() if v == "OKUNAMADI" and k != "_error"]
    if okunamadi_alanlar:
        st.warning(
            f"**{len(okunamadi_alanlar)} alan okunamadi:** "
            f"{', '.join(okunamadi_alanlar)}. "
            f"Lutfen bu alanlari manuel doldurun."
        )

    # ── Duzenlenebilir Form ──
    with st.form("receipt_edit_form"):
        col1, col2 = st.columns(2)

        with col1:
            isletme_adi = st.text_input(
                "Isletme Adi",
                value=parsed.get("isletme_adi", ""),
                key="f_isletme",
            )
            adres = st.text_area(
                "Adres",
                value=parsed.get("adres", ""),
                key="f_adres",
                height=80,
            )
            vergi_no = st.text_input(
                "VKN / TCKN",
                value=parsed.get("vergi_no", ""),
                key="f_vergi_no",
            )
            vergi_dairesi = st.text_input(
                "Vergi Dairesi",
                value=parsed.get("vergi_dairesi", ""),
                key="f_vergi_dairesi",
            )

        with col2:
            tarih = st.text_input(
                "Tarih (GG.AA.YYYY)",
                value=parsed.get("tarih", ""),
                key="f_tarih",
            )
            saat = st.text_input(
                "Saat (SS:DD)",
                value=parsed.get("saat", ""),
                key="f_saat",
            )
            fis_no = st.text_input(
                "Fis No",
                value=parsed.get("fis_no", ""),
                key="f_fis_no",
            )

            # Tutar
            tutar_val = parsed.get("tutar", 0.0)
            try:
                tutar_val = float(tutar_val)
            except (ValueError, TypeError):
                tutar_val = 0.0
            tutar = st.number_input(
                "Tutar (TL)",
                value=tutar_val,
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="f_tutar",
            )

            # KDV Orani
            kdv_val = parsed.get("kdv_orani", 0.0)
            try:
                kdv_val = float(kdv_val)
            except (ValueError, TypeError):
                kdv_val = 0.0
            kdv_orani = st.number_input(
                "KDV Orani (%)",
                value=kdv_val,
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                format="%.0f",
                key="f_kdv",
            )

            # Fis Turu
            fis_turu_val = parsed.get("fis_turu", "diger")
            if fis_turu_val not in FIS_TURU_OPTIONS:
                fis_turu_val = "diger"
            fis_turu_idx = FIS_TURU_OPTIONS.index(fis_turu_val)
            fis_turu = st.selectbox(
                "Fis Turu",
                options=FIS_TURU_OPTIONS,
                index=fis_turu_idx,
                key="f_fis_turu",
            )

        # ── Kalem Detaylari ──
        st.divider()
        st.subheader("Kalem Detaylari")

        kalemler = parsed.get("kalemler", [])
        if kalemler:
            # Tablo baslik
            hdr1, hdr2, hdr3, hdr4 = st.columns([3, 1, 1.5, 1.5])
            hdr1.markdown("**Urun**")
            hdr2.markdown("**Adet**")
            hdr3.markdown("**Birim Fiyat**")
            hdr4.markdown("**Toplam**")

            for i, item in enumerate(kalemler):
                c1, c2, c3, c4 = st.columns([3, 1, 1.5, 1.5])
                c1.text_input("urun", value=item.get("urun", ""), key=f"k_urun_{i}", label_visibility="collapsed")
                try:
                    adet_v = max(0.0, float(item.get("adet", 1)))
                except (ValueError, TypeError):
                    adet_v = 1.0
                try:
                    birim_v = max(0.0, float(item.get("birim_fiyat", 0)))
                except (ValueError, TypeError):
                    birim_v = 0.0
                try:
                    toplam_v = max(0.0, float(item.get("toplam", 0)))
                except (ValueError, TypeError):
                    toplam_v = 0.0
                c2.number_input("adet", value=adet_v, min_value=0.0, step=1.0, key=f"k_adet_{i}", label_visibility="collapsed")
                c3.number_input("birim", value=birim_v, min_value=0.0, step=0.01, format="%.2f", key=f"k_birim_{i}", label_visibility="collapsed")
                c4.number_input("toplam", value=toplam_v, min_value=0.0, step=0.01, format="%.2f", key=f"k_toplam_{i}", label_visibility="collapsed")
        else:
            st.info("Fiste kalem detayi okunamadi.")

        st.divider()

        # Butonlar
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

    # ── Form islemleri ──
    if submitted:
        # Yasal kontrol
        legal_ok, legal_msg = check_legal(fis_turu)

        if not legal_ok:
            st.error(f"MASRAF KAYDEDILEMEZ: {legal_msg}")
            return

        # Kalemleri formdan topla
        saved_kalemler = []
        kalem_count = len(parsed.get("kalemler", []))
        for i in range(kalem_count):
            urun_val = st.session_state.get(f"k_urun_{i}", "")
            adet_val = st.session_state.get(f"k_adet_{i}", 1)
            birim_val = st.session_state.get(f"k_birim_{i}", 0)
            toplam_val = st.session_state.get(f"k_toplam_{i}", 0)
            if urun_val:
                saved_kalemler.append({
                    "urun": urun_val,
                    "adet": adet_val,
                    "birim_fiyat": birim_val,
                    "toplam": toplam_val,
                })

        # DB'ye kaydet
        receipt_data = {
            "isletme_adi": isletme_adi,
            "adres": adres,
            "vergi_no": vergi_no,
            "vergi_dairesi": vergi_dairesi,
            "tarih": tarih,
            "saat": saat,
            "fis_no": fis_no,
            "tutar": tutar,
            "kdv_orani": kdv_orani,
            "fis_turu": fis_turu,
            "kalemler": saved_kalemler,
        }

        db_conn = get_receipt_db()
        receipt_id = save_receipt(db_conn, receipt_data)

        st.success(f"Fis basariyla kaydedildi! (ID: {receipt_id})")
        st.balloons()

        # Upload moduna don
        st.session_state["receipt_mode"] = "upload"
        st.session_state["receipt_parsed_data"] = None
        st.session_state["receipt_uploaded_image"] = None

    if cancelled:
        # Upload moduna don
        st.session_state["receipt_mode"] = "upload"
        st.session_state["receipt_parsed_data"] = None
        st.session_state["receipt_uploaded_image"] = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# MOD 3: GECMIS FISLER
# ══════════════════════════════════════════════════════════════════════
# Daha once okutulan ve kaydedilen fislerin listesi.
# st.dataframe() ile gosterilir.
# ══════════════════════════════════════════════════════════════════════


def _render_history_mode():
    """Gecmis fisleri listeler."""

    st.title("Okuttuğum Fisler")
    st.markdown("Daha once okutulup kaydedilen fislerin listesi.")

    db_conn = get_receipt_db()
    df = get_all_receipts(db_conn)

    if df.empty:
        st.info("Henuz kaydedilmis fis bulunmuyor. Yeni fis okutmak icin sidebar'daki butonu kullanin.")
        return

    # Ozet istatistikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Fis", len(df))
    with col2:
        st.metric("Toplam Tutar", f"{df['tutar'].sum():,.2f} TL")
    with col3:
        en_cok_tur = df["fis_turu"].mode().iloc[0] if not df["fis_turu"].mode().empty else "-"
        st.metric("En Cok Tur", en_cok_tur)
    with col4:
        ort_tutar = df["tutar"].mean()
        st.metric("Ortalama Tutar", f"{ort_tutar:,.2f} TL")

    st.divider()

    # Gosterilecek sutunlari sec ve yeniden adlandir
    display_cols = ["id", "isletme_adi", "tarih", "tutar", "kdv_orani", "fis_turu", "fis_no", "olusturma_zamani"]
    available_cols = [c for c in display_cols if c in df.columns]
    df_display = df[available_cols].copy()

    # Sutun adlarini Turkceye cevir
    column_rename = {
        "id": "ID",
        "isletme_adi": "Isletme",
        "tarih": "Tarih",
        "tutar": "Tutar (TL)",
        "kdv_orani": "KDV (%)",
        "fis_turu": "Tur",
        "fis_no": "Fis No",
        "olusturma_zamani": "Kayit Zamani",
    }
    df_display = df_display.rename(columns=column_rename)

    st.dataframe(df_display, use_container_width=True, hide_index=True)
