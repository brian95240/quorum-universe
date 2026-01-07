#!/usr/bin/env python3
"""
Voice-Aware Debate System
L1/L2 Redis caching + Speaker diarization + Symbiotic chunking
Enables real-time debate assistance with separate tracking of user vs opponents
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

try:
    import redis
    import sounddevice as sd
except ImportError:
    print("ERROR: Install dependencies: pip install redis sounddevice")
    exit(1)


# ============================================================================
# VOICE FINGERPRINTING (Speaker Diarization)
# ============================================================================

class VoiceFingerprinter:
    """
    Voice fingerprinting using audio embeddings.
    In production: use pyannote.audio for speaker diarization
    """
    
    def __init__(self):
        self.user_profiles: Dict[str, np.ndarray] = {}
        self.load_user_profiles()
    
    def load_user_profiles(self):
        """Load saved voice fingerprints from storage"""
        # In production: load from PostgreSQL
        # For now: placeholder
        pass
    
    def match_speaker(self, audio_embedding: np.ndarray) -> Optional[str]:
        """
        Match audio embedding against known user profiles.
        Returns user_id if match confidence > 0.85
        """
        for user_id, profile_embedding in self.user_profiles.items():
            similarity = np.dot(audio_embedding, profile_embedding)
            if similarity > 0.85:
                return user_id
        return None
    
    def extract_embedding(self, audio_chunk: bytes) -> np.ndarray:
        """
        Extract voice embedding from audio chunk.
        In production: use pretrained model
        """
        # Placeholder: random deterministic embedding
        audio_hash = hashlib.sha256(audio_chunk[:1000]).hexdigest()
        seed = int(audio_hash[:8], 16)
        np.random.seed(seed % (2**32))
        return np.random.randn(128)  # 128-dim embedding


# ============================================================================
# L1/L2 REDIS CACHING
# ============================================================================

class VoiceCache:
    """
    Two-tier caching for voice conversations:
    L1 (hot): Active speaker segments (300s TTL)
    L2 (warm): Synthesis + follow-up crafting (3600s TTL)
    """
    
    def __init__(self):
        try:
            self.l1 = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.l2 = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
            self.l1.ping()
            self.l2.ping()
        except Exception as e:
            print(f"ERROR: Redis not available: {e}")
            exit(1)
    
    def store_segment_l1(self, session_id: str, speaker_id: str, segment: Dict):
        """Store speaker segment in L1 (hot cache)"""
        key = f"session:{session_id}:speaker:{speaker_id}:segments"
        
        self.l1.lpush(key, json.dumps(segment))
        self.l1.expire(key, 300)  # 5 minutes TTL
    
    def get_segments_l1(self, session_id: str, speaker_id: str) -> List[Dict]:
        """Retrieve speaker segments from L1"""
        key = f"session:{session_id}:speaker:{speaker_id}:segments"
        
        segments_raw = self.l1.lrange(key, 0, -1)
        return [json.loads(s) for s in segments_raw]
    
    def store_synthesis_l2(self, session_id: str, user_id: str, synthesis: Dict):
        """Store synthesis in L2 (warm cache)"""
        key = f"session:{session_id}:user:{user_id}:synthesis"
        
        self.l2.hset(key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else v 
                                    for k, v in synthesis.items()})
        self.l2.expire(key, 3600)  # 1 hour TTL
    
    def get_synthesis_l2(self, session_id: str, user_id: str) -> Dict:
        """Retrieve synthesis from L2"""
        key = f"session:{session_id}:user:{user_id}:synthesis"
        
        data = self.l2.hgetall(key)
        return {k: json.loads(v) if k in ['rebuttal', 'follow_ups', 'tribunal_verdict'] else v 
                for k, v in data.items()}


# ============================================================================
# SYMBIOTIC CHUNKER (Practice Mode)
# ============================================================================

class SymbioticChunker:
    """
    Learn user's optimal chunk size and delivery speed.
    Enables natural back-and-forth conversation flow.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.profile = self.load_profile()
    
    def load_profile(self) -> Dict:
        """Load learned preferences from storage"""
        # Default profile
        return {
            'words_per_chunk': 20,
            'speech_speed_wpm': 140,
            'pause_threshold_ms': 800,
            'confidence': 0.65
        }
    
    def create_chunks(self, text: str) -> List[str]:
        """
        Split text into optimal chunks based on:
        - User's words_per_chunk preference
        - Natural sentence boundaries
        - Logical pause points
        """
        words = text.split()
        chunks = []
        
        current_chunk = []
        for word in words:
            current_chunk.append(word)
            
            # Check if we've hit target size
            if len(current_chunk) >= self.profile['words_per_chunk']:
                # Look for natural break
                if word.endswith(('.', '!', '?', ',', ';', ':')):
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
        
        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def practice_session(self, sample_text: str) -> Dict:
        """
        Interactive practice to learn user's rhythm:
        1. User speaks
        2. AI delivers chunk
        3. Wait for user pause
        4. Continue until seamless
        """
        chunks = self.create_chunks(sample_text)
        
        timings = []
        
        for i, chunk in enumerate(chunks):
            print(f"\n[Chunk {i+1}/{len(chunks)}]")
            print(f"User: (speaking...)")
            
            # Simulate user speech detection
            await asyncio.sleep(2)
            
            print(f"AI: {chunk}")
            
            # Simulate delivery
            words = len(chunk.split())
            delivery_time = (words / self.profile['speech_speed_wpm']) * 60
            await asyncio.sleep(delivery_time)
            
            # Wait for next user segment
            await asyncio.sleep(1)
            
            # Record timing
            timings.append({
                'chunk_index': i,
                'seamlessness_score': 0.9  # Simplified
            })
        
        # Update profile based on timings
        avg_score = np.mean([t['seamlessness_score'] for t in timings])
        
        self.profile['confidence'] = min(self.profile['confidence'] + 0.05, 0.95)
        
        return {
            'profile': self.profile,
            'practice_score': avg_score
        }
    
    def calculate_delivery_time(self, chunk: str) -> float:
        """Calculate delivery time for chunk at user's speed"""
        words = len(chunk.split())
        return (words / self.profile['speech_speed_wpm']) * 60


# ============================================================================
# VOICE-AWARE DEBATE SYSTEM
# ============================================================================

class VoiceAwareDebateSystem:
    """
    Main system integrating voice fingerprinting, caching, and debate assistance
    """
    
    def __init__(self):
        self.fingerprinter = VoiceFingerprinter()
        self.cache = VoiceCache()
        self.active_sessions: Dict[str, Dict] = {}
    
    async def process_audio_stream(
        self,
        session_id: str,
        audio_chunk: bytes,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Real-time processing of audio stream.
        Identifies speakers, caches conversations separately.
        """
        
        # Step 1: Extract voice embedding
        embedding = self.fingerprinter.extract_embedding(audio_chunk)
        
        # Step 2: Match against user profiles
        user_match = self.fingerprinter.match_speaker(embedding)
        
        if user_match:
            speaker_type = 'user'
            speaker_id = user_match
        else:
            speaker_type = 'anomaly'
            speaker_id = f"anomaly_{hashlib.sha256(audio_chunk[:100]).hexdigest()[:8]}"
        
        # Step 3: Transcribe (simplified - use Whisper in production)
        text = await self.transcribe(audio_chunk)
        
        # Step 4: Store in L1 cache
        segment = {
            'speaker_type': speaker_type,
            'speaker_id': speaker_id,
            'text': text,
            'timestamp': time.time(),
            'embedding': embedding.tolist()[:10]  # Store first 10 dims
        }
        
        self.cache.store_segment_l1(session_id, speaker_id, segment)
        
        # Step 5: Trigger L2 synthesis if anomaly speaking
        if speaker_type == 'anomaly':
            asyncio.create_task(
                self.synthesize_responses(session_id, speaker_id)
            )
        
        return {
            'speaker_type': speaker_type,
            'speaker_id': speaker_id,
            'text': text,
            'cached': True
        }
    
    async def transcribe(self, audio_chunk: bytes) -> str:
        """
        Transcribe audio to text.
        In production: use Whisper or similar
        """
        # Placeholder
        return "[Transcribed speech placeholder]"
    
    async def synthesize_responses(self, session_id: str, anomaly_id: str):
        """
        L2 synthesis: Craft user's follow-up while anomaly is speaking.
        Runs in parallel to L1 conversation tracking.
        """
        
        # Get all segments
        user_segments = []
        anomaly_segments = []
        
        # Find user ID in this session
        # Simplified - would track in session metadata
        user_id = "user_default"
        
        # Get user's position
        user_segments = self.cache.get_segments_l1(session_id, user_id)
        user_position = "\n".join([s['text'] for s in user_segments])
        
        # Get anomaly's points
        anomaly_segments = self.cache.get_segments_l1(session_id, anomaly_id)
        anomaly_points = [s['text'] for s in anomaly_segments]
        
        # Parallel synthesis tasks
        tasks = [
            self.craft_rebuttal(user_position, anomaly_points),
            self.craft_follow_ups(anomaly_points),
            self.craft_clarifications(user_position)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Store in L2
        synthesis = {
            'rebuttal': results[0],
            'follow_ups': results[1],
            'clarifications': results[2],
            'timestamp': time.time()
        }
        
        self.cache.store_synthesis_l2(session_id, user_id, synthesis)
        
        print(f"✓ L2 synthesis complete for session {session_id}")
    
    async def craft_rebuttal(self, user_position: str, anomaly_points: List[str]) -> str:
        """
        Craft rebuttal using archetype router.
        In production: integrate with archetype_router.py
        """
        # Placeholder
        return f"Rebuttal to opponent's {len(anomaly_points)} points..."
    
    async def craft_follow_ups(self, anomaly_points: List[str]) -> List[str]:
        """Generate follow-up questions"""
        # Placeholder
        return [f"Follow-up question {i+1}" for i in range(3)]
    
    async def craft_clarifications(self, user_position: str) -> str:
        """Generate clarifying points"""
        # Placeholder
        return "Clarification of your position..."
    
    async def get_debate_assistance(self, session_id: str, user_id: str) -> Dict:
        """
        Retrieve crafted responses from L2 cache.
        User calls this when ready to respond.
        """
        synthesis = self.cache.get_synthesis_l2(session_id, user_id)
        
        if not synthesis:
            return {
                'status': 'not_ready',
                'message': 'Synthesis still processing or no opponent detected'
            }
        
        # Chunk rebuttal for symbiotic delivery
        chunker = SymbioticChunker(user_id)
        rebuttal_chunks = chunker.create_chunks(synthesis['rebuttal'])
        
        return {
            'status': 'ready',
            'rebuttal': synthesis['rebuttal'],
            'rebuttal_chunks': rebuttal_chunks,
            'follow_up_questions': synthesis['follow_ups'],
            'clarifications': synthesis['clarifications'],
            'delivery_profile': chunker.profile
        }


# ============================================================================
# SPEECH REFINER (Export/Import)
# ============================================================================

class SpeechRefiner:
    """
    Export/import speeches for tribunal refinement.
    Enables memorization-ready delivery.
    """
    
    async def export_interaction(
        self,
        session_id: str,
        format: str = 'json'
    ) -> str:
        """
        Export complete interaction with analysis.
        """
        cache = VoiceCache()
        
        # Get all segments from L1
        # Simplified - would iterate over all speakers
        user_segments = cache.get_segments_l1(session_id, "user_default")
        
        # Get synthesis from L2
        synthesis = cache.get_synthesis_l2(session_id, "user_default")
        
        export_data = {
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat(),
            'user_segments': user_segments,
            'synthesis': synthesis,
            'memorization_chunks': self.create_memorization_chunks(
                synthesis.get('rebuttal', '')
            )
        }
        
        if format == 'json':
            return json.dumps(export_data, indent=2)
        elif format == 'markdown':
            return self.format_as_markdown(export_data)
        else:
            return str(export_data)
    
    def create_memorization_chunks(self, text: str) -> List[Dict]:
        """Break text into memorizable chunks"""
        chunker = SymbioticChunker("user_default")
        chunks = chunker.create_chunks(text)
        
        return [
            {
                'index': i,
                'text': chunk,
                'word_count': len(chunk.split()),
                'estimated_duration': chunker.calculate_delivery_time(chunk)
            }
            for i, chunk in enumerate(chunks)
        ]
    
    def format_as_markdown(self, data: Dict) -> str:
        """Format export as markdown"""
        md = []
        md.append(f"# Debate Session: {data['session_id']}")
        md.append(f"\n**Timestamp:** {data['timestamp']}\n")
        
        md.append("## User Segments")
        for seg in data['user_segments']:
            md.append(f"- {seg['text']}")
        
        md.append("\n## Synthesis")
        md.append(data['synthesis'].get('rebuttal', 'N/A'))
        
        md.append("\n## Memorization Chunks")
        for chunk in data['memorization_chunks']:
            md.append(f"\n### Chunk {chunk['index'] + 1}")
            md.append(f"{chunk['text']}")
            md.append(f"*({chunk['word_count']} words, ~{chunk['estimated_duration']:.1f}s)*")
        
        return "\n".join(md)


# ============================================================================
# CLI INTERFACE
# ============================================================================

async def demo():
    """Demo the voice-aware debate system"""
    print("\n" + "="*80)
    print("VOICE-AWARE DEBATE SYSTEM - DEMO")
    print("="*80 + "\n")
    
    system = VoiceAwareDebateSystem()
    
    # Simulate a debate session
    session_id = "demo_session_001"
    
    print("Simulating debate with 2 speakers...\n")
    
    # User speaks
    print("[User speaking...]")
    await system.process_audio_stream(
        session_id,
        b"user_audio_chunk_1",
        context={'topic': 'AI safety'}
    )
    
    await asyncio.sleep(1)
    
    # Opponent speaks
    print("[Opponent speaking...]")
    await system.process_audio_stream(
        session_id,
        b"opponent_audio_chunk_1",
        context={'topic': 'AI safety'}
    )
    
    print("\n⏳ Synthesizing responses in L2 cache...\n")
    await asyncio.sleep(2)
    
    # User requests assistance
    print("[User requests debate assistance]\n")
    assistance = await system.get_debate_assistance(session_id, "user_default")
    
    if assistance['status'] == 'ready':
        print("✓ Assistance ready:")
        print(f"\nRebuttal (chunked):")
        for i, chunk in enumerate(assistance['rebuttal_chunks'], 1):
            print(f"  {i}. {chunk}")
        
        print(f"\nFollow-ups:")
        for q in assistance['follow_up_questions']:
            print(f"  - {q}")
        
        print(f"\nDelivery profile:")
        print(f"  Words per chunk: {assistance['delivery_profile']['words_per_chunk']}")
        print(f"  Speech speed: {assistance['delivery_profile']['speech_speed_wpm']} WPM")
    
    # Export session
    print("\n" + "-"*80)
    print("Exporting session...\n")
    
    refiner = SpeechRefiner()
    markdown = await refiner.export_interaction(session_id, format='markdown')
    
    print(markdown)
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(demo())
