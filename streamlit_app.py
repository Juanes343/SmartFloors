from __future__ import annotations  # 👈 Debe ser la primera línea

"""Streamlit dashboard for the SmartFloors MVP."""

import streamlit as st  # 👈 Streamlit SIEMPRE primero

# 📌 Configuración de la página — debe ejecutarse inmediatamente después del import
st.set_page_config(page_title="SmartFloors", layout="wide")
st.title("SmartFloors – Monitoreo predictivo por piso")

# === 🔧 FIX IMPORT PATH ===
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# ==========================

from functools import lru_cache
from typing import Dict, List
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# Intento de import para autorefresco sin bloquear la UI
try:
    from streamlit_autorefresh import st_autorefresh
    _HAS_AUTOREFRESH = True
except Exception:
    _HAS_AUTOREFRESH = False

# Importa desde SmartFloors
from SmartFloors import (
    ALERT_LEVELS,
    detect_alerts,
    generate_forecasts,
    generate_recommendation,
    load_dataset,
)
from SmartFloors.analytics import Alert
from SmartFloors.notifications import send_email_alert


# =========================
# CARGA DE DATOS
# =========================
@lru_cache
def _load_default_dataset() -> pd.DataFrame:
    """Carga el dataset por defecto desde SmartFloors.data"""
    return load_dataset()


def _load_data() -> pd.DataFrame:
    """Carga un CSV personalizado o el dataset por defecto"""
    uploaded = st.sidebar.file_uploader(
        "Cargar CSV personalizado", type="csv",
        help="CSV con columnas: timestamp, edificio, piso, temp_c, humedad_pct, energia_kw"
    )

    if uploaded:
        df = pd.read_csv(uploaded, parse_dates=["timestamp"])

        # Normalización mínima
        if "edificio" not in df.columns:
            df["edificio"] = "A"

        required = {"timestamp", "edificio", "piso", "temp_c", "humedad_pct", "energia_kw"}
        missing = required - set(df.columns)
        if missing:
            st.error(f"Faltan columnas: {', '.join(missing)}")
            st.stop()

        df = df.sort_values("timestamp").reset_index(drop=True)

        # Reinicia simulación si cambia archivo
        st.session_state.setdefault("_last_rows_hash", None)
        current_hash = hash(df.head(5).to_csv(index=False))

        if st.session_state["_last_rows_hash"] != current_hash:
            st.session_state["_last_rows_hash"] = current_hash
            st.session_state["monitoring_index"] = 1

        return df

    # Dataset por defecto
    df = _load_default_dataset()
    if "edificio" not in df.columns:
        df["edificio"] = "A"
    return df


# =========================
# FUNCIONES AUXILIARES
# =========================
def _alert_level_priority(level: str) -> int:
    return {"OK": 0, "Informativa": 1, "Media": 2, "Crítica": 3}.get(level, 0)


def _floor_summary(df: pd.DataFrame, alerts: List[Alert]) -> Dict[int, Dict[str, str]]:
    summary: Dict[int, Dict[str, str]] = {}
    if df.empty:
        return summary

    grouped = df.groupby("piso").tail(1).set_index("piso")
    alerts_by_floor = {}

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
    return (
        f"<span style='background-color:{colors[level]};"
        "padding:0.15rem 0.45rem; border-radius:0.5rem; color:white;'>"
        f"{level}</span>"
    )


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def main() -> None:
    df_full = _load_data()

    # ---------------------
    # Simulación en tiempo real
    # ---------------------
    if "monitoring_index" not in st.session_state:
        st.session_state.monitoring_index = 1
    if "monitoring_active" not in st.session_state:
        st.session_state.monitoring_active = False

    st.sidebar.header("Monitoreo en tiempo real")
    c1, c2 = st.sidebar.columns(2)

    if c1.button("▶️ Iniciar / Pausar"):
        st.session_state.monitoring_active = not st.session_state.monitoring_active
    if c2.button("⟲ Reiniciar"):
        st.session_state.monitoring_index = 1
        st.session_state.monitoring_active = False

    if st.session_state.monitoring_active:
        if _HAS_AUTOREFRESH:
            st_autorefresh(interval=5000, key="data_refresh")
        else:
            st.sidebar.warning("Instala streamlit-autorefresh para refresco automático.")

    total_rows = len(df_full)
    if st.session_state.monitoring_active:
        st.session_state.monitoring_index = min(st.session_state.monitoring_index + 1, total_rows)

    df_visible = df_full.iloc[: st.session_state.monitoring_index]

    st.progress(st.session_state.monitoring_index / total_rows)
    st.caption(f"📈 Progreso: {st.session_state.monitoring_index}/{total_rows} registros procesados")

    # ---------------------
    # Filtros
    # ---------------------
    st.sidebar.header("Filtros")
    edificios = sorted(df_visible["edificio"].unique())
    edificio_filter = st.sidebar.selectbox("Edificio", edificios)
    df_visible = df_visible[df_visible["edificio"] == edificio_filter]

    pisos = sorted(df_visible["piso"].unique())
    piso_filter = st.sidebar.multiselect("Pisos", pisos, default=pisos)
    nivel_filter = st.sidebar.multiselect("Nivel de alerta", ALERT_LEVELS, default=ALERT_LEVELS)

    # ---------------------
    # Notificaciones email
    # ---------------------
    st.sidebar.header("Notificaciones por correo")
    enable_mail = st.sidebar.checkbox("Activar envío de alertas", value=False)
    to_email = st.sidebar.text_input("Enviar a:", "destinatario@correo.com")

    smtp = st.secrets.get("smtp", {})
    smtp_host = smtp.get("host", "")
    smtp_port = int(smtp.get("port", 0) or 0)
    smtp_user = smtp.get("user", "")
    smtp_pass = smtp.get("password", "")

    # ---------------------
    # Detección de alertas
    # ---------------------
    df_filtered = df_visible[df_visible["piso"].isin(piso_filter)]
    forecasts = generate_forecasts(df_filtered)
    alerts = detect_alerts(df_filtered, forecasts)

    st.sidebar.metric(
        "Alertas activas",
        sum(a.nivel in {"Media", "Crítica"} for a in alerts),
        help="Número de alertas medias o críticas."
    )

    # ---------------------
    # Estado general
    # ---------------------
    st.subheader(f"Estado general por piso — Edificio {edificio_filter}")
    summary = _floor_summary(df_filtered, alerts)

    cols = st.columns(len(summary))
    for col, (piso, info) in zip(cols, summary.items()):
        col.markdown(f"### Piso {piso}")
        col.markdown(_level_badge(info["nivel"]), unsafe_allow_html=True)
        col.metric("Temperatura", info["temp"])
        col.metric("Humedad", info["humedad"])
        col.metric("Energía", info["energia"])
        col.caption(info["resumen"])

    # ---------------------
    # Gráficos de tendencia (ventana dinámica)
    # ---------------------
    st.subheader("Tendencias por piso (últimas horas)")

    charts = {
        "Temperatura (°C)": "temp_c",
        "Humedad relativa (%)": "humedad_pct",
        "Energía (kW)": "energia_kw",
    }

    # Umbrales
    UMBRAL_INFO = {"temp_c": 25, "humedad_pct": 50, "energia_kw": 20}
    UMBRAL_MEDIA = {"temp_c": 28, "humedad_pct": 60, "energia_kw": 25}
    UMBRAL_CRITICA = {"temp_c": 31, "humedad_pct": 70, "energia_kw": 30}

    if not df_filtered.empty:
        max_time = df_filtered["timestamp"].max()
        min_time = df_filtered["timestamp"].min()
        total_minutes = max(1, int((max_time - min_time).total_seconds() // 60))

        if total_minutes <= 60:
            hours_window = 1
        elif total_minutes <= 120:
            hours_window = 2
        else:
            hours_window = 4

        wmin = max_time - pd.Timedelta(hours=hours_window)
        window = df_filtered[df_filtered["timestamp"] >= wmin]

        st.caption(f"📊 Mostrando datos de las últimas **{hours_window} horas**.")

        # --- Graficado por piso ---
        for label, column in charts.items():
            st.markdown(f"### {label}")

            for piso in sorted(window["piso"].unique()):
                piso_df = window[window["piso"] == piso]

                if piso_df.empty:
                    continue

                # Predict +60m
                try:
                    x = (piso_df["timestamp"] - piso_df["timestamp"].min()).dt.total_seconds().values.reshape(-1, 1)
                    y = piso_df[column].values.reshape(-1, 1)
                    model = LinearRegression()
                    model.fit(x, y)
                    pred = float(model.predict([[x[-1][0] + 3600]])[0][0])
                except Exception:
                    pred = float(piso_df[column].iloc[-1])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=piso_df["timestamp"],
                    y=piso_df[column],
                    mode="lines+markers",
                    line=dict(color="#FF7F0E"),
                ))

                # Predicción +60 min
                fig.add_trace(go.Scatter(
                    x=[piso_df["timestamp"].iloc[-1], piso_df["timestamp"].iloc[-1] + pd.Timedelta(minutes=60)],
                    y=[piso_df[column].iloc[-1], pred],
                    mode="lines+markers+text",
                    text=[None, f"Pred +60m: {pred:.2f}"],
                    textposition="top right",
                    line=dict(color="#FF4500", dash="dash"),
                    marker=dict(symbol="diamond", size=9),
                ))

                # Horizontales
                for val, colr, name in [
                    (UMBRAL_INFO[column], "deepskyblue", "Info"),
                    (UMBRAL_MEDIA[column], "goldenrod", "Media"),
                    (UMBRAL_CRITICA[column], "red", "Crítica")
                ]:
                    fig.add_hline(y=val, line_dash="dot", line_color=colr,
                                  annotation_text=name, annotation_position="right")

                fig.update_layout(
                    title=f"Trend — Piso {piso} (Ventana: {hours_window}h)",
                    xaxis_title="Hora",
                    yaxis_title=label,
                    xaxis=dict(tickformat="%H:%M"),
                    template="plotly_dark",
                    height=350,
                )

                st.plotly_chart(fig, use_container_width=True)

    # ---------------------
    # Tabla de alertas
    # ---------------------
    st.subheader("Alertas y recomendaciones")
    alert_rows = []

    for alert in alerts:
        if alert.nivel not in nivel_filter or alert.piso not in piso_filter:
            continue

        explicacion = getattr(alert, "explicacion", None)

        alert_rows.append({
            "timestamp": alert.timestamp,
            "edificio": edificio_filter,
            "piso": alert.piso,
            "variable": alert.variable,
            "nivel": alert.nivel,
            "tipo": alert.tipo,
            "mensaje": alert.mensaje,
            "recomendacion": generate_recommendation(alert),
            "explicacion": explicacion or "",
        })

    if alert_rows:
        df_alerts = pd.DataFrame(alert_rows)
        st.dataframe(df_alerts, use_container_width=True)
        st.download_button(
            "Descargar alertas (CSV)",
            df_alerts.to_csv(index=False).encode("utf-8"),
            "SmartFloors_alertas.csv",
            "text/csv",
        )
    else:
        st.success("Sin alertas activas.")

    st.caption(
        "Monitoreo simulado en tiempo real. Predicción basada en regresión lineal (+60m) "
        "usando ventanas dinámicas de 1–4 horas."
    )


# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    main()
