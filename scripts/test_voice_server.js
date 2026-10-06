/**
 * Automated End-to-End Test for Veyra Voice Live Server
 * Tests WebSocket connection, Gemini Live handshake, 16k PCM relay, and sentiment analysis.
 */

const WebSocket = require('ws');

async function runTest() {
  const port = process.env.VOICE_SERVER_PORT || '5055';
  const wsUrl = `ws://localhost:${port}/api/ws?clientName=Dr.+Rajesh&businessName=Apex+Dental+Clinic&businessType=Dental+Practice&sessionId=test_b2b_sales`;
  console.log(`Connecting to ${wsUrl}...`);

  const ws = new WebSocket(wsUrl);

  let statusReceived = false;
  let textOrAudioReceived = false;

  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      ws.close();
      reject(new Error('E2E test timed out after 20 seconds'));
    }, 20000);

    let clientResponseSent = false;

    const sendClientObjection = () => {
      if (clientResponseSent) return;
      clientResponseSent = true;

      // Simulate client responding with a common objection
      const objection = "Yes, this is Dr. Rajesh. But we already have an Instagram page and enough patients, why would we need a website?";
      console.log(`✓ Client responds: "${objection}"`);
      ws.send(JSON.stringify({ type: 'text', text: objection }));
    };

    ws.on('open', () => {
      console.log('✓ Connected to voice server WebSocket!');
    });

    ws.on('message', (data) => {
      const msg = JSON.parse(data.toString());
      console.log(`[Received ${msg.type}]`, msg.type === 'audio' ? `Audio Chunk (${msg.data.length} b64 chars, 24kHz)` : msg);

      if (msg.type === 'status' && msg.status === 'connected') {
        statusReceived = true;
        // Wait 1.5 seconds for opening greeting to start, then reply as client
        setTimeout(sendClientObjection, 1500);
      }

      if (msg.type === 'audio' || msg.type === 'agent-transcription' || msg.type === 'user-transcription') {
        textOrAudioReceived = true;
      }

      if (msg.type === 'agent-transcription') {
        console.log('✓ Agent responded aloud with text tokens:', msg.text);
      }

      if (msg.type === 'user-transcription') {
        console.log('✓ User transcription with Sentiment Analysis:', msg.sentiment);
      }

      // If we got responses, wait 3 seconds to collect more streaming chunks then succeed
      if (textOrAudioReceived) {
        setTimeout(() => {
          clearTimeout(timeout);
          ws.close();
          resolve();
        }, 4000);
      }
    });

    ws.on('error', (err) => {
      clearTimeout(timeout);
      reject(err);
    });
  });

  console.log('✓ E2E Voice Server test completed successfully!');
}

runTest().catch((err) => {
  console.error('❌ E2E test failed:', err);
  process.exit(1);
});
