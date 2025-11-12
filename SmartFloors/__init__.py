"""SmartFloors monitoring and alerting core package."""

# Importa funciones y constantes desde los submódulos
from .data import load_dataset
from .analytics import (
    ALERT_LEVELS,
    generate_forecasts,
    detect_alerts,
)
from .recommendations import generate_recommendation

__all__ = [
    "ALERT_LEVELS",
    "load_dataset",
    "generate_forecasts",
    "detect_alerts",
    "generate_recommendation",
]