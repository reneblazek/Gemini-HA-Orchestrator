"""HTTP views and Web Console for Gemini HA Orchestrator."""
from __future__ import annotations

import difflib
import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_MODEL, DEFAULT_MODEL, DOMAIN
from .services import GeminiFileModifier

_LOGGER = logging.getLogger(__name__)

# Temporary memory cache for actions awaiting user confirmation
PENDING_ACTIONS: Dict[str, Dict[str, Any]] = {}


class GeminiConsoleView(HomeAssistantView):
    """View serving the Web Console interface inside Home Assistant."""

    url = "/api/gemini_ha_orchestrator/console"
    name = "api:gemini_ha_orchestrator:console"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the console view."""
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Render the Web Console interface."""
        entry_data = {}
        if DOMAIN in getattr(self.hass, "data", {}) and self.hass.data[DOMAIN]:
            for entry_val in self.hass.data[DOMAIN].values():
                if isinstance(entry_val, dict):
                    entry_data = entry_val
                    break

        if not entry_data and hasattr(self.hass, "config_entries") and hasattr(self.hass.config_entries, "async_entries"):
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                entry_data = {**entry.data, **getattr(entry, "options", {})}
                break

        model_name = entry_data.get(CONF_MODEL, DEFAULT_MODEL)
        html_content = """<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gemini HA Orchestrator Console</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-primary: #111827;
      --bg-secondary: #1f2937;
      --bg-tertiary: #374151;
      --text-primary: #f9fafb;
      --text-secondary: #9ca3af;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --gemini-gradient: linear-gradient(135deg, #4285f4, #9b51e0, #ea4335);
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
      --border: #374151;
      --card-bg: #1e293b;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    body {
      background-color: var(--bg-primary);
      color: var(--text-primary);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* Header */
    header {
      background-color: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-logo {
      width: 32px;
      height: 32px;
      background: var(--gemini-gradient);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 18px;
      box-shadow: 0 2px 8px rgba(66, 133, 244, 0.4);
    }

    .brand-title {
      font-size: 1.1rem;
      font-weight: 700;
      background: var(--gemini-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .header-badges {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .badge {
      background-color: var(--bg-tertiary);
      color: var(--text-secondary);
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--border);
    }

    .badge.active {
      color: var(--success);
      border-color: rgba(16, 185, 129, 0.3);
    }

    /* Main Container */
    .main-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      max-width: 1000px;
      width: 100%;
      margin: 0 auto;
      height: calc(100vh - 60px);
      padding: 16px;
      gap: 16px;
    }

    /* Chat Messages */
    #chat-messages {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding-right: 8px;
    }

    #chat-messages::-webkit-scrollbar {
      width: 6px;
    }

    #chat-messages::-webkit-scrollbar-thumb {
      background-color: var(--bg-tertiary);
      border-radius: 4px;
    }

    .message {
      display: flex;
      gap: 12px;
      max-width: 90%;
      animation: fadeIn 0.25s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message.assistant {
      align-self: flex-start;
    }

    .message-avatar {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 14px;
    }

    .message.user .message-avatar {
      background-color: var(--accent);
      color: white;
    }

    .message.assistant .message-avatar {
      background: var(--gemini-gradient);
      color: white;
    }

    .message-content {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border);
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 0.95rem;
      line-height: 1.5;
      color: var(--text-primary);
      overflow-x: auto;
    }

    .message.user .message-content {
      background-color: #1e3a8a;
      border-color: #2563eb;
      border-bottom-right-radius: 4px;
    }

    .message.assistant .message-content {
      border-bottom-left-radius: 4px;
    }

    pre {
      background-color: #0f172a;
      border: 1px solid #1e293b;
      padding: 12px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 10px 0;
      font-family: monospace;
      font-size: 0.88rem;
    }

    code {
      font-family: monospace;
      color: #38bdf8;
    }

    /* Confirmation Card */
    .confirm-card {
      background-color: #1e1b4b;
      border: 1px solid #6366f1;
      border-radius: 10px;
      padding: 16px;
      margin: 12px 0;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    .confirm-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      font-weight: 600;
      color: #a5b4fc;
    }

    .diff-box {
      background-color: #0b0f19;
      border: 1px solid #312e81;
      border-radius: 6px;
      padding: 10px;
      max-height: 250px;
      overflow-y: auto;
      font-family: monospace;
      font-size: 0.82rem;
      white-space: pre-wrap;
      margin: 10px 0;
    }

    .diff-add { color: #4ade80; }
    .diff-del { color: #f87171; }
    .diff-info { color: #60a5fa; }

    .confirm-actions {
      display: flex;
      gap: 10px;
      margin-top: 12px;
    }

    .btn-approve {
      background-color: var(--success);
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s;
    }

    .btn-approve:hover { background-color: #059669; }

    .btn-reject {
      background-color: var(--danger);
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s;
    }

    .btn-reject:hover { background-color: #dc2626; }

    /* Suggestions */
    .suggestions {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 4px;
      flex-shrink: 0;
    }

    .suggestion-chip {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border);
      color: var(--text-secondary);
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 0.8rem;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.2s;
    }

    .suggestion-chip:hover {
      background-color: var(--bg-tertiary);
      color: var(--text-primary);
      border-color: var(--accent);
    }

    /* Input area */
    .input-container {
      background-color: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      align-items: flex-end;
      gap: 10px;
      flex-shrink: 0;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .input-container:focus-within {
      border-color: var(--accent);
    }

    textarea {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      color: var(--text-primary);
      font-size: 0.95rem;
      resize: none;
      max-height: 120px;
      min-height: 24px;
      line-height: 1.4;
      padding: 4px 0;
    }

    .send-btn {
      background: var(--gemini-gradient);
      color: white;
      border: none;
      width: 36px;
      height: 36px;
      border-radius: 8px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      transition: transform 0.1s, opacity 0.2s;
    }

    .send-btn:hover {
      opacity: 0.9;
    }

    .send-btn:active {
      transform: scale(0.95);
    }

    .send-btn:disabled {
      background: var(--bg-tertiary);
      color: var(--text-secondary);
      cursor: not-allowed;
    }

    /* Loading Spinner */
    .typing-indicator {
      display: inline-flex;
      gap: 4px;
      align-items: center;
      padding: 4px 0;
    }

    .dot {
      width: 6px;
      height: 6px;
      background-color: var(--text-secondary);
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out both;
    }

    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }

    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-logo"><i class="fa-solid fa-sparkles"></i></div>
      <div>
        <div class="brand-title">Gemini HA Orchestrator</div>
      </div>
    </div>
    <div class="header-badges">
      <div class="badge active" id="status-badge"><i class="fa-solid fa-circle"></i> Pripravený</div>
      <div class="badge" id="model-badge"><i class="fa-solid fa-microchip"></i> __MODEL_NAME__</div>
    </div>
  </header>

  <div class="main-container">
    <div id="chat-messages">
      <div class="message assistant">
        <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="message-content">
          <strong>Ahoj! Som tvoj Gemini asistent pre Home Assistant.</strong><br>
          Môžem ti pomôcť vytvárať blueprinty, upravovať <code>configuration.yaml</code> a kontrolovať automatizácie. Pred každým zápisom alebo úpravou súboru ťa vždy najprv požiadam o potvrdenie s náhľadom diffu.
        </div>
      </div>
    </div>

    <div class="suggestions">
      <div class="suggestion-chip" onclick="sendSuggestion('Vytvor blueprint na postupné rozsvecovanie svetiel pri rannom budíku')">💡 Blueprint: Ranné budenie svetlom</div>
      <div class="suggestion-chip" onclick="sendSuggestion('Aké súbory sa nachádzajú v konfiguračnom adresári Home Assistanta?')">📁 Zoznam konfiguračných súborov</div>
      <div class="suggestion-chip" onclick="sendSuggestion('Vytvor automatizáciu pre notifikáciu pri otvorení dverí')">🔔 Notifikácia otvorených dverí</div>
      <div class="suggestion-chip" onclick="sendSuggestion('Ako môžem optimalizovať svoje automatizácie v Home Assistant?')">⚡ Tipy na optimalizáciu</div>
    </div>

    <div class="input-container">
      <textarea id="user-input" placeholder="Napíš správu pre Gemini AI..." rows="1"></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()"><i class="fa-solid fa-paper-plane"></i></button>
    </div>
  </div>

  <script>
    const messagesContainer = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    let conversationHistory = [];

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = (this.scrollHeight) + 'px';
    });

    userInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    function sendSuggestion(text) {
      userInput.value = text;
      sendMessage();
    }

    function appendMessage(role, text) {
      const msgDiv = document.createElement('div');
      msgDiv.className = `message ${role}`;

      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      avatar.innerHTML = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

      const content = document.createElement('div');
      content.className = 'message-content';
      
      // Basic markdown formatting
      let formatted = text
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\\*\\*([^\\*]+)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\n/g, '<br>');

      content.innerHTML = formatted;

      msgDiv.appendChild(avatar);
      msgDiv.appendChild(content);
      messagesContainer.appendChild(msgDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      return content;
    }

    function appendConfirmationCard(actionData) {
      const card = document.createElement('div');
      card.className = 'confirm-card';
      card.id = `confirm-${actionData.token}`;

      let diffHtml = '';
      if (actionData.diff) {
        const lines = actionData.diff.split('\\n');
        diffHtml = lines.map(line => {
          if (line.startsWith('+')) return `<span class="diff-add">${escapeHtml(line)}</span>`;
          if (line.startsWith('-')) return `<span class="diff-del">${escapeHtml(line)}</span>`;
          if (line.startsWith('@@')) return `<span class="diff-info">${escapeHtml(line)}</span>`;
          return escapeHtml(line);
        }).join('\\n');
      } else if (actionData.new_content) {
        diffHtml = `<span class="diff-add">${escapeHtml(actionData.new_content)}</span>`;
      }

      card.innerHTML = `
        <div class="confirm-header">
          <span><i class="fa-solid fa-shield-halved"></i> Vyžaduje sa potvrdenie: ${actionData.action}</span>
        </div>
        <div style="font-size: 0.85rem; color: #cbd5e1; margin-bottom: 6px;">
          📁 <strong>Cieľ:</strong> <code>${escapeHtml(actionData.file_path)}</code>
        </div>
        <div class="diff-box">${diffHtml}</div>
        <div class="confirm-actions">
          <button class="btn-approve" onclick="handleConfirmation('${actionData.token}', true)">
            <i class="fa-solid fa-check"></i> Schváliť a vykonať zmenu
          </button>
          <button class="btn-reject" onclick="handleConfirmation('${actionData.token}', false)">
            <i class="fa-solid fa-xmark"></i> Odmietnuť zmenu
          </button>
        </div>
      `;

      messagesContainer.appendChild(card);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHtml(text) {
      return (text || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    async function handleConfirmation(token, approved) {
      const card = document.getElementById(`confirm-${token}`);
      if (card) {
        card.innerHTML = `<div style="color: ${approved ? 'var(--success)' : 'var(--danger)'}; padding: 8px;">
          <i class="fa-solid ${approved ? 'fa-circle-check' : 'fa-circle-xmark'}"></i> 
          ${approved ? 'Zmena bola schválená a aplikovaná do systému.' : 'Zmena bola odmietnutá používateľom.'}
        </div>`;
      }

      try {
        const response = await fetch('/api/gemini_ha_orchestrator/confirm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: token, approved: approved })
        });
        const data = await response.json();
        if (data.reply) {
          appendMessage('assistant', data.reply);
        }
      } catch (err) {
        appendMessage('assistant', '⚠️ Chyba pri odosielaní potvrdenia: ' + err.message);
      }
    }

    async function sendMessage() {
      const text = userInput.value.trim();
      if (!text) return;

      appendMessage('user', text);
      userInput.value = '';
      userInput.style.height = 'auto';
      sendBtn.disabled = true;

      // Loading indicator
      const loadingDiv = document.createElement('div');
      loadingDiv.className = 'message assistant';
      loadingDiv.id = 'loading-msg';
      loadingDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="message-content">
          <div class="typing-indicator"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
        </div>
      `;
      messagesContainer.appendChild(loadingDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        const response = await fetch('/api/gemini_ha_orchestrator/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            history: conversationHistory
          })
        });

        const data = await response.json();
        const loading = document.getElementById('loading-msg');
        if (loading) loading.remove();

        if (data.model) {
          const modelBadge = document.getElementById('model-badge');
          if (modelBadge) {
            modelBadge.innerHTML = `<i class="fa-solid fa-microchip"></i> ${data.model}`;
          }
        }

        if (data.confirmation_required) {
          if (data.message) {
            appendMessage('assistant', data.message);
          }
          appendConfirmationCard(data.action_data);
        } else if (data.reply) {
          appendMessage('assistant', data.reply);
          conversationHistory.push({ role: 'user', content: text });
          conversationHistory.push({ role: 'assistant', content: data.reply });
        } else if (data.error) {
          appendMessage('assistant', '⚠️ Chyba: ' + data.error);
        }
      } catch (err) {
        const loading = document.getElementById('loading-msg');
        if (loading) loading.remove();
        appendMessage('assistant', '⚠️ Nastala chyba komunikácie: ' + err.message);
      } finally {
        sendBtn.disabled = false;
        userInput.focus();
      }
    }
  </script>
</body>
</html>"""
        rendered_html = html_content.replace("__MODEL_NAME__", model_name)
        return web.Response(text=rendered_html, content_type="text/html")


class GeminiChatApiView(HomeAssistantView):
    """API view handling prompt conversation with Gemini."""

    url = "/api/gemini_ha_orchestrator/chat"
    name = "api:gemini_ha_orchestrator:chat"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize chat API view."""
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Process incoming chat message."""
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON body"}, status=400)

        message = data.get("message", "").strip()
        if not message:
            return web.json_response({"error": "Message is empty"}, status=400)

        # Retrieve integration config
        entry_data = {}
        if DOMAIN in getattr(self.hass, "data", {}) and self.hass.data[DOMAIN]:
            for entry_val in self.hass.data[DOMAIN].values():
                if isinstance(entry_val, dict):
                    entry_data = entry_val
                    break

        if not entry_data and hasattr(self.hass, "config_entries") and hasattr(self.hass.config_entries, "async_entries"):
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                entry_data = {**entry.data, **getattr(entry, "options", {})}
                break

        api_key = entry_data.get(CONF_API_KEY) or os.getenv("GEMINI_API_KEY", "")
        model_name = entry_data.get(CONF_MODEL, DEFAULT_MODEL)
        config_dir = getattr(self.hass.config, "config_dir", ".")

        if not api_key:
            return web.json_response({
                "reply": "⚠️ Google Gemini API kľúč nie je nakonfigurovaný. Prosím nastavte ho v Home Assistant Integráciách alebo cez premennú prostredia `GEMINI_API_KEY`.",
                "model": model_name,
            })

        # Process message with Google GenAI SDK in executor
        try:
            result = await self.hass.async_add_executor_job(
                self._process_gemini_message,
                message,
                api_key,
                model_name,
                config_dir,
            )
            if isinstance(result, dict):
                result.setdefault("model", model_name)
            return web.json_response(result)
        except Exception as e:
            _LOGGER.exception(f"Error calling Gemini: {e}")
            return web.json_response({"error": str(e), "model": model_name}, status=500)

    def _process_gemini_message(
        self,
        message: str,
        api_key: str,
        model_name: str,
        config_dir: str,
    ) -> Dict[str, Any]:
        """Calls Gemini API and handles tool calls with confirmation."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            return {"error": "Google GenAI SDK is not installed on this instance."}

        client = genai.Client(api_key=api_key)

        # Gemini tool declarations
        save_blueprint_decl = types.FunctionDeclaration(
            name="save_blueprint",
            description="Creates a new Home Assistant Blueprint and saves it to blueprints/automation/<name>.yaml.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(type=types.Type.STRING, description="Blueprint identifier name (e.g. morning_routine)"),
                    "yaml_code": types.Schema(type=types.Type.STRING, description="Complete valid YAML blueprint content"),
                },
                required=["name", "yaml_code"],
            ),
        )

        modify_yaml_decl = types.FunctionDeclaration(
            name="modify_yaml_section",
            description="Safely adds or modifies a configuration domain block in a YAML configuration file.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "file_path": types.Schema(type=types.Type.STRING, description="Relative path to file, e.g. configuration.yaml"),
                    "domain_key": types.Schema(type=types.Type.STRING, description="Top level YAML domain key, e.g. input_boolean"),
                    "yaml_content": types.Schema(type=types.Type.STRING, description="YAML content string to place under this domain key"),
                },
                required=["file_path", "domain_key", "yaml_content"],
            ),
        )

        read_file_decl = types.FunctionDeclaration(
            name="read_file",
            description="Reads the text content of a file in Home Assistant configuration directory.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "file_path": types.Schema(type=types.Type.STRING, description="Relative path of file to read"),
                },
                required=["file_path"],
            ),
        )

        list_files_decl = types.FunctionDeclaration(
            name="list_files",
            description="Lists files and directories in Home Assistant configuration directory.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "sub_directory": types.Schema(type=types.Type.STRING, description="Optional subdirectory path"),
                },
            ),
        )

        tools = [
            types.Tool(function_declarations=[save_blueprint_decl, modify_yaml_decl, read_file_decl, list_files_decl])
        ]

        system_instruction = (
            "You are Gemini HA Orchestrator, an AI assistant for Home Assistant. "
            "You help manage configurations and generate valid blueprints. "
            "Always produce clean and correct YAML. File modifications require confirmation."
        )

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            temperature=0.2,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=message,
            config=config,
        )

        # Check for function calls
        for candidate in getattr(response, "candidates", []):
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []):
                fn_call = getattr(part, "function_call", None)
                if fn_call:
                    fn_name = getattr(fn_call, "name", "")
                    fn_args = getattr(fn_call, "args", {}) or {}

                    # Read operations can run automatically
                    if fn_name == "read_file":
                        fpath = os.path.join(config_dir, fn_args.get("file_path", ""))
                        if os.path.exists(fpath) and os.path.isfile(fpath):
                            with open(fpath, "r", encoding="utf-8") as f:
                                file_text = f.read()
                            return {"reply": f"Obsah súboru `{fn_args.get('file_path')}`:\n```yaml\n{file_text}\n```"}
                        return {"reply": f"Súbor `{fn_args.get('file_path')}` nebol nájdený."}

                    if fn_name == "list_files":
                        target_dir = os.path.join(config_dir, fn_args.get("sub_directory", ""))
                        if os.path.exists(target_dir):
                            items = os.listdir(target_dir)
                            return {"reply": f"Súbory v `{fn_args.get('sub_directory') or '/'}`:\n" + "\n".join(f"- `{i}`" for i in items)}
                        return {"reply": f"Adresár `{fn_args.get('sub_directory')}` nebol nájdený."}

                    # Write operations require Human-in-the-Loop confirmation
                    token = str(uuid.uuid4())
                    if fn_name == "save_blueprint":
                        bp_name = fn_args.get("name", "blueprint")
                        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in bp_name]).strip("_") + ".yaml"
                        target_path = os.path.join("blueprints", "automation", safe_name)
                        full_target = os.path.join(config_dir, target_path)
                        old_content = ""
                        if os.path.exists(full_target):
                            with open(full_target, "r", encoding="utf-8") as f:
                                old_content = f.read()

                        new_code = fn_args.get("yaml_code", "")
                        diff = "".join(difflib.unified_diff(
                            old_content.splitlines(keepends=True),
                            new_code.splitlines(keepends=True),
                            fromfile=f"a/{safe_name}",
                            tofile=f"b/{safe_name}",
                            n=3
                        ))

                        PENDING_ACTIONS[token] = {
                            "action": "save_blueprint",
                            "name": bp_name,
                            "yaml_content": new_code,
                            "target_path": full_target,
                        }

                        return {
                            "confirmation_required": True,
                            "message": f"Gemini navrhuje vytvoriť/aktualizovať blueprint **{bp_name}**.",
                            "action_data": {
                                "token": token,
                                "action": f"Uložiť Blueprint ({bp_name})",
                                "file_path": target_path,
                                "diff": diff,
                                "new_content": new_code,
                            }
                        }

                    if fn_name == "modify_yaml_section":
                        fpath = fn_args.get("file_path", "configuration.yaml")
                        domain_key = fn_args.get("domain_key", "")
                        yaml_content = fn_args.get("yaml_content", "")
                        full_target = os.path.join(config_dir, fpath)
                        old_content = ""
                        if os.path.exists(full_target):
                            with open(full_target, "r", encoding="utf-8") as f:
                                old_content = f.read()

                        PENDING_ACTIONS[token] = {
                            "action": "modify_yaml_section",
                            "file_path": full_target,
                            "domain_key": domain_key,
                            "yaml_content": yaml_content,
                        }

                        return {
                            "confirmation_required": True,
                            "message": f"Gemini navrhuje upraviť sekciu `{domain_key}` v súbore `{fpath}`.",
                            "action_data": {
                                "token": token,
                                "action": f"Upraviť sekciu [{domain_key}]",
                                "file_path": fpath,
                                "diff": f"+ {domain_key}:\n+ {yaml_content}",
                                "new_content": yaml_content,
                            }
                        }

        reply_text = getattr(response, "text", "") or "Nebola vygenerovaná žiadna odpoveď."
        return {"reply": reply_text}


class GeminiConfirmApiView(HomeAssistantView):
    """API view handling user approval/rejection of pending modifications."""

    url = "/api/gemini_ha_orchestrator/confirm"
    name = "api:gemini_ha_orchestrator:confirm"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize confirm API view."""
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        """Confirm or reject a pending action."""
        try:
            data = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        token = data.get("token")
        approved = bool(data.get("approved"))

        if not token or token not in PENDING_ACTIONS:
            return web.json_response({"error": "Akcia nebola nájdená alebo vypršala."}, status=404)

        action = PENDING_ACTIONS.pop(token)

        if not approved:
            return web.json_response({
                "status": "cancelled",
                "reply": "❌ Úprava súboru bola na váš pokyn zrušená. Žiadne zmeny neboli vykonané."
            })

        # Execute approved action
        try:
            modifier = GeminiFileModifier(self.hass)
            if action["action"] == "save_blueprint":
                bp_name = action["name"]
                content = action["yaml_content"]
                await self.hass.async_add_executor_job(modifier.save_blueprint, bp_name, content)
                await self.hass.services.async_call("blueprint", "reload")
                return web.json_response({
                    "status": "success",
                    "reply": f"✅ Blueprint **{bp_name}** bol úspešne uložený a blueprinty v Home Assistante boli obnovené."
                })

            elif action["action"] == "modify_yaml_section":
                domain_key = action["domain_key"]
                content = action["yaml_content"]
                # Modifying yaml section
                await self.hass.async_add_executor_job(modifier.modify_configuration_yaml, domain_key, content)
                return web.json_response({
                    "status": "success",
                    "reply": f"✅ Sekcia **{domain_key}** bola úspešne zapísaná do konfigurácie."
                })
        except Exception as e:
            _LOGGER.exception(f"Error applying approved change: {e}")
            return web.json_response({"error": str(e)}, status=500)

        return web.json_response({"status": "unknown"})
