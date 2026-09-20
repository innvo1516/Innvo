# ⚡ Innvo - Cross-Platform Local RL AI Assistant

**Innvo** is a personal AI assistant (like Jarvis) engineered for **low-end hardware (laptops and Android phones)** with **zero paid APIs**, **bilingual Hindi & English support**, **free internet search**, and an **interactive Reinforcement Learning (RL) memory engine**.

---

## 🌟 Key Features

1. **Zero Cloud/API Fees**: Operates 100% locally or using free protocols (DuckDuckGo search, Wikipedia REST, Edge Neural TTS).
2. **Interactive RL Memory**:
   - Innvo listens and extracts candidate facts, preferences, and rules.
   - **Asks for user approval before saving**: *"Bhai, maine notice kiya ki aapne bola: '...'. Kya main ise apni permanent memory me save kar lu? (Haan/Nahi)"*
   - Positive feedback (`Haan` / `Yes`) gives **+1.0 Reward** and boosts the memory's Q-value.
   - Rejection (`Nahi` / `No`) discards candidate and records a negative penalty.
   - Corrections trigger **Reflexion** and update behavioral constraints.
3. **Hyper-Realistic Indian Voice**:
   - **Default Voice**: `hi-IN-MadhurNeural` (deep, natural Indian male voice).
   - **Android (Termux)**: Native `termux-tts-speak` for zero-overhead speech.
   - **Offline Fallback**: Windows SAPI5 (`pyttsx3`).
4. **Free Live Internet Search**:
   - Real-time web info via DuckDuckGo and Wikipedia without needing any API keys.
5. **Ultra-Lightweight Sci-Fi TUI**:
   - Built with `Rich`.
   - Runs directly in Windows Terminal/PowerShell and Android Termux using less than **40 MB RAM**.

---

## 🚀 Running on Windows Laptop

### 1. Start Innvo in Voice & Terminal Mode
```bash
# Standard interactive mode (type 'v' or press Enter to speak into mic)
python main.py

# Continuous Hands-Free Voice Mode (Innvo speaks, then listens to you automatically)
python main.py --continuous

# Text-only mode (No speech output)
python main.py --no-voice
```

---

## 🎙️ How to Talk with Your Voice

When Innvo is running:
- Type **`v`** or **`/listen`** and press Enter.
- The terminal will display: `🎙️ Listening... (Speak naturally in Hindi, English, or Hinglish)`.
- Speak into your microphone (e.g. *"Innvo, kal mera birthday hai"* or *"What is ISRO?"*).
- Innvo transcribes your voice, thinks via local Ollama (`gemma2:2b`), searches the internet if needed, updates RL memory, and **speaks back to you using `hi-IN-MadhurNeural`**!
- Type **`/continuous`** to toggle hands-free conversation mode where Innvo automatically listens after every response!

---

## 📱 Running on Android Phone (via Termux)

### Step 1: Install Termux & Termux:API
1. Install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/).
2. Install **Termux:API** from F-Droid.

### Step 2: Setup in Termux
Open Termux and run:
```bash
pkg update && pkg upgrade -y
pkg install python git termux-api -y
```

### Step 3: Clone or Copy Innvo & Install
```bash
git clone https://github.com/your-username/Innvo.git
cd Innvo
pip install -r requirements.txt
python main.py
```

---

## 🛠️ In-App Commands

While chatting with Innvo in the terminal, you can type:
- `/tools` — View all active built-in and self-developed tools with their RL Q-scores.
- `/context` — View active multi-turn conversation history.
- `/clear` — Reset active conversation context (start a fresh topic).
- `/memories` — View all permanently approved memories and their RL Q-scores.
- `/stats` — View Reinforcement Learning performance metrics.
- `/voice on` / `/voice off` — Toggle Indian Neural Voice.
- `/help` — Show help menu.
- `exit` or `alvida` — Shutdown Innvo.

---

## ⚡ Self-Developing Tools & Skill Synthesis

Innvo can write new tools for itself on the fly:
1. Simply ask: *"Innvo, ek naya tool banao jo mere laptop ki IP address nikaale"*
2. Innvo synthesizes a Python tool, tests it in its execution sandbox, and verifies the output.
3. Innvo asks for your approval:
   > *"Sir, maine 'ip_fetcher' tool develop kiya hai. Test output: '192.168.1.5'. Kya main ise permanent skill library me save kar lu? (Haan/Nahi)"*
4. Say **"Haan"** $\rightarrow$ It gets saved to `tools/dynamic/` and registered with a **+1.0 RL Q-score** for immediate reuse!
