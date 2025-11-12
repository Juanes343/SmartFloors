# 🏢 SmartFloors MVP

**SmartFloors** es un panel predictivo e interactivo para **monitorear condiciones ambientales y eléctricas por piso** en edificios corporativos.  
El MVP permite la **ingestión de datos simulados**, **predicciones a 60 minutos**, **detección de anomalías**, **explicaciones automáticas**, y **recomendaciones accionables**.  
Además, incluye **envío de alertas por correo electrónico** y simulación de datos en tiempo real.

---

## 🚀 Requisitos

- Python **3.10+**
- Dependencias listadas en [`requirements.txt`](./requirements.txt)

Instalación rápida:

```bash
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🧠 Funcionalidades principales

✅ **Simulación en tiempo real**  
Carga un CSV de datos históricos y el sistema los “reproduce” en vivo (cada 5 segundos), actualizando el panel.

✅ **Predicciones a corto plazo (60 min)**  
Cada variable (temperatura, humedad y energía) es proyectada mediante un modelo de **Regresión Lineal (scikit-learn)**.  

✅ **Detección de anomalías / alertas**  
El sistema evalúa las métricas frente a umbrales dinámicos para clasificar eventos como:
- 🟢 OK  
- 🟡 Informativa  
- 🟠 Media  
- 🔴 Crítica  

✅ **Explicabilidad automática**  
Cada alerta incluye una breve explicación del motivo (e.g., *“Temperatura superó el umbral de 28°C durante los últimos 10 minutos”*).

✅ **Recomendaciones inteligentes**  
El módulo `generate_recommendation()` sugiere acciones específicas según el tipo de alerta y variable afectada.

✅ **Visualización avanzada (Plotly)**  
Los gráficos muestran tendencias y líneas de referencia con umbrales configurables (Info, Media, Crítica), y una predicción +60 min.

✅ **Envío de alertas por correo**  
Permite notificar automáticamente eventos de nivel *Medio* o *Crítico* a correos configurados mediante SMTP.

---

## 💻 Uso

Ejecuta el panel Streamlit:

```bash
streamlit run streamlit_app.py
```

El panel se abrirá automáticamente en [http://localhost:8501](http://localhost:8501) mostrando:

- Tarjetas de **estado por piso** con temperatura, humedad y energía.
- **Gráficos de tendencia** (últimas 1, 2 o 4 horas) para cada variable.
- **Tabla de alertas** con filtros por piso y nivel, incluyendo explicaciones y recomendaciones.
- Botón de **descarga en CSV** de las alertas actuales.
- Simulación de monitoreo con controles *Iniciar / Pausar* y *Reiniciar*.

---

## 📊 Carga de datos

Puedes cargar tu propio archivo CSV usando el panel lateral.  
El archivo debe incluir las siguientes columnas obligatorias:

```
timestamp, edificio, piso, temp_c, humedad_pct, energia_kw
```

Ejemplo:

```csv
2024-05-01T06:00:00,A,1,26.5,55.1,19.3
2024-05-01T06:01:00,A,1,26.8,54.7,19.0
2024-05-01T06:02:00,A,2,27.4,59.2,20.9
```

---

## 📦 Estructura del proyecto

```
HACKATHON/
├── SmartFloors/
│   ├── __init__.py
│   ├── analytics.py        # Predicciones y detección de alertas
│   ├── data.py             # Carga de datasets y datos de ejemplo
│   ├── notifications.py    # Envío de correos de alerta (SMTP)
│   ├── recommendations.py  # Recomendaciones según tipo de alerta
├── streamlit_app.py        # Panel principal en Streamlit
├── requirements.txt        # Dependencias del proyecto
├── README.md               # Este archivo
└── data/
    └── smartfloors_sample.csv   # Datos simulados de ejemplo
```

---

## ⚙️ Configuración del correo (SMTP)

Para habilitar el envío de notificaciones por correo, crea el archivo:

```
.streamlit/secrets.toml
```

Con la siguiente estructura:

```toml
[smtp]
host = "smtp.gmail.com"
port = 465
user = "tu_correo@gmail.com"
password = "tu_clave_de_aplicacion"
```

📌 **Importante:**  
No subas este archivo a GitHub (ya está excluido en `.gitignore`).

---

## 🧮 Predicción

El modelo usa **Regresión Lineal** (`sklearn.linear_model.LinearRegression`) para predecir cada variable en un horizonte de **+60 minutos**.  
El proceso es el siguiente:

1. Se convierten las marcas de tiempo a segundos (`timestamp → t`).
2. Se entrena una regresión `y = a*t + b` con los datos de la ventana seleccionada.
3. Se calcula el valor futuro a `t + 3600` segundos.
4. Se muestra la predicción en el gráfico (línea punteada naranja).

---

## ⚠️ Umbrales de alerta

| Nivel        | Temperatura (°C) | Humedad (%) | Energía (kW) |
|---------------|------------------|--------------|---------------|
| Informativa   | > 25             | > 50         | > 20          |
| Media         | > 28             | > 60         | > 25          |
| Crítica       | > 31             | > 70         | > 30          |

Cada alerta se genera cuando una variable supera su umbral en las predicciones o lecturas recientes.

---

## 📈 Gráficos de tendencia

- Muestran la evolución por piso y variable.
- Permiten ajustar la **ventana temporal manualmente**:
  - 1 hora  
  - 2 horas  
  - 4 horas  
  - Todo el histórico
- Incluyen los **umbrales visuales** (Info, Media, Crítica) y la **predicción a +60 min**.

---

## 🧪 Tests

El módulo incluye pruebas básicas sobre la lógica de detección de alertas.  
Ejecuta:

```bash
pytest
```

---

## 🧰 Datos de ejemplo

El directorio `data/` contiene `smartfloors_sample.csv` con **24 horas de datos simulados**  
(a razón de un registro por minuto) para los pisos 1–3 del **Edificio A**.

---

## 🧩 Demo funcional (Hackathon)

- Dashboard 100% funcional en Streamlit.  
- Monitoreo en tiempo real con autorefresco cada 5 segundos.  
- Predicciones y alertas actualizadas dinámicamente.  
- Gráficos interactivos y descarga de reportes.  
- Explicabilidad del origen de cada alerta.  
- Integración opcional con envío de correo.

---

## 🧠 Tecnologías utilizadas

- **Python 3.10+**
- **Streamlit** – Interfaz web y visualización  
- **Plotly** – Gráficas interactivas  
- **Pandas / NumPy** – Procesamiento de datos  
- **Scikit-learn** – Modelado predictivo (Regresión Lineal)  
- **Streamlit-Autorefresh** – Simulación en tiempo real  
- **smtplib / ssl / email** – Envío de notificaciones

---

## 🪪 Licencia

Este proyecto se distribuye bajo licencia **MIT**.  
Puedes usarlo, modificarlo y compartirlo libremente dando crédito al equipo desarrollador.

---

## 👨‍💻 Equipo SmartFloors

Proyecto desarrollado para el **Hackathon Zona F 2025**  
📧 Contacto: smartfloors.team@gmail.com  
🌐 Categoría: *Soluciones predictivas y eficiencia energética en edificios inteligentes.*