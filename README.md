<p align="center">
  <img src="icon.svg" alt="Gemini HA Orchestrator Icon" width="140" height="140">
</p>

# Gemini HA Orchestrator

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-reneblazek__apps-yellow.svg)](https://www.buymeacoffee.com/reneblazek_apps)

**Gemini HA Orchestrator** is a custom Home Assistant (HA) integration designed to bridge Google Gemini generative AI capabilities with Home Assistant automation orchestration. It provides Gemini function-calling tool definitions and integration services allowing AI models to safely write, modify, and reload Home Assistant blueprints and YAML configurations.

---

## Overview

Gemini HA Orchestrator enables conversational and autonomous AI agents powered by the Google GenAI SDK to directly create and manage Home Assistant blueprints and configuration entries:

- **UI Installation & Setup (Config Flow)**: Seamlessly set up and configure your Google Gemini API key, model selection, and preferences directly via Home Assistant UI (**Settings** > **Devices & Services** > **Add Integration**). No manual YAML configuration required.
- **Home Assistant Sidebar Web Console**: An interactive Gemini AI console directly embedded into the Home Assistant left sidebar menu. Chat with Gemini, inspect files, and approve/reject changes with visual diff cards right inside your browser.
- **AI Function Calling Definition**: Defines a structured Google Gemini tool schema (`save_blueprint_tool`) that instructs Gemini how to generate and submit valid Home Assistant blueprint code.
- **Interactive CLI Console**: A standalone CLI assistant (`gemini_console.py`) allowing terminal-based chat with Google Gemini models with **mandatory human-in-the-loop confirmation (diff preview + prompt)** before applying any filesystem change.
- **Blueprint Management**: Safely sanitizes blueprint names, saves generated YAML code into Home Assistant's `blueprints/automation/` directory, and automatically triggers `blueprint.reload`.
- **Safe Configuration Modification**: Uses `ruamel.yaml` to preserve comments and quote formatting when reading and writing configuration files.
- **Home Assistant Service Handler**: Exposes the `gemini_ha_orchestrator.save_blueprint` service for execution within automations, scripts, or LLM agents.

---

## Tech Stack

- **Language**: Python 3.12+
- **Platform / Framework**: [Home Assistant](https://www.home-assistant.io/) Custom Component / [HACS](https://hacs.xyz/)
- **Core Dependencies**:
  - `google-genai` (`== 0.1.1`) - Google GenAI SDK for Gemini tool schemas and models
  - `ruamel.yaml` (`== 0.18.6`) - YAML parser preserving comments, indentation, and quotes
  - `homeassistant` - Core Home Assistant runtime and service registries
- **Package Manager**: `pip` (Python package manager) / Home Assistant manifest dependency resolver

---

## Requirements

- Home Assistant Core 2024.x or newer
- Python 3.12+ (matching your Home Assistant runtime)
- Google Gemini API Key

---

## Project Structure

```text
Gemini-HA-Orchestrator/
├── custom_components/
│   └── gemini_ha_orchestrator/
│       ├── __init__.py         # Component init, lifecycle & sidebar panel registration
│       ├── config_flow.py      # UI configuration flow & options flow
│       ├── const.py            # Integration constants and model definitions
│       ├── manifest.json       # Home Assistant integration metadata & dependencies
│       ├── services.py         # GeminiFileModifier class & service registration
│       ├── views.py            # Web Console frontend & REST API endpoints
│       ├── strings.json        # Base translation keys for config flow
│       └── translations/       # UI translations (en.json, sk.json)
├── gemini_console.py           # Interactive CLI console with human-in-the-loop confirmation
├── tests/                      # Automated unit tests (console, config flow, lifecycle)
├── hacs.json                   # HACS repository configuration
├── LICENSE                     # GNU General Public License v3.0 (GPL-3.0)
└── README.md                   # Project documentation
```

---

## Installation & Setup

### 1. Install the Integration Files

#### Option A: Via HACS (Custom Repository)
1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** > Three dots menu (top right) > **Custom repositories**.
3. Add this repository URL, select category **Integration**, and click **Add**.
4. Download **Gemini HA Orchestrator** and restart Home Assistant.

#### Option B: Manual Installation
1. Copy the `custom_components/gemini_ha_orchestrator` folder into your Home Assistant `<config>/custom_components/` directory:
   ```bash
   cp -r custom_components/gemini_ha_orchestrator /path/to/homeassistant/config/custom_components/
   ```
2. Restart Home Assistant.

### 2. Add Integration via UI (No `configuration.yaml` editing required!)

1. In Home Assistant, go to **Settings (Nastavenia)** > **Devices & Services (Zariadenia a služby)** > **Add Integration (Pridať integráciu)**.
2. Search for **Gemini HA Orchestrator**.
3. Enter your **Google Gemini API Key** and choose your desired model (e.g., `gemini-2.5-flash`).
4. Keep **Show Console in Sidebar Menu** checked to have the **Gemini AI** console icon added to your left sidebar.
5. Click **Submit**.

---

## 🖥️ Home Assistant Sidebar Console

Once configured, **Gemini HA Orchestrator** adds an interactive **Gemini AI** panel to your Home Assistant sidebar menu:

- **Live Chat**: Chat directly with Google Gemini models inside Home Assistant.
- **Safety Diff Cards**: When Gemini generates a blueprint or suggests modifying a configuration file, it presents a visual diff card with `[✅ Schváliť / Approve]` and `[❌ Odmietnuť / Reject]` buttons.
- **One-Click Blueprint Reload**: Approved blueprints are saved directly to `blueprints/automation/` and Home Assistant automatically reloads them.

---

## Interactive CLI Console (`gemini_console.py`)

Gemini HA Orchestrator includes a standalone interactive command-line console (`gemini_console.py`) designed to converse directly with Google Gemini AI models. Gemini can inspect files, generate blueprints, and propose configuration adjustments, while keeping **you firmly in control**.

### 🛡️ Human-in-the-Loop Safety Guard
Before any file is written, modified, or saved, the console:
1. Displays the target file path and the proposed action.
2. Renders a colored unified diff (for edits) or full preview (for new files).
3. Prompts: `Súhlasíte s vykonaním tejto zmeny? / Do you confirm this action? [y/N]:`
4. If you decline (`n`), the modification is cancelled immediately and Gemini is notified.

### Running the Console

1. Export your Gemini API Key and run:
   ```bash
   export GEMINI_API_KEY="your-google-gemini-api-key"
   python3 gemini_console.py --config-dir /path/to/homeassistant/config
   ```

2. Available CLI Arguments:
   - `--config-dir`, `-c`: Path to Home Assistant configuration directory (default: current directory or `$HA_CONFIG_DIR`).
   - `--api-key`, `-k`: Google Gemini API key (default: `$GEMINI_API_KEY`).
   - `--model`, `-m`: Gemini model (default: `gemini-2.5-flash`).
   - `--prompt`, `-p`: Execute a single prompt directly in batch mode.

3. In-Console Commands:
   - `/help`: Display list of commands.
   - `/config`: Show current configuration directory and model.
   - `/model <name>`: Switch active Gemini model on the fly.
   - `/clear`: Clear conversation history.
   - `/exit` or `quit`: Exit the console.

---

## Services & Usage

### Service: `gemini_ha_orchestrator.save_blueprint`

Saves or overwrites a Home Assistant blueprint file under `blueprints/automation/` and triggers a blueprint reload.

#### Service Data Attributes:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Name / identifier of the blueprint (e.g., `morning_routine`) |
| `yaml_code` | string | Yes | Complete valid YAML blueprint content |

#### Example Call (Developer Tools -> Services):

```yaml
service: gemini_ha_orchestrator.save_blueprint
data:
  name: "morning_routine"
  yaml_code: |
    blueprint:
      name: Morning Routine
      description: Turn on lights gradually in the morning
      domain: automation
      input:
        target_light:
          name: Light
          selector:
            target:
              entity:
                domain: light
    trigger:
      - trigger: time
        at: "07:00:00"
    action:
      - action: light.turn_on
        target: !input target_light
```

---

## Environment Variables & Configuration

- **`GEMINI_API_KEY`**: Set in your environment or entered during the UI setup flow when adding the integration in Home Assistant.
- **Home Assistant Configuration**:
  - UI Config Flow (`config_flow.py`) and Options Flow enabled.
  - Setup hooks (`async_setup` / `async_setup_entry`) automatically initialize services, web views, and sidebar panels.

---

## Development & Testing

### Local Development Setup

To work on this integration locally:

1. Clone the repository:
   ```bash
   git clone https://github.com/vas-github-profil/Gemini-HA-Orchestrator.git
   cd Gemini-HA-Orchestrator
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install google-genai==0.1.1 ruamel.yaml==0.18.6
   ```

### Tests

Run unit tests covering the CLI console, config flow, lifecycle, and views:
```bash
python3 -m unittest discover tests
```

---

## Roadmap & TODOs

- [x] Complete `custom_components/gemini_ha_orchestrator/const.py` with domain constants and configuration keys.
- [x] Implement `custom_components/gemini_ha_orchestrator/config_flow.py` for UI setup in Home Assistant.
- [x] Implement Home Assistant Sidebar panel integration for Web Console.
- [x] Connect `async_setup_services` and Web views in `__init__.py`.
- [x] Add translation files (`translations/en.json`, `translations/sk.json`, `strings.json`).
- [x] Add automated unit test suite (`tests/test_console.py`, `tests/test_config_flow.py`).
- [ ] Add additional Gemini orchestration tools (e.g., automation verification, entity inspection).

---

## Support & Donation

If you find this project helpful and want to support its ongoing development, feel free to buy me a coffee!

<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js" data-name="bmc-button" data-slug="reneblazek_apps" data-color="#FFDD00" data-emoji=""  data-font="Cookie" data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000" data-coffee-color="#ffffff" ></script>

[![Buy Me A Coffee](https://raw.githubusercontent.com/buymeacoffee/Cookie-widget/master/assets/bmc-button.png)](https://www.buymeacoffee.com/reneblazek_apps)

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for details.
