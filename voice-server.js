/**
 * Veyra Voice - High-Performance Gemini Multimodal Live Voice Server
 * 
 * Based on the Ask Vedika Voice Tutor Architecture:
 * - Sub-second full-duplex conversational voice engine
 * - Google Gemini Multimodal Live API (@google/genai)
 * - 16kHz PCM audio streaming from browser microphone
 * - 24kHz PCM audio playback streaming to browser speaker
 * - Real-time barge-in / interruption handling
 * - Real-time multilingual sentiment analysis engine
 * - Multi-key load balancing and API key rotation
 * - Long-term conversational memory & context injection
 */

const http = require('http');
const { WebSocketServer } = require('ws');
const dotenv = require('dotenv');
const { GoogleGenAI, Modality } = require('@google/genai');

// Load environment variables
dotenv.config();

// Port configuration (Defaults to 5055 to ensure complete isolation from other projects)
const PORT = parseInt(process.env.VOICE_SERVER_PORT || process.env.VOICE_PORT || '5055', 10);
const HOST = process.env.VOICE_SERVER_HOST || '0.0.0.0';

// Multi-key rotation pool
const GEMINI_KEYS = [
  process.env.GEMINI_API_KEY,
  process.env.GEMINI_API_KEY_1,
  process.env.GEMINI_API_KEY_2,
  process.env.GEMINI_API_KEY_3,
  process.env.GEMINI_API_KEY_4,
].filter((k) => k && k.trim().length > 5);

let connectionCounter = 0;

/**
 * Get round-robin Gemini client from pool
 */
function getGeminiClient() {
  if (GEMINI_KEYS.length === 0) {
    throw new Error('GEMINI_API_KEY environment variable is required.');
  }
  const apiKey = GEMINI_KEYS[connectionCounter % GEMINI_KEYS.length];
  connectionCounter++;
  return new GoogleGenAI({
    apiKey,
    httpOptions: { headers: { 'User-Agent': 'veyra-voice-live' } },
  });
}

// Optional Upstash Redis memory initialization
let redisClient = null;
if (process.env.UPSTASH_REDIS_REST_URL && process.env.UPSTASH_REDIS_REST_TOKEN) {
  try {
    const { Redis } = require('@upstash/redis');
    redisClient = new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL,
      token: process.env.UPSTASH_REDIS_REST_TOKEN,
    });
    console.log('[Memory] Connected to Upstash Redis for persistent memory');
  } catch (err) {
    console.warn('[Memory] Failed to initialize Upstash Redis, using in-memory store:', err.message);
  }
}

// In-memory fallback session memory store
const memoryStore = new Map();

async function loadMemoryContext(sessionId, userId) {
  if (!sessionId && !userId) return '';

  const cacheKey = `mem:${userId || sessionId}`;
  if (redisClient) {
    try {
      const data = await redisClient.get(cacheKey);
      if (data) {
        return `\nSTUDENT BACKGROUND & RECENT TOPICS: ${typeof data === 'string' ? data : JSON.stringify(data)}\n`;
      }
    } catch (err) {
      console.warn('[Memory] Redis read error:', err.message);
    }
  }

  const inMemory = memoryStore.get(cacheKey);
  if (inMemory && inMemory.length > 0) {
    return `\nPAST SESSION CONVERSATION CONTEXT: ${inMemory.slice(-4).join('; ')}\n`;
  }
  return '';
}

async function saveMemorySnippet(sessionId, userId, snippet) {
  const cacheKey = `mem:${userId || sessionId}`;
  const existing = memoryStore.get(cacheKey) || [];
  existing.push(snippet);
  if (existing.length > 20) existing.shift();
  memoryStore.set(cacheKey, existing);

  if (redisClient) {
    try {
      await redisClient.set(cacheKey, existing.slice(-5).join(' | '), { ex: 86400 * 7 });
    } catch (_) {}
  }
}

/**
 * Real-Time Multilingual Sentiment Analysis Engine (B2B Prospect Tone)
 * Analyzes English, Telugu, Hindi, Hinglish, Teluglish utterances.
 */
function analyzeSentiment(text) {
  if (!text) return { label: 'Neutral / Listening', score: 0.0, emoji: '😐' };
  const lowercase = text.toLowerCase();

  const skepticalWords = [
    "expensive", "costly", "not interested", "busy", "don't need", "waste", "later",
    "no need", "have instagram", "already have", "not now", "call later", "dont want",
    "ఖర్చు", "అవసరం లేదు", "బిజీగా ఉన్నాను", "వద్దు", "తర్వాత చూద్దాం",
    "kharcha", "zaroorat nahi", "fursat nahi", "nahi chahiye", "baad mein", "vaddu", "chooddam", "tarvata",
  ];

  const interestedWords = [
    "interesting", "sounds good", "tell me more", "how much", "send demo", "prototype",
    "schedule", "meeting", "makes sense", "yes", "okay", "sure", "share details", "booking",
    "బాగుంది", "వివరాలు చెప్పు", "చూద్దాం", "సరే", "డెమో పంపు",
    "accha hai", "sahi hai", "baagundi", "chappandi", "samjhao", "theek hai", "batao", "ha bolo",
  ];

  const curiousWords = [
    "what website", "how does it work", "examples", "features", "portfolio", "timeline",
    "how do you build", "how will it help", "who are you", "what company",
    "ఎలా పనిచేస్తుంది", "ఫీచర్స్ ఏమిటి", "ఎవరు మీరు",
    "kya features", "kaise hoga", "ela untundi", "kya cost hai", "kaun ho",
  ];

  const skepticalCount = skepticalWords.filter((w) => lowercase.includes(w)).length;
  const interestedCount = interestedWords.filter((w) => lowercase.includes(w)).length;
  const curiousCount = curiousWords.filter((w) => lowercase.includes(w)).length;

  if (skepticalCount > interestedCount && skepticalCount >= curiousCount) {
    return { label: 'Hesitant / Objecting', score: -0.6, emoji: '😟' };
  }
  if (interestedCount > skepticalCount && interestedCount >= curiousCount) {
    return { label: 'Interested / Receptive', score: 0.8, emoji: '😊' };
  }
  if (curiousCount > skepticalCount && curiousCount > interestedCount) {
    return { label: 'Curious / Evaluating', score: 0.4, emoji: '🤔' };
  }
  return { label: 'Neutral / Listening', score: 0.0, emoji: '😐' };
}

/**
 * Build dynamic conversational instruction for B2B Outbound Software Pitching
 */
function buildSystemInstruction(
  language,
  memoryCtx,
  customPersona,
  customObjective,
  clientName = 'Dr. Rajesh',
  businessName = 'Apex Dental Clinic',
  businessType = 'Healthcare & Dental Practice',
  pitchGoal = 'a modern responsive website with 24/7 online patient booking and automated WhatsApp appointment reminders',
  agentName = 'Aarav from Veyra Software Solutions',
  leadNotes = '',
  city = '',
  dealValue = '',
  phone = ''
) {
  const persona = customPersona ||
    `You are ${agentName}, an elite, highly consultative, and natural B2B outbound tech growth representative from Veyra Software Solutions.`;

  let prompt =
    `${persona} ` +
    `YOUR CALL CONTEXT & PROSPECT DETAILS: ` +
    `- You are placing a live outbound phone call to ${clientName}, the business owner / principal of ${businessName}. ` +
    `- Business Industry / Type: ${businessType}. ` +
    `- What their business needs (Your Value Pitch): ${pitchGoal}. You noticed ${businessName} currently either lacks a modern web application or is losing high-intent local customers to digital competitors on Google. ` +
    `CONVERSATIONAL OBJECTIVES & PLAYBOOK: ` +
    `1. Opening: Greet ${clientName} respectfully by name, state that you're calling from Veyra Software Solutions, and ask if this is a quick 2 minutes to talk about ${businessName}. ` +
    `2. Value Hook: Concisely explain that today 75%+ of customers search on Google and book appointments/orders online, and having a tailored web application for ${businessName} directly drives more revenue and automates repetitive customer inquiries. ` +
    `3. Consultative Discovery: Ask 1 simple open discovery question (e.g. "How are most of your new customers finding you right now?", "Are your staff spending hours taking bookings manually?"). ` +
    `4. Handling Common Objections with High EQ: ` +
    `   - If they say "We don't need a website" or "Word of mouth is enough": Compliment their word-of-mouth reputation, but explain how a modern website captures high-intent customers who search online before visiting. ` +
    `   - If they say "We already have Instagram or Facebook": Acknowledge social media is great for branding, but explain that Google searchers want direct booking and ordering without app friction or commissions. ` +
    `   - If they say "Too busy / Not interested right now": Graciously respect their time: "Completely understand! Would it be alright if I sent a 2-minute prototype preview to your WhatsApp or email for you to glance at later?" ` +
    `   - If they ask "What does it cost?": Explain that Veyra builds custom, high-ROI solutions starting at very accessible packages designed to pay for themselves within weeks. ` +
    `5. Closing Goal: Secure agreement for a quick, zero-obligation 10-minute online demo or send a custom prototype walkthrough tailored specifically for ${businessName}. ` +
    `VOICE & CADENCE RULES: ` +
    `- Speak in an engaging, confident, warm Indian English rhythm (use natural conversational touches like "makes total sense", "absolutely", "got it ya", "super simple"). ` +
    `- STRICT BREVITY: Keep every spoken turn to ONLY 1 TO 2 SHORT SENTENCES! This is a live voice call—never monologue, never lecture. Keep it reciprocal and human. ` +
    `- Never recite markdown, bullet points, asterisks, emojis, or raw numbers into spoken speech. `;

  if (leadNotes && leadNotes.trim()) {
    prompt += ` PROSPECT SPECIFIC INTELLIGENCE & PAIN POINTS: ${leadNotes.trim()}. Refer to these specific challenges naturally to establish high credibility and trust. `;
  }
  if (city && city.trim()) {
    prompt += ` PROSPECT MARKET / CITY: ${city.trim()}. `;
  }
  if (dealValue && dealValue.trim()) {
    prompt += ` ESTIMATED DEAL / BUDGET VALUE: ${dealValue.trim()}. `;
  }

  if (customObjective) {
    prompt += ` ADDITIONAL CAMPAIGN OBJECTIVE: ${customObjective}. `;
  }

  if (language === 'telugu') {
    prompt += 'LANGUAGE MODE: You must speak in professional, warm, conversational Telugu/Teluglish only. ';
  } else if (language === 'hindi') {
    prompt += 'LANGUAGE MODE: You must speak in warm, professional, conversational Hindi/Hinglish. ';
  } else if (language === 'english') {
    prompt += 'LANGUAGE MODE: Speak in clear, polished Indian English. ';
  } else {
    prompt +=
      'CODE-SWITCHING & MIRRORING: Dynamically match and mirror the client\'s exact language mix. ' +
      'If the client speaks in Hindi/Hinglish, seamlessly switch to friendly Hindi/Hinglish. ' +
      'If they speak in Telugu/Teluglish, seamlessly switch to friendly Telugu/Teluglish. ' +
      'If English, respond in polished Indian English. ';
  }

  if (memoryCtx) {
    prompt += memoryCtx;
  }

  return prompt;
}

// HTTP Health Check and Info Server
const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === '/api/health' || req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        status: 'healthy',
        service: 'Veyra Voice - Gemini Live Multimodal Server',
        geminiConfigured: GEMINI_KEYS.length > 0,
        keysLoaded: GEMINI_KEYS.length,
        model: process.env.GEMINI_MODEL || 'gemini-3.1-flash-live-preview',
        voice: process.env.GEMINI_VOICE_NAME || 'Zephyr',
        activeConnections: activeSockets.size,
      })
    );
  } else {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Veyra Voice - Gemini Live Multimodal WebSocket Server\nConnect via WebSocket at /api/ws');
  }
});

// WebSocket Server
const wss = new WebSocketServer({ server });
const activeSockets = new Set();

wss.on('connection', async (clientWs, request) => {
  activeSockets.add(clientWs);
  const reqUrl = new URL(request.url || '', 'http://localhost');
  const pathname = reqUrl.pathname;

  // Accept connections on /api/ws, /ws/agent/test, or any query path
  if (!pathname.startsWith('/api/ws') && !pathname.startsWith('/ws/agent/test') && pathname !== '/') {
    // Keep tolerant of different path routes
  }

  const searchParams = reqUrl.searchParams;
  const language = searchParams.get('language') || 'all';
  const sessionId = searchParams.get('sessionId') || `sess_${Date.now().toString(36)}`;
  const userId = searchParams.get('userId') || 'user_default';
  const customPersona = searchParams.get('persona');
  const customObjective = searchParams.get('objective');
  const voiceName = searchParams.get('voiceName') || process.env.GEMINI_VOICE_NAME || 'Zephyr';

  // Prospect Client & Business Pitch Parameters
  const clientName = searchParams.get('clientName') || searchParams.get('prospectName') || 'Dr. Rajesh';
  const businessName = searchParams.get('businessName') || 'Apex Dental Clinic';
  const businessType = searchParams.get('businessType') || searchParams.get('industry') || 'Healthcare & Dental Practice';
  const pitchGoal = searchParams.get('pitchGoal') || searchParams.get('suggestedSolution') ||
    'a modern responsive website with 24/7 online patient booking and automated WhatsApp appointment reminders';
  const agentName = searchParams.get('agentName') || 'Aarav from Veyra Software Solutions';
  const leadNotes = searchParams.get('notes') || searchParams.get('painPoints') || searchParams.get('leadNotes') || '';
  const city = searchParams.get('city') || searchParams.get('location') || '';
  const dealValue = searchParams.get('dealValue') || searchParams.get('budget') || '';
  const phone = searchParams.get('phone') || '';
  const triggerGreeting = searchParams.get('proactiveGreeting') !== 'false';

  console.log(`[VoiceServer] Outbound Call to ${clientName} (${businessName}, ${businessType}) | Lang: ${language} | Notes: ${leadNotes ? leadNotes.substring(0, 40) + '...' : 'None'} | Agent: ${agentName}`);

  let geminiSession = null;
  let isSessionActive = true;
  const pendingMessages = [];

  const processClientMessage = (rawData) => {
    try {
      const msg = JSON.parse(rawData.toString());

      // Audio packet relay: 16kHz PCM Little-Endian Base64
      if (msg.type === 'audio' && msg.data) {
        if (geminiSession) {
          geminiSession.sendRealtimeInput({
            audio: {
              data: msg.data,
              mimeType: 'audio/pcm;rate=16000',
            },
          });
        }
      } else if (msg.type === 'text' && msg.text) {
        // Text input fallback / chat typing
        if (geminiSession) {
          geminiSession.sendClientContent({
            turns: [{ role: 'user', parts: [{ text: msg.text }] }],
            turnComplete: true,
          });
        }
      } else if (msg.type === 'end') {
        if (geminiSession) {
          try {
            geminiSession.close();
          } catch (_) {}
        }
        clientWs.close();
      }
    } catch (parseErr) {
      console.warn('[VoiceServer] Malformed packet from client:', parseErr.message);
    }
  };

  // Register message listener immediately so incoming packets are never dropped during handshake
  clientWs.on('message', (rawData) => {
    if (!geminiSession) {
      pendingMessages.push(rawData);
    } else {
      processClientMessage(rawData);
    }
  });

  try {
    // 1. Load memory context
    const memoryCtx = await loadMemoryContext(sessionId, userId);

    // 2. Obtain Gemini Client
    const ai = getGeminiClient();
    const model = process.env.GEMINI_MODEL || 'gemini-3.1-flash-live-preview';

    console.log(`[VoiceServer] Connecting to Gemini Live API with model ${model}...`);

    // 3. Connect to Gemini Multimodal Live API
    geminiSession = await ai.live.connect({
      model,
      callbacks: {
        onopen: () => {
          console.log(`[VoiceServer] Gemini Live session opened for ${sessionId}`);
          if (clientWs.readyState === clientWs.OPEN) {
            clientWs.send(
              JSON.stringify({
                type: 'status',
                status: 'connected',
                message: 'Tutor is ready! Ask your question or start talking.',
              })
            );
          }
        },
        onmessage: (message) => {
          if (!isSessionActive || clientWs.readyState !== clientWs.OPEN) return;

          const content = message.serverContent;
          if (content) {
            // 1. Model Audio Chunks (24kHz 16-bit PCM Mono)
            for (const part of content.modelTurn?.parts || []) {
              if (part.inlineData?.data) {
                clientWs.send(
                  JSON.stringify({
                    type: 'audio',
                    data: part.inlineData.data,
                    sampleRate: 24000,
                  })
                );
              }
            }

            // 2. Model Transcript
            if (content.outputTranscription?.text) {
              const text = content.outputTranscription.text;
              clientWs.send(
                JSON.stringify({
                  type: 'agent-transcription',
                  text,
                })
              );
            }

            // 3. Interruption / Barge-in Event
            if (content.interrupted) {
              console.log(`[VoiceServer] Interruption detected in session ${sessionId}`);
              clientWs.send(
                JSON.stringify({
                  type: 'interrupted',
                })
              );
            }

            // 4. User Transcript & Real-Time Sentiment
            if (content.inputTranscription?.text?.trim()) {
              const userText = content.inputTranscription.text.trim();
              const sentiment = analyzeSentiment(userText);
              void saveMemorySnippet(sessionId, userId, `User: ${userText}`);

              clientWs.send(
                JSON.stringify({
                  type: 'user-transcription',
                  text: userText,
                  sentiment,
                })
              );
            }
          }
        },
        onclose: (closeEvent) => {
          console.log(`[VoiceServer] Gemini Live session closed for ${sessionId}`);
          if (clientWs.readyState === clientWs.OPEN) {
            clientWs.send(
              JSON.stringify({
                type: 'status',
                status: 'disconnected',
                message: 'Tutor session ended.',
              })
            );
          }
        },
        onerror: (err) => {
          console.error(`[VoiceServer] Gemini Live error for ${sessionId}:`, err);
          if (clientWs.readyState === clientWs.OPEN) {
            clientWs.send(
              JSON.stringify({
                type: 'error',
                message: 'Gemini Live Session encountered an issue. Please retry.',
              })
            );
          }
        },
      },
      config: {
        responseModalities: [Modality.AUDIO],
        speechConfig: {
          voiceConfig: {
            prebuiltVoiceConfig: {
              voiceName,
            },
          },
        },
        systemInstruction: buildSystemInstruction(
          language,
          memoryCtx,
          customPersona,
          customObjective,
          clientName,
          businessName,
          businessType,
          pitchGoal,
          agentName,
          leadNotes,
          city,
          dealValue,
          phone
        ),
        outputAudioTranscription: {},
        inputAudioTranscription: {},
      },
    });

    // Flush any pending packets received while handshake was establishing
    while (pendingMessages.length > 0) {
      const pendingRaw = pendingMessages.shift();
      processClientMessage(pendingRaw);
    }

    // Notify client that connection setup is complete
    if (clientWs.readyState === clientWs.OPEN) {
      clientWs.send(
        JSON.stringify({
          type: 'status',
          status: 'connected',
          message: `Connected! Calling ${clientName} (${businessName})...`,
          clientDetails: {
            clientName,
            businessName,
            businessType,
            pitchGoal,
            agentName,
          },
        })
      );
    }

    // Proactively trigger the agent to speak its opening sales pitch greeting immediately!
    if (triggerGreeting) {
      console.log(`[VoiceServer] Outbound call active. Triggering proactive greeting for ${clientName}...`);
      geminiSession.sendClientContent({
        turns: [{
          role: 'user',
          parts: [{
            text: `[Call connected. The prospect ${clientName} just picked up the phone and said: "Hello?". Immediately speak your natural opening outbound greeting: greet them warmly by name, introduce yourself as ${agentName}, and ask if this is a quick 2 minutes to talk about ${businessName}.]`
          }]
        }],
        turnComplete: true,
      });
    }
  } catch (err) {
    console.error(`[VoiceServer] Failed to establish Gemini Live connection for ${sessionId}:`, err);
    if (clientWs.readyState === clientWs.OPEN) {
      clientWs.send(
        JSON.stringify({
          type: 'error',
          message: `Connection failed: ${err.message || 'Gemini Live initialization error'}`,
        })
      );
      clientWs.close();
    }
    return;
  }

  clientWs.on('close', () => {
    console.log(`[VoiceServer] Client disconnected: ${sessionId}`);
    activeSockets.delete(clientWs);
    isSessionActive = false;
    if (geminiSession) {
      try {
        geminiSession.close();
      } catch (_) {}
    }
  });

  clientWs.on('error', (socketErr) => {
    console.error(`[VoiceServer] Socket error on ${sessionId}:`, socketErr.message);
    activeSockets.delete(clientWs);
    isSessionActive = false;
    if (geminiSession) {
      try {
        geminiSession.close();
      } catch (_) {}
    }
  });
});

// Start Server
server.listen(PORT, HOST, () => {
  console.log('================================================================');
  console.log(`✨ Veyra Voice Live Server running on http://${HOST}:${PORT}`);
  console.log(`📡 WebSocket endpoint: ws://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}/api/ws`);
  console.log(`🔑 Loaded ${GEMINI_KEYS.length} Gemini API Key(s) for load balancing`);
  console.log(`🎙️ Model: ${process.env.GEMINI_MODEL || 'gemini-3.1-flash-live-preview'}`);
  console.log(`🔊 Voice: ${process.env.GEMINI_VOICE_NAME || 'Zephyr'}`);
  console.log('================================================================');
});
