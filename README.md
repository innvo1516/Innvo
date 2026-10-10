# ⚡ Innvo - Cross-Platform Local Autonomous AI Companion

**Innvo** is a personal AI companion (like Jarvis) engineered to run across **all your devices (Windows laptop, Android phone, Linux / Raspberry Pi, Mac, and embedded satellites)** with:
- **Zero Paid APIs / 100% Free**: Operates locally or via free protocols.
- **Constitutional Security & Dual Kill-Switch Tripwires**: Tamper-proof rulebook & poison-pill memory boundary.
- **Air-Gapped Shadow Brain Cold Vault**: Encrypted snapshots recoverable via a 12-word seed phrase.
- **Bilingual Hindi & English Audio**: Natural Indian male neural voice (`hi-IN-MadhurNeural`) with offline fallbacks.
- **Interactive Reinforcement Learning (RL) Memory**: Learns facts & preferences only with human approval.
- **Self-Developing Dynamic Tools**: Writes, tests, and saves its own Python tools on the fly.
- **Semantic Knowledge Graph & Truth Triangulation**: Multi-source fact verification across DuckDuckGo and Wikipedia.
- **Autonomous Idle Curiosity**: Explores topics in background only when idle & plugged in (strictly opt-in switch `/idle on/off`).
- **Distributed Hive-Mind P2P Sync**: Lightweight micro-delta sync packets (< 50 KB) across devices.

---

## 💻 1. Running on Windows PC / Laptop

### Step 1: Install Requirements
1. Install **Python 3.10+** (if not already installed).
2. Install **Ollama** from [ollama.com](https://ollama.com/) and pull a lightweight model:
   ```powershell
   ollama run gemma2:2b
   ```

### Step 2: Clone & Install Dependencies
```powershell
git clone https://github.com/innvo1516/Innvo.git
cd Innvo
pip install -r requirements.txt
```

### Step 3: Run Innvo
```powershell
# Standard interactive mode (Voice + Rich Sci-Fi TUI)
python main.py

# Continuous Hands-Free Voice Mode (Automatic continuous listening loop)
python main.py --continuous

# Text-only mode (Silent, no audio output)
python main.py --no-voice
```

---

## 📱 2. Running on Android Phone (via Termux)

Runs 100% free on budget Android phones (2GB-4GB RAM) using Termux!

### Step 1: Install Termux & Termux:API
1. Download & install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/) *(do not use Google Play Store version as it is outdated)*.
2. Download & install **Termux:API** from [F-Droid](https://f-droid.org/en/packages/com.termux.api/).

### Step 2: 1-Click Setup
Open Termux and run:
```bash
pkg update -y && pkg install -y git
git clone https://github.com/innvo1516/Innvo.git
cd Innvo
chmod +x setup_termux.sh
./setup_termux.sh
```

### Step 3: Connect to Laptop Brain OR Run Standalone
- **Option A (Distributed Hive-Mind — Recommended for 0% Phone CPU usage)**:
  Make sure your phone and laptop are on the same Wi-Fi. Run:
  ```bash
  export OLLAMA_HOST=http://<YOUR_LAPTOP_IP>:11434
  python main.py
  ```
  *(To find your Laptop IP, run `ipconfig` in Windows PowerShell)*.

- **Option B (Fully Standalone on Phone)**:
  Run a quantized 1B/2B model directly inside Termux:
  ```bash
  python main.py
  ```

---

## 🐧 3. Running on Linux / Raspberry Pi / SBC (Smart Home / Car / Robot)

Ideal for Raspberry Pi 4/5, Orange Pi, Ubuntu servers, or smart vehicle hubs.

### 1-Click Setup:
```bash
git clone https://github.com/innvo1516/Innvo.git
cd Innvo
chmod +x setup_linux.sh
./setup_linux.sh
```

### Run as Foreground or Background Daemon:
```bash
# Foreground with terminal UI
python3 main.py

# Headless / Background service (e.g. for car/robot)
nohup python3 main.py --no-voice > innvo.log 2>&1 &
```

---

## 🍎 4. Running on Mac (macOS)

```bash
git clone https://github.com/innvo1516/Innvo.git
cd Innvo
pip3 install -r requirements.txt
python3 main.py
```

---

## 🌐 5. Distributed Hive-Mind Cross-Device Sync

Keep your laptop, phone, and Raspberry Pi brains synchronized without cloud servers:

1. **On Device 1 (e.g. Laptop)**:
   In the Innvo TUI, type:
   ```
   /sync
   ```
   This exports a lightweight micro-delta packet (`< 50 KB`) containing new memories, dynamic tools, and Knowledge Graph triples to `data/sync/`.

2. **On Device 2 (e.g. Phone)**:
   Send the micro-delta JSON file to the phone (via Bluetooth, local Wi-Fi, or Termux curl) and import it:
   ```bash
   python -c "from sync.sync_broker import SyncBroker; from pathlib import Path; SyncBroker().import_from_file(Path('sync_delta.json'))"
   ```

---

## 🛡️ Sovereign Human Operator Security CLI

You (the human operator) have exclusive sovereign control over Innvo's constitution and cold recovery:

```bash
# 1. View all 5 constitutional laws
python security/admin_cli.py view-rules

# 2. Generate a 12-word master recovery phrase
python security/admin_cli.py generate-seed

# 3. Re-sign rules after manual edits to constitution.json
python security/admin_cli.py sign-rules

# 4. Verify constitutional cryptographic HMAC-SHA256 integrity
python security/admin_cli.py verify-rules

# 5. Take an encrypted cold backup snapshot
python security/admin_cli.py backup

# 6. Resurrect Innvo from shadow vault
python security/admin_cli.py resurrect
```

---

## 🕹️ In-App Terminal Commands

While chatting with Innvo, you can run any of the following commands:
- `v` or `/listen`: Activate microphone for Hindi/English speech
- `/continuous`: Toggle continuous hands-free voice loop
- `/rules`: View constitutional laws & kill-switch tripwires
- `/kg`: View semantic Knowledge Graph entity triples
- `/idle on` / `/idle off`: Toggle autonomous background idle learning
- `/sync`: Export a lightweight Hive-Mind Delta Sync packet
- `/vault`: Check air-gapped cold snapshot status
- `/tools`: View all active built-in & self-developed tools
- `/memories`: View all permanent memories and RL Q-scores
- `/context`: Inspect multi-turn short-term conversation context
- `/clear`: Clear active conversation context (start fresh topic)
- `/stats`: View Reinforcement Learning performance metrics
- `/voice on` / `/voice off`: Toggle Indian neural voice
- `/help`: Display help center
- `exit` or `alvida`: Shutdown Innvo
