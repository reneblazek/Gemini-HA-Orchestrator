# Developer & Agent Guidelines for Gemini HA Orchestrator

This document provides technical instructions, architecture guidelines, and operational procedures for developing, testing, and debugging the Gemini HA Orchestrator project.

---

## 1. Project Overview & Architecture

Gemini HA Orchestrator consists of two primary components:
1. **Home Assistant Custom Component** (`custom_components/gemini_ha_orchestrator/`):
   - A Home Assistant integration enabling Google Gemini models to generate and manage automation blueprints and modify YAML configurations.
   - Provides a UI config flow, an embedded web console sidebar panel, REST API views, and service handlers (`gemini_ha_orchestrator.save_blueprint`).
2. **Interactive CLI Console** (`gemini_console.py`):
   - A standalone CLI tool for chatting with Gemini models, previewing unified diffs, and applying file/blueprint changes with mandatory human-in-the-loop confirmation.

### Key Files & Modules
- `custom_components/gemini_ha_orchestrator/__init__.py`: Component lifecycle (`async_setup`, `async_setup_entry`, `async_unload_entry`, `async_reload_entry`), view/sidebar registration, and Gemini tool schemas.
- `custom_components/gemini_ha_orchestrator/config_flow.py`: UI setup flow (`GeminiHAConfigFlow`) and options flow (`GeminiHAOptionsFlow`).
- `custom_components/gemini_ha_orchestrator/const.py`: Domain, configuration keys (`api_key`, `model`, `sidebar_panel`), default values, and available Gemini models (`gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-1.5-flash`, `gemini-1.5-pro`).
- `custom_components/gemini_ha_orchestrator/services.py`: `GeminiFileModifier` handling YAML manipulation via `ruamel.yaml` and saving blueprints under `blueprints/automation/`.
- `custom_components/gemini_ha_orchestrator/views.py`: `GeminiConsoleView` (HTML UI), `GeminiChatApiView` (REST API proxying Gemini requests), and `GeminiConfirmApiView` (two-phase user confirmation queue).
- `custom_components/gemini_ha_orchestrator/manifest.json`: Home Assistant integration metadata and runtime dependencies.
- `gemini_console.py`: Standalone CLI assistant with `HAFileManager`, ANSI terminal styling, diff previews, and tool handlers.

---

## 2. Build & Configuration Instructions

### Prerequisites
- Python 3.12+ (matching Home Assistant runtime requirements; test runner works with Python 3.12/3.13 standard library).
- Google Gemini API Key.

### Dependencies
Runtime dependencies specified in `manifest.json`:
- `google-genai >= 0.1.1`
- `ruamel.yaml >= 0.18.6`

### Environment Setup
To set up a local development environment for running the CLI tool or installing optional packages:

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install runtime dependencies
pip install "google-genai>=0.1.1" "ruamel.yaml>=0.18.6"
```

### Running the CLI Console
Set the Gemini API key in the environment and run:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
python3 gemini_console.py --config-dir /path/to/homeassistant/config --model gemini-2.5-flash
```

---

## 3. Testing Information

The project uses Python's standard `unittest` framework. Tests do not require a live Home Assistant instance or external test dependencies.

### Running Tests
Execute the entire test suite using `unittest` discovery:

```bash
python3 -m unittest discover -s tests -v
```

Run a specific test module:

```bash
# Config flow and integration lifecycle tests
python3 -m unittest tests/test_config_flow.py -v

# Standalone CLI and file manager tests
python3 -m unittest tests/test_console.py -v
```

Run a specific test case or class:

```bash
python3 -m unittest tests.test_console.TestHAFileManager.test_save_blueprint -v
```

### Test Strategy & Mocking Conventions
- **Home Assistant Mocking**: When testing HA components without HA installed, mock required modules (`homeassistant`, `voluptuous`, `aiohttp`) in `sys.modules` before importing component modules (refer to `_setup_mocks()` in `tests/test_config_flow.py`).
- **Filesystem Isolation**: File operations must always operate within isolated temporary directories created with `tempfile.mkdtemp()` in `setUp()` and cleaned up with `shutil.rmtree(..., ignore_errors=True)` in `tearDown()`.
- **User Confirmation Mocking**: `GeminiHAConsole` supports a custom `confirm_fn` callable (`confirm_fn=lambda action, target, old, new: True/False`). Use this parameter in tests to bypass interactive terminal prompts and verify both approval and rejection branches.

### Example: Adding a New Unit Test
When adding a new test for file or service management:

```python
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
from custom_components.gemini_ha_orchestrator.services import GeminiFileModifier


class TestGeminiFileModifier(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.hass = MagicMock()
        self.hass.config.config_dir = self.test_dir
        self.modifier = GeminiFileModifier(self.hass)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_blueprint(self):
        bp_name = "motion_lights"
        bp_yaml = "blueprint:\n  name: Motion Lights\n  domain: automation\n"
        success = self.modifier.save_blueprint(bp_name, bp_yaml)
        self.assertTrue(success)
        saved_file = self.modifier.config_dir + "/blueprints/automation/motion_lights.yaml"
        with open(saved_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), bp_yaml)


if __name__ == "__main__":
    unittest.main()
```

---

## 4. Code Style & Development Guidelines

- **Style & Formatting**: Follow PEP 8 standards with 4-space indentation.
- **Type Hints**: Use type annotations (`from __future__ import annotations`, `typing.Optional`, `typing.Dict`, `typing.List`, `typing.Any`).
- **YAML Handling**: Always use `ruamel.yaml` with `preserve_quotes = True` when editing configuration YAML files to avoid stripping comments or altering existing formatting. Fall back gracefully to `yaml` (PyYAML) if `ruamel.yaml` is unavailable.
- **Security & Safety Guardrails**:
  - **Directory Traversal Protection**: All file paths accessed or written must be validated using `Path.resolve()` and checked with `target.relative_to(config_dir)` to prevent traversal outside the Home Assistant configuration directory.
  - **Filename Sanitization**: Blueprint names must be sanitized (`safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in name]).strip("_")`).
  - **Human-in-the-Loop**: File modifications must never occur automatically without explicit user confirmation (via CLI prompt or Web Console confirm view).
- **Internationalization (i18n)**:
  - Translations for config flows are maintained in `custom_components/gemini_ha_orchestrator/translations/` (`en.json`, `sk.json`) and `strings.json`.
  - When adding new configuration options or error codes, update `strings.json` and all translation files accordingly.
