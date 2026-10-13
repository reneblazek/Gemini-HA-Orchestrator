"""Gemini HA Orchestrator integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SIDEBAR_ICON,
    CONF_SIDEBAR_PANEL,
    CONF_SIDEBAR_TITLE,
    DEFAULT_SIDEBAR_ICON,
    DEFAULT_SIDEBAR_PANEL,
    DEFAULT_SIDEBAR_TITLE,
    DOMAIN,
)
from .services import async_setup_services
from .views import GeminiChatApiView, GeminiConfirmApiView, GeminiConsoleView

_LOGGER = logging.getLogger(__name__)

try:
    from homeassistant.components import frontend
except Exception:
    frontend = None

try:
    from google import genai
    from google.genai import types

    # Tool definition for Gemini
    save_blueprint_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="save_blueprint",
                description="Creates a new Home Assistant Blueprint and saves it to the system.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "name": types.Schema(type=types.Type.STRING, description="Blueprint name (e.g. morning_routine)"),
                        "yaml_code": types.Schema(type=types.Type.STRING, description="Complete valid YAML code of the blueprint"),
                    },
                    required=["name", "yaml_code"],
                ),
            )
        ]
    )
except Exception:
    save_blueprint_tool = None


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Gemini HA Orchestrator component from configuration.yaml (if any)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gemini HA Orchestrator from a config entry (UI setup)."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {**entry.data, **entry.options}

    # Register services
    await async_setup_services(hass)

    # Register HTTP Views for Web Console and API
    hass.http.register_view(GeminiConsoleView(hass))
    hass.http.register_view(GeminiChatApiView(hass))
    hass.http.register_view(GeminiConfirmApiView(hass))

    # Register Sidebar Panel if enabled
    config_data = {**entry.data, **entry.options}
    if config_data.get(CONF_SIDEBAR_PANEL, DEFAULT_SIDEBAR_PANEL):
        sidebar_title = config_data.get(CONF_SIDEBAR_TITLE, DEFAULT_SIDEBAR_TITLE)
        sidebar_icon = config_data.get(CONF_SIDEBAR_ICON, DEFAULT_SIDEBAR_ICON)

        try:
            if frontend is not None:
                frontend.async_register_built_in_panel(
                    hass,
                    component_name="iframe",
                    sidebar_title=sidebar_title,
                    sidebar_icon=sidebar_icon,
                    frontend_url_path="gemini_console",
                    config={"url": "/api/gemini_ha_orchestrator/console"},
                    require_admin=False,
                    update=True,
                )
                _LOGGER.info("Gemini Console registered in Home Assistant sidebar panel")
            elif hasattr(hass.components, "frontend"):
                hass.components.frontend.async_register_built_in_panel(
                    hass,
                    component_name="iframe",
                    sidebar_title=sidebar_title,
                    sidebar_icon=sidebar_icon,
                    frontend_url_path="gemini_console",
                    config={"url": "/api/gemini_ha_orchestrator/console"},
                    require_admin=False,
                    update=True,
                )
                _LOGGER.info("Gemini Console registered in Home Assistant sidebar panel")
        except Exception as e:
            _LOGGER.warning("Could not register sidebar panel: %s", e)
    else:
        try:
            if frontend is not None:
                frontend.async_remove_panel(hass, "gemini_console")
            elif hasattr(hass.components, "frontend"):
                hass.components.frontend.async_remove_panel(hass, "gemini_console")
        except Exception as e:
            _LOGGER.debug("Error removing sidebar panel: %s", e)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove sidebar panel
    try:
        if frontend is not None:
            frontend.async_remove_panel(hass, "gemini_console")
        elif hasattr(hass.components, "frontend"):
            hass.components.frontend.async_remove_panel(hass, "gemini_console")
    except Exception as e:
        _LOGGER.debug("Error removing sidebar panel: %s", e)

    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
