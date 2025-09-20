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
from threading import Thread
import queue

response_queue = queue.Queue()

# -------------------------------
# 0. Setup & Dependency Helpers
# -------------------------------

def ensure_package(package, import_name=None, extra_args=None):
    import_name = import_name or package
    try:
        __import__(import_name)
        return True
    except Exception:
        print(f"[Setup] Installing Python package '{package}'...")
        cmd = [sys.executable, "-m", "pip", "install", package]
        if extra_args:
            cmd.extend(extra_args)
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if res.stdout:
                print(res.stdout.strip())
            __import__(import_name)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Setup] Failed to install '{package}': {e.stderr or e}")
            return False

# Core deps
ensure_package("pillow", "PIL")
ensure_package("pytesseract")
ensure_package("keyring")

from PIL import Image, ImageGrab  # type: ignore
import pytesseract  # type: ignore
import keyring  # type: ignore

# Optional GUI
try:
    import tkinter as tk
except Exception:
    tk = None  # type: ignore


def ensure_tesseract_binary():
    if shutil.which("tesseract"):
        return True
    print("[Setup] Tesseract OCR is not installed or not on PATH.")
    sysname = platform.system()
    if sysname == "Darwin":
        print("[Setup] Install via Homebrew: 'brew install tesseract'")
    elif sysname == "Windows":
        print("[Setup] Install via Chocolatey: 'choco install tesseract' or download from 'https://github.com/UB-Mannheim/tesseract/wiki'")
    else:
        print("[Setup] Install via apt: 'sudo apt-get install tesseract-ocr' or your distro equivalent.")
    return False


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
# 4. Prompt + LLM Providers (Ollama and Gemini)
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
        result = subprocess.run(["ollama", "run", model], input=prompt, text=True, capture_output=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[LLM Error] {e.stderr or str(e)}"


def query_with_gemini(prompt, model, api_key):
    ok = ensure_package("google-generativeai", "google.generativeai")
    if not ok:
        return "[Setup] Failed to install google-generativeai. Please run: pip install google-generativeai"
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        try:
            chat = genai.GenerativeModel(model)
            resp = chat.generate_content(prompt)
            return (getattr(resp, "text", None) or "").strip() or "[LLM Error] Empty response from Gemini"
        except Exception as inner:
            # Fallback to 1.5 if 2.5 not available for the user
            if model != "gemini-1.5-flash":
                try:
                    fallback_model = "gemini-1.5-flash"
                    chat = genai.GenerativeModel(fallback_model)
                    resp = chat.generate_content(prompt)
                    return (getattr(resp, "text", None) or "").strip() or "[LLM Error] Empty response from Gemini"
                except Exception:
                    raise inner
            else:
                raise inner
    except Exception as e:
        return f"[LLM Error] {e}"


def generate_hints(text, qtype, difficulty, args):
    prompt = build_prompt(text, qtype, difficulty)
    provider = (os.getenv("HINTIFY_PROVIDER") or args.provider or "").lower()
    gem_key = os.getenv("GEMINI_API_KEY") or (keyring.get_password("hintify", "gemini_api_key") or None)
    ollama_model = os.getenv("HINTIFY_OLLAMA_MODEL") or args.ollama_model
    gem_model = os.getenv("GEMINI_MODEL") or args.gemini_model

    if provider == "gemini":
        if not gem_key:
            return "[Setup] GEMINI_API_KEY not set. Export GEMINI_API_KEY to use Gemini."
        return query_with_gemini(prompt, gem_model, gem_key)

    # Default to Ollama if available; otherwise fallback to Gemini if API key exists
    if have_ollama():
        # Ensure model pulled before first use
        ensure_ollama_model(ollama_model)
        return query_with_ollama(prompt, ollama_model)
    if gem_key:
        print("[Info] Ollama not found. Falling back to Gemini.")
        return query_with_gemini(prompt, gem_model, gem_key)
    return "[Setup] No LLM provider available. Install Ollama or set GEMINI_API_KEY."


# -------------------------------
# 5. Main Clipboard Monitor
# -------------------------------

def monitor_clipboard(args):
    print("🔍 SnapAssist AI is running... Press Ctrl+C to stop.")
    last_hash = None

    while True:
        try:
            image_bytes = get_clipboard_image_bytes()
            if image_bytes:
                current_hash = hashlib.md5(image_bytes).hexdigest()
                if current_hash != last_hash:
                    last_hash = current_hash
                    print("📸 Screenshot detected. Processing...")

                    text = extract_text_from_image(image_bytes)
                    if not text:
                        print("⚠️ No text found in the screenshot.")
                        time.sleep(args.poll_interval)
                        continue

                    qtype = classify_question(text)
                    difficulty = detect_difficulty(text)

                    print(f"🧠 Detected Question Type: {qtype}, Difficulty: {difficulty}")
                    response = generate_hints(text, qtype, difficulty, args)

                    response_queue.put(response)

            time.sleep(args.poll_interval)
        except KeyboardInterrupt:
            print("\n🛑 SnapAssist AI stopped.")
            break
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(max(1.0, args.poll_interval))


# -------------------------------
# 6. Fixed Window GUI (optional)
# -------------------------------

class FixedWindow:
    def __init__(self, root):
        root.title("SnapAssist AI - Hints")
        root.geometry("500x400+100+100")
        root.configure(bg="white")

        frame = tk.Frame(root, bg="white", padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        self.text_widget = tk.Text(
            frame, wrap="word", bg="white", fg="black", font=("Helvetica", 16)
        )
        self.text_widget.config(state="disabled")
        self.text_widget.pack(fill="both", expand=True)

    def show(self, response):
        if not self.text_widget.winfo_exists():
            return
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", response)
        self.text_widget.config(state="disabled")


def gui_loop():
    if tk is None:
        print("[GUI] tkinter not available. Running in headless mode.")
        # Headless: print responses as they arrive
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

    root = tk.Tk()
    app = FixedWindow(root)

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
    parser.add_argument("--provider", choices=["ollama", "gemini"], default=None, help="Force provider (overrides env HINTIFY_PROVIDER)")
    parser.add_argument("--ollama-model", default=os.getenv("HINTIFY_OLLAMA_MODEL", "llama3.2:3b"), help="Ollama model to use")
    parser.add_argument("--gemini-model", default=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), help="Gemini model to use")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Pre-flight checks
    ensure_tesseract_binary()
    if not have_ollama():
        print("[Info] Ollama not detected. To install: macOS 'brew install ollama', Windows 'winget install Ollama.Ollama', Linux see https://ollama.com/download")
        # Offer Gemini onboarding if no key is configured
        stored_key = keyring.get_password("hintify", "gemini_api_key")
        if not os.getenv("GEMINI_API_KEY") and not stored_key:
            print("[Setup] You can use Google's Gemini as an alternative.")
            try:
                choice = input("Open Gemini API key page in your browser now? [Y/n]: ").strip().lower()
            except Exception:
                choice = "y"
            if choice in ("", "y", "yes"): 
                try:
                    webbrowser.open("https://aistudio.google.com/apikey", new=2)
                    print("[Setup] Opened: https://aistudio.google.com/apikey")
                except Exception as e:
                    print(f"[Setup] Please visit https://aistudio.google.com/apikey (auto-open failed: {e})")
            try:
                pasted = input("Paste your Gemini API key here (or press Enter to skip): ").strip()
            except Exception:
                pasted = ""
            if pasted:
                os.environ["GEMINI_API_KEY"] = pasted
                try:
                    keyring.set_password("hintify", "gemini_api_key", pasted)
                    print("[Setup] Gemini API key saved securely to system keychain.")
                except Exception as e:
                    print(f"[Setup] Could not save key to keychain: {e}")
                if not args.provider:
                    args.provider = "gemini"
                print("[Setup] GEMINI_API_KEY set for this session. To persist, export it in your shell profile.")
        elif stored_key and not os.getenv("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = stored_key
            if not args.provider:
                args.provider = "gemini"
            print("[Setup] Using Gemini API key from system keychain.")

    # Start threads
    Thread(target=monitor_clipboard, args=(args,), daemon=True).start()

    if args.no_gui:
        # Headless loop that prints responses
        try:
            while True:
                try:
                    response = response_queue.get(timeout=0.5)
                    if response:
                        print("\n📘 Hints:\n" + response + "\n")
                except Exception:
                    pass
        except KeyboardInterrupt:
            pass
    else:
        gui_loop()
