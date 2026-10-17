def get_web_ui_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="theme-color" content="#0a0e17">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <title>Innvo AI Companion</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: #0a0e17; color: #f1f5f9; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    
    /* Header */
    header { background: #0f172a; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #1e293b; }
    .logo { display: flex; align-items: center; gap: 10px; font-weight: 800; letter-spacing: 2px; color: #00e5ff; font-size: 16px; }
    .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #00ff9d; box-shadow: 0 0 10px #00ff9d; }
    .btn-icon { background: none; border: none; color: #94a3b8; font-size: 20px; cursor: pointer; padding: 4px; }
    
    /* Orb Section */
    .orb-section { display: flex; justify-content: center; align-items: center; padding: 16px 0; background: linear-gradient(180deg, #0f172a 0%, #0a0e17 100%); }
    .orb { width: 100px; height: 100px; border-radius: 50%; background: radial-gradient(circle, #00ffd1 20%, #0088ff 60%, transparent 100%); box-shadow: 0 0 35px rgba(0,229,255,0.5); display: flex; align-items: center; justify-content: center; animation: pulse 3s infinite alternate; transition: all 0.3s ease; }
    .orb.thinking { animation: pulse-fast 1s infinite alternate; box-shadow: 0 0 50px rgba(0,255,157,0.8); background: radial-gradient(circle, #00ff9d 20%, #7000ff 70%, transparent 100%); }
    .orb-inner { width: 44px; height: 44px; border-radius: 50%; background: #0a0f1d; border: 2px solid #00e5ff; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #00e5ff; }
    
    @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.85; } 100% { transform: scale(1.05); opacity: 1; } }
    @keyframes pulse-fast { 0% { transform: scale(0.9); } 100% { transform: scale(1.15); } }
    
    /* Shortcut Pills */
    .pills-bar { display: flex; gap: 8px; overflow-x: auto; padding: 8px 14px; scrollbar-width: none; background: #0a0e17; }
    .pills-bar::-webkit-scrollbar { display: none; }
    .pill { background: #1e293b; color: #e2e8f0; font-size: 12px; padding: 6px 12px; border-radius: 20px; border: 1px solid rgba(0,229,255,0.2); white-space: nowrap; cursor: pointer; }
    .pill:active { background: #334155; }

    /* Chat Area */
    .chat-area { flex: 1; overflow-y: auto; padding: 14px; display: flex; flex-direction: column; gap: 12px; }
    .msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 15px; line-height: 1.4; word-wrap: break-word; }
    .msg-user { align-self: flex-end; background: #0284c7; color: #fff; border-bottom-right-radius: 4px; }
    .msg-bot { align-self: flex-start; background: #1e293b; color: #f1f5f9; border-bottom-left-radius: 4px; border: 1px solid #334155; }
    .badge { display: inline-block; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; background: rgba(0,255,157,0.15); color: #00ff9d; }

    /* Approval Card */
    .approval-card { background: #1e1b4b; border: 1.5px solid #818cf8; border-radius: 12px; padding: 12px; margin-top: 8px; }
    .approval-card p { font-size: 13px; color: #e0e7ff; margin-bottom: 8px; }
    .approval-btns { display: flex; justify-content: flex-end; gap: 8px; }
    .btn-approve { background: #00ff9d; color: #000; font-weight: bold; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; }
    .btn-reject { background: none; border: 1px solid #ef4444; color: #ef4444; padding: 6px 14px; border-radius: 6px; cursor: pointer; }

    /* Input Bar */
    .input-bar { background: #0f172a; padding: 10px 14px; display: flex; align-items: center; gap: 8px; border-top: 1px solid #1e293b; }
    .input-bar input { flex: 1; background: #1e293b; border: none; outline: none; color: #fff; padding: 12px 16px; border-radius: 24px; font-size: 15px; }
    .btn-mic { width: 44px; height: 44px; border-radius: 50%; background: #1e293b; border: 1px solid #00e5ff; color: #00e5ff; display: flex; align-items: center; justify-content: center; font-size: 20px; cursor: pointer; transition: 0.2s; }
    .btn-mic.listening { background: #ef4444; border-color: #ef4444; color: #fff; animation: pulse-fast 0.6s infinite alternate; }
    .btn-send { width: 44px; height: 44px; border-radius: 50%; background: #00e5ff; border: none; color: #000; font-size: 18px; display: flex; align-items: center; justify-content: center; cursor: pointer; }
  </style>
</head>
<body>
  <header>
    <div class="logo">
      <div class="status-dot"></div>
      <span>INNVO CORE</span>
    </div>
    <button class="btn-icon" onclick="clearChat()">🗑️</button>
  </header>

  <div class="orb-section">
    <div class="orb" id="orb">
      <div class="orb-inner" id="orb-icon">⚡</div>
    </div>
  </div>

  <div class="pills-bar">
    <div class="pill" onclick="sendQuery('Battery kitni hai?')">⚡ Battery</div>
    <div class="pill" onclick="sendQuery('What time is it?')">🕒 Time</div>
    <div class="pill" onclick="showMemories()">🧠 Memories</div>
    <div class="pill" onclick="showTools()">🛠️ Tools</div>
    <div class="pill" onclick="showRules()">⚖️ Rules</div>
  </div>

  <div class="chat-area" id="chat">
    <div class="msg msg-bot">
      Namaste Sir! Main Innvo hoon. Aap mic tap karke bol sakte hain ya message type kar sakte hain.
    </div>
  </div>

  <div class="input-bar">
    <button class="btn-mic" id="mic-btn" onclick="toggleMic()">🎙️</button>
    <input type="text" id="query-input" placeholder="Speak or type in Hindi/English..." onkeydown="if(event.key==='Enter') sendInput()">
    <button class="btn-send" onclick="sendInput()">➤</button>
  </div>

  <script>
    const chat = document.getElementById('chat');
    const input = document.getElementById('query-input');
    const orb = document.getElementById('orb');
    const micBtn = document.getElementById('mic-btn');
    let isListening = false;
    let recognition = null;

    // Web Speech API for voice recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'hi-IN'; // Recognizes natural Hindi/English

      recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        input.placeholder = "Listening... (Bolna shuru karein)";
      };

      recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        input.value = transcript;
        sendInput();
      };

      recognition.onerror = () => stopMic();
      recognition.onend = () => stopMic();
    }

    function toggleMic() {
      if (!recognition) {
        alert("Microphone not supported on this browser. Use Chrome or Safari.");
        return;
      }
      if (isListening) {
        recognition.stop();
        stopMic();
      } else {
        recognition.start();
      }
    }

    function stopMic() {
      isListening = false;
      micBtn.classList.remove('listening');
      input.placeholder = "Speak or type in Hindi/English...";
    }

    function addMessage(text, isUser, badge = null, proposal = null) {
      const div = document.createElement('div');
      div.className = `msg ${isUser ? 'msg-user' : 'msg-bot'}`;
      
      let html = '';
      if (badge) html += `<div class="badge">${badge}</div><br>`;
      html += text.replace(/\\n/g, '<br>');

      if (proposal) {
        html += `
          <div class="approval-card">
            <p><strong>Learning Proposal:</strong> ${proposal}</p>
            <div class="approval-btns">
              <button class="btn-reject" onclick="sendQuery('Nahi, rehne do')">Nahi</button>
              <button class="btn-approve" onclick="sendQuery('Haan, save kar lo')">Haan</button>
            </div>
          </div>
        `;
      }

      div.innerHTML = html;
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }

    async function sendInput() {
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      sendQuery(text);
    }

    async function sendQuery(text) {
      addMessage(text, true);
      orb.classList.add('thinking');

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        orb.classList.remove('thinking');

        let badge = null;
        if (data.tool_used) badge = `Tool: ${data.tool_used}`;
        else if (data.search_used) badge = `Web Verified`;

        addMessage(data.reply, false, badge, data.pending_approval ? data.proposal : null);

        // Voice output fallback using browser TTS
        if ('speechSynthesis' in window && data.reply) {
          const cleanText = data.reply.replace(/\\[.*?\\]/g, '').replace(/https?:\\S+/g, '');
          const utter = new SpeechSynthesisUtterance(cleanText);
          utter.lang = 'hi-IN';
          window.speechSynthesis.speak(utter);
        }
      } catch (e) {
        orb.classList.remove('thinking');
        addMessage("[Error]: Connection lost with Innvo Engine.", false);
      }
    }

    async function showMemories() {
      const res = await fetch('/api/memories');
      const data = await res.json();
      let msg = "🧠 **Permanent Memories:**\\n";
      if (!data.memories || data.memories.length === 0) {
        msg += "No memories saved yet.";
      } else {
        data.memories.forEach(m => {
          msg += `• [${m.category}] ${m.content} (Q: ${m.q_value.toFixed(2)})\\n`;
        });
      }
      addMessage(msg, false);
    }

    async function showTools() {
      const res = await fetch('/api/tools');
      const data = await res.json();
      let msg = "🛠️ **Available Skills:**\\n";
      data.tools.forEach(t => {
        msg += `• **${t.name}**: ${t.description}\\n`;
      });
      addMessage(msg, false);
    }

    async function showRules() {
      const res = await fetch('/api/rules');
      const data = await res.json();
      let msg = "⚖️ **Sovereign Constitution Laws:**\\n";
      data.laws.forEach(l => {
        msg += `• [${l.id}] **${l.name}**: ${l.statement}\\n`;
      });
      addMessage(msg, false);
    }

    async function clearChat() {
      await fetch('/api/clear', { method: 'POST' });
      chat.innerHTML = '<div class="msg msg-bot">Active conversation context cleared. Fresh session started!</div>';
    }
  </script>
</body>
</html>
"""
