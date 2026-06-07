<div align="center">
  <br/>
  <pre>

███╗   ███╗ ██████╗ ███████╗ ██████╗
████╗ ████║██╔═══██╗██╔════╝██╔═══██╗
██╔████╔██║██║   ██║███████╗██║   ██║
██║╚██╔╝██║██║   ██║╚════██║██║   ██║
██║ ╚═╝ ██║╚██████╔╝███████║╚██████╔╝
╚═╝     ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝

  </pre>
  <h1>MOSO AI</h1>
  <h3>Privacy-First · Local-First · Adaptive Artificial Intelligence</h3>
  <br/>
</div>

<p align="center">
  <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-8A2BE2?style=flat-square" alt="Architecture"/></a>
  <a href="#-core-components"><img src="https://img.shields.io/badge/Components-00B4D8?style=flat-square" alt="Components"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/Tech%20Stack-00C853?style=flat-square" alt="Tech Stack"/></a>
  <a href="#-getting-started"><img src="https://img.shields.io/badge/Getting%20Started-FF6D00?style=flat-square" alt="Getting Started"/></a>
  <a href="#-roadmap"><img src="https://img.shields.io/badge/Roadmap-E91E63?style=flat-square" alt="Roadmap"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-FFB300?style=flat-square" alt="License"/></a>
</p>

<p align="center">
  <b>English</b> •
  <a href="docs/i18n/README.zh.md">中文</a> •
  <a href="docs/i18n/README.ja.md">日本語</a> •
  <a href="docs/i18n/README.ko.md">한국어</a>
</p>

---

> **MOSO** (M0S0) is a privacy-first, local-first adaptive AI assistant that runs entirely on your device. It learns from your behavior, adapts to your preferences, and grows with you — without ever compromising your privacy.

<br/>

<div align="center">
  <table>
    <tr>
      <td align="center"><b>App</b></td>
      <td align="center"><b>Engine</b></td>
      <td align="center"><b>Persona</b></td>
      <td align="center"><b>Memory</b></td>
    </tr>
    <tr>
      <td align="center">MOSO App</td>
      <td align="center">MOSO Core</td>
      <td align="center">M0S0</td>
      <td align="center">MoSo Memory Engine</td>
    </tr>
  </table>
</div>

<br/>

---

## ✦ Philosophy

MOSO AI is built on a simple belief: **AI should adapt to you, not the other way around.**

| Principle | Meaning |
|-----------|---------|
| **Privacy-First** | Everything runs locally. Your data never leaves your device unless you explicitly choose to sync. |
| **Local-First** | Full AI capability offline. No cloud dependency for core functionality. |
| **Adaptive** | Learns from your behavior, habits, and preferences to become more helpful over time. |
| **Cross-Platform** | One AI, every device — Android, iOS, macOS, Windows, Linux. |
| **Modular** | Every component is a pluggable module. Swap models, change engines, extend functionality. |

---

## ✦ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        MOSO APP                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Android  │  │   iOS    │  │  macOS   │  │ Windows  │   │
│  │  (Kotlin)│  │ (SwiftUI)│  │  (Swift) │  │  (C#/UI) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └──────────────┼──────────────┼──────────────┘        │
│                      └──────┬──────┘                        │
│                    ┌────────┴────────┐                      │
│                    │  Flutter Shell  │                      │
│                    └────────┬────────┘                      │
└─────────────────────────────┼──────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────┐
│                    MOSO CORE (AI Runtime)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ llama.cpp│ │  ONNX    │ │  CoreML  │ │   MLX/ET    │  │
│  │  (CPU)   │ │ (GPU/CPU)│ │ (Neural) │ │  (Apple/MC) │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Pipeline Orchestrator                      │  │
│  │  [Text] [Voice] [Image] [Multimodal] [Reasoning]     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────┼──────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────┐
│                  MoSo MEMORY ENGINE                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Episodic │ │ Semantic │ │Procedural│ │  Preference   │  │
│  │  Memory  │ │  Memory  │ │  Memory  │ │   Learning    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │  Vector  │ │    RAG   │ │Summariza-│                   │
│  │    DB    │ │ Retrieval│ │  tion    │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────┼──────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────┐
│              SHARED ENGINES + BACKEND                       │
│  [AI Engine] [Emotion] [Behavior] [Recommendation]         │
│  [Sync] [Encryption] [Analytics]                           │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Gateway  │ │   Auth   │ │   Sync   │ │  WebSocket   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✦ Core Components

### MOSO Core

The foundational AI runtime that powers all inference across platforms.

| Module | Description | Backends |
|--------|-------------|----------|
| **Inference** | Unified model inference layer | llama.cpp, ONNX Runtime, CoreML, MLX, ExecuTorch |
| **Pipelines** | Modality-specific processing | Text, Voice, Image, Multimodal, Reasoning |
| **Orchestration** | Dynamic pipeline composition | Priority scheduling, model routing, fallback chains |
| **Agents** | Autonomous task execution | Goal decomposition, tool use, self-reflection |
| **Safety** | Content filtering and guardrails | Prompt injection detection, output sanitization |

### M0S0 Assistant

The conversational personality layer that makes MOSO feel alive.

- **Adaptive Personality** — Shifts tone and style based on user context
- **Emotional Intelligence** — Detects and adapts to emotional states
- **Contextual Awareness** — Remembers past conversations and preferences
- **Voice-First Interaction** — Natural conversation with wake word support

### MoSo Memory Engine

A three-tier memory system inspired by human cognition.

| Memory Type | Function | Storage |
|-------------|----------|---------|
| **Episodic** | Personal experiences and conversations | SQLite + Vector DB |
| **Semantic** | Facts, knowledge, and concepts | Vector DB (ChromaDB/LanceDB) |
| **Procedural** | Skills, habits, and routines | Behavioral model + SQLite |

### Voice System

Full-duplex voice interaction pipeline.

```
Microphone → Wake Word → Whisper STT → AI Processing → Coqui TTS → Speaker
```

### Vision System

On-device visual understanding without cloud calls.

- **CLIP Embeddings** — Zero-shot image classification and search
- **LLaVA** — Image understanding and description
- **OCR** — Text extraction from images
- **Multimodal Reasoning** — Combine vision + text for deep understanding

### Recommendation Engine

Behavioral AI that helps you be more productive.

- **Behavioral Scoring** — Models your daily patterns
- **Habit Tracking** — Identifies and reinforces positive habits
- **Adaptive Recommendations** — Suggests actions based on context
- **Productivity Optimization** — Learns your peak focus times

---

## ✦ Tech Stack

<table>
  <tr>
    <th>Layer</th>
    <th>Technology</th>
    <th>Purpose</th>
  </tr>
  <tr>
    <td rowspan="3"><b>Frontend</b></td>
    <td>Flutter</td>
    <td>Cross-platform UI shell</td>
  </tr>
  <tr>
    <td>SwiftUI</td>
    <td>Native Apple platform optimization</td>
  </tr>
  <tr>
    <td>Kotlin Multiplatform</td>
    <td>Shared business logic</td>
  </tr>
  <tr>
    <td rowspan="5"><b>AI Runtime</b></td>
    <td>llama.cpp</td>
    <td>CPU-optimized LLM inference</td>
  </tr>
  <tr>
    <td>ONNX Runtime</td>
    <td>Cross-platform model execution</td>
  </tr>
  <tr>
    <td>CoreML</td>
    <td>Apple Neural Engine acceleration</td>
  </tr>
  <tr>
    <td>MLX</td>
    <td>Apple Silicon-optimized ML framework</td>
  </tr>
  <tr>
    <td>ExecuTorch</td>
    <td>On-device PyTorch execution</td>
  </tr>
  <tr>
    <td rowspan="4"><b>Models</b></td>
    <td>Phi-3 Mini / Gemma 2B / Llama 3.2</td>
    <td>On-device LLM</td>
  </tr>
  <tr>
    <td>Whisper Tiny/Base</td>
    <td>Speech-to-text</td>
  </tr>
  <tr>
    <td>Coqui / Piper TTS</td>
    <td>Text-to-speech</td>
  </tr>
  <tr>
    <td>CLIP / LLaVA</td>
    <td>Vision understanding</td>
  </tr>
  <tr>
    <td rowspan="3"><b>Memory</b></td>
    <td>SQLite</td>
    <td>Relational memory storage</td>
  </tr>
  <tr>
    <td>ChromaDB / LanceDB</td>
    <td>Vector embeddings & retrieval</td>
  </tr>
  <tr>
    <td>HNSWLIB</td>
    <td>Approximate nearest neighbor search</td>
  </tr>
  <tr>
    <td rowspan="4"><b>Backend</b></td>
    <td>FastAPI (Python)</td>
    <td>Sync & cloud APIs</td>
  </tr>
  <tr>
    <td>Rust</td>
    <td>High-performance microservices</td>
  </tr>
  <tr>
    <td>PostgreSQL</td>
    <td>Cloud persistence</td>
  </tr>
  <tr>
    <td>Redis</td>
    <td>Caching & pub/sub</td>
  </tr>
  <tr>
    <td rowspan="4"><b>DevOps</b></td>
    <td>Docker</td>
    <td>Containerized services</td>
  </tr>
  <tr>
    <td>GitHub Actions</td>
    <td>CI/CD pipelines</td>
  </tr>
  <tr>
    <td>Terraform</td>
    <td>Cloud infrastructure</td>
  </tr>
  <tr>
    <td>Cloudflare Tunnel</td>
    <td>Secure ingress</td>
  </tr>
</table>

---

## ✦ Repository Structure

```
moso-ai/
├── apps/                    # Platform applications
│   ├── android/             # Android (Kotlin + Flutter)
│   ├── ios/                 # iOS (SwiftUI + Flutter)
│   ├── macos/               # macOS native app
│   ├── windows/             # Windows desktop app
│   └── linux/               # Linux desktop app
├── shared/                  # Cross-platform shared engines
│   ├── ai-engine/           # Core AI logic
│   ├── memory-engine/       # Memory interfaces
│   ├── prompt-engine/       # Prompt management
│   ├── emotion-engine/      # Emotional tone adaptation
│   ├── behavior-engine/     # Behavioral modeling
│   ├── recommendation-engine/ # Recommendation system
│   ├── sync-engine/         # Zero-knowledge sync
│   ├── encryption/          # Cryptographic utilities
│   └── analytics/           # Privacy-preserving analytics
├── moso-core/               # Core AI inference runtime
│   ├── inference/           # Model backends
│   ├── pipelines/           # Modality pipelines
│   ├── orchestration/       # Pipeline composition
│   ├── scheduler/           # Resource scheduling
│   ├── agents/              # Agent system
│   └── safety/              # Guardrails & filtering
├── moso-memory-engine/      # Memory & retrieval system
│   ├── episodic-memory/     # Conversation & experience memory
│   ├── semantic-memory/     # Knowledge & facts memory
│   ├── procedural-memory/   # Habit & skill memory
│   ├── embeddings/          # Embedding generation
│   ├── vector-db/           # Vector database adapters
│   ├── retrieval/           # RAG retrieval pipeline
│   ├── summarization/       # Memory summarization
│   └── personalization/     # User preference learning
├── models/                  # AI model configurations
│   ├── llm/                 # Language models
│   ├── speech/              # STT & TTS models
│   ├── vision/              # Vision models
│   └── embeddings/          # Embedding models
├── backend/                 # Cloud backend services
│   ├── gateway/             # API gateway
│   ├── auth/                # Authentication
│   ├── sync/                # Data sync service
│   ├── notifications/       # Push notifications
│   ├── telemetry/           # Anonymous telemetry
│   ├── websocket/           # Real-time communication
│   └── api/                 # REST & GraphQL APIs
├── cloud/                   # Cloud infrastructure
│   ├── aws/                 # AWS configurations
│   ├── gcp/                 # GCP configurations
│   ├── cloudflare/          # Cloudflare configs
│   └── firebase/            # Firebase configs
├── docs/                    # Documentation
│   ├── architecture/        # Architecture docs
│   ├── api/                 # API reference
│   ├── memory-system/       # Memory system docs
│   ├── prompts/             # Prompt engineering guides
│   └── research/            # Research papers & notes
├── scripts/                 # Build & utility scripts
├── datasets/                # Training & evaluation datasets
├── tests/                   # All test suites
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── performance/         # Benchmarks
│   ├── ai-evaluation/       # Model eval
│   └── security/            # Security tests
└── tools/                   # Developer tools
    ├── prompt-debugger/     # Prompt testing tool
    ├── memory-inspector/    # Memory inspection
    ├── embedding-viewer/    # Embedding visualization
    └── model-manager/       # Model download & management
```

---

## ✦ Getting Started

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Git | 2.40+ | Version control |
| Flutter SDK | 3.16+ | Cross-platform UI |
| Python | 3.11+ | ML pipelines & backend |
| Rust | 1.75+ | Native modules |
| Docker | 24+ | Backend services |

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Harsha240105/MOSO.git
cd moso-ai

# Set up environment
cp .env.example .env

# Install Python dependencies
pip install -r backend/requirements.txt

# Download a model (example)
python scripts/model-download/download_phi3.py

# Run backend services (optional, for sync features)
docker compose up -d

# Run the Flutter app
cd apps/android  # or apps/ios, apps/macos
flutter run
```

### Model Downloads

MOSO AI uses quantized GGUF models optimized for on-device inference.

```bash
# List available models
python scripts/model-download/list_models.py

# Download a specific model
python scripts/model-download/download_model.py --model phi-3-mini-4k-instruct-q4
```

---

## ✦ Configuration

MOSO is configured via environment variables or a `.env` file:

```env
# Model Selection
MOSO_LLM_MODEL=phi-3-mini-4k-instruct-q4.gguf
MOSO_WHISPER_MODEL=base
MOSO_TTS_MODEL=piper

# Memory Engine
MEMORY_VECTOR_DB=chroma
MEMORY_RAG_TOP_K=5

# Privacy
SYNC_ENABLED=false
TELEMETRY_OPT_IN=false
```

---

## ✦ Building from Source

### Android

```bash
cd apps/android
./gradlew assembleRelease
```

### iOS

```bash
cd apps/ios
xcodebuild -scheme MOSOApp -configuration Release
```

### macOS

```bash
cd apps/macos
xcodebuild -scheme "MOSO macOS" -configuration Release
```

### Windows

```bash
cd apps/windows
dotnet publish -c Release
```

---

## ✦ Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture/OVERVIEW.md) | System architecture and design decisions |
| [Memory System](docs/memory-system/OVERVIEW.md) | How MoSo Memory Engine works |
| [API Reference](docs/api/REFERENCE.md) | Backend API documentation |
| [Prompt Engineering](docs/prompts/GUIDE.md) | Crafting effective prompts for M0S0 |
| [Deployment](docs/deployment/GUIDE.md) | Production deployment guide |
| [Privacy](docs/privacy/WHITEPAPER.md) | Privacy architecture whitepaper |

---

## ✦ Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/ai-evaluation/

# Run benchmarks
python tests/performance/benchmark.py
```

---

## ✦ License

MOSO AI is released under the [MIT License](LICENSE).

---

## ✦ Acknowledgments

Built with love for privacy, open source AI, and the belief that intelligence should be personal.

<p align="center">
  <sub>Made with ❤️ by the MOSO team</sub>
  <br/>
  <sub>© 2024-2025 MOSO AI. All rights reserved.</sub>
</p>
