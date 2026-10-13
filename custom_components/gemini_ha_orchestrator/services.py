import os
import logging
from ruamel.yaml import YAML
from homeassistant.core import HomeAssistant, ServiceCall

_LOGGER = logging.getLogger(__name__)
DOMAIN = "gemini_ha"

class GeminiFileModifier:
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self.config_dir = hass.config.config_dir
        self.yaml = YAML()
        self.yaml.preserve_quotes = True  # Zachová úvodzovky v HA kóde

    def modify_configuration_yaml(self, domain_key: str, new_data: dict):
        """Bezpečne pridá alebo zmení sekciu v hlavnom configuration.yaml."""
        config_path = os.path.join(self.config_dir, "configuration.yaml")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = self.yaml.load(f) or {}

            # Aktualizácia dát pod konkrétnou doménou (napr. input_boolean:)
            config_data[domain_key] = new_data

            with open(config_path, "w", encoding="utf-8") as f:
                self.yaml.dump(config_data, f)

            _LOGGER.info(f"Sekcia {domain_key} úspešne upravená v configuration.yaml")
            return True
        except Exception as e:
            _LOGGER.error(f"Chyba pri zápise do configuration.yaml: {e}")
            return False

    def save_blueprint(self, blueprint_name: str, yaml_content: str):
        """Vytvorí alebo prepíše šablónu (Blueprint) v príslušnom priečinku."""
        # Nastavenie cesty do blueprints/automation/
        blueprint_dir = os.path.join(self.config_dir, "blueprints", "automation")
        os.makedirs(blueprint_dir, exist_ok=True)

        # Očistenie názvu súboru od nebezpečných znakov
        safe_name = "".join([c if c.isalnum() else "_" for c in blueprint_name]).strip("_")
        file_path = os.path.join(blueprint_dir, f"{safe_name}.yaml")

        try:
            # Gemini vráti čistý reťazec YAML kódu, ktorý zapíšeme
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            _LOGGER.info(f"Blueprint {blueprint_name} bol úspešne uložený do {file_path}")
            return True
        except Exception as e:
            _LOGGER.error(f"Nepodarilo sa uložiť Blueprint: {e}")
            return False

async def async_setup_services(hass: HomeAssistant):
    """Zaregistruje akcie (Services), ktoré môže spúšťať systém alebo automatizácia."""
    modifier = GeminiFileModifier(hass)

    async def handle_save_blueprint(call: ServiceCall):
        name = call.data.get("name")
        code = call.data.get("yaml_code")
        # Keďže I/O operácie sú synchrónne, spustíme ich v executore
        await hass.async_add_executor_job(modifier.save_blueprint, name, code)
        # Po zápise povieme Home Assistantu, nech znova načíta šablóny
        await hass.services.async_call("blueprint", "reload")

    hass.services.async_register(DOMAIN, "save_blueprint", handle_save_blueprint)
