"""Tests for Config Flow and Home Assistant component lifecycle."""
import asyncio
import sys
import unittest
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

# Setup lightweight mocks for Home Assistant modules if not present in test environment
def _setup_mocks():
    if "voluptuous" not in sys.modules:
        vol = ModuleType("voluptuous")
        vol.Schema = lambda schema: schema
        vol.Required = lambda key, default=None: key
        vol.Optional = lambda key, default=None: key
        vol.In = lambda items: items
        sys.modules["voluptuous"] = vol

    if "aiohttp" not in sys.modules:
        aiohttp = ModuleType("aiohttp")
        aiohttp_web = ModuleType("aiohttp.web")
        class Response:
            def __init__(self, text="", content_type="text/plain", status=200):
                self.text = text
                self.content_type = content_type
                self.status = status
        aiohttp_web.Response = Response
        aiohttp_web.json_response = lambda data, status=200: Response(text=str(data), content_type="application/json", status=status)
        aiohttp_web.Request = MagicMock
        aiohttp.web = aiohttp_web
        sys.modules["aiohttp"] = aiohttp
        sys.modules["aiohttp.web"] = aiohttp_web

    if "homeassistant" not in sys.modules:
        ha = ModuleType("homeassistant")
        ha_core = ModuleType("homeassistant.core")
        ha_core.HomeAssistant = MagicMock
        ha_core.ServiceCall = MagicMock
        ha_core.callback = lambda f: f

        ha_config_entries = ModuleType("homeassistant.config_entries")
        class ConfigFlow:
            def __init_subclass__(cls, domain=None, **kwargs):
                super().__init_subclass__(**kwargs)
                cls.domain = domain
            def async_show_form(self, step_id, data_schema=None, errors=None):
                return {"type": "form", "step_id": step_id, "schema": data_schema, "errors": errors or {}}
            def async_create_entry(self, title, data):
                return {"type": "create_entry", "title": title, "data": data}
            async def async_set_unique_id(self, uid):
                pass
            def _abort_if_unique_id_configured(self):
                pass

        class OptionsFlow:
            def async_show_form(self, step_id, data_schema=None, errors=None):
                return {"type": "form", "step_id": step_id, "schema": data_schema, "errors": errors or {}}
            def async_create_entry(self, title, data):
                return {"type": "create_entry", "title": title, "data": data}

        ha_config_entries.ConfigFlow = ConfigFlow
        ha_config_entries.OptionsFlow = OptionsFlow
        ha_config_entries.ConfigEntry = MagicMock

        ha_data_entry_flow = ModuleType("homeassistant.data_entry_flow")
        ha_data_entry_flow.FlowResult = dict

        ha_components = ModuleType("homeassistant.components")
        ha_components_http = ModuleType("homeassistant.components.http")
        class HomeAssistantView:
            url = ""
            name = ""
            requires_auth = False
        ha_components_http.HomeAssistantView = HomeAssistantView
        ha_components.http = ha_components_http

        ha_components_frontend = ModuleType("homeassistant.components.frontend")
        ha_components_frontend.async_register_built_in_panel = MagicMock()
        ha_components_frontend.async_remove_panel = MagicMock()
        ha_components.frontend = ha_components_frontend

        ha.core = ha_core
        ha.config_entries = ha_config_entries
        ha.data_entry_flow = ha_data_entry_flow
        ha.components = ha_components
        ha.components.http = ha_components_http
        ha.components.frontend = ha_components_frontend

        sys.modules["homeassistant"] = ha
        sys.modules["homeassistant.core"] = ha_core
        sys.modules["homeassistant.config_entries"] = ha_config_entries
        sys.modules["homeassistant.data_entry_flow"] = ha_data_entry_flow
        sys.modules["homeassistant.components"] = ha_components
        sys.modules["homeassistant.components.http"] = ha_components_http
        sys.modules["homeassistant.components.frontend"] = ha_components_frontend

_setup_mocks()

from custom_components.gemini_ha_orchestrator.const import (
    CONF_API_KEY,
    CONF_MODEL,
    CONF_SIDEBAR_PANEL,
    DEFAULT_MODEL,
    DOMAIN,
)
from custom_components.gemini_ha_orchestrator.config_flow import (
    GeminiHAConfigFlow,
    GeminiHAOptionsFlow,
)
from custom_components.gemini_ha_orchestrator.views import (
    PENDING_ACTIONS,
    GeminiConsoleView,
    GeminiConfirmApiView,
)
from custom_components.gemini_ha_orchestrator import (
    async_setup,
    async_setup_entry,
    async_unload_entry,
)


class TestConfigFlow(unittest.TestCase):
    """Test suite for config flow and options flow."""

    def test_config_flow_user_form(self):
        """Test user flow displays form on initial step."""
        flow = GeminiHAConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = asyncio.run(flow.async_step_user(user_input=None))
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["step_id"], "user")

    def test_config_flow_user_empty_api_key(self):
        """Test error when API key is empty."""
        flow = GeminiHAConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = asyncio.run(flow.async_step_user(user_input={CONF_API_KEY: "   "}))
        self.assertEqual(result["type"], "form")
        self.assertEqual(result["errors"], {CONF_API_KEY: "invalid_api_key"})

    def test_config_flow_user_success(self):
        """Test successful config entry creation."""
        flow = GeminiHAConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = asyncio.run(flow.async_step_user(user_input={
            CONF_API_KEY: "test-gemini-key",
            CONF_MODEL: "gemini-3.8-pro",
            CONF_SIDEBAR_PANEL: True,
        }))
        self.assertEqual(result["type"], "create_entry")
        self.assertIn("Gemini Orchestrator", result["title"])
        self.assertEqual(result["data"][CONF_API_KEY], "test-gemini-key")

    def test_options_flow(self):
        """Test options flow initialization and update."""
        config_entry = MagicMock()
        config_entry.data = {CONF_API_KEY: "key1", CONF_MODEL: DEFAULT_MODEL}
        config_entry.options = {}

        # Test both instantiations
        options_flow = GeminiHAOptionsFlow(config_entry)
        options_flow.hass = MagicMock()

        # Step form
        res_form = asyncio.run(options_flow.async_step_init(user_input=None))
        self.assertEqual(res_form["type"], "form")

        # Step update
        res_save = asyncio.run(options_flow.async_step_init(user_input={
            CONF_API_KEY: "new-key",
            CONF_MODEL: "gemini-3.8-pro",
        }))
        self.assertEqual(res_save["type"], "create_entry")
        self.assertEqual(res_save["data"][CONF_API_KEY], "new-key")

        # Test factory callback
        flow_from_factory = GeminiHAConfigFlow.async_get_options_flow(config_entry)
        self.assertIsInstance(flow_from_factory, GeminiHAOptionsFlow)


class TestComponentLifecycle(unittest.TestCase):
    """Test suite for setup, entry loading and views."""

    def test_async_setup(self):
        """Test async_setup sets up domain dict."""
        hass = MagicMock()
        hass.data = {}
        result = asyncio.run(async_setup(hass, {}))
        self.assertTrue(result)
        self.assertIn(DOMAIN, hass.data)

    def test_async_setup_and_unload_entry(self):
        """Test async_setup_entry registers views and panel, and unload cleans up."""
        import homeassistant.components.frontend as frontend_mod
        frontend_mod.async_register_built_in_panel.reset_mock()
        frontend_mod.async_remove_panel.reset_mock()

        hass = MagicMock()
        hass.data = {}
        hass.services.async_register = MagicMock()
        hass.http.register_view = MagicMock()

        entry = MagicMock()
        entry.entry_id = "test_entry_123"
        entry.data = {
            CONF_API_KEY: "test_key",
            CONF_MODEL: DEFAULT_MODEL,
            CONF_SIDEBAR_PANEL: True,
        }
        entry.options = {}
        entry.add_update_listener = MagicMock()
        entry.async_on_unload = MagicMock()

        # Setup entry
        res_setup = asyncio.run(async_setup_entry(hass, entry))
        self.assertTrue(res_setup)
        self.assertIn("test_entry_123", hass.data[DOMAIN])
        self.assertEqual(hass.http.register_view.call_count, 3)
        frontend_mod.async_register_built_in_panel.assert_called_once()
        args, kwargs = frontend_mod.async_register_built_in_panel.call_args
        self.assertEqual(args[0], hass)
        self.assertEqual(kwargs.get("component_name"), "iframe")
        self.assertEqual(kwargs.get("frontend_url_path"), "gemini_console")

        # Unload entry
        res_unload = asyncio.run(async_unload_entry(hass, entry))
        self.assertTrue(res_unload)
        self.assertNotIn("test_entry_123", hass.data[DOMAIN])
        frontend_mod.async_remove_panel.assert_called_once_with(hass, "gemini_console")

    def test_async_setup_entry_sidebar_disabled(self):
        """Test setup when sidebar panel is disabled removes panel."""
        import homeassistant.components.frontend as frontend_mod
        frontend_mod.async_register_built_in_panel.reset_mock()
        frontend_mod.async_remove_panel.reset_mock()

        hass = MagicMock()
        hass.data = {}
        hass.services.async_register = MagicMock()
        hass.http.register_view = MagicMock()

        entry = MagicMock()
        entry.entry_id = "test_entry_disabled"
        entry.data = {
            CONF_API_KEY: "test_key",
            CONF_MODEL: DEFAULT_MODEL,
            CONF_SIDEBAR_PANEL: False,
        }
        entry.options = {}
        entry.add_update_listener = MagicMock()
        entry.async_on_unload = MagicMock()

        res_setup = asyncio.run(async_setup_entry(hass, entry))
        self.assertTrue(res_setup)
        frontend_mod.async_register_built_in_panel.assert_not_called()
        frontend_mod.async_remove_panel.assert_called_once_with(hass, "gemini_console")

    def test_services_yaml_exists_and_valid(self):
        """Test that services.yaml exists and defines save_blueprint service."""
        import os
        services_file = os.path.join(
            os.path.dirname(__file__), "..", "custom_components", "gemini_ha_orchestrator", "services.yaml"
        )
        self.assertTrue(os.path.exists(services_file), "services.yaml should exist")
        with open(services_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("save_blueprint:", content)
        self.assertIn("fields:", content)
        self.assertIn("name:", content)
        self.assertIn("yaml_code:", content)

    def test_gemini_file_modifier_lazy_yaml(self):
        """Test that GeminiFileModifier lazily initializes ruamel.yaml instance."""
        from custom_components.gemini_ha_orchestrator.services import GeminiFileModifier
        hass = MagicMock()
        hass.config.config_dir = "/tmp"
        modifier = GeminiFileModifier(hass)
        self.assertIsNone(modifier._yaml)
        yaml_inst = modifier.yaml
        if yaml_inst is not None:
            self.assertIsNotNone(modifier._yaml)
            self.assertTrue(modifier.yaml.preserve_quotes)

    def test_console_view_html(self):
        """Test console view delivers valid HTML."""
        hass = MagicMock()
        view = GeminiConsoleView(hass)
        response = asyncio.run(view.get(MagicMock()))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.content_type, "text/html")
        self.assertIn("Gemini HA Orchestrator", response.text)

    def test_confirm_view_cancellation(self):
        """Test confirmation view rejection."""
        hass = MagicMock()
        view = GeminiConfirmApiView(hass)

        PENDING_ACTIONS["test-token"] = {
            "action": "save_blueprint",
            "name": "test_bp",
            "yaml_content": "blueprint:\n  name: Test",
        }

        request = MagicMock()
        request.json = AsyncMock(return_value={"token": "test-token", "approved": False})

        response = asyncio.run(view.post(request))
        self.assertEqual(response.status, 200)
        self.assertNotIn("test-token", PENDING_ACTIONS)


if __name__ == "__main__":
    unittest.main()
