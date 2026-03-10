"""
Uretim Optimizasyonu - Fire Orani Hesaplama ve Parametre Analizi.

Duz cam uretim hattindaki parametrelerin fire oranina etkisini
hesaplar. Her parametrenin optimal degerden sapmasi fire'a
katki yapar.

Uretim Hatti Adimlari:
  Kesim → Rodaj → Kenar Isleme → Delik → Baski → Temper → Hurdalama
"""
import numpy as np


# ══════════════════════════════════════════════════════════════════════
# PARAMETRE KONFIGURASYONU
# ══════════════════════════════════════════════════════════════════════

PARAM_CONFIG = {
    "bant_hizi": {
        "label": "Bant Hizi",
        "min": 1.0,
        "max": 5.0,
        "step": 0.1,
        "optimal": 3.0,
        "unit": "m/dk",
        "type": "slider",
    },
    "ortam_sicakligi": {
        "label": "Ortam Sicakligi",
        "min": 18.0,
        "max": 35.0,
        "step": 0.5,
        "optimal": 22.0,
        "unit": "°C",
        "type": "slider",
    },
    "cam_sekli": {
        "label": "Cam Sekli",
        "options": ["Dikdortgen", "Kare", "Daire", "Oval", "L-Sekil"],
        "optimal": "Dikdortgen",
        "unit": "",
        "type": "select",
    },
    "trim_payi": {
        "label": "Trim Payi",
        "min": 1.0,
        "max": 5.0,
        "step": 0.1,
        "optimal": 3.5,
        "unit": "mm",
        "type": "slider",
    },
    "kesim_basinci": {
        "label": "Kesim Basinci",
        "min": 2.0,
        "max": 6.0,
        "step": 0.1,
        "optimal": 3.75,
        "unit": "bar",
        "type": "slider",
    },
    "yag_kalitesi": {
        "label": "Yag Kalitesi",
        "min": 1,
        "max": 10,
        "step": 1,
        "optimal": 9,
        "unit": "index",
        "type": "slider",
    },
    "sogutma_sivisi_sicakligi": {
        "label": "Sogutma Sivisi Sicakligi",
        "min": 5.0,
        "max": 25.0,
        "step": 0.5,
        "optimal": 8.0,
        "unit": "°C",
        "type": "slider",
    },
    "stok_bekleme_suresi": {
        "label": "Stok Bekleme Suresi",
        "min": 0.0,
        "max": 72.0,
        "step": 1.0,
        "optimal": 0.0,
        "unit": "saat",
        "type": "slider",
    },
    "cam_kalinligi": {
        "label": "Cam Kalinligi",
        "options": [3, 4, 5, 6, 8, 10],
        "optimal": 10,
        "unit": "mm",
        "type": "select_slider",
    },
    "temperleme_sicakligi": {
        "label": "Temperleme Sicakligi",
        "min": 600.0,
        "max": 700.0,
        "step": 1.0,
        "optimal": 655.0,
        "unit": "°C",
        "type": "slider",
    },
}


# ══════════════════════════════════════════════════════════════════════
# FIRE ORANI HESAPLAMA
# ══════════════════════════════════════════════════════════════════════

# Cam sekli → fire katkisi eslemesi
_SEKIL_FIRE = {
    "Dikdortgen": 0.0,
    "Kare": 0.2,
    "Daire": 1.5,
    "Oval": 1.8,
    "L-Sekil": 2.5,
}

# Cam kalinligi → fire katkisi eslemesi (ince = hassas)
_KALINLIK_FIRE = {
    3: 2.0,
    4: 1.2,
    5: 0.7,
    6: 0.3,
    8: 0.1,
    10: 0.0,
}


def calculate_fire_rate(params: dict, add_noise: bool = False) -> float:
    """
    Uretim parametrelerinden fire oranini (%) hesaplar.

    Her parametrenin optimal degerden sapmasi fire'a katki yapar.
    Fiziksel uretim mantigi ile modellenmistir.

    Args:
        params: Parametre dict'i (slider degerlerinden olusur)
        add_noise: True ise rastgele gurultu ekler (veri uretimi icin)

    Returns:
        Fire orani (yuzde olarak, 0-35 arasi)
    """
    fire = 0.0

    # 1. Bant Hizi (optimal: 3.0 m/dk)
    # Cok yavas: soguma kaybi; cok hizli: kesim hassasiyeti duser
    optimal_hiz = 3.0
    fire += 1.5 * (params.get("bant_hizi", optimal_hiz) - optimal_hiz) ** 2

    # 2. Ortam Sicakligi (ideal: 20-22°C)
    # Yuksek sicaklik cam genlesme sorunlari yaratir
    fire += 0.08 * max(0, params.get("ortam_sicakligi", 22) - 22)

    # 3. Cam Sekli karmasiklik katsayisi
    sekil = params.get("cam_sekli", "Dikdortgen")
    fire += _SEKIL_FIRE.get(sekil, 0.5)

    # 4. Trim Payi (optimal: 3.5mm)
    # Cok kucuk trim payi kirilma riski artirir
    fire += 1.2 * max(0, 3.0 - params.get("trim_payi", 3.5))

    # 5. Kesim Basinci (optimal: 3.75 bar)
    optimal_basinc = 3.75
    fire += 0.8 * (params.get("kesim_basinci", optimal_basinc) - optimal_basinc) ** 2

    # 6. Yag Kalitesi (yuksek = iyi, 1-10)
    # Dusuk yag kalitesi kesim hatasi artirir
    fire += 0.5 * max(0, 7 - params.get("yag_kalitesi", 9))

    # 7. Sogutma Sivisi Sicakligi (ideal: 8°C)
    # Yuksek sicaklik termal sok riskini artirir
    fire += 0.12 * max(0, params.get("sogutma_sivisi_sicakligi", 8) - 10)

    # 8. Stok Bekleme Suresi (kisa = iyi)
    # Uzun bekleme yuzey bozulmasi ve nem absorpsiyonu
    fire += 0.04 * params.get("stok_bekleme_suresi", 0)

    # 9. Cam Kalinligi (ince cam = daha hassas)
    kalinlik = params.get("cam_kalinligi", 10)
    fire += _KALINLIK_FIRE.get(kalinlik, 0.5)

    # 10. Temperleme Sicakligi (optimal: 655°C)
    optimal_temper = 655
    fire += 0.003 * (params.get("temperleme_sicakligi", optimal_temper) - optimal_temper) ** 2

    # Gurultu (sadece veri uretiminde)
    if add_noise:
        noise = np.random.normal(0, 0.5)
        fire += noise

    # 0.5 - 35.0 araligina sinirla
    fire = max(0.5, min(fire, 35.0))

    return round(fire, 2)


# ══════════════════════════════════════════════════════════════════════
# OPTIMAL PARAMETRELER
# ══════════════════════════════════════════════════════════════════════


def get_optimal_params() -> dict:
    """Tum parametrelerin optimal degerlerini dondurur."""
    return {
        key: cfg["optimal"]
        for key, cfg in PARAM_CONFIG.items()
    }


# ══════════════════════════════════════════════════════════════════════
# PARAMETRE KATKISI ANALIZI
# ══════════════════════════════════════════════════════════════════════


def get_parameter_contributions(params: dict) -> dict:
    """
    Her parametrenin fire oranina olan bireysel katkisini hesaplar.

    Tek tek her parametreyi optimalden mevcut degere degistirip
    fire farkini olcer.

    Args:
        params: Mevcut parametre degerleri

    Returns:
        {parametre_adi: fire_katkisi} dict'i
    """
    optimal = get_optimal_params()
    optimal_fire = calculate_fire_rate(optimal)

    contributions = {}
    for key in PARAM_CONFIG:
        # Sadece bu parametreyi mevcut degere getir, diger hepsini optimal tut
        test_params = optimal.copy()
        test_params[key] = params.get(key, optimal[key])
        test_fire = calculate_fire_rate(test_params)
        contributions[key] = round(max(0, test_fire - optimal_fire), 2)

    return contributions


# ══════════════════════════════════════════════════════════════════════
# HASSASIYET ANALIZI
# ══════════════════════════════════════════════════════════════════════


def get_sensitivity_data(
    params: dict,
    vary_param: str,
    n_points: int = 50,
) -> tuple:
    """
    Bir parametreyi degistirirken fire oraninin nasil degistigini hesaplar.

    Secilen parametreyi min-max araliginda degistirip diger parametreleri
    sabit tutar. Hassasiyet egrisi icin veri uretir.

    Args:
        params: Mevcut parametre degerleri (sabit tutulacaklar)
        vary_param: Degistirilecek parametrenin adi
        n_points: Hesaplanacak nokta sayisi

    Returns:
        (x_values, y_values) tuple'i
    """
    cfg = PARAM_CONFIG.get(vary_param)
    if not cfg:
        return [], []

    # Cam sekli kategorik oldugu icin hassasiyet analizine uygun degil
    if cfg["type"] == "select" and vary_param == "cam_sekli":
        x_vals = cfg["options"]
        y_vals = []
        for option in x_vals:
            test_params = params.copy()
            test_params[vary_param] = option
            y_vals.append(calculate_fire_rate(test_params))
        return x_vals, y_vals

    # Cam kalinligi ayrik degerler
    if cfg["type"] == "select_slider":
        x_vals = cfg["options"]
        y_vals = []
        for val in x_vals:
            test_params = params.copy()
            test_params[vary_param] = val
            y_vals.append(calculate_fire_rate(test_params))
        return x_vals, y_vals

    # Surekli parametreler icin
    x_vals = np.linspace(cfg["min"], cfg["max"], n_points).tolist()
    y_vals = []
    for val in x_vals:
        test_params = params.copy()
        test_params[vary_param] = round(val, 2)
        y_vals.append(calculate_fire_rate(test_params))

    return x_vals, y_vals
