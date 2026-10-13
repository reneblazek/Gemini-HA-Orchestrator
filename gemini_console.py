#!/usr/bin/env python3
"""
Gemini HA Orchestrator - Interactive CLI Console
------------------------------------------------
Provides an interactive command-line interface to chat with Google Gemini AI
to manage Home Assistant configurations, write blueprints, and edit YAML files
with mandatory human-in-the-loop confirmation before any filesystem modification.
"""

import os
import sys
import json
import difflib
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

# ANSI color escape codes for terminal styling
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLUE = "\033[44m"
    BG_DARK = "\033[48;5;236m"


def style(text: str, *styles: str) -> str:
    """Applies ANSI styles if stdout is a tty."""
    if not sys.stdout.isatty():
        return text
    return f"{''.join(styles)}{text}{Colors.RESET}"


class HAFileManager:
    """Handles safe reading and writing of Home Assistant files."""

    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir).resolve()
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_or_absolute_path: str) -> Path:
        """Resolves path and prevents directory traversal attacks outside config_dir."""
        target = Path(relative_or_absolute_path)
        if not target.is_absolute():
            target = (self.config_dir / target).resolve()
        else:
            target = target.resolve()

        try:
            target.relative_to(self.config_dir)
        except ValueError:
            raise PermissionError(f"Access denied: path '{relative_or_absolute_path}' is outside Home Assistant config directory '{self.config_dir}'.")

        return target

    def read_file(self, file_path: str) -> str:
        """Reads file content from the Home Assistant config directory."""
        target = self._resolve_safe_path(file_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if target.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        return target.read_text(encoding="utf-8")

    def list_files(self, sub_directory: str = "") -> List[str]:
        """Lists files and directories in the Home Assistant config directory."""
        target_dir = self._resolve_safe_path(sub_directory) if sub_directory else self.config_dir
        if not target_dir.exists() or not target_dir.is_dir():
            raise NotADirectoryError(f"Directory not found: {sub_directory}")

        entries = []
        for item in sorted(target_dir.iterdir()):
            rel_path = item.relative_to(self.config_dir)
            if item.name.startswith(".") and item.name not in (".storage",):
                continue
            suffix = "/" if item.is_dir() else ""
            entries.append(f"{rel_path}{suffix}")
        return entries

    def save_blueprint(self, name: str, yaml_content: str) -> Tuple[Path, Optional[str]]:
        """Saves a blueprint YAML under blueprints/automation/<name>.yaml."""
        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in name]).strip("_")
        if not safe_name:
            safe_name = "custom_blueprint"
        if not safe_name.endswith(".yaml"):
            safe_name = f"{safe_name}.yaml"

        blueprint_dir = self.config_dir / "blueprints" / "automation"
        blueprint_dir.mkdir(parents=True, exist_ok=True)
        file_path = blueprint_dir / safe_name

        old_content = file_path.read_text(encoding="utf-8") if file_path.exists() else None
        file_path.write_text(yaml_content, encoding="utf-8")
        return file_path, old_content

    def write_file(self, file_path: str, content: str) -> Tuple[Path, Optional[str]]:
        """Writes or creates any file safely in the config directory."""
        target = self._resolve_safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        old_content = target.read_text(encoding="utf-8") if target.exists() else None
        target.write_text(content, encoding="utf-8")
        return target, old_content

    def modify_yaml_section(self, file_path: str, domain_key: str, yaml_or_data: Any) -> Tuple[Path, Optional[str], str]:
        """Modifies or adds a domain section in a YAML file (e.g. configuration.yaml)."""
        target = self._resolve_safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        old_content = target.read_text(encoding="utf-8") if target.exists() else ""

        # Attempt to use ruamel.yaml if available, else PyYAML or manual append
        new_content = ""
        try:
            from ruamel.yaml import YAML
            yaml_parser = YAML()
            yaml_parser.preserve_quotes = True
            if old_content.strip():
                import io
                data = yaml_parser.load(old_content) or {}
            else:
                data = {}

            if isinstance(yaml_or_data, str):
                import io
                parsed_val = yaml_parser.load(yaml_or_data)
                data[domain_key] = parsed_val
            else:
                data[domain_key] = yaml_or_data

            buf = io.StringIO()
            yaml_parser.dump(data, buf)
            new_content = buf.getvalue()
        except ImportError:
            # Fallback if ruamel.yaml is not installed
            import yaml
            data = yaml.safe_load(old_content) or {} if old_content.strip() else {}
            if isinstance(yaml_or_data, str):
                parsed_val = yaml.safe_load(yaml_or_data)
                data[domain_key] = parsed_val
            else:
                data[domain_key] = yaml_or_data
            new_content = yaml.dump(data, sort_keys=False)

        target.write_text(new_content, encoding="utf-8")
        return target, (old_content if old_content else None), new_content


class GeminiHAConsole:
    """Interactive console communicating with Gemini with user confirmation prompts."""

    SYSTEM_INSTRUCTION = """You are Gemini HA Orchestrator, an expert AI assistant for Home Assistant.
You help users manage Home Assistant configuration files, write blueprints, inspect automations, and troubleshoot setups.

You have access to tools that can read and modify files in the Home Assistant configuration directory.
IMPORTANT RULES:
1. Always explore existing files (using read_file or list_files) before modifying them when appropriate.
2. When creating a blueprint, use save_blueprint with clean, valid Home Assistant YAML.
3. When updating configuration.yaml or other config files, use modify_yaml_section or write_file.
4. Keep YAML syntax valid according to official Home Assistant standards.
5. All file modifications will be prompted to the user for explicit confirmation before being applied. Provide clear explanations of what you are proposing and why.
"""

    def __init__(
        self,
        config_dir: str = ".",
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        confirm_fn: Optional[Callable[[str, str, Optional[str], str], bool]] = None,
    ):
        self.config_dir = config_dir
        self.file_manager = HAFileManager(config_dir)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model
        self.history: List[Dict[str, Any]] = []
        self.confirm_fn = confirm_fn or self.default_confirm_prompt
        self.client = None

    def _init_client(self):
        """Initializes the Google GenAI SDK client."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please provide --api-key or set the GEMINI_API_KEY environment variable.")
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "Google GenAI SDK ('google-genai') is not installed. Install it with: pip install google-genai"
            )

    def default_confirm_prompt(self, action_name: str, target_path: str, old_content: Optional[str], new_content: str) -> bool:
        """Displays diff / proposed change and prompts user for confirmation."""
        print()
        print(style("=" * 70, Colors.BOLD, Colors.YELLOW))
        print(style(f" ⚠️  POTVRDENIE ZMENY / CONFIRMATION REQUIRED: {action_name}", Colors.BOLD, Colors.YELLOW))
        print(style(f" 📁 Cieľový súbor / Target file: {target_path}", Colors.BOLD, Colors.CYAN))
        print(style("=" * 70, Colors.BOLD, Colors.YELLOW))
        print()

        if old_content is not None and old_content.strip():
            print(style("--- Pôvodný obsah / Current ---", Colors.DIM))
            print(style("+++ Nový obsah / Proposed +++", Colors.GREEN))
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{os.path.basename(target_path)}",
                tofile=f"b/{os.path.basename(target_path)}",
                n=3,
            )
            diff_lines = list(diff)
            if diff_lines:
                for line in diff_lines:
                    if line.startswith("+"):
                        print(style(line, Colors.GREEN), end="")
                    elif line.startswith("-"):
                        print(style(line, Colors.RED), end="")
                    elif line.startswith("@"):
                        print(style(line, Colors.CYAN), end="")
                    else:
                        print(line, end="")
                print()
            else:
                print(style("[Žiadna zmena obsahu / No changes detected]", Colors.DIM))
        else:
            print(style("📄 Nový súbor / New file content:", Colors.BOLD, Colors.GREEN))
            print(style("-" * 50, Colors.DIM))
            for line in new_content.splitlines():
                print(style(f"  {line}", Colors.GREEN))
            print(style("-" * 50, Colors.DIM))

        print()
        prompt_text = style("Súhlasíte s vykonaním tejto zmeny? / Do you confirm this action? [y/N]: ", Colors.BOLD, Colors.WHITE)
        try:
            choice = input(prompt_text).strip().lower()
            return choice in ("y", "yes", "ano", "áno", "1")
        except (EOFError, KeyboardInterrupt):
            print()
            return False

    def get_tool_definitions(self) -> List[Any]:
        """Returns tool declarations for Gemini SDK."""
        from google.genai import types

        return [
            types.FunctionDeclaration(
                name="read_file",
                description="Reads the text content of a file in the Home Assistant configuration directory.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(type=types.Type.STRING, description="Relative path to the file (e.g. configuration.yaml, automations.yaml)"),
                    },
                    required=["file_path"],
                ),
            ),
            types.FunctionDeclaration(
                name="list_files",
                description="Lists files and directories inside the Home Assistant configuration directory.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "sub_directory": types.Schema(type=types.Type.STRING, description="Optional subdirectory to list (e.g. blueprints, custom_components)"),
                    },
                ),
            ),
            types.FunctionDeclaration(
                name="save_blueprint",
                description="Creates or updates a Home Assistant blueprint YAML in blueprints/automation/. Always requires user confirmation.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "name": types.Schema(type=types.Type.STRING, description="Blueprint identifier/name (e.g. motion_light_dimmer)"),
                        "yaml_code": types.Schema(type=types.Type.STRING, description="Valid YAML content of the Home Assistant blueprint"),
                    },
                    required=["name", "yaml_code"],
                ),
            ),
            types.FunctionDeclaration(
                name="modify_yaml_section",
                description="Modifies or adds a specific domain section in a YAML configuration file. Always requires user confirmation.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(type=types.Type.STRING, description="File to modify, e.g. configuration.yaml"),
                        "domain_key": types.Schema(type=types.Type.STRING, description="Top-level domain or key, e.g. input_boolean, homeassistant"),
                        "yaml_content": types.Schema(type=types.Type.STRING, description="YAML code for this section"),
                    },
                    required=["file_path", "domain_key", "yaml_content"],
                ),
            ),
            types.FunctionDeclaration(
                name="write_file",
                description="Writes or overwrites a configuration or helper file in the Home Assistant config directory. Always requires user confirmation.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "file_path": types.Schema(type=types.Type.STRING, description="Relative path of file to write (e.g. automations.yaml, scripts.yaml)"),
                        "content": types.Schema(type=types.Type.STRING, description="Full text content of the file"),
                    },
                    required=["file_path", "content"],
                ),
            ),
        ]

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tool with confirmation guards for modifying actions."""
        if name == "read_file":
            path = args.get("file_path", "")
            try:
                content = self.file_manager.read_file(path)
                return {"success": True, "file_path": path, "content": content}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif name == "list_files":
            subdir = args.get("sub_directory", "")
            try:
                entries = self.file_manager.list_files(subdir)
                return {"success": True, "directory": subdir or ".", "entries": entries}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif name == "save_blueprint":
            bp_name = args.get("name", "custom_blueprint")
            yaml_code = args.get("yaml_code", "")
            target_path = str(self.file_manager.config_dir / "blueprints" / "automation" / f"{bp_name}.yaml")
            existing = None
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        existing = f.read()
                except Exception:
                    pass

            confirmed = self.confirm_fn("Save Blueprint", target_path, existing, yaml_code)
            if not confirmed:
                print(style("❌ Akcia zrušená používateľom. / Action cancelled by user.", Colors.BOLD, Colors.RED))
                return {
                    "success": False,
                    "cancelled": True,
                    "message": "User declined to save the blueprint. Do not retry without modifying according to user feedback.",
                }

            try:
                saved_path, _ = self.file_manager.save_blueprint(bp_name, yaml_code)
                print(style(f"✅ Blueprint uložený / Blueprint saved: {saved_path}", Colors.BOLD, Colors.GREEN))
                return {"success": True, "file_path": str(saved_path), "message": "Blueprint saved successfully."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif name == "modify_yaml_section":
            file_path = args.get("file_path", "configuration.yaml")
            domain_key = args.get("domain_key", "")
            yaml_content = args.get("yaml_content", "")
            target_path = str(self.file_manager._resolve_safe_path(file_path))
            
            existing = None
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        existing = f.read()
                except Exception:
                    pass

            # Prepare preview of modified content
            preview_content = f"# Section: {domain_key}\n{yaml_content}"
            confirmed = self.confirm_fn(f"Modify YAML section [{domain_key}]", target_path, existing, preview_content)
            if not confirmed:
                print(style("❌ Akcia zrušená používateľom. / Action cancelled by user.", Colors.BOLD, Colors.RED))
                return {
                    "success": False,
                    "cancelled": True,
                    "message": "User declined the YAML section modification.",
                }

            try:
                saved_path, _, _ = self.file_manager.modify_yaml_section(file_path, domain_key, yaml_content)
                print(style(f"✅ Konfigurácia upravená / Configuration updated: {saved_path}", Colors.BOLD, Colors.GREEN))
                return {"success": True, "file_path": str(saved_path), "message": f"Section {domain_key} updated."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif name == "write_file":
            file_path = args.get("file_path", "")
            content = args.get("content", "")
            target_path = str(self.file_manager._resolve_safe_path(file_path))
            
            existing = None
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        existing = f.read()
                except Exception:
                    pass

            confirmed = self.confirm_fn("Write File", target_path, existing, content)
            if not confirmed:
                print(style("❌ Akcia zrušená používateľom. / Action cancelled by user.", Colors.BOLD, Colors.RED))
                return {
                    "success": False,
                    "cancelled": True,
                    "message": "User declined the file write operation.",
                }

            try:
                saved_path, _ = self.file_manager.write_file(file_path, content)
                print(style(f"✅ Súbor zapísaný / File written: {saved_path}", Colors.BOLD, Colors.GREEN))
                return {"success": True, "file_path": str(saved_path), "message": "File written successfully."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": f"Unknown tool: {name}"}

    def process_prompt(self, user_prompt: str) -> str:
        """Sends user prompt to Gemini, handles tool calling loop with confirmations."""
        from google.genai import types

        if not self.client:
            self._init_client()

        # Append user turn to history
        self.history.append({"role": "user", "parts": [user_prompt]})

        # Build contents from history
        contents = []
        for msg in self.history:
            role = msg["role"]
            parts = []
            for p in msg["parts"]:
                if isinstance(p, str):
                    parts.append(types.Part.from_text(text=p))
                elif isinstance(p, types.Part):
                    parts.append(p)
                elif isinstance(p, dict) and "function_response" in p:
                    parts.append(types.Part.from_function_response(
                        name=p["function_response"]["name"],
                        response=p["function_response"]["response"]
                    ))
            contents.append(types.Content(role=role, parts=parts))

        tool_declarations = self.get_tool_definitions()
        tools = [types.Tool(function_declarations=tool_declarations)]

        config = types.GenerateContentConfig(
            system_instruction=self.SYSTEM_INSTRUCTION,
            tools=tools,
            temperature=0.2,
        )

        max_turns = 8
        turn = 0
        final_text = ""

        while turn < max_turns:
            turn += 1
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config,
            )

            # Check if model produced tool calls
            function_calls = []
            if response.function_calls:
                function_calls = response.function_calls
            elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)

            if response.text:
                final_text = response.text

            if not function_calls:
                # No more tools to call, record assistant message
                self.history.append({"role": "model", "parts": [final_text]})
                return final_text

            # Execute tool calls
            # First append model's turn with function calls to contents
            model_parts = []
            for fc in function_calls:
                model_parts.append(types.Part.from_function_call(name=fc.name, args=fc.args))
            contents.append(types.Content(role="model", parts=model_parts))

            # Execute each function call and gather responses
            response_parts = []
            for fc in function_calls:
                call_name = fc.name
                call_args = dict(fc.args) if fc.args else {}
                print(style(f"\n⚙️  Gemini volá nástroj / Calling tool: {call_name}...", Colors.DIM, Colors.CYAN))
                tool_result = self.execute_tool(call_name, call_args)
                response_parts.append(types.Part.from_function_response(
                    name=call_name,
                    response={"result": tool_result}
                ))

            # Append user response parts
            contents.append(types.Content(role="user", parts=response_parts))

        return final_text

    def start_repl(self):
        """Starts interactive Read-Eval-Print Loop."""
        print(style("=" * 70, Colors.BOLD, Colors.CYAN))
        print(style("  🤖 GEMINI HA ORCHESTRATOR - INTERAKTÍVNA KONZOLA / CONSOLE", Colors.BOLD, Colors.CYAN))
        print(style("=" * 70, Colors.BOLD, Colors.CYAN))
        print(style(f"  • Konfiguračný priečinok / HA Config: {self.config_dir}", Colors.WHITE))
        print(style(f"  • Model: {self.model_name}", Colors.WHITE))
        print(style("  • Bezpečnostná kontrola: Potvrdenie pred každou zmenou súborov je AKTÍVNE [ON]", Colors.GREEN))
        print(style("  • Príkazy / Commands: /help, /config, /clear, /model <name>, /exit", Colors.DIM))
        print(style("=" * 70, Colors.BOLD, Colors.CYAN))
        print()

        try:
            self._init_client()
        except Exception as e:
            print(style(f"⚠️  Chyba inicializácie klienta / Client initialization error: {e}", Colors.BOLD, Colors.RED))
            print(style("Nastavte premennú GEMINI_API_KEY alebo použite parameter --api-key.", Colors.YELLOW))
            print()

        while True:
            try:
                prompt_line = style("Gemini HA > ", Colors.BOLD, Colors.GREEN)
                user_input = input(prompt_line).strip()
            except (KeyboardInterrupt, EOFError):
                print("\n" + style("Ukončujem konzolu... Dovidenia! / Exiting console. Goodbye!", Colors.CYAN))
                break

            if not user_input:
                continue

            # Command handling
            if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                print(style("Ukončujem konzolu... / Exiting console.", Colors.CYAN))
                break
            elif user_input.lower() == "/help":
                print(style("\n--- Dostupné príkazy / Available commands ---", Colors.BOLD, Colors.WHITE))
                print("  /help           - Zobrazí túto nápovedu / Show this help")
                print("  /config         - Zobrazí aktuálne nastavenia / Show current configuration")
                print("  /clear          - Vymaže históriu konverzácie / Clear chat history")
                print("  /model <name>   - Zmení Gemini model (napr. gemini-2.5-flash, gemini-1.5-pro)")
                print("  /exit, quit     - Ukončí konzolu / Exit console\n")
                continue
            elif user_input.lower() == "/config":
                print(style(f"\nKonfigurácia / Config:", Colors.BOLD, Colors.WHITE))
                print(f"  HA Config Directory : {self.config_dir}")
                print(f"  Model               : {self.model_name}")
                print(f"  API Key nastavený   : {'Áno / Yes' if self.api_key else 'Nie / No'}\n")
                continue
            elif user_input.lower() == "/clear":
                self.history.clear()
                print(style("História konverzácie vymazaná. / Chat history cleared.\n", Colors.YELLOW))
                continue
            elif user_input.startswith("/model "):
                new_model = user_input.split(maxsplit=1)[1].strip()
                if new_model:
                    self.model_name = new_model
                    print(style(f"Model zmenený na: {self.model_name}\n", Colors.GREEN))
                continue

            try:
                print(style("\nGemini premýšľa / Gemini is thinking...", Colors.DIM))
                response_text = self.process_prompt(user_input)
                print()
                print(style("🤖 Gemini:", Colors.BOLD, Colors.BLUE))
                print(response_text)
                print()
            except Exception as e:
                print()
                print(style(f"❌ Chyba / Error: {e}", Colors.BOLD, Colors.RED))
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Gemini HA Orchestrator - Interactive CLI console with user confirmation for Home Assistant"
    )
    parser.add_argument(
        "--config-dir",
        "-c",
        default=os.getenv("HA_CONFIG_DIR", "."),
        help="Path to Home Assistant configuration directory (default: current directory or $HA_CONFIG_DIR)",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        default=os.getenv("GEMINI_API_KEY", ""),
        help="Google Gemini API key (default: $GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gemini-2.5-flash",
        help="Gemini model name (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--prompt",
        "-p",
        help="Single prompt to execute in non-interactive batch mode",
    )

    args = parser.parse_args()

    console = GeminiHAConsole(
        config_dir=args.config_dir,
        api_key=args.api_key,
        model=args.model,
    )

    if args.prompt:
        # Non-interactive single command mode
        try:
            resp = console.process_prompt(args.prompt)
            print(resp)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Interactive REPL mode
        console.start_repl()


if __name__ == "__main__":
    main()
