"""
Uretim Optimizasyonu - Ornek Uretim Verisi Uretici.

Duz cam uretim hatti icin ~200 satirlik ornek Excel verisi uretir.
Her satir bir uretim batch'ini temsil eder.

Kullanim:
    python production_agent/data_generator.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from production_agent.optimizer import calculate_fire_rate


def generate_production_data(n_rows: int = 200) -> pd.DataFrame:
    """
    Ornek uretim verisi olusturur.

    Her satir bir uretim batch'ini temsil eder.
    Fire orani, parametrelere dayali fiziksel formul ile hesaplanir.

    Args:
        n_rows: Uretilecek satir sayisi

    Returns:
        Uretim verileri DataFrame'i
    """
    np.random.seed(42)

    data = {
        "tarih": pd.date_range(
            start="2024-01-01", periods=n_rows, freq="4h"
        ).strftime("%Y-%m-%d %H:%M"),
        "batch_no": [f"B-{i+1:04d}" for i in range(n_rows)],
        "bant_hizi": np.random.uniform(1.0, 5.0, n_rows).round(1),
        "ortam_sicakligi": np.random.uniform(18, 35, n_rows).round(1),
        "cam_sekli": np.random.choice(
            ["Dikdortgen", "Kare", "Daire", "Oval", "L-Sekil"],
            n_rows,
            p=[0.35, 0.25, 0.15, 0.10, 0.15],
        ),
        "trim_payi": np.random.uniform(1.0, 5.0, n_rows).round(1),
        "kesim_basinci": np.random.uniform(2.0, 6.0, n_rows).round(1),
        "yag_kalitesi": np.random.randint(1, 11, n_rows),
        "sogutma_sivisi_sicakligi": np.random.uniform(5, 25, n_rows).round(1),
        "stok_bekleme_suresi": np.random.uniform(0, 72, n_rows).round(1),
        "cam_kalinligi": np.random.choice([3, 4, 5, 6, 8, 10], n_rows),
        "temperleme_sicakligi": np.random.uniform(600, 700, n_rows).round(1),
    }

    df = pd.DataFrame(data)

    # Fire oranini formul ile hesapla (gurultulu)
    df["fire_orani"] = df.apply(
        lambda row: calculate_fire_rate(row.to_dict(), add_noise=True),
        axis=1,
    )

    return df


if __name__ == "__main__":
    output_path = Path(__file__).resolve().parent / "sample_production.xlsx"
    df = generate_production_data(200)

    df.to_excel(
        output_path,
        sheet_name="Uretim Verileri",
        index=False,
        engine="openpyxl",
    )

    print(f"Ornek uretim verisi olusturuldu: {output_path}")
    print(f"Satir sayisi: {len(df)}")
    print(f"Ortalama fire orani: %{df['fire_orani'].mean():.1f}")
    print(f"Min fire orani: %{df['fire_orani'].min():.1f}")
    print(f"Max fire orani: %{df['fire_orani'].max():.1f}")
    print(f"\nIlk 5 satir:\n{df.head()}")
