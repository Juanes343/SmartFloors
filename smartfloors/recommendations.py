"""Alert recommendation helpers."""

from __future__ import annotations

from typing import Dict

from .analytics import Alert

RECOMMENDATION_TEMPLATES: Dict[str, Dict[str, str]] = {
    "temperatura": {
        "Informativa": "Verificar setpoints de HVAC y confirmar si se requieren ajustes mínimos en el piso {piso}.",
        "Media": "Ajustar temperatura del Piso {piso} a 24 °C en los próximos 15 minutos; revisar puertas/celosías.",
        "Crítica": "Activar plan de contingencia térmica en Piso {piso}; redistribuir personal y priorizar ventilación forzada.",
    },
    "humedad": {
        "Informativa": "Monitorear humidificadores/deshumidificadores del Piso {piso} durante la próxima hora.",
        "Media": "Revisar sellos de ventanas y equipos HVAC del Piso {piso}; programar inspección en 30 min.",
        "Crítica": "Coordinar intervención inmediata para controlar humedad en Piso {piso}; verificar sensores adicionales.",
    },
    "energia": {
        "Informativa": "Revisar si hay equipos no críticos encendidos en Piso {piso}; programar apagado manual.",
        "Media": "Redistribuir carga eléctrica del Piso {piso} al Piso 1 en la próxima hora.",
        "Crítica": "Aplicar plan de alivio de carga: transferir equipos no esenciales del Piso {piso} y notificar mantenimiento.",
    },
}


def generate_recommendation(alert: Alert) -> str:
    """Return a short recommendation for a given alert."""

    templates = RECOMMENDATION_TEMPLATES.get(alert.variable, {})
    template = templates.get(alert.nivel)
    if not template:
        return f"Revisar condición reportada en Piso {alert.piso}."
    return template.format(piso=alert.piso)


__all__ = ["generate_recommendation"]
