# 🏛️ The Sovereign Desktop

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ollama](https://img.shields.io/badge/Ollama-Llama%203.2-green.svg)](https://ollama.ai/)

> **Your AI, Your Machine, Your Rules.**

A **local-first, offline-capable, multimodal Windows agent** that puts you in complete control. No cloud dependencies, no data leaving your machine, just pure AI-powered automation running entirely on your hardware.

---

## 🎯 Philosophy

### Local-First
Every component of The Sovereign Desktop is designed to run locally. Your data never leaves your machine. Your commands are processed on your hardware. Your privacy is absolute.

### Offline-Capable
After the initial model download, The Sovereign Desktop operates completely offline. No internet connection required for:
- Voice command processing
- Screen understanding and OCR
- Task execution and automation
- Conversation memory and context

### Multimodal Intelligence
Powered by **Llama 3.2 Vision** via **Ollama**, The Sovereign Desktop can:
- **See** your screen and understand UI elements
- **Listen** to your voice commands
- **Speak** responses naturally
- **Act** on your behalf with precision

### Python-Based OS Control
Built with Python for maximum extensibility and transparency. Every action the agent takes is:
- Auditable (full action logging)
- Customizable (plug-in architecture)
- Reversible (undo support where possible)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VOICE LOOP                               │
│    ┌─────────┐    ┌─────────────┐    ┌─────────────┐           │
│    │   STT   │───▶│  SEMANTIC   │───▶│    TTS      │           │
│    │(Whisper)│    │   ROUTER    │    │  (Piper)    │           │
│    └─────────┘    └──────┬──────┘    └─────────────┘           │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CORE                                     │
│    ┌─────────────────┐    ┌─────────────────────────┐           │
│    │   LLM ENGINE    │    │    CONTEXT MANAGER      │           │
│    │ (Ollama/Llama)  │    │  (Memory + State)       │           │
│    └─────────────────┘    └─────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
│   PERCEPTION    │ │  ACTUATORS  │ │   INTERFACES    │
│  ┌───────────┐  │ │ ┌─────────┐ │ │  ┌───────────┐  │
│  │  Vision   │  │ │ │ Windows │ │ │  │  Voice    │  │
│  │ Processing│  │ │ │ Control │ │ │  │   Loop    │  │
│  ├───────────┤  │ │ ├─────────┤ │ │  ├───────────┤  │
│  │ Listeners │  │ │ │  Audio  │ │ │  │   TTS     │  │
│  └───────────┘  │ │ ├─────────┤ │ │  ├───────────┤  │
│                 │ │ │ Browser │ │ │  │   STT     │  │
│                 │ │ └─────────┘ │ │  └───────────┘  │
└─────────────────┘ └─────────────┘ └─────────────────┘
```

---

## 📁 Project Structure

```
sovereign-desktop/
├── README.md                 # This file
├── pyproject.toml           # Project dependencies (Poetry)
├── requirements.txt         # Dependencies (pip)
├── config.yaml              # Main configuration
├── main.py                  # Entry point
│
├── core/                    # 🧠 Brain of the agent
│   ├── __init__.py
│   ├── llm_engine.py       # Ollama/Llama integration
│   ├── semantic_router.py  # Intent classification & routing
│   └── context_manager.py  # Memory and state management
│
├── perception/              # 👁️ Sensory input
│   ├── __init__.py
│   ├── vision.py           # Screen capture & processing
│   ├── ocr.py              # Text extraction from screen
│   └── listeners.py        # Event listeners (keyboard, mouse)
│
├── actuators/               # 🦾 Action execution
│   ├── __init__.py
│   ├── windows_control.py  # OS-level automation
│   ├── audio_control.py    # Audio/media management
│   └── browser_agent.py    # Web automation
│
├── interfaces/              # 🎙️ Human interaction
│   ├── __init__.py
│   ├── tts.py              # Text-to-Speech
│   ├── stt.py              # Speech-to-Text
│   └── voice_loop.py       # Continuous voice interaction
│
├── utils/                   # 🔧 Utilities
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── logging.py          # Logging infrastructure
│
└── tests/                   # ✅ Test suite
    ├── __init__.py
    ├── test_core/
    ├── test_perception/
    ├── test_actuators/
    └── test_interfaces/
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Ollama with Llama 3.2 Vision**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3.2-vision
   ```

3. **Windows 10/11** (primary target platform)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sovereign-desktop.git
cd sovereign-desktop

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure the agent
copy config.example.yaml config.yaml
# Edit config.yaml with your preferences
```

### Running

```bash
# Start the agent
python main.py

# Or with voice mode
python main.py --voice

# Or with debug logging
python main.py --debug
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
llm:
  model: "llama3.2-vision"
  host: "http://localhost:11434"
  temperature: 0.7
  context_length: 8192

voice:
  stt_model: "base"  # whisper model size
  tts_voice: "default"
  wake_word: null  # or "hey sovereign"
  push_to_talk_key: "ctrl+space"

vision:
  capture_interval: 1.0  # seconds
  ocr_enabled: true

logging:
  level: "INFO"
  file: "logs/sovereign.log"
  max_size_mb: 100
```

---

## 🔌 Extensibility

### Adding New Tools

1. Create a new module in the appropriate directory
2. Implement the standard tool interface
3. Register with the semantic router

```python
# actuators/my_custom_tool.py
from core.semantic_router import register_tool

@register_tool(
    name="my_tool",
    description="Does something useful",
    triggers=["do the thing", "make it happen"]
)
def my_custom_tool(params: dict) -> str:
    # Your implementation
    return "Done!"
```

---

## 🔒 Privacy & Security

- **100% Local Processing**: All AI inference runs on your machine
- **No Telemetry**: Zero data collection or phone-home behavior
- **Audit Trail**: Complete logging of all agent actions
- **Sandboxed**: Optional restricted mode for sensitive operations

---

## 📋 Roadmap

See [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) for the detailed development plan.

- [x] Phase 1: Environment Setup
- [ ] Phase 2: Tool Creation
- [ ] Phase 3: Router Implementation
- [ ] Phase 4: Voice Integration
- [ ] Phase 5: Polish & Release

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [Meta's Llama](https://llama.meta.com/) - The foundation model
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [Piper TTS](https://github.com/rhasspy/piper) - Local text-to-speech

---

<p align="center">
  <strong>The Sovereign Desktop</strong><br>
  <em>Your AI, Your Machine, Your Rules.</em>
</p>
