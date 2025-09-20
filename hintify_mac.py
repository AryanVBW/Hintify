import time
import re
import subprocess
import hashlib
from PIL import Image
from AppKit import NSPasteboard, NSPasteboardTypePNG
from Foundation import NSData
from io import BytesIO
import pytesseract
from threading import Thread
import tkinter as tk
import queue

response_queue = queue.Queue()

# -------------------------------
# 1. Screenshot Detection & OCR
# -------------------------------

def get_clipboard_image():
    pb = NSPasteboard.generalPasteboard()
    data = pb.dataForType_(NSPasteboardTypePNG)
    if data:
        image_data = NSData.dataWithData_(data)
        return bytes(image_data)
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

MCQ_PATTERN = re.compile(r"\(A\)|\(B\)|\(C\)|\(D\)|\d\)")

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
# 4. Hint Generation via Ollama
# -------------------------------

def query_ollama_for_hints(text, qtype, difficulty, model="granite3.2-vision:2b"):
    prompt = f"""
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
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[LLM Error] {e.stderr or str(e)}"

# -------------------------------
# 5. Main Clipboard Monitor
# -------------------------------

def monitor_clipboard():
    print("🔍 SnapAssist AI is running... Press Ctrl+C to stop.")
    last_hash = None

    while True:
        try:
            image_bytes = get_clipboard_image()
            if image_bytes:
                current_hash = hashlib.md5(image_bytes).hexdigest()
                if current_hash != last_hash:
                    last_hash = current_hash
                    print("📸 Screenshot detected. Processing...")

                    text = extract_text_from_image(image_bytes)
                    if not text:
                        print("⚠️ No text found in the screenshot.")
                        continue

                    qtype = classify_question(text)
                    difficulty = detect_difficulty(text)

                    print(f"🧠 Detected Question Type: {qtype}, Difficulty: {difficulty}")
                    response = query_ollama_for_hints(text, qtype, difficulty)

                    response_queue.put(response)

            time.sleep(1.5)  # slightly faster polling
        except KeyboardInterrupt:
            print("\n🛑 SnapAssist AI stopped.")
            break
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(2)

# -------------------------------
# 6. GUI Overlay
# -------------------------------

import time
import re
import subprocess
import hashlib
from PIL import Image
from AppKit import NSPasteboard, NSPasteboardTypePNG
from Foundation import NSData
from io import BytesIO
import pytesseract
from threading import Thread
import tkinter as tk
import queue

response_queue = queue.Queue()

# -------------------------------
# 1. Screenshot Detection & OCR
# -------------------------------

def get_clipboard_image():
    pb = NSPasteboard.generalPasteboard()
    data = pb.dataForType_(NSPasteboardTypePNG)
    if data:
        image_data = NSData.dataWithData_(data)
        return bytes(image_data)
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

MCQ_PATTERN = re.compile(r"\(A\)|\(B\)|\(C\)|\(D\)|\d\)")

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
# 4. Hint Generation via Ollama
# -------------------------------

def query_ollama_for_hints(text, qtype, difficulty, model="granite3.2-vision:2b"):
    prompt = f"""
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
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"[LLM Error] {e.stderr or str(e)}"

# -------------------------------
# 5. Main Clipboard Monitor
# -------------------------------

def monitor_clipboard():
    print("🔍 SnapAssist AI is running... Press Ctrl+C to stop.")
    last_hash = None

    while True:
        try:
            image_bytes = get_clipboard_image()
            if image_bytes:
                current_hash = hashlib.md5(image_bytes).hexdigest()
                if current_hash != last_hash:
                    last_hash = current_hash
                    print("📸 Screenshot detected. Processing...")

                    text = extract_text_from_image(image_bytes)
                    if not text:
                        print("⚠️ No text found in the screenshot.")
                        continue

                    qtype = classify_question(text)
                    difficulty = detect_difficulty(text)

                    print(f"🧠 Detected Question Type: {qtype}, Difficulty: {difficulty}")
                    response = query_ollama_for_hints(text, qtype, difficulty)

                    response_queue.put(response)

            time.sleep(1.5)  # slightly faster polling
        except KeyboardInterrupt:
            print("\n🛑 SnapAssist AI stopped.")
            break
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(2)

# -------------------------------
# 6. Fixed Window GUI
# -------------------------------

class FixedWindow:
    def __init__(self, root):
        root.title("SnapAssist AI - Hints")
        root.geometry("500x400+100+100")  # fixed size and position
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

if __name__ == "__main__":
    Thread(target=monitor_clipboard, daemon=True).start()
    gui_loop()
