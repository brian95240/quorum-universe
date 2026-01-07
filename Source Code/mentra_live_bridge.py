#!/usr/bin/env python3
"""
Mentra Live Bridge - AR Glasses Voice Interface
WebSocket bridge for real-time voice interaction with AR glasses

Architecture:
1. WebSocket server for bidirectional communication
2. Audio transcription (Whisper integration)
3. Query processing through ambient intelligence pipeline
4. Real-time response streaming to glasses display
5. Voice synthesis (TTS) for audio feedback
6. Gesture recognition (optional future enhancement)

Data Flow:
Glasses → Audio Stream → Transcription → Query → Pipeline → Response → 
  → Text Rendering (AR overlay) + TTS → Audio → Glasses

Performance Targets:
- Transcription latency: <500ms
- Query response: <3s (warm path)
- Total interaction: <4s (question to answer)
- WebSocket throughput: >100 messages/sec

Integration Points:
- Mentra Live WebSocket protocol
- Whisper (local speech-to-text)
- Piper TTS (local text-to-speech)
- Ambient intelligence pipeline (query processing)
"""

import asyncio
import json
import time
import wave
import io
import base64
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib

# WebSocket
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    print("WARNING: websockets not available. Install: pip install websockets")
    WEBSOCKETS_AVAILABLE = False

# Audio processing
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    print("WARNING: numpy not available")
    NUMPY_AVAILABLE = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class MessageType(Enum):
    """WebSocket message types"""
    AUDIO_CHUNK = "audio_chunk"           # Audio data from glasses
    TRANSCRIPTION = "transcription"       # Text from speech
    QUERY = "query"                       # User query
    RESPONSE_CHUNK = "response_chunk"     # Streaming response
    RESPONSE_COMPLETE = "response_complete"  # Final response
    TTS_AUDIO = "tts_audio"              # Generated speech audio
    ERROR = "error"                       # Error message
    PING = "ping"                         # Heartbeat
    PONG = "pong"                         # Heartbeat response
    METADATA = "metadata"                 # Session metadata


@dataclass
class AudioChunk:
    """Audio data chunk"""
    data: bytes
    sample_rate: int = 16000
    channels: int = 1
    timestamp: float = 0.0


@dataclass
class TranscriptionResult:
    """Speech-to-text result"""
    text: str
    confidence: float
    language: str = "en"
    timestamp: float = 0.0


@dataclass
class ARDisplayConfig:
    """AR display configuration"""
    font_size: int = 24
    color: str = "#FFFFFF"
    background_alpha: float = 0.7
    position: str = "bottom_center"  # bottom_center, top_left, etc.
    max_lines: int = 3
    word_wrap: bool = True


@dataclass
class VoiceSession:
    """Voice interaction session"""
    session_id: str
    user_id: str
    connection_time: float
    last_activity: float
    
    # Audio buffer
    audio_buffer: List[AudioChunk] = field(default_factory=list)
    
    # Conversation
    conversation_history: List[Dict] = field(default_factory=list)
    
    # State
    is_recording: bool = False
    is_processing: bool = False
    
    # Statistics
    total_queries: int = 0
    total_audio_chunks: int = 0
    avg_response_time: float = 0.0


# ============================================================================
# TRANSCRIPTION ENGINE
# ============================================================================

class TranscriptionEngine:
    """
    Local speech-to-text using Whisper.
    
    Provides real-time transcription with minimal latency.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize transcription engine.
        
        Args:
            model_name: Whisper model (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        
        # Try to import Whisper
        try:
            import whisper
            self.whisper = whisper
            self.model = whisper.load_model(model_name)
            print(f"✓ Whisper model loaded: {model_name}")
        except ImportError:
            print("WARNING: openai-whisper not available")
            print("  Install: pip install openai-whisper")
        
        # Statistics
        self.total_transcriptions = 0
        self.avg_transcription_time = 0.0
    
    async def transcribe(self, audio_chunks: List[AudioChunk]) -> TranscriptionResult:
        """
        Transcribe audio chunks to text.
        
        Args:
            audio_chunks: List of audio data chunks
        
        Returns:
            Transcription result
        """
        start_time = time.time()
        
        if not self.model:
            # Mock transcription
            return TranscriptionResult(
                text="This is a mock transcription",
                confidence=0.95,
                timestamp=time.time()
            )
        
        try:
            # Concatenate audio chunks
            audio_data = b''.join([chunk.data for chunk in audio_chunks])
            
            # Convert to numpy array (Whisper expects float32)
            if NUMPY_AVAILABLE:
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                # Fallback: mock
                return TranscriptionResult(
                    text="Mock transcription (numpy unavailable)",
                    confidence=0.95,
                    timestamp=time.time()
                )
            
            # Transcribe
            result = self.model.transcribe(audio_array, language="en")
            
            # Update statistics
            transcription_time = time.time() - start_time
            self.total_transcriptions += 1
            self.avg_transcription_time = (
                (self.avg_transcription_time * (self.total_transcriptions - 1) +
                 transcription_time) / self.total_transcriptions
            )
            
            return TranscriptionResult(
                text=result['text'].strip(),
                confidence=1.0,  # Whisper doesn't provide confidence
                language=result.get('language', 'en'),
                timestamp=time.time()
            )
        
        except Exception as e:
            print(f"Transcription error: {e}")
            return TranscriptionResult(
                text="[transcription error]",
                confidence=0.0,
                timestamp=time.time()
            )


# ============================================================================
# TTS ENGINE
# ============================================================================

class TTSEngine:
    """
    Local text-to-speech using Piper.
    
    Generates natural-sounding speech for AR audio feedback.
    """
    
    def __init__(self, voice: str = "en_US-lessac-medium"):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice model name
        """
        self.voice = voice
        
        print(f"TTSEngine initialized (voice: {voice})")
        print("  Note: Actual Piper TTS integration pending")
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio data (WAV format)
        """
        # Mock TTS (in production: use Piper)
        # For now, return empty audio
        
        # Generate simple WAV header (mock)
        sample_rate = 22050
        duration = len(text) * 0.05  # Approximate duration
        num_samples = int(sample_rate * duration)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # Silent audio (mock)
            if NUMPY_AVAILABLE:
                audio_data = np.zeros(num_samples, dtype=np.int16)
                wav_file.writeframes(audio_data.tobytes())
            else:
                wav_file.writeframes(b'\x00' * num_samples * 2)
        
        return wav_buffer.getvalue()


# ============================================================================
# MENTRA LIVE BRIDGE
# ============================================================================

class MentraLiveBridge:
    """
    WebSocket server for Mentra Live AR glasses.
    
    Handles voice interaction and real-time response streaming.
    """
    
    def __init__(self,
                 host: str = "0.0.0.0",
                 port: int = 8765,
                 pipeline_callback: Optional[Callable] = None):
        """
        Initialize Mentra Live bridge.
        
        Args:
            host: WebSocket host
            port: WebSocket port
            pipeline_callback: Callback for query processing
        """
        self.host = host
        self.port = port
        self.pipeline_callback = pipeline_callback
        
        # Components
        self.transcription_engine = TranscriptionEngine(model_name="base")
        self.tts_engine = TTSEngine()
        
        # Active sessions
        self.sessions: Dict[str, VoiceSession] = {}
        
        # Statistics
        self.total_connections = 0
        self.active_connections = 0
        
        print(f"MentraLiveBridge initialized")
        print(f"  WebSocket: {host}:{port}")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """
        Handle WebSocket client connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        # Generate session ID
        session_id = hashlib.sha256(
            f"{websocket.remote_address}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        # Create session
        session = VoiceSession(
            session_id=session_id,
            user_id="user_123",  # In production: authenticate
            connection_time=time.time(),
            last_activity=time.time()
        )
        
        self.sessions[session_id] = session
        self.total_connections += 1
        self.active_connections += 1
        
        print(f"✓ New connection: {session_id} from {websocket.remote_address}")
        
        try:
            # Send welcome message
            await self._send_message(websocket, {
                'type': MessageType.METADATA.value,
                'session_id': session_id,
                'message': 'Connected to Ambient Intelligence'
            })
            
            # Message loop
            async for message in websocket:
                await self._handle_message(websocket, session, message)
        
        except Exception as e:
            # Handle both websocket-specific and general errors
            if WEBSOCKETS_AVAILABLE and "ConnectionClosed" in str(type(e).__name__):
                print(f"✗ Connection closed: {session_id}")
            else:
                print(f"Error handling client: {e}")
        
        finally:
            # Cleanup session
            del self.sessions[session_id]
            self.active_connections -= 1
            print(f"  Active connections: {self.active_connections}")
    
    async def _handle_message(self,
                             websocket: WebSocketServerProtocol,
                             session: VoiceSession,
                             message: str):
        """
        Handle incoming WebSocket message.
        
        Args:
            websocket: WebSocket connection
            session: Session state
            message: Message data
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            session.last_activity = time.time()
            
            if msg_type == MessageType.AUDIO_CHUNK.value:
                await self._handle_audio_chunk(websocket, session, data)
            
            elif msg_type == MessageType.QUERY.value:
                await self._handle_query(websocket, session, data)
            
            elif msg_type == MessageType.PING.value:
                await self._send_message(websocket, {
                    'type': MessageType.PONG.value,
                    'timestamp': time.time()
                })
            
            else:
                print(f"Unknown message type: {msg_type}")
        
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON")
        
        except Exception as e:
            await self._send_error(websocket, str(e))
    
    async def _handle_audio_chunk(self,
                                  websocket: WebSocketServerProtocol,
                                  session: VoiceSession,
                                  data: Dict):
        """Handle audio chunk from glasses"""
        # Decode audio data
        audio_data = base64.b64decode(data.get('data', ''))
        
        chunk = AudioChunk(
            data=audio_data,
            sample_rate=data.get('sample_rate', 16000),
            channels=data.get('channels', 1),
            timestamp=time.time()
        )
        
        session.audio_buffer.append(chunk)
        session.total_audio_chunks += 1
        
        # Check if recording is complete
        if data.get('final', False):
            # Transcribe audio
            transcription = await self.transcription_engine.transcribe(
                session.audio_buffer
            )
            
            # Send transcription
            await self._send_message(websocket, {
                'type': MessageType.TRANSCRIPTION.value,
                'text': transcription.text,
                'confidence': transcription.confidence
            })
            
            # Process as query
            await self._handle_query(websocket, session, {
                'query': transcription.text
            })
            
            # Clear audio buffer
            session.audio_buffer.clear()
    
    async def _handle_query(self,
                           websocket: WebSocketServerProtocol,
                           session: VoiceSession,
                           data: Dict):
        """Handle user query"""
        query = data.get('query', '')
        
        if not query:
            return
        
        session.total_queries += 1
        session.is_processing = True
        
        # Add to conversation history
        session.conversation_history.append({
            'role': 'user',
            'content': query,
            'timestamp': time.time()
        })
        
        start_time = time.time()
        
        # Process through pipeline (or mock)
        if self.pipeline_callback:
            # Real pipeline
            response = await self.pipeline_callback(query, session.user_id)
        else:
            # Mock response
            await asyncio.sleep(0.5)  # Simulate processing
            response = f"Response to: {query}"
        
        # Stream response to glasses
        await self._stream_response(websocket, response)
        
        # Generate TTS audio
        tts_audio = await self.tts_engine.synthesize(response)
        
        # Send TTS audio
        await self._send_message(websocket, {
            'type': MessageType.TTS_AUDIO.value,
            'data': base64.b64encode(tts_audio).decode('utf-8'),
            'format': 'wav'
        })
        
        # Add to conversation history
        session.conversation_history.append({
            'role': 'assistant',
            'content': response,
            'timestamp': time.time()
        })
        
        # Update statistics
        response_time = time.time() - start_time
        session.avg_response_time = (
            (session.avg_response_time * (session.total_queries - 1) +
             response_time) / session.total_queries
        )
        
        session.is_processing = False
    
    async def _stream_response(self,
                              websocket: WebSocketServerProtocol,
                              response: str,
                              chunk_size: int = 30):
        """
        Stream response to glasses in chunks.
        
        Args:
            websocket: WebSocket connection
            response: Full response text
            chunk_size: Characters per chunk
        """
        # Stream in chunks
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i + chunk_size]
            
            await self._send_message(websocket, {
                'type': MessageType.RESPONSE_CHUNK.value,
                'chunk': chunk,
                'progress': (i + len(chunk)) / len(response)
            })
            
            await asyncio.sleep(0.05)  # 50ms delay for smooth streaming
        
        # Send completion
        await self._send_message(websocket, {
            'type': MessageType.RESPONSE_COMPLETE.value,
            'total_chars': len(response)
        })
    
    async def _send_message(self,
                           websocket: WebSocketServerProtocol,
                           data: Dict):
        """Send message to client"""
        try:
            await websocket.send(json.dumps(data))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def _send_error(self,
                         websocket: WebSocketServerProtocol,
                         error: str):
        """Send error message"""
        await self._send_message(websocket, {
            'type': MessageType.ERROR.value,
            'error': error
        })
    
    async def start(self):
        """Start WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            print("ERROR: websockets library not available")
            return
        
        print(f"\nStarting Mentra Live Bridge...")
        print(f"  WebSocket server: ws://{self.host}:{self.port}")
        print(f"  Waiting for connections...")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    def get_stats(self) -> Dict:
        """Get bridge statistics"""
        return {
            'total_connections': self.total_connections,
            'active_connections': self.active_connections,
            'total_sessions': len(self.sessions),
            'avg_transcription_time': self.transcription_engine.avg_transcription_time,
            'sessions': [
                {
                    'session_id': session.session_id,
                    'total_queries': session.total_queries,
                    'avg_response_time': session.avg_response_time,
                    'audio_chunks': session.total_audio_chunks
                }
                for session in self.sessions.values()
            ]
        }


# ============================================================================
# TESTING
# ============================================================================

async def mock_pipeline_callback(query: str, user_id: str) -> str:
    """Mock pipeline for testing"""
    await asyncio.sleep(0.5)
    return f"Mock response to: {query}"


async def test_bridge():
    """Test Mentra Live bridge"""
    
    # Initialize bridge
    bridge = MentraLiveBridge(
        host="0.0.0.0",
        port=8765,
        pipeline_callback=mock_pipeline_callback
    )
    
    print("\nTesting Mentra Live Bridge")
    print("=" * 80)
    print("\nConnect using WebSocket client:")
    print("  ws://localhost:8765")
    print("\nExample messages:")
    print('  Query: {"type": "query", "query": "What is quantum entanglement?"}')
    print('  Ping: {"type": "ping"}')
    print("\nPress Ctrl+C to stop")
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        
        # Show statistics
        stats = bridge.get_stats()
        print(f"\nSession Statistics:")
        print(f"  Total connections: {stats['total_connections']}")
        print(f"  Total sessions: {stats['total_sessions']}")
        
        if stats['sessions']:
            for session in stats['sessions']:
                print(f"\n  Session: {session['session_id']}")
                print(f"    Queries: {session['total_queries']}")
                print(f"    Avg response time: {session['avg_response_time']:.2f}s")


if __name__ == "__main__":
    asyncio.run(test_bridge())
