<p align="center">
  <img src="icon.svg" alt="Gemini HA Orchestrator Icon" width="140" height="140">
</p>

# Gemini HA Orchestrator

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

**Gemini HA Orchestrator** is a custom Home Assistant (HA) integration designed to bridge Google Gemini generative AI capabilities with Home Assistant automation orchestration. It provides Gemini function-calling tool definitions and integration services allowing AI models to safely write, modify, and reload Home Assistant blueprints and YAML configurations.

---

## Overview

Gemini HA Orchestrator enables conversational and autonomous AI agents powered by the Google GenAI SDK to directly create and manage Home Assistant blueprints and configuration entries:

- **AI Function Calling Definition**: Defines a structured Google Gemini tool schema (`save_blueprint_tool`) that instructs Gemini how to generate and submit valid Home Assistant blueprint code.
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
- Google Gemini API Key (see [Environment Variables & Configuration](#environment-variables--configuration))

---

## Project Structure

```text
Gemini-HA-Orchestrator/
├── custom_components/
│   └── gemini_ha_orchestrator/
│       ├── __init__.py         # Component init & Gemini Tool definition (`save_blueprint_tool`)
│       ├── config_flow.py      # UI configuration flow (TODO: implementation in progress)
│       ├── const.py            # Integration constants and domain definitions (TODO)
│       ├── manifest.json       # Home Assistant integration metadata & dependencies
│       └── services.py         # GeminiFileModifier class & service registration (`gemini_ha_orchestrator.save_blueprint`)
├── hacs.json                   # HACS repository configuration
├── LICENSE                     # GNU General Public License v3.0 (GPL-3.0)
└── README.md                   # Project documentation
```

---

## Installation & Setup

### Option 1: Manual Installation

1. Copy the `custom_components/gemini_ha_orchestrator` folder into your Home Assistant `<config>/custom_components/` directory:
   ```bash
   cp -r custom_components/gemini_ha_orchestrator /path/to/homeassistant/config/custom_components/
   ```
2. Restart Home Assistant.
3. Home Assistant will automatically install the requirements listed in `manifest.json` (`google-genai==0.1.1` and `ruamel.yaml==0.18.6`).

### Option 2: HACS (Custom Repository)

1. Open **HACS** in your Home Assistant instance.
2. Go to **Integrations** > Three dots menu (top right) > **Custom repositories**.
3. Add this repository URL, select category **Integration**, and click **Add**.
4. Download the integration and restart Home Assistant.

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

- **`GEMINI_API_KEY`**: Set in your environment or secrets for authenticating with Google Gemini models when orchestrating with the `google-genai` library.
- **Home Assistant Configuration**:
  - *TODO*: UI configuration flow (`config_flow.py`) and options flow are currently in development.
  - *TODO*: Integration setup hooks (`async_setup` / `async_setup_entry`) in `__init__.py` to automatically register services upon integration load.

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
   pip install google-genai==0.1.1 ruamel.yaml==0.18.6 homeassistant
   ```

### Tests

- *TODO*: Automated test suite (e.g., using `pytest` and `pytest-homeassistant-custom-component`) is not yet implemented.
- Recommended test run once configured:
  ```bash
  pytest tests/
  ```

---

## Roadmap & TODOs

- [ ] Complete `custom_components/gemini_ha_orchestrator/const.py` with domain constants and configuration keys.
- [ ] Implement `custom_components/gemini_ha_orchestrator/config_flow.py` for UI setup in Home Assistant.
- [ ] Connect `async_setup_services` to `async_setup` / `async_setup_entry` in `__init__.py`.
- [ ] Add translation files (`translations/en.json`, `strings.json`) for user-facing strings.
- [ ] Add automated unit and integration tests using `pytest-homeassistant-custom-component`.
- [ ] Add additional Gemini orchestration tools (e.g., automation verification, entity inspection).

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See the [LICENSE](LICENSE) file for details.
