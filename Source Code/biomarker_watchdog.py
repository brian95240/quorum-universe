#!/usr/bin/env python3
"""
Biomarker Watchdog - Real-time Health Monitoring
Lazy-loads medical archetypes based on physiological triggers
Integrates with wearables: smartwatch, heart strap, AR glasses
"""

import asyncio
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque

try:
    import redis
except ImportError:
    print("ERROR: Install redis: pip install redis")
    exit(1)


# ============================================================================
# BIOMARKER THRESHOLDS (Personalized per user)
# ============================================================================

DEFAULT_THRESHOLDS = {
    'hrv': {
        'min': 30,
        'max': 100,
        'critical_low': 20,
        'unit': 'ms'
    },
    'heart_rate': {
        'min': 50,
        'max': 100,
        'critical_high': 180,
        'unit': 'bpm'
    },
    'spo2': {
        'min': 95,
        'max': 100,
        'critical_low': 92,
        'unit': '%'
    },
    'respiratory_rate': {
        'min': 12,
        'max': 20,
        'critical_high': 30,
        'unit': 'breaths/min'
    },
    'glucose': {
        'min': 70,
        'max': 140,
        'critical_high': 180,
        'unit': 'mg/dL'
    },
    'cortisol': {
        'max': 25,
        'critical_high': 40,
        'unit': 'μg/dL'
    },
    'body_temp': {
        'min': 97.0,
        'max': 99.5,
        'critical_high': 101.0,
        'unit': '°F'
    }
}


# ============================================================================
# ORGAN SYSTEM MAPPING
# ============================================================================

BIOMARKER_TO_ORGAN = {
    'hrv': 'cardiovascular',
    'heart_rate': 'cardiovascular',
    'spo2': 'respiratory',
    'respiratory_rate': 'respiratory',
    'glucose': 'endocrine',
    'cortisol': 'stress_psychological',
    'body_temp': 'infectious_disease'
}

ORGAN_TO_ARCHETYPES = {
    'cardiovascular': ['harvard_med', 'longevity_research'],
    'respiratory': ['harvard_med', 'caltech_physics'],  # O2 transport
    'endocrine': ['harvard_med', 'broad_genomics'],
    'stress_psychological': ['berkeley_psychedelics', 'harvard_med'],
    'infectious_disease': ['harvard_med', 'baghdad_golden']
}


# ============================================================================
# BIOMARKER WATCHDOG
# ============================================================================

class BiomarkerWatchdog:
    """
    Real-time health monitoring with archetype lazy-loading.
    Monitors Redis stream for biomarker data from wearables.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Redis connection
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
            self.redis.ping()
        except Exception as e:
            print(f"ERROR: Redis not available: {e}")
            exit(1)
        
        # Load user thresholds
        self.thresholds = self.load_thresholds()
        
        # Active archetypes (lazy-loaded)
        self.active_archetypes = set()
        
        # History buffer (for trend analysis)
        self.history: Dict[str, deque] = {
            biomarker: deque(maxlen=100) for biomarker in DEFAULT_THRESHOLDS.keys()
        }
    
    def load_thresholds(self) -> Dict:
        """
        Load personalized thresholds from storage.
        In production: query from user profile in PostgreSQL
        """
        # Check cache
        cache_key = f"user:{self.user_id}:thresholds"
        cached = self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # Use defaults
        return DEFAULT_THRESHOLDS
    
    async def monitor_stream(self):
        """
        Continuous monitoring via Redis streams.
        Sensors publish to 'biomarkers' stream, watchdog consumes.
        """
        print(f"\n{'='*80}")
        print(f"BIOMARKER WATCHDOG - User: {self.user_id}")
        print(f"{'='*80}\n")
        
        print("Monitoring Redis stream: 'biomarkers'")
        print("Waiting for sensor data...\n")
        
        last_id = '0'  # Start from beginning
        
        while True:
            try:
                # Read from stream (blocking for 1 second)
                messages = self.redis.xread(
                    {'biomarkers': last_id},
                    count=10,
                    block=1000
                )
                
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, data in stream_messages:
                            last_id = message_id
                            await self.process_biomarker(data)
            
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping watchdog...")
                break
            
            except Exception as e:
                print(f"⚠️  Stream error: {e}")
                await asyncio.sleep(5)
    
    async def process_biomarker(self, data: Dict):
        """
        Check biomarker against thresholds.
        Lazy-load archetypes if warning detected.
        """
        biomarker = data.get('type')
        value = float(data.get('value', 0))
        timestamp = data.get('timestamp', time.time())
        source = data.get('source', 'unknown')
        
        # Check thresholds
        threshold = self.thresholds.get(biomarker)
        if not threshold:
            return  # Unknown biomarker
        
        status = self.check_threshold(biomarker, value, threshold)
        
        # Log to history
        self.history[biomarker].append({
            'value': value,
            'timestamp': timestamp,
            'status': status
        })
        
        # Print status
        unit = threshold.get('unit', '')
        print(f"[{datetime.fromtimestamp(float(timestamp)).strftime('%H:%M:%S')}] "
              f"{biomarker.upper()}: {value} {unit} [{status}] ({source})")
        
        # Take action based on status
        if status == 'critical':
            await self.trigger_emergency_protocol(biomarker, value, data)
        
        elif status == 'warning':
            await self.lazy_load_archetype(biomarker, value, data)
    
    def check_threshold(self, biomarker: str, value: float, threshold: Dict) -> str:
        """
        Determine if biomarker is normal, warning, or critical.
        """
        if 'critical_low' in threshold and value < threshold['critical_low']:
            return 'critical'
        if 'critical_high' in threshold and value > threshold['critical_high']:
            return 'critical'
        if value < threshold.get('min', float('-inf')):
            return 'warning'
        if value > threshold.get('max', float('inf')):
            return 'warning'
        return 'normal'
    
    async def lazy_load_archetype(self, biomarker: str, value: float, data: Dict):
        """
        Lazy-load specialized archetype based on biomarker.
        Only loads if not already active.
        """
        # Map biomarker to organ system
        organ = BIOMARKER_TO_ORGAN.get(biomarker)
        if not organ:
            return
        
        # Get required archetypes
        required_archetypes = ORGAN_TO_ARCHETYPES.get(organ, ['harvard_med'])
        
        # Check which aren't loaded
        new_archetypes = [
            arch for arch in required_archetypes
            if arch not in self.active_archetypes
        ]
        
        if new_archetypes:
            print(f"\n⚠️  WARNING DETECTED")
            print(f"   {biomarker}: {value} {self.thresholds[biomarker]['unit']}")
            print(f"   Organ system: {organ}")
            print(f"   🔥 Lazy-loading archetypes: {', '.join(new_archetypes)}\n")
            
            for archetype in new_archetypes:
                await self.load_archetype(archetype)
                self.active_archetypes.add(archetype)
            
            # Generate guidance
            guidance = await self.generate_guidance(biomarker, value, required_archetypes, data)
            
            # Display guidance
            print(f"{'─'*80}")
            print("GUIDANCE")
            print(f"{'─'*80}")
            print(guidance)
            print(f"{'─'*80}\n")
    
    async def load_archetype(self, archetype: str):
        """
        Background load archetype model.
        In production: use Ollama API to load model
        """
        print(f"   Loading {archetype}...")
        
        # Simulate load time
        await asyncio.sleep(0.5)
        
        print(f"   ✓ {archetype} ready")
    
    async def generate_guidance(
        self,
        biomarker: str,
        value: float,
        archetypes: List[str],
        context: Dict
    ) -> str:
        """
        Query loaded archetypes for health guidance.
        In production: integrate with archetype_router.py
        """
        guidance = []
        
        guidance.append(f"Biomarker alert: {biomarker} = {value} {self.thresholds[biomarker]['unit']}")
        guidance.append(f"Time: {datetime.fromtimestamp(float(context.get('timestamp', time.time()))).strftime('%Y-%m-%d %H:%M:%S')}")
        guidance.append(f"Source: {context.get('source', 'unknown')}")
        guidance.append("")
        
        # Analyze trend
        trend = self.analyze_trend(biomarker)
        guidance.append(f"Trend: {trend}")
        guidance.append("")
        
        # Generate recommendations (simplified)
        guidance.append("Recommendations:")
        
        if biomarker == 'hrv' and value < 30:
            guidance.append("  • HRV below normal range - consider stress reduction")
            guidance.append("  • Ensure adequate sleep (7-9 hours)")
            guidance.append("  • Avoid intense exercise today")
        
        elif biomarker == 'heart_rate' and value > 100:
            guidance.append("  • Elevated resting heart rate detected")
            guidance.append("  • Check for fever, dehydration, or stress")
            guidance.append("  • Monitor for 30 minutes - seek care if persists")
        
        elif biomarker == 'spo2' and value < 95:
            guidance.append("  • Oxygen saturation below normal")
            guidance.append("  • Take deep breaths, sit upright")
            guidance.append("  • If < 92%, seek immediate medical attention")
        
        elif biomarker == 'glucose' and value > 140:
            guidance.append("  • Elevated blood glucose detected")
            guidance.append("  • Avoid high-carb foods for 2-3 hours")
            guidance.append("  • Light walk may help lower glucose")
        
        elif biomarker == 'cortisol' and value > 25:
            guidance.append("  • Elevated cortisol (stress hormone)")
            guidance.append("  • Practice breathing exercises")
            guidance.append("  • Consider short meditation break")
        
        else:
            guidance.append(f"  • {biomarker} outside normal range")
            guidance.append("  • Monitor closely and note any symptoms")
        
        guidance.append("")
        guidance.append(f"Consulted: {', '.join(archetypes)}")
        
        return "\n".join(guidance)
    
    async def trigger_emergency_protocol(self, biomarker: str, value: float, data: Dict):
        """
        Critical value detected - emergency response.
        """
        print(f"\n🚨 CRITICAL ALERT 🚨")
        print(f"   {biomarker}: {value} {self.thresholds[biomarker]['unit']}")
        print(f"   IMMEDIATE ACTION REQUIRED\n")
        
        # Load all medical archetypes immediately
        medical_archetypes = ['harvard_med', 'longevity_research']
        
        for arch in medical_archetypes:
            if arch not in self.active_archetypes:
                await self.load_archetype(arch)
                self.active_archetypes.add(arch)
        
        # Generate emergency guidance
        guidance = await self.generate_guidance(biomarker, value, medical_archetypes, data)
        
        print(f"{'━'*80}")
        print("EMERGENCY GUIDANCE")
        print(f"{'━'*80}")
        print(guidance)
        print(f"{'━'*80}\n")
        
        # Optional: Notify emergency contact
        print("📞 Consider notifying emergency contact or seeking immediate care")
    
    def analyze_trend(self, biomarker: str) -> str:
        """
        Analyze recent trend for biomarker.
        """
        history = list(self.history[biomarker])
        
        if len(history) < 3:
            return "Insufficient data"
        
        # Get last 3 values
        recent = [h['value'] for h in history[-3:]]
        
        # Check trend
        if recent[-1] > recent[-2] > recent[-3]:
            return "Rising ↗"
        elif recent[-1] < recent[-2] < recent[-3]:
            return "Falling ↘"
        else:
            return "Stable →"


# ============================================================================
# WEARABLE INTEGRATOR (Simulated)
# ============================================================================

class WearableIntegrator:
    """
    Unified interface for wearable sensors.
    Publishes to Redis stream for watchdog consumption.
    """
    
    def __init__(self):
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=5, decode_responses=True)
            self.redis.ping()
        except Exception as e:
            print(f"ERROR: Redis not available: {e}")
            exit(1)
    
    async def simulate_sensors(self):
        """
        Simulate sensor data from wearables.
        In production: connect to actual APIs (Apple Health, Garmin Connect, etc.)
        """
        print("\n" + "="*80)
        print("WEARABLE INTEGRATOR - SIMULATION MODE")
        print("="*80 + "\n")
        
        print("Generating simulated sensor data...")
        print("Publishing to Redis stream: 'biomarkers'\n")
        
        sensors = [
            {'type': 'heart_rate', 'range': (60, 80), 'source': 'Apple Watch'},
            {'type': 'hrv', 'range': (40, 60), 'source': 'Polar H10'},
            {'type': 'spo2', 'range': (96, 99), 'source': 'Apple Watch'},
            {'type': 'glucose', 'range': (80, 120), 'source': 'CGM'},
            {'type': 'cortisol', 'range': (10, 20), 'source': 'Lab Result'},
        ]
        
        iteration = 0
        
        while True:
            try:
                iteration += 1
                
                for sensor in sensors:
                    # Generate value
                    if iteration % 10 == 0:  # Every 10th reading - spike
                        value = sensor['range'][1] + 15  # Above normal
                    elif iteration % 20 == 0:  # Every 20th - critical
                        value = sensor['range'][1] + 40  # Critical
                    else:
                        # Normal range
                        import random
                        value = random.uniform(sensor['range'][0], sensor['range'][1])
                    
                    # Publish to stream
                    self.redis.xadd('biomarkers', {
                        'type': sensor['type'],
                        'value': f"{value:.1f}",
                        'timestamp': str(time.time()),
                        'source': sensor['source']
                    })
                
                await asyncio.sleep(3)  # Reading every 3 seconds
            
            except KeyboardInterrupt:
                print("\n⏹️  Stopping sensor simulation...")
                break
            
            except Exception as e:
                print(f"⚠️  Sensor error: {e}")
                await asyncio.sleep(5)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python biomarker_watchdog.py monitor [user_id]   - Monitor biomarkers")
        print("  python biomarker_watchdog.py simulate            - Simulate sensors")
        return
    
    mode = sys.argv[1]
    
    if mode == 'monitor':
        user_id = sys.argv[2] if len(sys.argv) > 2 else 'user_default'
        
        watchdog = BiomarkerWatchdog(user_id)
        await watchdog.monitor_stream()
    
    elif mode == 'simulate':
        integrator = WearableIntegrator()
        await integrator.simulate_sensors()
    
    else:
        print(f"Unknown mode: {mode}")


if __name__ == '__main__':
    asyncio.run(main())
