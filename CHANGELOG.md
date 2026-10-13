# Changelog

All notable changes to the **Gemini HA Orchestrator** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.3] - 2026-10-13

### Fixed
- **Resolved Blocking Calls in Event Loop**:
  - Lazily initialized `ruamel.yaml` on first file access inside executor jobs instead of during component initialization on the main event loop, eliminating blocking `glob`, `iglob`, and `scandir` warnings.
- **Sidebar Panel Registration**:
  - Corrected parameter name from `url_path` to `frontend_url_path="gemini_console"` in `frontend.async_register_built_in_panel()`.
- **Service Metadata Schema (`services.yaml`)**:
  - Added missing `services.yaml` defining schema and UI selectors for the `gemini_ha_orchestrator.save_blueprint` service (`name` and `yaml_code` fields).
- **Test Coverage**:
  - Added unit test verifying existence and structure of `services.yaml`.
  - Added unit test verifying lazy initialization behavior for `GeminiFileModifier.yaml`.

---

## [1.1.1] - 2026-10-13

### Fixed
- **Config Flow 500 Internal Server Error**:
  - Resolved `500 Internal Server Error` preventing the config flow from loading during integration setup in Home Assistant.
  - Removed internal core integration names (`frontend`, `http`) from `manifest.json` `dependencies`.
  - Loosened package requirement pins (`google-genai>=0.1.1`, `ruamel.yaml>=0.18.6`) to prevent pip resolution conflicts during installation.
  - Added `"single_config_entry": true` to `manifest.json` ensuring single-instance integration management.
  - Fixed `GeminiHAOptionsFlow` to avoid setting the read-only `config_entry` property directly in modern Home Assistant (2024.4+).
  - Hardened optional library import exception handling in `__init__.py` and `services.py` to prevent uncaught runtime exceptions during startup.
- **Test Coverage**:
  - Added unit tests for `GeminiHAOptionsFlow` instantiation variants and the options flow factory callback.

---

## [1.1.0] - 2026-10-13

### Added
- **UI Configuration Flow (`config_flow.py`)**:
  - Full support for Home Assistant UI setup (**Settings** > **Devices & Services** > **Add Integration**).
  - Eliminates the need for manual configuration in `configuration.yaml`.
  - Configurable options flow for updating API keys, active model, and sidebar settings.
- **Home Assistant Sidebar Menu Console**:
  - Embedded web-based Gemini AI console accessible directly from Home Assistant's left sidebar panel.
  - Interactive chat interface with real-time markdown formatting and suggestion pills.
  - In-browser Human-in-the-Loop Diff review cards with `[✅ Schváliť / Approve]` and `[❌ Odmietnuť / Reject]` action buttons.
  - Automatic blueprint saving to `blueprints/automation/` and Home Assistant blueprint reload upon approval.
- **Backend HTTP Views & API Endpoints (`views.py`)**:
  - `GET /api/gemini_ha_orchestrator/console` (Web Console frontend interface).
  - `POST /api/gemini_ha_orchestrator/chat` (Gemini model communication and tool dispatch).
  - `POST /api/gemini_ha_orchestrator/confirm` (Approval/rejection execution handler).
- **Localization Files**:
  - Added `strings.json` and language translations in `translations/en.json` and `translations/sk.json`.
- **Integration Constants (`const.py`)**:
  - Domain constants, configuration keys, default models, and available Gemini models.
- **Component Lifecycle (`__init__.py`)**:
  - Implemented `async_setup`, `async_setup_entry`, `async_unload_entry`, and options reload listeners.
- **Config Flow & Lifecycle Test Suite (`tests/test_config_flow.py`)**:
  - Unit tests covering user step, empty API key validation, options flow, entry loading/unloading, panel registration, and confirmation view handling.

### Changed
- Bumped integration version to `1.1.0` and enabled `"config_flow": true` with `frontend` and `http` dependencies in `manifest.json`.
- Updated `README.md` with complete UI installation instructions, sidebar console usage, and project structure.

---

## [1.0.2] - 2026-10-13

### Added
- **Interactive CLI Console (`gemini_console.py`)**:
  - Direct conversational interface to Google Gemini models (`gemini-2.5-flash` by default).
  - Built-in tool calling support: `read_file`, `list_files`, `save_blueprint`, `modify_yaml_section`, and `write_file`.
  - In-console control commands: `/help`, `/config`, `/model <name>`, `/clear`, `/exit`.
  - Batch execution support via `-p` / `--prompt` argument.
- **Human-in-the-Loop Safety Confirmation**:
  - Interactive unified diff and file content preview prior to any filesystem modification.
  - Mandatory confirmation prompt (`[y/N]`) ensuring full user control over configuration changes.
- **Directory Traversal Protection**:
  - Strict path sanitization in `HAFileManager` to prevent operations outside the Home Assistant configuration directory.
- **Automated Test Suite (`tests/test_console.py`)**:
  - Unit tests for file operations, safety confirmation acceptance/rejection, and path isolation.

---

## [1.0.1] - 2026-10-13

### Added
- **Branding & Visual Identity** (Commit: `2a6a0c1`):
  - Added modern vector (`icon.svg`, `logo.svg`) and raster (`icon.png`, `logo.png`) assets blending Home Assistant smart home motif with Google Gemini 4-pointed AI star.
  - Assets added to root, `images/`, and `custom_components/gemini_ha_orchestrator/brand/` for HACS and Home Assistant UI compatibility.
  - Added `.gitignore` to prevent committing build/system artifacts.
- **Comprehensive Documentation** (Commit: `fc4d108`):
  - Added detailed `README.md` covering overview, tech stack, requirements, installation (manual & HACS), YAML examples, and roadmap.

### Changed
- **English Localization & Standardization** (Commit: `3a3095b`):
  - Standardized all docstrings, tool descriptions, and log messages across `__init__.py` and `services.py` into English.
- **Service Name Correction**:
  - Fixed domain prefix in service calls from `gemini_ha.save_blueprint` to `gemini_ha_orchestrator.save_blueprint`.

---

## [1.0.0] - 2026-10-13

### Added
- **Initial Implementation** (Commit: `360e223`):
  - Custom component structure under `custom_components/gemini_ha_orchestrator/`.
  - Gemini function-calling tool schema definition (`save_blueprint_tool`) in `__init__.py`.
  - `GeminiFileModifier` and service handler `gemini_ha_orchestrator.save_blueprint` in `services.py`.
  - `manifest.json` with dependencies (`google-genai==0.1.1`, `ruamel.yaml==0.18.6`).
  - HACS configuration metadata in `hacs.json`.
  - Scaffold files `config_flow.py` and `const.py`.
- **Repository Initialization** (Commit: `d29180e`):
  - Project repository created with GNU General Public License v3.0 (`LICENSE`).

---

## Commit History Reference

| Commit | Date | Message / Description |
|---|---|---|
| `d29180e` | 2026-10-13 | `Initial commit` (GPL-3.0 License) |
| `360e223` | 2026-10-13 | `Initial commit of Gemini HA Orchestrator` (Core custom component, tool definition & service handler) |
| `fc4d108` | 2026-10-13 | `Add comprehensive README for Gemini HA Orchestrator` (Documentation, guides & examples) |
| `3a3095b` | 2026-10-13 | `Update comments and strings in Gemini HA Orchestrator to English` (Localization standardization) |
| `2a6a0c1` | 2026-10-13 | `Add SVG and PNG assets for Gemini HA Orchestrator branding` (Vector & raster brand icons/logos) |
| *Working Tree* | 2026-10-13 | `Interactive CLI Console with Human-in-the-Loop safety guard` (`gemini_console.py`, tests, docs, v1.0.2) |
| *Working Tree* | 2026-10-13 | `UI Config Flow & Home Assistant Sidebar Menu Console` (`config_flow.py`, `views.py`, v1.1.0) |
