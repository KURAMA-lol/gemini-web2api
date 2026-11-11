#!/usr/bin/env python3
"""Render entrypoint for the upstream Gemini Web2API server.

Secrets are supplied only through Render environment variables. Never commit
cookie.txt or config.json to the repository.
"""
import importlib.util
import json
import os
import sys

APP_PATH = "/app/gemini_web2api.py"
spec = importlib.util.spec_from_file_location("gemini_web2api_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

_original_load_config = app.load_config
_original_load_cookie = app.load_cookie

def _render_load_config(path):
    _original_load_config(path)

    app.CONFIG["host"] = "0.0.0.0"
    app.CONFIG["port"] = int(os.environ.get("PORT", app.CONFIG.get("port", 8081)))

    api_keys = os.environ.get("GEMINI_API_KEYS", "").strip()
    api_key = os.environ.get("API_KEY", "").strip()
    if api_keys:
        app.CONFIG["api_keys"] = [item.strip() for item in api_keys.split(",") if item.strip()]
    elif api_key:
        app.CONFIG["api_keys"] = [api_key]

    env_map = {
        "GEMINI_DEFAULT_MODEL": "default_model",
        "GEMINI_BL": "gemini_bl",
        "GEMINI_XSRF_TOKEN": "xsrf_token",
        "GEMINI_PROXY": "proxy",
    }
    for env_name, config_name in env_map.items():
        value = os.environ.get(env_name)
        if value:
            app.CONFIG[config_name] = value

    auth_user = os.environ.get("GEMINI_AUTH_USER")
    if auth_user is not None and auth_user != "":
        app.CONFIG["auth_user"] = auth_user

    temporary = os.environ.get("GEMINI_TEMPORARY_CHATS")
    if temporary is not None:
        app.CONFIG["temporary_chats"] = temporary.lower() in ("1", "true", "yes", "on")

    if os.environ.get("GEMINI_COOKIE") or os.environ.get("GEMINI_COOKIES"):
        app.CONFIG["cookie_file"] = "Render environment variable"

def _cookie_from_environment():
    raw = os.environ.get("GEMINI_COOKIE") or os.environ.get("GEMINI_COOKIES")
    if not raw:
        return _original_load_cookie()

    raw = raw.strip()
    sapisid = None

    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            raw = str(data.get("cookie", "") or "")
            sapisid = data.get("sapisid") or None
        except (ValueError, TypeError):
            pass

    # Accept Netscape cookie exports as well as a Cookie header. Never allow
    # CR/LF characters to reach urllib's HTTP header validation.
    if "\t" in raw:
        pairs = []
        for line in raw.splitlines():
            if not line.strip() or (line.lstrip().startswith("#") and not line.startswith("#HttpOnly_")):
                continue
            columns = line.lstrip("#").split("\t")
            if len(columns) >= 7:
                pairs.append(columns[-2].strip() + "=" + columns[-1].strip())
        raw = "; ".join(p for p in pairs if p and "=" in p)
    else:
        raw = "; ".join(part.strip() for part in raw.replace("\r", "\n").split("\n") if part.strip())

    cookies = {}
    for part in raw.split(";"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            cookies[key.strip()] = value.strip()

    if not sapisid:
        sapisid = cookies.get("SAPISID")
    return raw, sapisid or None

app.load_config = _render_load_config
app.load_cookie = _cookie_from_environment

# The upstream handler does not implement HEAD and has no /health route.
_original_get = app.GeminiHandler.do_GET
def _render_get(self):
    if self.path in ("/health", "/healthz"):
        self.send_json({"status": "ok", "version": app.__version__})
        return
    return _original_get(self)

def _render_head(self):
    if self.path in ("/", "/health", "/healthz"):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()
    else:
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()

app.GeminiHandler.do_GET = _render_get
app.GeminiHandler.do_HEAD = _render_head

# The upstream exposes a Flash-Lite category under gemini-flash-lite. Keep
# that upstream ID and offer the requested OpenAI-client-friendly alias.
if "gemini-flash-lite" in app.MODELS:
    app.MODELS.setdefault(
        "gemini-2.5-flash-lite",
        {**app.MODELS["gemini-flash-lite"],
         "desc": "Flash-Lite mode alias (uses Gemini Web's Flash-Lite category)"}
    )

if not os.environ.get("GEMINI_DEFAULT_MODEL"):
    os.environ["GEMINI_DEFAULT_MODEL"] = "gemini-flash-lite"

sys.argv = [
    "gemini_web2api.py",
    "--config", "/app/config.json",
    "--port", os.environ.get("PORT", "8081"),
]
app.main()
