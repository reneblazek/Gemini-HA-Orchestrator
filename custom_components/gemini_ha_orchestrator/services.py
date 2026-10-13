import os
import logging
from homeassistant.core import HomeAssistant, ServiceCall

try:
    from ruamel.yaml import YAML
except Exception:
    YAML = None

_LOGGER = logging.getLogger(__name__)
DOMAIN = "gemini_ha_orchestrator"

class GeminiFileModifier:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.config_dir = hass.config.config_dir
        self._yaml = None

    @property
    def yaml(self):
        """Lazy load ruamel.yaml YAML instance to avoid blocking event loop during initialization."""
        if self._yaml is None and YAML is not None:
            self._yaml = YAML()
            self._yaml.preserve_quotes = True  # Preserves quotes in HA code
        return self._yaml

    def modify_configuration_yaml(self, domain_key: str, new_data: dict):
        """Safely adds or modifies a section in the main configuration.yaml."""
        config_path = os.path.join(self.config_dir, "configuration.yaml")

        try:
            if self.yaml:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = self.yaml.load(f) or {}

                config_data[domain_key] = new_data

                with open(config_path, "w", encoding="utf-8") as f:
                    self.yaml.dump(config_data, f)
            else:
                import yaml
                config_data = {}
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = yaml.safe_load(f) or {}
                config_data[domain_key] = new_data
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config_data, f, sort_keys=False)

            _LOGGER.info(f"Section {domain_key} successfully updated in configuration.yaml")
            return True
        except Exception as e:
            _LOGGER.error(f"Error writing to configuration.yaml: {e}")
            return False

    def save_blueprint(self, blueprint_name: str, yaml_content: str):
        """Creates or overwrites a blueprint in the appropriate directory."""
        # Set path to blueprints/automation/
        blueprint_dir = os.path.join(self.config_dir, "blueprints", "automation")
        os.makedirs(blueprint_dir, exist_ok=True)

        # Sanitize file name from unsafe characters
        safe_name = "".join([c if c.isalnum() else "_" for c in blueprint_name]).strip("_")
        file_path = os.path.join(blueprint_dir, f"{safe_name}.yaml")

        try:
            # Write raw YAML string returned by Gemini
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            _LOGGER.info(f"Blueprint {blueprint_name} was successfully saved to {file_path}")
            return True
        except Exception as e:
            _LOGGER.error(f"Failed to save Blueprint: {e}")
            return False

async def async_setup_services(hass: HomeAssistant):
    """Registers services that can be executed by the system or automation."""
    modifier = GeminiFileModifier(hass)

    async def handle_save_blueprint(call: ServiceCall):
        name = call.data.get("name")
        code = call.data.get("yaml_code")
        # Since I/O operations are synchronous, run them in the executor
        await hass.async_add_executor_job(modifier.save_blueprint, name, code)
        # After writing, notify Home Assistant to reload blueprints
        await hass.services.async_call("blueprint", "reload")

    hass.services.async_register(DOMAIN, "save_blueprint", handle_save_blueprint)
