"""Config flow for Gemini HA Orchestrator integration."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    AVAILABLE_MODELS,
    CONF_API_KEY,
    CONF_MODEL,
    CONF_SIDEBAR_ICON,
    CONF_SIDEBAR_PANEL,
    CONF_SIDEBAR_TITLE,
    DEFAULT_MODEL,
    DEFAULT_SIDEBAR_ICON,
    DEFAULT_SIDEBAR_PANEL,
    DEFAULT_SIDEBAR_TITLE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GeminiHAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gemini HA Orchestrator."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial setup step from UI."""
        errors: dict[str, str] = {}

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            if not api_key:
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                return self.async_create_entry(
                    title=f"Gemini Orchestrator ({user_input.get(CONF_MODEL, DEFAULT_MODEL)})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): vol.In(AVAILABLE_MODELS),
                vol.Optional(CONF_SIDEBAR_PANEL, default=DEFAULT_SIDEBAR_PANEL): bool,
                vol.Optional(CONF_SIDEBAR_TITLE, default=DEFAULT_SIDEBAR_TITLE): str,
                vol.Optional(CONF_SIDEBAR_ICON, default=DEFAULT_SIDEBAR_ICON): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return GeminiHAOptionsFlow(config_entry)


class GeminiHAOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Gemini HA Orchestrator."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the integration options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_config = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_API_KEY,
                    default=current_config.get(CONF_API_KEY, ""),
                ): str,
                vol.Optional(
                    CONF_MODEL,
                    default=current_config.get(CONF_MODEL, DEFAULT_MODEL),
                ): vol.In(AVAILABLE_MODELS),
                vol.Optional(
                    CONF_SIDEBAR_PANEL,
                    default=current_config.get(CONF_SIDEBAR_PANEL, DEFAULT_SIDEBAR_PANEL),
                ): bool,
                vol.Optional(
                    CONF_SIDEBAR_TITLE,
                    default=current_config.get(CONF_SIDEBAR_TITLE, DEFAULT_SIDEBAR_TITLE),
                ): str,
                vol.Optional(
                    CONF_SIDEBAR_ICON,
                    default=current_config.get(CONF_SIDEBAR_ICON, DEFAULT_SIDEBAR_ICON),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
