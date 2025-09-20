import os
import sys
import time
import re
import subprocess
import hashlib
import platform
import shutil
import argparse
import webbrowser
from io import BytesIO
import json
from threading import Thread
import queue
import site
from pathlib import Path

response_queue = queue.Queue()

# -------------------------------
# 0. Setup & Dependency Helpers
# -------------------------------

DEBUG = False

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored_print(text, color=None):
    if color:
        print(f"{color}{text}{Colors.ENDC}")
    else:
        print(text)

def ensure_package(package, import_name=None, extra_args=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except Exception:
        colored_print(f"[Setup] Installing Python package '{package}'...", Colors.OKCYAN)
        cmd = [sys.executable, "-m", "pip", "install", package]
        if extra_args:
            cmd.extend(extra_args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if res.stdout:
                colored_print(res.stdout.strip(), Colors.OKGREEN)
            __import__(import_name)
            return True
        except subprocess.CalledProcessError as e:
            colored_print(f"[Setup] Failed to install '{package}': {e.stderr or e}", Colors.FAIL)
            return False

# Core deps
ensure_package("pillow", "PIL")
ensure_package("pytesseract")
ensure_package("keyring")
ensure_package("requests")

from PIL import Image, ImageGrab  # type: ignore
import pytesseract  # type: ignore
import keyring  # type: ignore
import requests  # type: ignore

# Optional GUI
try:
    import tkinter as tk
except Exception:
    tk = None  # type: ignore

# Ensure Tesseract binary present (print guidance if missing)
def ensure_tesseract_binary():
    if shutil.which("tesseract"):
        return True
    colored_print("[Setup] Tesseract OCR is not installed or not on PATH.", Colors.WARNING)
    sysname = platform.system()
    if sysname == "Darwin":
        colored_print("[Setup] Install via Homebrew: 'brew install tesseract'", Colors.OKCYAN)
    elif sysname == "Windows":
        colored_print("[Setup] Install via Chocolatey: 'choco install tesseract' or download from 'https://github.com/UB-Mannheim/tesseract/wiki'", Colors.OKCYAN)
    else:
        colored_print("[Setup] Install via apt: 'sudo apt-get install tesseract-ocr' or your distro equivalent.", Colors.OKCYAN)
    return False

# ---------------------------------
# Sanitization & Formatting of Hints
# ---------------------------------

def sanitize_and_format_hints(raw_text):
    """
    Normalize model output into 3-5 'Hint N: ...' lines, stripping any final answers.
    - Remove lines that reveal final numeric answers or exact options like '(B) 42'.
    - Ensure between 3 and 5 hints; truncate extras, synthesize minimal hints if needed.
    - Always end with a short encouragement line.
    """
    if not raw_text:
        return "[LLM Error] Empty response"

    text = raw_text.strip()
    # Split into candidate lines
    lines = [l.strip() for l in re.split(r"[\n\r]+", text) if l.strip()]

    # Extract hint-like lines or bullet points
    hint_lines = []
    for line in lines:
        lowered = line.lower()
        # Skip obvious final answers
        if re.search(r"\b(answer|final|equals|=)\b", lowered):
            continue
        if re.search(r"\boption\s*[abcd]\b", lowered):
            continue
        if re.search(r"\([A-D]\)\s*\S+", line):
            continue
        # Collect bullets or lines starting with Hint/Step
        if re.match(r"^(hint|step)\s*\d*\s*[:\-]", lowered):
            hint_lines.append(line)
        elif re.match(r"^[\-\*•]", line):
            hint_lines.append(re.sub(r"^[\-\*•]\s*", "", line))
        else:
            # Short, hinty sentences
            if 3 <= len(line.split()) <= 30:
                hint_lines.append(line)

    # Deduplicate preserving order
    seen = set()
    filtered = []
    for h in hint_lines:
        k = h.lower()
        if k not in seen:
            seen.add(k)
            filtered.append(h)

    # Take 3 to 5
    if len(filtered) < 3:
        base = "Focus on identifying knowns, selecting a method, then setting up steps."
        while len(filtered) < 3:
            filtered.append(base)
    filtered = filtered[:5]

    # Number and label consistently
    numbered = []
    for i, h in enumerate(filtered, 1):
        h = re.sub(r"^(hint|step)\s*\d*\s*[:\-]\s*", "", h, flags=re.IGNORECASE)
        numbered.append(f"Hint {i}: {h}")

    encouragement = "Now try completing the final step on your own."
    return "\n".join(numbered + [encouragement])

# ---------------------------------
# Config (persisted settings)
# ---------------------------------

CONFIG_PATH = os.path.expanduser("~/.hintify_config.json")
DEFAULT_CONFIG = {
    "provider": "ollama",  # "ollama" | "gemini"
    "ollama_model": "granite3.2-vision:2b",
    "gemini_model": "gemini-2.0-flash",
    "theme": "dark",  # "dark" | "light" | "glass"
}


def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.loads(f.read() or "{}")
            # Merge with defaults
            merged = DEFAULT_CONFIG.copy()
            merged.update(cfg or {})
            return merged
    except Exception:
        pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(json.dumps(cfg, indent=2))
        return True
    except Exception as e:
        colored_print(f"[Config] Failed to save config: {e}", Colors.FAIL)
        return False

def get_available_ollama_models():
    """Get list of available Ollama models"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        for line in lines:
            if line.strip():
                model_name = line.split()[0]
                if model_name and model_name != "NAME":
                    models.append(model_name)
        return models
    except Exception:
        return ["granite3.2-vision:2b", "llama3.2:3b", "qwen2.5:7b"]

def get_gemini_models():
    """Get list of common Gemini models"""
    return ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

def load_image_icon(path, size=(32, 32)):
    """Load and resize image for use as icon"""
    try:
        if os.path.exists(path):
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        colored_print(f"[UI] Failed to load icon {path}: {e}", Colors.WARNING)
    return None


def find_asset(filename):
    """Best-effort search for packaged or local asset file."""
    candidates = []
    try:
        candidates.append(Path.cwd() / filename)
        candidates.append(Path(__file__).resolve().parent / filename)
    except Exception:
        pass
    try:
        for base in list(site.getsitepackages()) + ([site.getusersitepackages()] if hasattr(site, "getusersitepackages") else []):
            candidates.append(Path(base) / "share" / "hintify" / filename)
    except Exception:
        pass
    for p in candidates:
        try:
            if p.exists():
                return str(p)
        except Exception:
            continue
    return filename


# ---------------------------------
# First-launch System Check & Setup
# ---------------------------------

def prompt_input(message, default=None):
    try:
        val = input(message).strip()
        return val if val else default
    except Exception:
        return default


def has_brew():
    return shutil.which("brew") is not None


def try_install_ollama_via_brew():
    if platform.system() != "Darwin":
        return False
    if not has_brew():
        colored_print("[Setup] Homebrew is not installed.", Colors.WARNING)
        colored_print("[Setup] Install Homebrew first:", Colors.OKCYAN)
        colored_print("/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", Colors.OKBLUE)
        return False
    try:
        colored_print("[Setup] Installing Ollama via Homebrew...", Colors.OKCYAN)
        # Prefer cask; fallback to formula if needed
        res = subprocess.run(["brew", "install", "--cask", "ollama"], capture_output=True, text=True)
        if res.returncode != 0:
            # Try non-cask install
            res2 = subprocess.run(["brew", "install", "ollama"], capture_output=True, text=True)
            if res2.returncode != 0:
                colored_print(f"[Setup] Homebrew install failed: {res.stderr or res2.stderr}", Colors.FAIL)
                return False
        colored_print("[Setup] Ollama installed via Homebrew.", Colors.OKGREEN)
        return True
    except Exception as e:
        colored_print(f"[Setup] Could not run Homebrew: {e}", Colors.FAIL)
        return False


def guide_ollama_install():
    sysname = platform.system()
    colored_print("[Guide] Ollama installation steps:", Colors.HEADER)
    if sysname == "Darwin":
        colored_print("1) Install Homebrew if missing:", Colors.OKBLUE)
        colored_print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", Colors.OKCYAN)
        colored_print("2) Install Ollama:", Colors.OKBLUE)
        colored_print("   brew install --cask ollama", Colors.OKCYAN)
        colored_print("3) Launch Ollama once from Launchpad or 'ollama serve' if needed.", Colors.OKBLUE)
    elif sysname == "Windows":
        colored_print("1) Install Ollama from the official site.", Colors.OKBLUE)
        colored_print("   https://ollama.com/download", Colors.OKCYAN)
        colored_print("2) Ensure 'ollama' is available in PATH (reopen terminal).", Colors.OKBLUE)
    else:
        colored_print("1) Install Ollama for Linux as per docs:", Colors.OKBLUE)
        colored_print("   https://ollama.com/download", Colors.OKCYAN)
        colored_print("2) Start service: 'ollama serve' (if not auto-managed).", Colors.OKBLUE)


def ensure_provider_on_first_launch(args):
    cfg = load_config()
    if cfg.get("setup_completed"):
        return cfg

    colored_print("[Setup] Running first-time setup...", Colors.HEADER)

    # Ensure Python deps (usually installed via pip, but double-check)
    for pkg, imp in [("pillow", "PIL"), ("pytesseract", None), ("keyring", None), ("requests", None), ("google-generativeai", "google.generativeai"), ("pynput", None)]:
        ensure_package(pkg, imp or pkg)

    # Provider selection
    colored_print("Select AI provider:", Colors.OKBLUE)
    colored_print("  1) Ollama (local, recommended)", Colors.OKCYAN)
    colored_print("  2) Gemini (cloud)", Colors.OKCYAN)
    choice = prompt_input("Enter 1 or 2 [1]: ", "1")

    if choice == "2":
        cfg["provider"] = "gemini"
        # Guide for API key
        colored_print("[Setup] Opening Gemini API key page...", Colors.OKBLUE)
        try:
            webbrowser.open("https://aistudio.google.com/apikey", new=2)
        except Exception:
            pass
        key = prompt_input("Paste your Gemini API key here (or press Enter to skip): ", "")
        if key:
            try:
                keyring.set_password("hintify", "gemini_api_key", key)
                os.environ["GEMINI_API_KEY"] = key
                colored_print("[Setup] Gemini API key saved to keychain.", Colors.OKGREEN)
            except Exception as e:
                colored_print(f"[Setup] Could not save key to keychain: {e}", Colors.FAIL)
        cfg.setdefault("gemini_model", "gemini-2.0-flash")
    else:
        cfg["provider"] = "ollama"
        cfg.setdefault("ollama_model", "granite3.2-vision:2b")
        # Ensure Ollama
        if not have_ollama():
            colored_print("[Setup] Ollama not found.", Colors.WARNING)
            installed = False
            if platform.system() == "Darwin":
                installed = try_install_ollama_via_brew()
            if not installed:
                guide_ollama_install()
                prompt_input("Press Enter after you finish installing Ollama to continue...", "")
        # Pull model
        if have_ollama():
            colored_print(f"[Setup] Ensuring model '{cfg['ollama_model']}' is available...", Colors.OKBLUE)
            ensure_ollama_model(cfg["ollama_model"])
        else:
            colored_print("[Setup] Ollama still not available. You can switch to Gemini in Settings.", Colors.WARNING)

    cfg["setup_completed"] = True
    save_config(cfg)
    return cfg

# Global hotkey (macOS/Windows) via pynput
if platform.system() in ("Darwin", "Windows"):
    ensure_package("pynput")
    try:
        from pynput import keyboard  # type: ignore
    except Exception:
        keyboard = None  # type: ignore
else:
    keyboard = None  # type: ignore

# -------------------------------
# macOS/Windows Hotkey Daemon
# -------------------------------

def run_hotkey_daemon():
    """Run a small daemon that registers a global hotkey and triggers capture.
    This runs in a separate process so any crash won't bring down the main app.
    """
    sysname = platform.system()
    if keyboard is None:
        print("[Hotkey] Pynput unavailable; daemon exiting.")
        return

    def on_activate():
        try:
            if sysname == "Darwin":
                subprocess.run(["screencapture", "-i", "-c"], check=True)
            elif sysname == "Windows":
                if shutil.which("explorer"):
                    subprocess.Popen(["explorer", "ms-screenclip:"])
        except Exception as e:
            print(f"[Hotkey] Capture failed: {e}")

    try:
        if sysname == "Darwin":
            combo = '<cmd>+<shift>+h'
            print("[Hotkey] Daemon running. Global hotkey: Cmd+Shift+H")
            mapping = {combo: on_activate}
        elif sysname == "Windows":
            combo = '<ctrl>+<shift>+h'
            print("[Hotkey] Daemon running. Global hotkey: Ctrl+Shift+H")
            mapping = {combo: on_activate}
        else:
            return
        hk = keyboard.GlobalHotKeys(mapping)
        hk.start()
        # Keep the daemon alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            pass
    except Exception as e:
        print(f"[Hotkey] Daemon error: {e}")
        if sysname == "Darwin":
            print("[Hotkey] Grant Accessibility permission to your terminal/app in System Settings.")


def start_hotkey_daemon_subprocess():
    """Spawn the hotkey daemon subprocess; ignore failure."""
    try:
        subprocess.Popen([sys.executable, __file__, "--hotkey-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[Hotkey] Global hotkey daemon started (use Cmd+Shift+H on macOS, Ctrl+Shift+H on Windows).")
    except Exception as e:
        print(f"[Hotkey] Could not start daemon: {e}")

# -------------------------------
# 1. Screenshot Detection & OCR
# -------------------------------

def get_clipboard_image_bytes():
    try:
        grabbed = ImageGrab.grabclipboard()
    except Exception as e:
        print(f"[Clipboard] Failed to access clipboard: {e}")
        return None

    if grabbed is None:
        return None

    # If it's already an Image instance
    if isinstance(grabbed, Image.Image):
        buf = BytesIO()
        try:
            grabbed.convert("RGB").save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            return None

    # Some platforms return a list of file paths
    if isinstance(grabbed, list) and grabbed:
        first = grabbed[0]
        try:
            with Image.open(first) as im:
                buf = BytesIO()
                im.convert("RGB").save(buf, format="PNG")
                return buf.getvalue()
        except Exception:
            return None

    return None


def extract_text_from_image(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return re.sub(r"\s+", " ", text).strip()
    except Exception as e:
        return f"[OCR Error] {str(e)}"


# -------------------------------
# 2. Question Classification
# -------------------------------

MCQ_PATTERN = re.compile(r"\(A\)|\(B\)|\(C\)|\(D\)|\b\d\)\b")


def classify_question(text):
    if MCQ_PATTERN.search(text):
        return "MCQ"
    if "?" in text or re.search(r"(solve|find|calculate|prove|evaluate)", text, re.IGNORECASE):
        return "Descriptive"
    return "Not a Question"


# -------------------------------
# 3. Difficulty Detection
# -------------------------------

def detect_difficulty(text):
    word_count = text.count(" ") + 1
    if word_count < 15:
        return "Easy"
    elif word_count < 40:
        return "Medium"
    return "Hard"


# -------------------------------
# 4. Prompt + LLM Providers (Ollama only)
# -------------------------------

def build_prompt(text, qtype, difficulty):
    return f"""
You are SnapAssist AI, a study buddy for students.

The following text was extracted from a screenshot:
{text}

Classification:
- Type: {qtype}
- Difficulty: {difficulty}

Your role:
- Provide ONLY hints, NEVER the exact answer or final numeric/option.
- Do NOT solve the question fully.
- Do NOT mention which option is correct.
- Do NOT provide the final numeric value, simplified expression, or boxed result.
- Instead, give guiding clues that push the student to think.

Response format:
Always output between 3 to 5 hints in this style:
Hint 1: ...
Hint 2: ...
Hint 3: ...
(Hint 4 and Hint 5 only if needed)

Guidelines for hints:
- Focus on relevant formulae, rules, and methods.
- Use progressive layers: concept → formula → setup → approach → final nudge.
- Each hint should guide without completing the solution.
- Keep hints concise for faster responses.

End with an encouragement such as:
“Now try completing the final step on your own.”
or
“Work carefully through the last step to see which option fits.”

If the text is not a valid question, reply only:
⚠️ This does not appear to be a question.
"""


def have_ollama():
    return shutil.which("ollama") is not None


def ensure_ollama_model(model):
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        if model in (result.stdout or ""):
            return True
        print(f"[Setup] Pulling Ollama model '{model}'...")
        subprocess.run(["ollama", "pull", model], check=True)
        return True
    except Exception as e:
        print(f"[Setup] Could not ensure Ollama model '{model}': {e}")
        return False


def query_with_ollama(prompt, model):
    if not have_ollama():
        return "[Setup] Ollama CLI not found. Install from https://ollama.com/download and ensure 'ollama' is in your PATH."
    ensure_ollama_model(model)
    try:
        if DEBUG:
            print(f"[LLM] Calling Ollama model='{model}' (len(prompt)={len(prompt)})")
        result = subprocess.run(["ollama", "run", model], input=prompt, text=True, capture_output=True, check=True, timeout=120)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[LLM Error] Ollama request timed out. Try a smaller prompt or different model."
    except subprocess.CalledProcessError as e:
        return f"[LLM Error] {e.stderr or str(e)}"


def query_with_gemini(prompt, model, api_key):
    """Call Gemini via REST API, with fallback to gemini-1.5-flash if needed."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        if DEBUG:
            print(f"[LLM] Calling Gemini REST model='{model}' (len(prompt)={len(prompt)})")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 404 or resp.status_code == 403:
            # Not found / not allowed -> fallback
            fallback_model = "gemini-1.5-flash"
            if model != fallback_model:
                if DEBUG:
                    print(f"[LLM] Falling back to Gemini REST model='{fallback_model}' (status={resp.status_code})")
                return query_with_gemini(prompt, fallback_model, api_key)
        if resp.status_code != 200:
            return f"[LLM Error] Gemini HTTP {resp.status_code}: {resp.text.strip()}"
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return "[LLM Error] Empty response from Gemini"
        parts = ((candidates[0] or {}).get("content") or {}).get("parts") or []
        texts = []
        for part in parts:
            t = part.get("text")
            if isinstance(t, str) and t.strip():
                texts.append(t.strip())
        text = "\n".join(texts).strip()
        return text or "[LLM Error] Empty response from Gemini"
    except requests.Timeout:
        return "[LLM Error] Gemini request timed out. Try again later."
    except Exception as e:
        return f"[LLM Error] {e}"


def generate_hints(text, qtype, difficulty, args):
    prompt = build_prompt(text, qtype, difficulty)
    cfg = load_config()
    provider = (cfg.get("provider") or "ollama").lower()
    ollama_model = cfg.get("ollama_model") or os.getenv("HINTIFY_OLLAMA_MODEL") or args.ollama_model
    gem_model = cfg.get("gemini_model") or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    gem_key = os.getenv("GEMINI_API_KEY") or (keyring.get_password("hintify", "gemini_api_key") or None)

    if DEBUG:
        print(f"[Flow] Provider='ollama', qtype='{qtype}', difficulty='{difficulty}'")

    if provider == "ollama" and have_ollama():
        ok = ensure_ollama_model(ollama_model)
        if not ok:
            return "[Setup] Failed to pull required Ollama model. Please try again."
        raw = query_with_ollama(prompt, ollama_model)
        return sanitize_and_format_hints(raw)
    if provider == "gemini":
        if not gem_key:
            return "[Setup] GEMINI_API_KEY not set. Export GEMINI_API_KEY to use Gemini."
        raw = query_with_gemini(prompt, gem_model, gem_key)
        return sanitize_and_format_hints(raw)

    # Auto fallback: if configured provider unavailable
    if have_ollama():
        ok = ensure_ollama_model(ollama_model)
        if ok:
            raw = query_with_ollama(prompt, ollama_model)
            return sanitize_and_format_hints(raw)
    if gem_key:
        raw = query_with_gemini(prompt, gem_model, gem_key)
        return sanitize_and_format_hints(raw)
    return "[Setup] No LLM provider available. Install Ollama or set GEMINI_API_KEY."


# -------------------------------
# 5. Main Clipboard Monitor
# -------------------------------

def monitor_clipboard(args):
    colored_print("🔍 SnapAssist AI is running... Press Ctrl+C to stop.", Colors.HEADER)
    last_hash = None

    while True:
        try:
            image_bytes = get_clipboard_image_bytes()
            if image_bytes:
                current_hash = hashlib.md5(image_bytes).hexdigest()
                if current_hash != last_hash:
                    last_hash = current_hash
                    colored_print("📸 Screenshot detected. Processing...", Colors.OKCYAN)

                    text = extract_text_from_image(image_bytes)
                    if not text:
                        colored_print("⚠️ No text found in the screenshot.", Colors.WARNING)
                        time.sleep(args.poll_interval)
                        continue

                    qtype = classify_question(text)
                    difficulty = detect_difficulty(text)

                    colored_print(f"🧠 Detected Question Type: {qtype}, Difficulty: {difficulty}", Colors.OKBLUE)
                    response = generate_hints(text, qtype, difficulty, args)

                    response_queue.put(response)

            time.sleep(args.poll_interval)
        except KeyboardInterrupt:
            colored_print("\n🛑 SnapAssist AI stopped.", Colors.FAIL)
            break
        except Exception as e:
            colored_print(f"[Error] {e}", Colors.FAIL)
            time.sleep(max(1.0, args.poll_interval))


def process_clipboard_once(args):
    """Process current clipboard image immediately if present."""
    image_bytes = get_clipboard_image_bytes()
    if not image_bytes:
        print("⚠️ No image found in the clipboard.")
        return
    text = extract_text_from_image(image_bytes)
    if not text or text.startswith("[OCR Error]"):
        print(text or "⚠️ No text found in the screenshot.")
        return
    qtype = classify_question(text)
    difficulty = detect_difficulty(text)
    print(f"🧠 Detected Question Type: {qtype}, Difficulty: {difficulty}")
    response = generate_hints(text, qtype, difficulty, args)
    response_queue.put(response)


# -------------------------------
# 5b. On-demand Capture Helpers
# -------------------------------

def trigger_macos_selection_capture():
    try:
        subprocess.run(["screencapture", "-i", "-c"], check=True)
        return True
    except Exception as e:
        print(f"[macOS] Failed to capture selection: {e}")
        return False


def trigger_windows_selection_capture():
    try:
        if shutil.which("explorer"):
            subprocess.Popen(["explorer", "ms-screenclip:"])
            return True
        return False
    except Exception as e:
        print(f"[Windows] Failed to start screen clip: {e}")
        return False


def capture_and_process(args):
    sysname = platform.system()
    ok = False
    if sysname == "Darwin":
        ok = trigger_macos_selection_capture()
    elif sysname == "Windows":
        ok = trigger_windows_selection_capture()

    # After triggering, poll clipboard briefly for the image and process
    if ok:
        deadline = time.time() + (5 if sysname == "Darwin" else 12)
        while time.time() < deadline:
            image_bytes = get_clipboard_image_bytes()
            if image_bytes:
                process_clipboard_once(args)
                return
            time.sleep(0.25)
        print("⚠️ Timed out waiting for captured image on clipboard.")

# -------------------------------
# 6. Fixed Window GUI (optional)
# -------------------------------

class FixedWindow:
    def __init__(self, root, args):
        cfg = load_config()
        theme = (cfg.get("theme") or "dark").lower()

        # Enhanced theme tokens with glass effects
        if theme == "light":
            bg_root = "#f8fafc"
            fg_text = "#0f172a"
            panel_bg = "#ffffff"
            panel_alpha = "#ffffff"
            border = "#e2e8f0"
            accent = "#2563eb"
            accent_text = "#ffffff"
            label_color = "#1d4ed8"
            enc_color = "#059669"
            glass_bg = "#f1f5f9"
        elif theme == "glass":
            bg_root = "#1e293b"
            fg_text = "#f1f5f9"
            panel_bg = "#334155"
            panel_alpha = "#334155"  # Tkinter doesn't support alpha; using solid color
            border = "#475569"
            accent = "#06b6d4"
            accent_text = "#0f172a"
            label_color = "#38bdf8"
            enc_color = "#10b981"
            glass_bg = "#1e293b"  # Solid fallback without alpha
        else:  # dark
            bg_root = "#0f172a"
            fg_text = "#e5e7eb"
            panel_bg = "#111827"
            panel_alpha = "#111827"
            border = "#1f2937"
            accent = "#22c55e"
            accent_text = "#0f172a"
            label_color = "#93c5fd"
            enc_color = "#86efac"
            glass_bg = "#111827"

        root.title("SnapAssist AI")
        root.geometry("750x600+100+100")
        root.configure(bg=bg_root)
        
        # Set window icon to packaged/logo.png
        try:
            icon_path = find_asset("logo.png")
            icon_img = load_image_icon(icon_path, (64, 64))
            if icon_img:
                import io
                bio = io.BytesIO()
                icon_img.save(bio, format='PNG')
                bio.seek(0)
                self.icon_photo = tk.PhotoImage(data=bio.read())
                root.iconphoto(True, self.icon_photo)
        except Exception:
            pass

        # Store references for live theme application
        self.root = root
        self.args = args
        self._cfg = cfg
        self._theme = theme
        self._theme_tokens = {
            "bg_root": bg_root,
            "fg_text": fg_text,
            "panel_bg": panel_bg,
            "panel_alpha": panel_alpha,
            "border": border,
            "accent": accent,
            "accent_text": accent_text,
            "label_color": label_color,
            "enc_color": enc_color,
            "glass_bg": glass_bg,
        }

        # Main container with glass effect
        main_frame = tk.Frame(root, bg=glass_bg if theme == "glass" else bg_root)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.main_frame = main_frame

        # Top bar with logo and buttons
        # Clean navigation bar with solid background and no stray stripes
        topbar = tk.Frame(main_frame, bg=panel_bg, relief="flat", bd=0, highlightthickness=0)
        topbar.pack(fill="x", padx=0, pady=(0, 8))
        self.topbar = topbar

        # Logo and title section
        title_frame = tk.Frame(topbar, bg=panel_bg, highlightthickness=0, bd=0)
        title_frame.pack(side="left", fill="y")
        self.title_frame = title_frame

        # Logo intentionally removed per request for a cleaner headert

        title = tk.Label(title_frame, text="SnapAssist AI", fg=fg_text, bg=panel_bg, font=("SF Pro Display", 18, "bold"))
        title.pack(side="left", padx=12, pady=8)
        self.title_label = title

        # Action buttons with proper styling
        buttons_frame = tk.Frame(topbar, bg=panel_bg, highlightthickness=0, bd=0)
        buttons_frame.pack(side="right", padx=12, pady=6)
        self.buttons_frame = buttons_frame

        # Load button icons
        try:
            settings_img = load_image_icon("settings-94.png", (24, 24))
            capture_img = load_image_icon("screenshot-64.png", (24, 24))
            
            if settings_img:
                import io
                bio = io.BytesIO()
                settings_img.save(bio, format='PNG')
                bio.seek(0)
                self.settings_photo = tk.PhotoImage(data=bio.read())
            if capture_img:
                import io
                bio = io.BytesIO()
                capture_img.save(bio, format='PNG')
                bio.seek(0)
                self.capture_photo = tk.PhotoImage(data=bio.read())
        except Exception:
            self.settings_photo = None
            self.capture_photo = None

        # Settings button with integrated look
        self.settings_btn = tk.Button(
            buttons_frame,
            image=getattr(self, 'settings_photo', None) or None,
            text="⚙" if not hasattr(self, 'settings_photo') else "",
            command=lambda: self.open_settings(args),
            bg=panel_bg,
            fg=fg_text,
            activebackground=border,
            activeforeground=fg_text,
            relief="flat",
            bd=0,
            padx=8,
            pady=8,
        )
        self.settings_btn.pack(side="right", padx=(8, 0))

        # Capture button with integrated look
        self.capture_btn = tk.Button(
            buttons_frame,
            image=getattr(self, 'capture_photo', None) or None,
            text="📸" if not hasattr(self, 'capture_photo') else "",
            command=lambda: capture_and_process(args),
            bg=accent,
            fg=accent_text,
            activebackground=accent,
            activeforeground=accent_text,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
        )
        self.capture_btn.pack(side="right", padx=(0, 8))

        # Content area with glass effect
        content_bg = panel_alpha if theme == "glass" else panel_bg
        content = tk.Frame(main_frame, bg=content_bg, relief="flat", bd=1, highlightbackground=border, highlightthickness=1)
        content.pack(fill="both", expand=True)
        self.content = content

        # Text display with glass styling
        text_container = tk.Frame(content, bg=content_bg)
        text_container.pack(fill="both", expand=True, padx=12, pady=12)
        self.text_container = text_container

        # Scrollbar
        scrollbar = tk.Scrollbar(text_container, bg=panel_bg, troughcolor=border)
        scrollbar.pack(side="right", fill="y")
        self.scrollbar = scrollbar

        # Text widget with glass transparency
        self.text_widget = tk.Text(
            text_container,
            wrap="word",
            bg=content_bg,
            fg=fg_text,
            insertbackground=fg_text,
            font=("SF Pro Text", 15),
            relief="flat",
            bd=0,
            padx=16,
            pady=16,
            yscrollcommand=scrollbar.set,
        )
        self.text_widget.config(state="disabled")
        self.text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)

        # Text styling tags
        self.text_widget.tag_configure("hint_label", font=("SF Pro Text", 16, "bold"), foreground=label_color)
        self.text_widget.tag_configure("hint_text", font=("SF Pro Text", 15), foreground=fg_text)
        self.text_widget.tag_configure("enc", font=("SF Pro Text", 14, "italic"), foreground=enc_color)

        # Keyboard shortcut
        try:
            root.bind_all('<Key-c>', lambda e: capture_and_process(args))
        except Exception:
            pass

    def apply_theme(self, theme):
        theme = (theme or "dark").lower()
        if theme == "light":
            tokens = {
                "bg_root": "#f8fafc",
                "fg_text": "#0f172a",
                "panel_bg": "#ffffff",
                "border": "#e2e8f0",
                "accent": "#2563eb",
                "accent_text": "#ffffff",
                "label_color": "#1d4ed8",
                "enc_color": "#059669",
            }
        elif theme == "glass":
            tokens = {
                "bg_root": "#e5e7eb",
                "fg_text": "#0f172a",
                "panel_bg": "#ffffff",
                "border": "#cbd5e1",
                "accent": "#10b981",
                "accent_text": "#0b1320",
                "label_color": "#0ea5e9",
                "enc_color": "#059669",
            }
        else:
            tokens = {
                "bg_root": "#0f172a",
                "fg_text": "#e5e7eb",
                "panel_bg": "#111827",
                "border": "#1f2937",
                "accent": "#22c55e",
                "accent_text": "#0b1320",
                "label_color": "#93c5fd",
                "enc_color": "#86efac",
            }
        self._theme = theme
        self._theme_tokens = tokens
        # Apply to widgets
        self.root.configure(bg=tokens["bg_root"])
        self.topbar.configure(bg=tokens["bg_root"])
        self.title_label.configure(bg=tokens["bg_root"], fg=tokens["fg_text"])
        self.buttons_frame.configure(bg=tokens["bg_root"])
        self.settings_btn.configure(bg=tokens["panel_bg"], fg=tokens["fg_text"], activebackground=tokens["panel_bg"], activeforeground=tokens["fg_text"])
        self.capture_btn.configure(bg=tokens["accent"], fg=tokens["accent_text"], activebackground=tokens["accent"], activeforeground=tokens["accent_text"])
        self.content.configure(bg=tokens["panel_bg"], highlightbackground=tokens["border"])
        # text_frame no longer used; configure text_container instead
        if hasattr(self, "text_container"):
            self.text_container.configure(bg=tokens["panel_bg"]) 
        self.text_widget.configure(bg=tokens["panel_bg"], fg=tokens["fg_text"], insertbackground=tokens["fg_text"])
        self.text_widget.tag_configure("hint_label", foreground=tokens["label_color"]) 
        self.text_widget.tag_configure("hint_text", foreground=tokens["fg_text"]) 
        self.text_widget.tag_configure("enc", foreground=tokens["enc_color"]) 

    def show(self, response):
        if not self.text_widget.winfo_exists():
            return
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        # Pretty-print hints: bold labels, styled text
        lines = [l for l in (response or "").splitlines()]
        for idx, line in enumerate(lines):
            m = re.match(r"^(Hint\s+\d+:)(\s*)(.*)$", line.strip())
            if m:
                label, spaces, rest = m.group(1), m.group(2), m.group(3)
                self.text_widget.insert(tk.END, label, ("hint_label",))
                self.text_widget.insert(tk.END, spaces or " ")
                self.text_widget.insert(tk.END, rest + "\n", ("hint_text",))
            elif line.strip().lower().startswith("now try") or line.strip().lower().startswith("work carefully"):
                self.text_widget.insert(tk.END, line + "\n", ("enc",))
            else:
                self.text_widget.insert(tk.END, line + "\n", ("hint_text",))
        self.text_widget.config(state="disabled")

    def open_settings(self, args):
        cfg = load_config()
        top = tk.Toplevel()
        top.title("Settings")
        top.geometry("460x380+140+140")
        t = self._theme_tokens
        top.configure(bg=t["panel_bg"])

        # Provider
        provider_var = tk.StringVar(value=cfg.get("provider", "ollama"))
        tk.Label(top, text="Provider", bg=t["panel_bg"], fg=t["fg_text"]).pack(anchor="w", padx=12, pady=(12,2))
        provider_menu = tk.OptionMenu(top, provider_var, "ollama", "gemini")
        provider_menu.pack(fill="x", padx=12)

        # Models
        tk.Label(top, text="Ollama model", bg=t["panel_bg"], fg=t["fg_text"]).pack(anchor="w", padx=12, pady=(12,2))
        ollama_var = tk.StringVar(value=cfg.get("ollama_model", "granite3.2-vision:2b"))
        tk.Entry(top, textvariable=ollama_var).pack(fill="x", padx=12)

        tk.Label(top, text="Gemini model", bg=t["panel_bg"], fg=t["fg_text"]).pack(anchor="w", padx=12, pady=(12,2))
        gem_var = tk.StringVar(value=cfg.get("gemini_model", "gemini-2.0-flash"))
        tk.Entry(top, textvariable=gem_var).pack(fill="x", padx=12)

        # Gemini API key
        tk.Label(top, text="Gemini API key", bg=t["panel_bg"], fg=t["fg_text"]).pack(anchor="w", padx=12, pady=(12,2))
        current_key = os.getenv("GEMINI_API_KEY") or (keyring.get_password("hintify", "gemini_api_key") or "")
        key_var = tk.StringVar(value=current_key)
        key_entry = tk.Entry(top, textvariable=key_var, show="•")
        key_entry.pack(fill="x", padx=12)

        # Theme
        tk.Label(top, text="Theme", bg=t["panel_bg"], fg=t["fg_text"]).pack(anchor="w", padx=12, pady=(12,2))
        theme_var = tk.StringVar(value=cfg.get("theme", "dark"))
        theme_menu = tk.OptionMenu(top, theme_var, "dark", "light", "glass")
        theme_menu.pack(fill="x", padx=12)

        btns = tk.Frame(top, bg=t["panel_bg"])
        btns.pack(fill="x", pady=12)

        def save_key():
            val = (key_var.get() or "").strip()
            if val:
                try:
                    keyring.set_password("hintify", "gemini_api_key", val)
                    os.environ["GEMINI_API_KEY"] = val
                    print("[Settings] Gemini API key saved to keychain.")
                except Exception as e:
                    print(f"[Settings] Failed to save key: {e}")

        def clear_key():
            try:
                keyring.delete_password("hintify", "gemini_api_key")
                if "GEMINI_API_KEY" in os.environ:
                    del os.environ["GEMINI_API_KEY"]
                key_var.set("")
                print("[Settings] Gemini API key cleared.")
            except Exception as e:
                print(f"[Settings] Failed to clear key: {e}")

        def save_and_apply():
            new_cfg = {
                "provider": provider_var.get(),
                "ollama_model": ollama_var.get().strip() or "granite3.2-vision:2b",
                "gemini_model": gem_var.get().strip() or "gemini-2.0-flash",
                "theme": theme_var.get(),
            }
            save_config(new_cfg)
            # Save key if provided
            if key_var.get().strip():
                save_key()
            # Apply theme live
            self.apply_theme(new_cfg["theme"])
            top.destroy()
            print("[Settings] Saved.")

        tk.Button(btns, text="Save", command=save_and_apply, bg=t["accent"], fg=t["accent_text"], relief="flat").pack(side="right", padx=(6,12))
        tk.Button(btns, text="Save key", command=save_key, relief="groove").pack(side="left", padx=12)
        tk.Button(btns, text="Clear key", command=clear_key, relief="groove").pack(side="left")
        tk.Button(btns, text="Cancel", command=top.destroy, relief="groove").pack(side="right")


def headless_print_loop():
    try:
        while True:
            try:
                response = response_queue.get(timeout=0.5)
                if response:
                    print("\n📘 Hints:\n" + response + "\n")
            except Exception:
                pass
    except KeyboardInterrupt:
        return


def gui_loop(args):
    if tk is None:
        print("[GUI] tkinter not available. Running in headless mode.")
        headless_print_loop()
        return
    try:
        root = tk.Tk()
    except Exception as e:
        print(f"[GUI] Failed to initialize tkinter GUI ({e}). Falling back to headless mode.")
        headless_print_loop()
        return
    app = FixedWindow(root, args)

    def poll_queue():
        while not response_queue.empty():
            response = response_queue.get()
            app.show(response)
        root.after(500, poll_queue)

    root.after(500, poll_queue)
    root.mainloop()


# -------------------------------
# 7. Main Entry
# -------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="SnapAssist AI - cross-platform clipboard-to-hints")
    parser.add_argument("--no-gui", action="store_true", help="Run without tkinter GUI")
    parser.add_argument("--poll-interval", type=float, default=1.5, help="Clipboard polling interval in seconds")
    # Provider is no longer selectable; we keep the flag for compatibility but ignore it
    parser.add_argument("--provider", choices=["ollama", "gemini"], default=None, help="(Ignored) Provider selection; Ollama is enforced")
    parser.add_argument("--ollama-model", default=os.getenv("HINTIFY_OLLAMA_MODEL", "granite3.2-vision:2b"), help="Ollama model to use")
    parser.add_argument("--gemini-model", default=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), help="(Unused) Gemini model")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--capture-now", action="store_true", help="Immediately prompt to select an area and process once")
    parser.add_argument("--hotkey-daemon", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def main():
    args = parse_args()

    # Hotkey daemon mode (separate process)
    if getattr(args, "hotkey_daemon", False):
        run_hotkey_daemon()
        sys.exit(0)

    # Set debug flag
    DEBUG = getattr(args, "debug", False)

    # Pre-flight checks
    ensure_tesseract_binary()
    # First-launch guided setup
    ensure_provider_on_first_launch(args)

    # macOS guidance with colors
    try:
        if platform.system() == "Darwin":
            colored_print("[macOS] Tip: Use Cmd+Ctrl+Shift+4 to copy a selection screenshot to the clipboard.", Colors.OKCYAN)
            colored_print("[macOS] Or use Cmd+Ctrl+Shift+5 → Options → Clipboard to copy captures.", Colors.OKCYAN)
            colored_print("[macOS] Global capture hotkey: Cmd+Shift+H (grant Accessibility permission if needed).", Colors.HEADER)
    except Exception:
        pass

    if not have_ollama():
        colored_print("[Setup] Ollama not detected. Install from https://ollama.com/download", Colors.WARNING)
        if platform.system() == "Darwin":
            colored_print("[Setup] On macOS: brew install --cask ollama", Colors.OKCYAN)
        else:
            colored_print("[Setup] See install instructions for your OS at https://ollama.com/download", Colors.OKCYAN)
        try:
            webbrowser.open("https://ollama.com/download", new=2)
        except Exception:
            pass
        sys.exit(1)

    # Ensure the required model is present before starting
    if not ensure_ollama_model(args.ollama_model):
        colored_print("[Setup] Could not ensure the required Ollama model. Please check your network and try again.", Colors.FAIL)
        sys.exit(1)

    # Start hotkey daemon subprocess (won't crash main app if it fails)
    start_hotkey_daemon_subprocess()

    # Optional immediate capture
    if getattr(args, "capture_now", False) and platform.system() == "Darwin":
        capture_and_process(args)

    # Start clipboard monitor thread
    Thread(target=monitor_clipboard, args=(args,), daemon=True).start()

    if args.no_gui:
        headless_print_loop()
    else:
        gui_loop(args)

if __name__ == "__main__":
    main()
