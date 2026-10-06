# Ask Vedika Voice Tutor: Complete Architecture & Re-Engineering Blueprint

This document is a comprehensive, production-grade reverse-engineering specification of the **"Ask Vedika" Voice Tutor** implemented in the Vedika AI ecosystem. It covers the full technical stack, system architecture, data flow, client-side Web Audio API capture/playback, WebSocket streaming protocol, Google Gemini Multimodal Live API integration, configuration, prompts, and deployment requirements so that it can be replicated in any new project.

---

## Table of Contents

1. [High-Level Architecture Overview](#1-high-level-architecture-overview)
2. [End-to-End System Flow & Architecture Diagram](#2-end-to-end-system-flow--architecture-diagram)
3. [Prerequisites & Dependencies](#3-prerequisites--dependencies)
   - [Frontend Dependencies (npm)](#frontend-dependencies-npm)
   - [Backend Voice Server Dependencies (npm)](#backend-voice-server-dependencies-npm)
   - [Python Desktop Pet Alternative (Optional)](#python-desktop-pet-alternative-optional)
4. [Environment Variables & Configuration](#4-environment-variables--configuration)
5. [Client-Side Implementation: `VoiceAgentView`](#5-client-side-implementation-voiceagentview)
   - [Microphone Audio Capture & PCM Encoding (16kHz 16-bit Mono)](#microphone-audio-capture--pcm-encoding-16khz-16-bit-mono)
   - [WebSocket Connection Lifecycle & Resilience](#websocket-connection-lifecycle--resilience)
   - [Audio Chunk Playback & Gapless Web Audio Scheduling (24kHz)](#audio-chunk-playback--gapless-web-audio-scheduling-24khz)
   - [Barge-In / Interruption Handling](#barge-in--interruption-handling)
   - [State Management & UI Transitions](#state-management--ui-transitions)
6. [Backend WebSocket Server: `voice-server.js`](#6-backend-websocket-server-voice-serverjs)
   - [Gemini Multimodal Live API Connection (`@google/genai`)](#gemini-multimodal-live-api-connection-googlegenai)
   - [Voice Persona & Voice Configuration (`Zephyr`)](#voice-persona--voice-configuration-zephyr)
   - [System Instruction & Multilingual Socratic Prompting](#system-instruction--multilingual-socratic-prompting)
   - [Multi-Key Load Balancing & Rotation](#multi-key-load-balancing--rotation)
   - [Real-Time Sentiment Analysis Engine](#real-time-sentiment-analysis-engine)
   - [Long-Term Memory Injection (Upstash Redis)](#long-term-memory-injection-upstash-redis)
7. [Visualizer: 3D Animated Robot (`Three.js`)](#7-visualizer-3d-animated-robot-threejs)
8. [Entry Points & UI Integration](#8-entry-points--ui-integration)
   - [Vedika 3D Chamber Hub (`/vedika-ai`)](#vedika-3d-chamber-hub-vedika-ai)
   - [General Tutor View (`/vedika-ai/ask`)](#general-tutor-view-vedika-aiask)
9. [Step-by-Step Guide to Re-create in a New Project](#9-step-by-step-guide-to-re-create-in-a-new-project)

---

## 1. High-Level Architecture Overview

The Ask Vedika Voice Tutor provides a **sub-second full-duplex conversational voice tutoring experience**. Rather than a traditional "Record Audio ➔ Speech-to-Text (STT) ➔ LLM Text Completion ➔ Text-to-Speech (TTS)" pipeline (which takes 3–6 seconds per turn), Vedika uses the **Google Gemini Multimodal Live API**:

1. **Direct Audio-to-Audio Streaming**: The user's microphone stream is sent raw as 16kHz PCM chunks over a bidirectional WebSocket to the Node.js backend.
2. **Streaming WebSocket Proxy**: The Node.js backend maintains a persistent Live session with Google Gemini (`gemini-3.1-flash-live-preview` / `gemini-2.0-flash-live-001`) via `@google/genai`.
3. **Low-Latency Voice Output**: Gemini directly synthesizes voice audio tokens and streams back 24kHz PCM chunks.
4. **Client Web Audio API Queue**: The browser plays back PCM chunks with sub-100ms jitter buffers, achieving immediate, natural conversation.
5. **Real-Time Interruption (Barge-In)**: If the student speaks while the AI is talking, Gemini detects speech overlap, fires an `interrupted` event, and the browser immediately flushes its audio queue and cuts off playback.

---

## 2. End-to-End System Flow & Architecture Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Browser)
    participant UI as VoiceAgentView (React/Next.js)
    participant AudioContext as Web Audio API
    participant WS as Node.js Voice Server (voice-server.js)
    participant Redis as Upstash Redis (Memory)
    participant Gemini as Gemini Live API (Google Gen AI)

    Note over Student,UI: User navigates to /vedika-ai/ask & clicks "START SESSION"
    UI->>AudioContext: getUserMedia({ echoCancellation, noiseSuppression })
    UI->>AudioContext: new AudioContext({ sampleRate: 16000 })
    UI->>WS: WebSocket Connect: /api/ws?language=all&subject=all&sessionId=...
    WS->>Redis: Fetch past conversation history & student memories
    Redis-->>WS: Return memory context string
    WS->>Gemini: ai.live.connect({ model: "gemini-3.1-flash-live-preview", voice: "Zephyr", systemInstruction })
    Gemini-->>WS: Session open acknowledged
    WS-->>UI: Send { type: "status", message: "Tutor is ready! Ask your academic questions." }

    loop Continuous Audio Streaming (User Speaking)
        AudioContext->>UI: ScriptProcessor onaudioprocess (Float32Array)
        UI->>UI: Convert Float32 [-1.0, 1.0] to Int16 PCM, Base64 encode
        UI->>WS: Send { type: "audio", data: "<base64 PCM 16kHz>" }
        WS->>Gemini: sendRealtimeInput({ audio: { data, mimeType: "audio/pcm;rate=16000" } })
    end

    loop Direct Audio Streaming (Gemini Responding)
        Gemini-->>WS: onmessage(serverContent.modelTurn.parts[].inlineData.data)
        WS-->>UI: Send { type: "audio", data: "<base64 PCM 24kHz>" }
        UI->>AudioContext: Decode Int16 PCM, load into AudioBuffer(24000Hz)
        UI->>AudioContext: BufferSource.start(nextPlayTime) (Gapless playback)
        Gemini-->>WS: onmessage(serverContent.outputTranscription.text)
        WS-->>UI: Send { type: "agent-transcription", text: "..." }
        Gemini-->>WS: onmessage(serverContent.inputTranscription.text)
        WS->>WS: analyzeSentiment(text)
        WS-->>UI: Send { type: "user-transcription", text: "...", sentiment: {...} }
    end

    opt Interruption / Barge-in
        Student->>AudioContext: Speaks while Tutor is talking
        Gemini-->>WS: onmessage(serverContent.interrupted = true)
        WS-->>UI: Send { type: "interrupted" }
        UI->>AudioContext: stopAllAudioPlaybacks() (Immediate playback halt)
    end
```

---

## 3. Prerequisites & Dependencies

### Frontend Dependencies (npm)

In the frontend Next.js/React project:

```bash
npm install lucide-react three react-markdown remark-gfm
```

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `react` | `^18.3.1` | Core UI library |
| `react-dom` | `^18.3.1` | React DOM renderer |
| `next` | `^14.2.5` | Next.js App Router framework |
| `three` | `^0.150.0` | 3D WebGL Robot visualizer (`VoiceRobotVisualizer`) & Chamber Scene |
| `lucide-react` | `^0.395.0` | Clean UI icons (Mic, Brain, Zap, ArrowLeft, Sun, Chevron, etc.) |
| `react-markdown` | `^10.1.0` | Render live text transcriptions |
| `remark-gfm` | `^4.0.1` | GitHub Flavored Markdown support |

### Backend Voice Server Dependencies (npm)

In the standalone voice WebSocket server or Next.js custom server:

```bash
npm install @google/genai ws dotenv @upstash/redis express
```

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `@google/genai` | `^0.1.1` or `^2.8.0` | **Official Google Gen AI SDK** with WebSocket Live API client (`ai.live.connect`) |
| `ws` | `^8.17.0` | High-performance WebSocket server |
| `dotenv` | `^16.4.5` | Environment variable loader from `.env` |
| `@upstash/redis` | `^1.34.3` | Serverless Redis client for conversational memory and student profiles |
| `express` | `^4.19.2` | Optional HTTP router if running combined with Next.js |

### Python Desktop Pet Alternative (Optional)

If implementing the desktop pet version instead of the browser web version:

```bash
pip install google-genai PySide6 pyaudio numpy
```

---

## 4. Environment Variables & Configuration

Create a `.env` file with the following variables:

```env
# =================================================================
# GEMINI API KEYS (Multi-Key Rotation / Fallback)
# =================================================================
# Primary key reserved for Voice Agent
GEMINI_API_KEY=AIzaSy...

# Optional: Extra keys for load balancing across concurrent sessions
GEMINI_API_KEY_1=AIzaSy...
GEMINI_API_KEY_2=AIzaSy...
GEMINI_API_KEY_3=AIzaSy...
GEMINI_API_KEY_4=AIzaSy...

# Gemini Live Model (Recommended: gemini-3.1-flash-live-preview or gemini-2.0-flash-live-001)
GEMINI_MODEL=gemini-3.1-flash-live-preview

# =================================================================
# VOICE SERVER PORT & ENDPOINTS
# =================================================================
PORT=5001
NODE_ENV=development

# Frontend WebSocket Target (Local or Production)
NEXT_PUBLIC_VOICE_WS_URL=ws://localhost:5001/api/ws
# For production on Render / Cloud:
# NEXT_PUBLIC_VOICE_WS_URL=wss://your-voice-server.onrender.com/api/ws

# =================================================================
# MEMORY & PERSISTENCE (Upstash Redis)
# =================================================================
UPSTASH_REDIS_REST_URL=https://your-upstash-database.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
```

---

## 5. Client-Side Implementation: `VoiceAgentView`

The core component is [`frontend/components/voice-tutor/VoiceAgentView.jsx`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/components/voice-tutor/VoiceAgentView.jsx).

### Microphone Audio Capture & PCM Encoding (16kHz 16-bit Mono)

Gemini Live requires linear PCM 16-bit mono audio at 16,000 Hz. The browser Web Audio API handles this cleanly:

```javascript
// 1. Request user microphone with browser-native noise suppression and echo cancellation
const stream = await navigator.mediaDevices.getUserMedia({
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
  }
});
micStreamRef.current = stream;

// 2. Initialize AudioContext at exactly 16,000 Hz sample rate
const audioCtx = new (window.AudioContext || window.webkitAudioContext)({
  sampleRate: 16000
});
audioCtxRef.current = audioCtx;

// 3. Connect microphone stream to a ScriptProcessorNode
const source = audioCtx.createMediaStreamSource(stream);
sourceRef.current = source;

// 4096 buffer size, 1 input channel, 1 output channel
const processor = audioCtx.createScriptProcessor(4096, 1, 1);
processorRef.current = processor;

source.connect(processor);
processor.connect(audioCtx.destination);

// 4. Transform audio chunks to 16-bit signed PCM and encode to Base64
processor.onaudioprocess = (e) => {
  if (wsRef.current?.readyState !== WebSocket.OPEN || isMutedRef.current) return;

  const float32Data = e.inputBuffer.getChannelData(0); // [-1.0, 1.0]
  const pcmBuffer = new ArrayBuffer(float32Data.length * 2); // 2 bytes per Int16 sample
  const dataView = new DataView(pcmBuffer);

  let offset = 0;
  for (let i = 0; i < float32Data.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, float32Data[i]));
    dataView.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true); // Little-endian
  }

  // Convert binary to Base64 string
  let binary = '';
  const bytes = new Uint8Array(pcmBuffer);
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64Data = btoa(binary);

  // Send packet to backend
  wsRef.current.send(JSON.stringify({ type: 'audio', data: base64Data }));
};
```

---

### WebSocket Connection Lifecycle & Resilience

```javascript
const wsHost = process.env.NEXT_PUBLIC_VOICE_WS_URL || (
  window.location.hostname === 'localhost'
    ? 'ws://localhost:5001'
    : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
);

const voiceSid = sessionId || Date.now().toString(36);
const wsUrl = `${wsHost}/api/ws?language=${selectedLanguage}&subject=${selectedSubject}&sessionId=${voiceSid}&userId=${activeUserId}`;

const ws = new WebSocket(wsUrl);
wsRef.current = ws;

// 10-second timeout guard to prevent infinite "connecting" UI hangs
const connTimeout = setTimeout(() => {
  if (ws.readyState !== WebSocket.OPEN) {
    ws.close();
    setConnectionStatus('error');
    setStatusMessage('Connection timed out. Ensure the voice server is running.');
  }
}, 10000);

ws.onopen = () => {
  clearTimeout(connTimeout);
  setConnectionStatus('connected');
  setStatusMessage('Tutor connected! Start speaking.');
  // Activate microphone processing here
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  switch (message.type) {
    case 'status':
      setStatusMessage(message.message);
      break;
    case 'audio':
      playPcmAudioChunk(message.data);
      break;
    case 'interrupted':
      stopAllAudioPlaybacks();
      setConnectionStatus('connected');
      setStatusMessage('Tutor was interrupted. Listening now...');
      break;
    case 'agent-transcription':
      // Append text tokens to AI speech bubble
      appendAgentTranscript(message.text);
      break;
    case 'user-transcription':
      // Append user text and sentiment
      appendUserTranscript(message.text, message.sentiment);
      break;
    case 'error':
      setStatusMessage(message.message);
      setConnectionStatus('error');
      break;
  }
};
```

---

### Audio Chunk Playback & Gapless Web Audio Scheduling (24kHz)

Gemini returns raw 24,000 Hz 16-bit PCM mono audio. Because network packets arrive in small fragmented bursts, naïve immediate playback results in robotic stuttering or clicks. 

The implementation uses **Web Audio API scheduling (`nextPlayTimeRef`)** to queue each chunk to start precisely when the previous chunk ends:

```javascript
const nextPlayTimeRef = useRef(0);
const audioSourcesQueueRef = useRef([]);

const playPcmAudioChunk = (base64Data) => {
  if (isMutedRef.current || !audioCtxRef.current) return;

  try {
    const audioCtx = audioCtxRef.current;
    
    // 1. Decode base64 to binary ArrayBuffer
    const binaryString = atob(base64Data);
    const buffer = new ArrayBuffer(binaryString.length);
    const view = new Uint8Array(buffer);
    for (let i = 0; i < binaryString.length; i++) {
      view[i] = binaryString.charCodeAt(i);
    }

    // 2. Interpret as Int16 signed integers
    const int16Samples = new Int16Array(buffer);

    // 3. Create AudioBuffer at Gemini's output rate (24000 Hz)
    const audioBuffer = audioCtx.createBuffer(1, int16Samples.length, 24000);
    const channelData = audioBuffer.getChannelData(0);

    // 4. Normalize Int16 [-32768, 32767] to Float32 [-1.0, 1.0]
    for (let i = 0; i < int16Samples.length; i++) {
      channelData[i] = int16Samples[i] / 32768.0;
    }

    // 5. Create AudioBufferSourceNode
    const bufferSource = audioCtx.createBufferSource();
    bufferSource.buffer = audioBuffer;
    bufferSource.connect(audioCtx.destination);

    audioSourcesQueueRef.current.push(bufferSource);

    bufferSource.onended = () => {
      audioSourcesQueueRef.current = audioSourcesQueueRef.current.filter((src) => src !== bufferSource);
      if (audioSourcesQueueRef.current.length === 0) {
        setConnectionStatus('connected');
        setStatusMessage('Tutor is listening... Feel free to talk.');
      }
    };

    // 6. Schedule gapless sequential playback
    const now = audioCtx.currentTime;
    if (nextPlayTimeRef.current < now) {
      nextPlayTimeRef.current = now + 0.05; // 50ms initial safety jitter buffer
    }

    setConnectionStatus('tutor-speaking');
    setStatusMessage('Tutor is speaking...');
    bufferSource.start(nextPlayTimeRef.current);
    nextPlayTimeRef.current += audioBuffer.duration; // Advance playhead
  } catch (err) {
    console.error('Playback error:', err);
  }
};
```

---

### Barge-In / Interruption Handling

When Gemini detects speech overlap, the server emits `{ type: 'interrupted' }`. The client immediately cancels all scheduled audio sources:

```javascript
const stopAllAudioPlaybacks = useCallback(() => {
  audioSourcesQueueRef.current.forEach((source) => {
    try {
      source.stop();
      source.disconnect();
    } catch {}
  });
  audioSourcesQueueRef.current = [];
  nextPlayTimeRef.current = 0;
}, []);
```

---

### State Management & UI Transitions

| State | Color Token | Visual Feedback |
| :--- | :--- | :--- |
| `disconnected` | `T.dim` (Grey `#666`) | "Tap the microphone to start your tutoring session" |
| `connecting` | `T.amber` (Amber `#ffb703`) | Pulsing status indicator, "Establishing low-latency connection..." |
| `connected` | `T.green` (Green `#39FF14`) | 3D Robot floats gently, "Tutor is listening... Feel free to talk." |
| `tutor-speaking` | `T.purple` (Purple `#9B6EF8`)| 3D Robot core pulses dynamically, "Tutor is speaking..." |
| `error` | `T.red` (Red `#ef4444`) | Error message with retry guidance |

---

## 6. Backend WebSocket Server: `voice-server.js`

The backend proxy resides at [`frontend/voice-server.js`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/voice-server.js).

### Gemini Multimodal Live API Connection (`@google/genai`)

```javascript
const http = require('http');
const { WebSocketServer } = require('ws');
const { GoogleGenAI, Modality } = require('@google/genai');

const server = http.createServer((req, res) => {
  if (req.url === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'healthy', geminiConfigured: !!process.env.GEMINI_API_KEY }));
  } else {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Voice Tutor WebSocket Server');
  }
});

const wss = new WebSocketServer({ server, path: '/api/ws' });

wss.on('connection', async (clientWs, request) => {
  const searchParams = new URL(request.url || '', 'http://localhost').searchParams;
  const language = searchParams.get('language') || 'all';
  const subject = searchParams.get('subject') || 'all';
  const sessionId = searchParams.get('sessionId');
  const userId = searchParams.get('userId');

  // Load past memories from Redis
  const memoryCtx = await loadMemoryContext(sessionId, userId);

  // Initialize Gemini Client
  const ai = getGeminiClient();

  const geminiSession = await ai.live.connect({
    model: process.env.GEMINI_MODEL || 'gemini-3.1-flash-live-preview',
    callbacks: {
      onmessage: (message) => {
        const content = message.serverContent;
        if (content) {
          // 1. Model Audio Chunks
          for (const part of content.modelTurn?.parts || []) {
            if (part.inlineData?.data) {
              clientWs.send(JSON.stringify({ type: 'audio', data: part.inlineData.data }));
            }
          }
          // 2. Model Transcript
          if (content.outputTranscription?.text) {
            clientWs.send(JSON.stringify({ type: 'agent-transcription', text: content.outputTranscription.text }));
          }
          // 3. User Speech Interruption Event
          if (content.interrupted) {
            clientWs.send(JSON.stringify({ type: 'interrupted' }));
          }
          // 4. User Transcript & Real-Time Sentiment
          if (content.inputTranscription?.text?.trim()) {
            const sentiment = analyzeSentiment(content.inputTranscription.text);
            clientWs.send(JSON.stringify({ type: 'user-transcription', text: content.inputTranscription.text, sentiment }));
          }
        }
      },
      onclose: () => {
        clientWs.send(JSON.stringify({ type: 'status', message: 'Tutor connection closed.' }));
      },
      onerror: (error) => {
        clientWs.send(JSON.stringify({ type: 'error', message: 'Gemini Live Session error.' }));
      },
    },
    config: {
      responseModalities: [Modality.AUDIO],
      speechConfig: {
        voiceConfig: {
          prebuiltVoiceConfig: {
            voiceName: 'Zephyr', // Clean, expressive voice
          },
        },
      },
      systemInstruction: buildSystemInstruction(language, subject, memoryCtx),
      outputAudioTranscription: {},
      inputAudioTranscription: {},
    },
  });

  // Client to Gemini Message Forwarding
  clientWs.on('message', (buffer) => {
    try {
      const msg = JSON.parse(buffer.toString());
      if (msg.type === 'audio' && msg.data) {
        geminiSession.sendRealtimeInput({
          audio: {
            data: msg.data,
            mimeType: 'audio/pcm;rate=16000',
          },
        });
      }
    } catch (e) {
      console.error('Audio relay error:', e);
    }
  });

  clientWs.on('close', () => {
    if (geminiSession) {
      try { geminiSession.close(); } catch {}
    }
  });
});
```

---

### Voice Persona & Voice Configuration (`Zephyr`)

The voice model chosen for Vedika is **`Zephyr`**:
- Natural Indian English cadence and warmth.
- Fluid pronunciation of Indian vocabulary (*"chalo"*, *"samajhte hain"*, *"choodu"*).
- Pre-built voice configured in `speechConfig`:

```javascript
speechConfig: {
  voiceConfig: {
    prebuiltVoiceConfig: {
      voiceName: 'Zephyr'
    }
  }
}
```

---

### System Instruction & Multilingual Socratic Prompting

The prompt in `voice-server.js` enforces specific constraints essential for voice:

```javascript
function buildSystemInstruction(language, subject, memoryCtx) {
  let prompt =
    'Your name is Vedika. You are a warm, highly humanized, and friendly academic tutor supporting school students. ' +
    'VOICE & HUMANIZATION GUIDELINES: ' +
    'Speak in a smooth, expressive, warm, and natural human tone with a familiar, conversational Indian accent rhythm in English ' +
    '(using natural phrases like "chalo", "got it ya", "super simple", "no problem at all", "don\'t worry!"). ' +
    'Sound like an encouraging elder sibling or personal tutor: warm, relatable, dynamic, and full of natural life. ' +
    'Keep answers strictly short and fluid (usually 1 to 2 short sentences per turn) so text-to-speech voice output sounds immediate, crisp, and human. ' +
    'Never output markdown symbols, asterisks, bullet points, numbers, or complex formulas into text, as they disrupt natural voice synthesis. ';

  if (language === 'telugu') {
    prompt += 'LANGUAGE MODE: You must speak in sweet, conversational Telugu only (unless referring to specific scientific/mathematical English terms). ';
  } else if (language === 'hindi') {
    prompt += 'LANGUAGE MODE: You must speak in simple, warm, conversational Hindi. ';
  } else if (language === 'english') {
    prompt += 'LANGUAGE MODE: Speak in clear, warm, expressive Indian English with friendly colloquial phrasing. ';
  } else {
    prompt +=
      'CODE-SWITCHING & LANGUAGE MATCHING: Dynamically match and mirror the student\'s exact language mix and tone. ' +
      'If the user speaks in Teluglish (e.g., "Artham kaledu brother", "Ela cheyyali cheppu"), respond in natural, sweet Teluglish. ' +
      'If the user speaks in Hinglish (e.g., "Samajh nahi aaya, phir se batao"), respond in natural, friendly Hinglish. ' +
      'If the user speaks in English, respond in natural, warm Indian English.';
  }

  if (subject === 'math') {
    prompt += ' SUBJECT FOCUS: Currently helping with Mathematics! Explain concepts using simple physical analogies.';
  } else if (subject === 'science') {
    prompt += ' SUBJECT FOCUS: Currently helping with Science! Explain concepts with fun real-world facts.';
  } else if (subject === 'languages') {
    prompt += ' SUBJECT FOCUS: Currently helping with Languages & Reading! Expand vocabulary and grammar.';
  }

  if (memoryCtx) prompt += memoryCtx;

  return prompt;
}
```

---

### Multi-Key Load Balancing & Rotation

To prevent rate-limit bottlenecks on free-tier Gemini API keys, the server pools all `GEMINI_API_KEY*` variables and rotates them:

```javascript
const GEMINI_KEYS = [
  process.env.GEMINI_API_KEY,
  process.env.GEMINI_API_KEY_1,
  process.env.GEMINI_API_KEY_2,
  process.env.GEMINI_API_KEY_3,
  process.env.GEMINI_API_KEY_4
].filter(Boolean);

let connectionCount = 0;

function getGeminiClient() {
  if (GEMINI_KEYS.length === 0) {
    throw new Error('GEMINI_API_KEY environment variable is required.');
  }
  const apiKey = GEMINI_KEYS[connectionCount % GEMINI_KEYS.length];
  connectionCount++;
  return new GoogleGenAI({
    apiKey,
    httpOptions: { headers: { 'User-Agent': 'aistudio-build' } }
  });
}
```

---

### Real-Time Sentiment Analysis Engine

The server checks student transcription keywords to detect emotional state across English, Hindi, and Telugu:

```javascript
function analyzeSentiment(text) {
  const lowercase = text.toLowerCase();
  const confusedWords = ["don't understand","not sure","confused","cannot get","difficult","hard","stuck","doubt","అర్థం కాలేదు","కష్టంగా ఉంది","సందేహం","ardham raledu","samajh nahi","mushkil"];
  const positiveWords = ["understand","got it","easy","awesome","perfect","clear","great","అర్థమైంది","సూపర్","ardhamaindi","samajh gaya","badhiya"];
  const curiousWords = ["what is","how do","tell me about","why is","curious","learn","ఏమిటి","ఎలా","ఎందుకు","emiti","kya hai","kaise"];

  let confusedCount = confusedWords.filter(w => lowercase.includes(w)).length;
  let positiveCount = positiveWords.filter(w => lowercase.includes(w)).length;
  let curiousCount = curiousWords.filter(w => lowercase.includes(w)).length;

  if (confusedCount > positiveCount && confusedCount >= curiousCount)
    return { label: 'Struggling / Confused', score: -0.6, emoji: '😟' };
  if (positiveCount > confusedCount && positiveCount >= curiousCount)
    return { label: 'Happy / Confident', score: 0.8, emoji: '😊' };
  if (curiousCount > confusedCount && curiousCount > positiveCount)
    return { label: 'Curious / Inquisitive', score: 0.4, emoji: '🤔' };
  return { label: 'Calm / Conversational', score: 0.0, emoji: '😐' };
}
```

---

## 7. Visualizer: 3D Animated Robot (`Three.js`)

The component [`frontend/components/voice-tutor/VoiceRobotVisualizer.jsx`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/components/voice-tutor/VoiceRobotVisualizer.jsx) renders a Three.js canvas featuring a wireframe icosahedron and a glowing core that pulsates:

```javascript
import * as THREE from 'three';

// Head Wireframe Icosahedron
const headGeo = new THREE.IcosahedronGeometry(1.2, 1);
const headMat = new THREE.MeshPhongMaterial({
  color: 0x9B6EF8,
  wireframe: true,
  emissive: 0x490080,
  emissiveIntensity: 0.6,
});
const head = new THREE.Mesh(headGeo, headMat);
robotGroup.add(head);

// Core Glowing Sphere
const coreGeo = new THREE.SphereGeometry(0.6, 32, 32);
const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
const core = new THREE.Mesh(coreGeo, coreMat);
robotGroup.add(core);

// Continuous floating & breathing animation loop
const animate = () => {
  animationId = requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  robotGroup.position.y = Math.sin(t * 1.5) * 0.15;
  robotGroup.rotation.y += 0.01;
  robotGroup.rotation.z = Math.sin(t * 0.5) * 0.1;

  // Pulse core scale
  const scale = 1 + Math.sin(t * 4) * 0.15;
  core.scale.set(scale, scale, scale);

  renderer.render(scene, camera);
};
```

---

## 8. Entry Points & UI Integration

### Vedika 3D Chamber Hub (`/vedika-ai`)

In [`frontend/app/vedika-ai/page.jsx`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/app/vedika-ai/page.jsx):
- Avatar 0 is **"Ask Vedika"** (`id: 'ask'`, `route: '/vedika-ai/ask'`, Neon Green theme `#39FF14`).
- Clicking **"Enter World"** on the hero card navigates to `/vedika-ai/ask`.

### General Tutor View (`/vedika-ai/ask`)

In [`frontend/app/vedika-ai/ask/page.jsx`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/app/vedika-ai/ask/page.jsx) and [`components/GeneralTutor.jsx`](file:///c:/Users/25002/Desktop/V0.1/Vedika/vedika/Vyomanta/frontend/components/GeneralTutor.jsx):
- Header pill toggle: **`[ Text | Voice ]`**.
- Toggling to **Voice** switches the view to `<VoiceAgentView inline={true} />`.
- Clicking the microphone button triggers `handleMicToggle()`, acquiring the microphone and opening the WebSocket connection.

---

## 9. Step-by-Step Guide to Re-create in a New Project

1. **Initialize Project & Install Dependencies**:
   ```bash
   npx create-next-app@latest my-voice-app
   cd my-voice-app
   npm install @google/genai ws dotenv lucide-react three react-markdown remark-gfm
   ```

2. **Add Environment Variables (`.env`)**:
   ```env
   GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
   GEMINI_MODEL=gemini-3.1-flash-live-preview
   PORT=5001
   NEXT_PUBLIC_VOICE_WS_URL=ws://localhost:5001/api/ws
   ```

3. **Copy the Voice Server File (`voice-server.js`)**:
   - Use the code from Section 6 above.
   - Run the server in a separate terminal:
     ```bash
     node voice-server.js
     ```

4. **Copy the Frontend Voice Component (`VoiceAgentView.jsx`)**:
   - Copy `VoiceAgentView.jsx`, `VoiceRobotVisualizer.jsx`, and `VoiceChatMessages.jsx` into your components directory.

5. **Create a Page Route (`app/ask-vedika/page.jsx`)**:
   ```jsx
   'use client';
   import VoiceAgentView from '@/components/VoiceAgentView';

   export default function AskVedikaPage() {
     return (
       <div className="w-full h-screen bg-slate-950 text-white">
         <VoiceAgentView inline={false} onClose={() => {}} />
       </div>
     );
   }
   ```

6. **Start the Next.js Dev Server**:
   ```bash
   npm run dev
   ```

7. **Test the Live Voice Tutor**:
   - Open `http://localhost:3000/ask-vedika`.
   - Click **"START SESSION"** and grant microphone permissions.
   - Start talking in English, Hindi, or Telugu—Vedika will respond aloud within ~500ms using the natural `Zephyr` voice.
