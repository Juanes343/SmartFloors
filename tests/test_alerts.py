from datetime import datetime, timedelta

import pandas as pd

from SmartFloors.analytics import Alert, generate_forecasts, detect_alerts


def build_df(temp: float, humidity: float, energy: float) -> pd.DataFrame:
    base_time = datetime(2024, 5, 1, 12, 0)
    data = []
    for minute in range(5):
        data.append(
            {
                "timestamp": base_time + timedelta(minutes=minute),
                "edificio": "A",
                "piso": 1,
                "temp_c": temp + minute * 0.1,
                "humedad_pct": humidity,
                "energia_kw": energy,
            }
        )
    return pd.DataFrame(data)


def test_detects_temperature_alert():
    df = build_df(30.2, 60.0, 15.0)
    forecasts = generate_forecasts(df)
    alerts = detect_alerts(df, forecasts)
    assert any(alert.variable == "temperatura" and alert.nivel == "Crítica" for alert in alerts)


def test_predictive_alerts_triggered():
    df = build_df(27.5, 60.0, 15.0)
    df.loc[:, "temp_c"] = [27.5, 27.6, 27.9, 28.5, 29.2]
    forecasts = generate_forecasts(df)
    alerts = detect_alerts(df, forecasts)
    predictive = [a for a in alerts if a.tipo == "Predictiva" and a.variable == "temperatura"]
    assert predictive, "Se espera alerta predictiva cuando la tendencia apunta a valor crítico"
