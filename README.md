# 🎓 StudyBot – Multimodal AI Study & Exam Assistant

A local AI study assistant built with Python, Streamlit, LangChain, and Groq LLMs. StudyBot processes document notes (PDFs) and exam images (JPG/PNG via local OCR) to generate study plans, SOS exam topic predictions, self-assessment quizzes, interactive flashcards, and real-time chat support.

---

## 🌟 Key Features

- 📄 **Multimodal Ingestion:** Unified support for both PDFs and images (JPG, PNG).
- 🔍 **Local OCR Engine:** Integrates Tesseract OCR (`pytesseract`) for Greek & English text extraction from photos.
- 🛡️ **Dynamic LLM Routing & Failover:** Dynamically queries available Groq API models (e.g., `llama-3.3-70b-versatile`) to prevent API 404/model errors.
- ⚡ **LLM Telemetry:** Real-time API latency tracking for model response monitoring.
- 🎴 **Active Recall & E-Learning Tools:**
  - **SOS Predictor:** Highlights top exam topics & 3-step action plans with multi-format exports (`.txt`, `.md`).
  - **5-Question Quiz Generator:** Auto-generated multiple-choice tests with answer keys.
  - **Interactive Flashcards:** Flashcard system for rapid self-assessment.
  - **Live Chatbot:** Context-aware assistant memory.

---

## 🏗️ Architecture Overview

```text
[User Uploads: PDFs / Images]
              │
              ▼
 [PyPDF Engine / Tesseract OCR]
              │
              ▼
[Unified Text Context Aggregation]
              │
              ▼
[Dynamic Groq LLM Router (Llama-3.3 70B)]
              │
              ▼
  [Streamlit Interactive UI]
