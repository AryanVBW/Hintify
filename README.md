# 📘 SnapAssist AI – Real-time Study Assistant

SnapAssist AI is a **real-time AI-powered study assistant** that helps students solve problems independently by giving **progressive hints instead of direct answers**.

Students can take a **screenshot of a question** (from assignments, PDF notes, practice exams, etc.), and SnapAssist will:

* Detect the screenshot from the clipboard.
* Extract text via OCR.
* Classify the question (MCQ or Descriptive).
* Estimate difficulty.
* Query an AI model (via Ollama) to generate **stepwise hints**.
* Display hints in a **non-intrusive overlay GUI**.

---

## ✨ Features

* 📸 **Real-time Screenshot Detection** – Monitors clipboard continuously.
* 🔎 **OCR Integration** – Extracts text from images using Tesseract.
* 🧩 **Question Classification** – Detects MCQs vs. descriptive questions.
* ⚖️ **Difficulty Estimation** – Lightweight heuristic (Easy/Medium/Hard).
* 🤖 **AI Hint Generation** – Uses Ollama with `granite3.2-vision:2b`.
* 🖼️ **Overlay GUI** – Always-on-top Tkinter overlay for hints.
* 🔄 **Concurrency** – Clipboard monitoring and GUI run in parallel threads.
* 🎯 **Learning-first Approach** – Only hints, never full answers.

---

## 🛠 Tech Stack

**Languages & Libraries**

* `Python`
* `pytesseract` → OCR
* `PIL.Image` → Image handling
* `AppKit`, `Foundation` → macOS clipboard
* `tkinter` → GUI overlay
* `queue`, `threading` → Async communication

**External Tools**

* **Tesseract OCR** → Text recognition
* **Ollama** → Local AI inference with `granite3.2-vision:2b`

---

## ⚙️ Workflow

1. Student takes a screenshot (`⌘+Shift+4` on Mac).
2. Screenshot copied to clipboard.
3. SnapAssist detects it → runs OCR.
4. Text classified (MCQ / Descriptive / Not a Question).
5. Difficulty estimated.
6. Ollama queried → structured prompt sent.
7. Progressive hints generated (Concept → Formula → Setup → Nudge).
8. Overlay GUI displays hints.
9. Student solves independently.

---

## 🔄 Flowchart

<img width="616" height="414" alt="image" src="https://github.com/user-attachments/assets/52f7f789-64e1-451b-9bfb-50ac9fd4732c" />


---

## 📂 Key Modules

* **Clipboard Detection & OCR** → Extracts text from screenshots.
* **Question Classification** → Identifies MCQs vs. descriptive questions.
* **Difficulty Estimation** → Easy, Medium, Hard.
* **Hint Generation** → AI-driven hints only.
* **GUI Overlay** → Non-intrusive, semi-transparent Tkinter window.
* **Concurrency** → Background thread for monitoring + main thread for GUI.

---

## 🚀 Possible Extensions

* ✅ Windows/Linux clipboard support.
* ✅ Smarter difficulty detection (NLP-based).
* ✅ Text-to-speech for audio hints.
* ✅ Local hint history log for revision.
* ✅ Chrome extension integration.
* ✅ Multi-language OCR.

---

## 📌 Project Highlights

* 🔄 **Real-time monitoring** without user clicks.
* 🖼 **Overlay UI** that doesn’t interrupt workflow.
* 📚 **Learning-first** – Encourages solving, not spoon-feeding.
* 🔗 **Cross-cutting design** – Combines OCR, NLP, GUI.
* 🛠 **Extensible** – Swap models, add features, redesign UI easily.
