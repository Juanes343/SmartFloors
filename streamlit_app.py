"""Streamlit dashboard for the SmartFloors MVP."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

import pandas as pd
import streamlit as st

from smartfloors import (
    ALERT_LEVELS,
    detect_alerts,
    generate_forecasts,
    generate_recommendation,
    load_dataset,
)
from smartfloors.analytics import Alert, Forecast

st.set_page_config(page_title="SmartFloors", layout="wide")
st.title("SmartFloors – Monitoreo predictivo por piso")


@lru_cache
def _load_default_dataset() -> pd.DataFrame:
    return load_dataset()


def _load_data() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader(
        "Cargar CSV personalizado", type="csv", help="Debe incluir las columnas definidas en el reto."
    )
    if uploaded:
        df = pd.read_csv(uploaded, parse_dates=["timestamp"])
        return df.sort_values("timestamp").reset_index(drop=True)
    return _load_default_dataset()


def _alert_level_priority(level: str) -> int:
    priority = {"OK": 0, "Informativa": 1, "Media": 2, "Crítica": 3}
    return priority.get(level, 0)


def _floor_summary(df: pd.DataFrame, alerts: List[Alert]) -> Dict[int, Dict[str, str]]:
    summary: Dict[int, Dict[str, str]] = {}
    grouped = df.groupby("piso").tail(1).set_index("piso")
    alerts_by_floor: Dict[int, List[Alert]] = {}
    for alert in alerts:
        alerts_by_floor.setdefault(alert.piso, []).append(alert)

    for piso, row in grouped.iterrows():
        piso_alerts = alerts_by_floor.get(int(piso), [])
        if piso_alerts:
            level = max(piso_alerts, key=lambda a: _alert_level_priority(a.nivel)).nivel
            resumen = piso_alerts[0].mensaje
        else:
            level = "OK"
            resumen = "Condiciones dentro de rango"

        summary[int(piso)] = {
            "nivel": level,
            "resumen": resumen,
            "temp": f"{row['temp_c']:.1f} °C",
            "humedad": f"{row['humedad_pct']:.1f} %",
            "energia": f"{row['energia_kw']:.1f} kW",
        }
    return summary


def _level_badge(level: str) -> str:
    colors = {
        "OK": "#2d9d5f",
        "Informativa": "#f2c744",
        "Media": "#f2994a",
        "Crítica": "#eb5757",
    }
    return f"<span style='background-color:{colors.get(level, '#999')}; padding:0.15rem 0.45rem; border-radius:0.5rem; color:white;'>{level}</span>"


def main() -> None:
    df = _load_data()
    st.sidebar.header("Filtros")
    pisos = sorted(df["piso"].unique())
    piso_filter = st.sidebar.multiselect("Pisos", pisos, default=pisos)
    nivel_filter = st.sidebar.multiselect("Nivel de alerta", ALERT_LEVELS, default=ALERT_LEVELS)

    df_filtered = df[df["piso"].isin(piso_filter)]
    forecasts = generate_forecasts(df_filtered)
    alerts = detect_alerts(df_filtered, forecasts)

    st.sidebar.metric(
        "Alertas activas",
        sum(1 for a in alerts if a.nivel in {"Media", "Crítica"}),
        help="Número de alertas medias/críticas considerando filtros actuales.",
    )

    summary = _floor_summary(df_filtered, alerts)
    st.subheader("Estado general por piso")
    cols = st.columns(len(summary) or 1)
    for col, (piso, info) in zip(cols, summary.items()):
        col.markdown(f"### Piso {piso}")
        col.markdown(_level_badge(info["nivel"]), unsafe_allow_html=True)
        col.metric("Temperatura", info["temp"])
        col.metric("Humedad", info["humedad"])
        col.metric("Energía", info["energia"])
        col.caption(info["resumen"])

    st.subheader("Tendencias (últimas 4 horas)")
    window = df_filtered[df_filtered["timestamp"] >= df_filtered["timestamp"].max() - pd.Timedelta(hours=4)]
    if window.empty:
        st.info("No hay datos suficientes en la ventana seleccionada.")
    else:
        charts = {
            "Temperatura (°C)": "temp_c",
            "Humedad relativa (%)": "humedad_pct",
            "Energía (kW)": "energia_kw",
        }
        for label, column in charts.items():
            chart_df = window[["timestamp", "piso", column]].rename(columns={column: label})
            st.line_chart(chart_df.set_index("timestamp"), x_label="Tiempo", y_label=label)

    st.subheader("Alertas y recomendaciones")
    alert_rows = []
    for alert in alerts:
        if alert.nivel not in nivel_filter or alert.piso not in piso_filter:
            continue
        alert_rows.append(
            {
                "timestamp": alert.timestamp,
                "piso": alert.piso,
                "variable": alert.variable,
                "nivel": alert.nivel,
                "tipo": alert.tipo,
                "mensaje": alert.mensaje,
                "recomendacion": generate_recommendation(alert),
            }
        )

    if alert_rows:
        alert_df = pd.DataFrame(alert_rows)
        st.dataframe(alert_df, use_container_width=True)
        st.download_button(
            "Descargar alertas (CSV)",
            data=alert_df.to_csv(index=False).encode("utf-8"),
            file_name="smartfloors_alertas.csv",
            mime="text/csv",
        )
    else:
        st.success("Sin alertas para los filtros seleccionados.")

    st.caption(
        "Predicciones basadas en tendencia lineal de los últimos 120 minutos. "
        "Los umbrales pueden ajustarse según las políticas del edificio."
    )


if __name__ == "__main__":
    main()
