# SmartFloors MVP

SmartFloors es un panel predictivo para monitorear condiciones ambientales y eléctricas por piso en edificios corporativos. El MVP incluye ingestión de datos simulados, generación de predicciones a 60 minutos, detección de anomalías y recomendaciones accionables.

## Requisitos

- Python 3.10+
- Dependencias listadas en `requirements.txt`

Instalación rápida:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Uso

Ejecuta el panel Streamlit:

```bash
streamlit run streamlit_app.py
```

El panel se abrirá en `http://localhost:8501` mostrando:

- Tarjetas de estado por piso con resumen de temperatura, humedad y energía.
- Gráficos de tendencia (últimas 4 horas) para cada variable.
- Tabla de alertas con filtros por piso y nivel, incluyendo recomendaciones y descarga en CSV.

Puedes cargar tu propio archivo CSV usando el panel lateral. Debe incluir las columnas:

```
timestamp, edificio, piso, temp_c, humedad_pct, energia_kw
```

## Estructura

```
smartfloors/
├── analytics.py        # Predicciones y detección de alertas
├── data.py             # Carga de datasets
├── recommendations.py  # Recomendaciones por alerta
streamlit_app.py        # Panel Streamlit
requirements.txt        # Dependencias
```

## Tests

Incluimos pruebas básicas sobre la lógica de alertas. Ejecuta:

```bash
pytest
```

## Datos de ejemplo

El directorio `data/` contiene `smartfloors_sample.csv` con 24 horas de datos simulados a razón de un registro por minuto para los pisos 1–3 del Edificio A.
