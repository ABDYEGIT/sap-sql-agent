"""
Uretim Optimizasyonu Agent - Streamlit Sayfa Modulu.

Duz cam uretim parametrelerini interaktif sliderlar ile ayarlayarak
fire oranini tahmin eder ve canli grafiklerle gosterir.

Bolumler:
  1. Ozet Metrikler - Tahmini fire, optimal fire, fark
  2. Parametre Kontrolleri - Interaktif sliderlar (ses acma mantigi)
  3. Grafikler - Gauge, bar chart, hassasiyet egrisi
  4. Optimizasyon Onerileri - Mevcut vs optimal karsilastirma
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from production_agent.optimizer import (
    calculate_fire_rate,
    get_optimal_params,
    get_parameter_contributions,
    get_sensitivity_data,
    PARAM_CONFIG,
)


# ══════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSIYONLAR
# ══════════════════════════════════════════════════════════════════════


def _get_current_params() -> dict:
    """Session state'teki slider degerlerinden parametre dict'i olusturur."""
    params = {}
    for key, cfg in PARAM_CONFIG.items():
        state_key = f"prod_slider_{key}"
        if state_key in st.session_state:
            params[key] = st.session_state[state_key]
        else:
            params[key] = cfg.get("optimal", cfg.get("options", [None])[0])
    return params


def _load_sample_data():
    """Ornek Excel verisini yukler."""
    sample_path = Path(__file__).resolve().parent / "sample_production.xlsx"
    if sample_path.exists():
        df = pd.read_excel(sample_path, engine="openpyxl")
        st.session_state["prod_production_df"] = df
        st.session_state["prod_data_loaded"] = True
        return df
    return None


# ══════════════════════════════════════════════════════════════════════
# ANA RENDER FONKSIYONU
# ══════════════════════════════════════════════════════════════════════


def render_production_agent():
    """Uretim Optimizasyonu agent arayuzunu render eder."""

    # ── Session state baslat ──
    if "prod_data_loaded" not in st.session_state:
        st.session_state["prod_data_loaded"] = False
    if "prod_production_df" not in st.session_state:
        st.session_state["prod_production_df"] = None

    # ══════════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════════
    with st.sidebar:
        st.subheader("Uretim Verisi")

        # Dosya yukleme
        uploaded = st.file_uploader(
            "Uretim Verisi (Excel)",
            type=["xlsx"],
            key="prod_uploader",
            help="Uretim batch verilerini iceren Excel dosyasi.",
        )

        if uploaded:
            df = pd.read_excel(uploaded, engine="openpyxl")
            st.session_state["prod_production_df"] = df
            st.session_state["prod_data_loaded"] = True
            st.success(f"{len(df)} satir veri yuklendi")

        # Ornek veri butonu
        if not st.session_state["prod_data_loaded"]:
            if st.button(
                "Ornek Veri Yukle",
                use_container_width=True,
                type="primary",
                key="prod_sample_btn",
            ):
                _load_sample_data()
                st.rerun()

        # Veri ozeti
        if st.session_state["prod_data_loaded"]:
            df = st.session_state["prod_production_df"]
            st.divider()
            st.metric("Batch Sayisi", len(df))
            st.metric("Ort. Fire Orani", f"%{df['fire_orani'].mean():.1f}")
            st.metric("Min Fire Orani", f"%{df['fire_orani'].min():.1f}")
            st.metric("Max Fire Orani", f"%{df['fire_orani'].max():.1f}")

        st.divider()

        # Hassasiyet parametresi secimi
        st.subheader("Hassasiyet Analizi")
        sensitivity_options = [k for k in PARAM_CONFIG.keys() if k != "cam_sekli"]
        st.selectbox(
            "Degisken Parametre",
            options=sensitivity_options,
            format_func=lambda x: PARAM_CONFIG[x]["label"],
            key="prod_sensitivity_param",
        )

    # ══════════════════════════════════════════
    # ANA ICERIK
    # ══════════════════════════════════════════
    st.title("Uretim Optimizasyonu")
    st.markdown(
        "Duz cam uretim parametrelerini ayarlayarak **fire oranini minimize edin**. "
        "Sliderlari hareket ettirdikce grafikler canli olarak guncellenir."
    )

    # ── PARAMETRE KONTROLLERI ──
    st.subheader("Uretim Parametreleri")
    st.caption("Parametreleri ayarlayarak fire orani tahminini gercek zamanli gorun.")

    col_left, col_right = st.columns(2)

    # Sol kolon parametreleri
    params_left = [
        "bant_hizi", "ortam_sicakligi", "cam_sekli",
        "trim_payi", "kesim_basinci",
    ]
    # Sag kolon parametreleri
    params_right = [
        "yag_kalitesi", "sogutma_sivisi_sicakligi",
        "stok_bekleme_suresi", "cam_kalinligi", "temperleme_sicakligi",
    ]

    with col_left:
        for key in params_left:
            _render_parameter_control(key)

    with col_right:
        for key in params_right:
            _render_parameter_control(key)

    # ── MEVCUT PARAMETRELERI AL ──
    current_params = _get_current_params()
    current_fire = calculate_fire_rate(current_params)
    optimal = get_optimal_params()
    optimal_fire = calculate_fire_rate(optimal)

    # ── OZET METRIKLER ──
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tahmini Fire Orani", f"%{current_fire:.1f}")
    m2.metric("Optimal Fire Orani", f"%{optimal_fire:.1f}")

    fark = current_fire - optimal_fire
    m3.metric(
        "Fark",
        f"%{fark:.1f}",
        delta=f"{fark:+.1f}",
        delta_color="inverse",
    )

    if st.session_state["prod_data_loaded"]:
        df = st.session_state["prod_production_df"]
        m4.metric("Veri Ortalama Fire", f"%{df['fire_orani'].mean():.1f}")
    else:
        m4.metric("Veri Ortalama Fire", "Veri yok")

    # ══════════════════════════════════════════
    # GRAFIKLER
    # ══════════════════════════════════════════
    st.divider()
    st.subheader("Fire Orani Analizi")

    chart_col1, chart_col2 = st.columns([1, 1])

    # ── GAUGE CHART ──
    with chart_col1:
        _render_gauge_chart(current_fire, optimal_fire)

    # ── BAR CHART (parametre katkilari) ──
    with chart_col2:
        contributions = get_parameter_contributions(current_params)
        _render_contribution_chart(contributions)

    # ── HASSASIYET GRAFIGI ──
    st.divider()
    st.subheader("Hassasiyet Grafigi")
    vary_param = st.session_state.get("prod_sensitivity_param", "bant_hizi")
    _render_sensitivity_chart(current_params, vary_param)

    # ── OPTIMIZASYON ONERILERI ──
    st.divider()
    _render_recommendations(current_params, contributions)


# ══════════════════════════════════════════════════════════════════════
# PARAMETRE KONTROLU RENDER
# ══════════════════════════════════════════════════════════════════════


def _render_parameter_control(key: str):
    """Tek bir parametre icin slider veya selectbox render eder."""
    cfg = PARAM_CONFIG[key]
    label = f"{cfg['label']} ({cfg['unit']})" if cfg["unit"] else cfg["label"]

    if cfg["type"] == "select":
        st.selectbox(
            label,
            options=cfg["options"],
            index=cfg["options"].index(cfg["optimal"]),
            key=f"prod_slider_{key}",
        )
    elif cfg["type"] == "select_slider":
        st.select_slider(
            label,
            options=cfg["options"],
            value=cfg["optimal"],
            key=f"prod_slider_{key}",
        )
    else:
        # Yag kalitesi integer
        if isinstance(cfg["min"], int):
            st.slider(
                label,
                min_value=cfg["min"],
                max_value=cfg["max"],
                value=cfg["optimal"],
                step=cfg["step"],
                key=f"prod_slider_{key}",
            )
        else:
            st.slider(
                label,
                min_value=float(cfg["min"]),
                max_value=float(cfg["max"]),
                value=float(cfg["optimal"]),
                step=float(cfg["step"]),
                key=f"prod_slider_{key}",
            )


# ══════════════════════════════════════════════════════════════════════
# GRAFIK RENDER FONKSIYONLARI
# ══════════════════════════════════════════════════════════════════════


def _render_gauge_chart(current_fire: float, optimal_fire: float):
    """Fire orani gauge (gosterge) grafigi."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=current_fire,
            delta={
                "reference": optimal_fire,
                "increasing": {"color": "#f44336"},
                "decreasing": {"color": "#4CAF50"},
            },
            title={"text": "Tahmini Fire Orani (%)", "font": {"size": 16}},
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 25], "tickwidth": 1, "tickcolor": "#555"},
                "bar": {"color": "#FF5722"},
                "bgcolor": "rgba(30,30,46,0.5)",
                "steps": [
                    {"range": [0, 3], "color": "rgba(76,175,80,0.3)"},
                    {"range": [3, 8], "color": "rgba(255,152,0,0.3)"},
                    {"range": [8, 25], "color": "rgba(244,67,54,0.3)"},
                ],
                "threshold": {
                    "line": {"color": "#4CAF50", "width": 3},
                    "thickness": 0.75,
                    "value": optimal_fire,
                },
            },
        )
    )
    fig.update_layout(
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_contribution_chart(contributions: dict):
    """Parametre bazli fire katkisi yatay bar chart."""
    # Katkilara gore sirala
    sorted_items = sorted(contributions.items(), key=lambda x: x[1], reverse=True)

    labels = [PARAM_CONFIG[k]["label"] for k, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors = [
        "#f44336" if v > 1.5 else "#FF9800" if v > 0.3 else "#4CAF50"
        for v in values
    ]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"%{v:.1f}" for v in values],
            textposition="auto",
        )
    )
    fig.update_layout(
        title={"text": "Parametre Bazli Fire Katkisi", "font": {"size": 16}},
        xaxis_title="Fire Katkisi (%)",
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_sensitivity_chart(current_params: dict, vary_param: str):
    """Secilen parametrenin hassasiyet egrisi."""
    cfg = PARAM_CONFIG.get(vary_param)
    if not cfg:
        return

    x_vals, y_vals = get_sensitivity_data(current_params, vary_param)

    fig = go.Figure()

    # Ana egri
    if cfg["type"] == "select_slider":
        # Ayrik degerler icin bar + line
        fig.add_trace(
            go.Bar(
                x=[str(x) for x in x_vals],
                y=y_vals,
                marker_color=[
                    "#FF5722" if x == current_params.get(vary_param) else "#FF9800"
                    for x in x_vals
                ],
                name="Fire Orani",
            )
        )
    else:
        # Surekli parametreler icin line
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                line=dict(color="#FF5722", width=3),
                name="Fire Orani",
                fill="tozeroy",
                fillcolor="rgba(255,87,34,0.1)",
            )
        )

        # Mevcut deger cizgisi
        current_val = current_params.get(vary_param)
        if current_val is not None:
            fig.add_vline(
                x=float(current_val),
                line_dash="dash",
                line_color="#FF9800",
                line_width=2,
                annotation_text=f"Mevcut: {current_val}",
                annotation_font_color="#FF9800",
            )

        # Optimal deger cizgisi
        optimal_val = cfg.get("optimal")
        if optimal_val is not None:
            fig.add_vline(
                x=float(optimal_val),
                line_dash="dot",
                line_color="#4CAF50",
                line_width=2,
                annotation_text=f"Optimal: {optimal_val}",
                annotation_font_color="#4CAF50",
            )

    unit = f" ({cfg['unit']})" if cfg["unit"] else ""
    fig.update_layout(
        title={
            "text": f"{cfg['label']}{unit} - Fire Orani Iliskisi",
            "font": {"size": 16},
        },
        xaxis_title=f"{cfg['label']}{unit}",
        yaxis_title="Fire Orani (%)",
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e6edf3"},
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# OPTIMIZASYON ONERILERI
# ══════════════════════════════════════════════════════════════════════


def _render_recommendations(current_params: dict, contributions: dict):
    """Parametre bazli optimizasyon onerileri."""
    st.subheader("Optimizasyon Onerileri")

    optimal = get_optimal_params()
    recommendations = []

    for key, cfg in PARAM_CONFIG.items():
        current = current_params.get(key)
        optimal_val = cfg.get("optimal")
        contribution = contributions.get(key, 0)

        if current != optimal_val and contribution > 0.1:
            recommendations.append({
                "key": key,
                "label": cfg["label"],
                "unit": cfg["unit"],
                "current": current,
                "optimal": optimal_val,
                "impact": contribution,
            })

    if not recommendations:
        st.success(
            "Tum parametreler optimal degerlerde! "
            "Fire orani minimize edilmistir."
        )
        return

    # Etkiye gore sirala
    recommendations.sort(key=lambda x: x["impact"], reverse=True)

    for rec in recommendations:
        if rec["impact"] > 1.5:
            icon = "🔴"
        elif rec["impact"] > 0.5:
            icon = "🟡"
        else:
            icon = "🟢"

        unit = f" {rec['unit']}" if rec["unit"] else ""
        st.markdown(
            f"{icon} **{rec['label']}**: "
            f"Mevcut = `{rec['current']}{unit}` → "
            f"Optimal = `{rec['optimal']}{unit}` "
            f"(Fire etkisi: **%{rec['impact']:.1f}**)"
        )
