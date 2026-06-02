

# 🚀 **Offline Multimodal Hybrid RAG System**

### *(Electron Desktop App + Django API Gateway + FastAPI AI-Service)*

### **Smart India Hackathon 2025 – Grand Finale**

---

## 📌 **Overview**

This project is a fully offline, multimodal **Retrieval-Augmented Generation (RAG)** system that can ingest, index, and semantically search across **PDF, DOCX, images, screenshots, and audio recordings** in a unified framework.

The system supports:

* 🔍 **Text-to-Image search**
* 🖼 **Image-to-Text search**
* 🎧 **Audio-to-Text & cross-modal search**
* 🤖 **Grounded LLM answers with citations**
* 🖥 **Desktop-first UI (Electron)** for secure government/offline environments

This architecture ensures zero cloud dependency, making it ideal for confidential use cases and environments with restricted internet access.

---

# 🧠 **Key Features**

### **✓ Offline Multimodal RAG**

Works fully offline with local embeddings, local vector DB, local LLM.

### **✓ Multimodal Ingestion**

Supports:

* PDF → text + HTML
* DOCX → structured text
* Image → OCR + CLIP embedding
* Audio → Whisper transcription
* Screenshot → semantic description

### **✓ Hybrid Retrieval Engine**

* FAISS for fast vector search
* Neo4j for cross-modal & cross-document relationships
* Reciprocal Rank Fusion (RRF) for merging top-K results

### **✓ Offline LLM Reasoning**

* Qwen / LLaMA3 / Mistral (GGUF)
* Chain-of-Thought (CoT)
* Grounded citations (`[CIT1]`, `[CIT2]`)

### **✓ Electron Desktop UI**

* Chat-based interface
* Drag-and-drop file upload
* Citation expansion
* PDF preview, image preview, audio playback

---

# 🏗 **System Architecture**

```
Electron Desktop App
        │
        ▼
Django API Gateway (File Manager + Router)
        │
        ▼
FastAPI AI-Service (Ingestion + Embeddings + Retrieval + LLM)
        │
        ├── FAISS Vector Store   (text/image/audio embeddings)
        ├── Neo4j Graph Store    (cross-modal links)
        └── MongoDB Metadata     (raw text, transcripts, OCR)
```

---

# 📂 **Project Structure**

```
sih-multimodal-rag/
│
├── frontend/               # Electron Desktop App (UI)
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/                # Django API Gateway
│   ├── core/
│   ├── api/
│   ├── media/
│   └── manage.py
│
├── ai-service/             # FastAPI Multimodal RAG Engine
│   ├── app/
│   │   ├── services/       # Ingestion + embeddings + RAG
│   │   ├── models/
│   │   ├── utils/
│   │   └── main.py
│   ├── vector_store/
│   ├── graph_store/
│   ├── raw_data/
│   └── models/             # Local LLM + embedding models
│
└── docs/                   # Reports, diagrams, PPT
```

---

# 🔧 **Tech Stack**

### **Frontend**

* Electron.js (Electron-Vite)
* React.js + TailwindCSS
* Axios for API communication

### **Backend (Gateway)**

* Django + Django REST Framework
* File manager, routing, metadata

### **AI-Service (Core RAG Engine)**

* FastAPI
* Whisper (speech-to-text)
* CLIP / SigLIP / BGE / Voyage embeddings
* FAISS vector database
* Neo4j graph database
* MongoDB metadata store
* Qwen / LLaMA / Mistral LLMs (offline GGUF)

---

# 🚀 **How It Works (End-to-End Pipeline)**

### **1. Ingestion**

User uploads PDF/DOCX/Image/Audio via Electron → Django → AI-Service
AI-Service extracts:

* Text
* OCR text
* Image embeddings
* Audio transcripts
* Metadata (page, timestamp, file origin)

### **2. Indexing**

* All embeddings stored in FAISS
* Entities and relationships stored in Neo4j
* Raw content stored in MongoDB

### **3. Querying**

User asks a question → Django → AI-Service:

AI-Service:

1. Converts query to embedding
2. Runs parallel search:

   * FAISS text
   * FAISS image
   * FAISS audio
   * Neo4j graph traversal
3. Applies RRF fusion
4. Builds multimodal context

### **4. LLM Reasoning**

LLM generates a grounded answer with citations linking back to:

* Pages
* Image snippets
* Audio timestamps

### **5. UI Display**

Electron shows:

* Final answer
* Citations
* Source preview

---

# 🛠 **Installation Guide**

## **1. Clone the repo**

```bash
git clone https://github.com/your-org/sih-multimodal-rag.git
cd sih-multimodal-rag
```

## **2. Setup Electron Frontend**

```bash
cd frontend
npm install
npm run dev
```

## **3. Setup Django Backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## **4. Setup AI-Service**

```bash
cd ai-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

# 🧪 **Sample Query Examples**

### **Text Query**

> "Find the report which mentions international development in 2024."

### **Image Query**

Drag & drop a screenshot → retrieve matching documents + audio notes.

### **Audio Query**

Speak:

> "Find the audio part where they discussed budget allocations."

---

# 🏅 **Why This Solution Stands Out (SIH Ready)**

* Full offline capability
* Multimodal ingestion + reasoning
* Graph-enhanced retrieval (rare + powerful)
* Grounded citations (transparency)
* Desktop-secure UI
* Modular architecture (easy teamwork)
* Real-world applications in:

  * Government
  * Research labs
  * Legal & compliance
  * Defense environments

---

# 🧑‍🤝‍🧑 **Team Members & Module Division**

✔ Ingestion Engine – Member 1
✔ Embedding + FAISS – Member 2
✔ Graph Store – Member 3
✔ Retrieval + Fusion – Member 1 & 2
✔ LLM Reasoning – Member 3
✔ Django Backend – Backend/Fullstack
✔ Electron UI – Frontend

---
## Future Enhancements

- Multi-language document support
- Improved OCR accuracy
- Video file ingestion support

---

# 📜 **License**

MIT License © 2025


