"""Constants for the Gemini HA Orchestrator integration."""

DOMAIN = "gemini_ha_orchestrator"

CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_SIDEBAR_PANEL = "sidebar_panel"
CONF_SIDEBAR_TITLE = "sidebar_title"
CONF_SIDEBAR_ICON = "sidebar_icon"

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_SIDEBAR_PANEL = True
DEFAULT_SIDEBAR_TITLE = "Gemini AI"
DEFAULT_SIDEBAR_ICON = "mdi:robot"

AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]
