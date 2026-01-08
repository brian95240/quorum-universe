#!/usr/bin/env python3
"""
Admin Dashboard - Gradio Web Interface
Mobile-friendly control panel for ambient intelligence system

Key Features:
- Knowledge source injection (paste URLs from phone)
- Voice command processing (reuses Mentra Live STT)
- Live metrics visualization
- Compression statistics
- System health monitoring
- Archetype management

Access:
- Local: http://localhost:7860
- Tailscale: http://<tailscale-ip>:7860 (mobile browser)

Integration:
- Shares Redis sessions with production API
- Reuses Mentra Live transcription engine
- Embeds metrics dashboard visualizations
- Direct knowledge graph insertion
"""

import asyncio
import os
import yaml
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    print("ERROR: gradio not available. Install: pip install gradio")
    GRADIO_AVAILABLE = False

# Import system components
try:
    import sys
    sys.path.append(os.path.dirname(__file__))
    
    from redis_state_manager import RedisStateManager, CacheType
    from compression_manager import CompressionManager
    from metrics_dashboard import MetricsCollector
    
    # Optional: Import if available
    try:
        from mentra_live_bridge import TranscriptionEngine, AudioChunk
        TRANSCRIPTION_AVAILABLE = True
    except ImportError:
        TRANSCRIPTION_AVAILABLE = False
    
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: Some components unavailable: {e}")
    COMPONENTS_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class DashboardConfig:
    """Dashboard configuration"""
    HOST = "0.0.0.0"  # Accessible over Tailscale
    PORT = 7860
    
    # Sources configuration file
    SOURCES_YAML = "sources.yaml"
    
    # Redis connection
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    
    # Available archetypes (loaded from YAML)
    ARCHETYPES = [
        'mit_engineering', 'caltech_physics', 'oxford_philosophy',
        'harvard_medicine', 'stanford_ai', 'princeton_math',
        'cambridge_nlp', 'eth_zurich_robotics', 'tokyo_quantum',
        'beijing_classical', 'nalanda_vedic', 'baghdad_golden',
        'broad_genomics', 'maps_psychedelics', 'nber_economics',
        'ideo_design', 'anthropic_safety', 'calico_longevity',
        'deepmind_agi', 'openai_alignment'
    ]
    
    # Ingestion methods
    METHODS = [
        "arxiv_api",
        "rss_feed", 
        "direct_download",
        "html_scrape",
        "pdf_extract"
    ]


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

class AdminDashboard:
    """
    Gradio-based admin interface for ambient intelligence system.
    
    Provides mobile-friendly controls for:
    - Knowledge injection
    - Voice commands
    - System monitoring
    - Compression analytics
    """
    
    def __init__(self):
        """Initialize dashboard"""
        self.config = DashboardConfig()
        
        # Initialize components
        if COMPONENTS_AVAILABLE:
            self.state_manager = RedisStateManager(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT
            )
            
            self.compressor = CompressionManager()
            self.metrics = MetricsCollector(enable_prometheus=False)
            
            if TRANSCRIPTION_AVAILABLE:
                self.transcription_engine = TranscriptionEngine(model_name="base")
            else:
                self.transcription_engine = None
        
        # Load sources configuration
        self.sources = self._load_sources()
        
        print("AdminDashboard initialized")
    
    def _load_sources(self) -> Dict:
        """Load sources configuration from YAML"""
        if os.path.exists(self.config.SOURCES_YAML):
            with open(self.config.SOURCES_YAML, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default structure
            return {'archetypes': {arch: [] for arch in self.config.ARCHETYPES}}
    
    def _save_sources(self, sources: Dict):
        """Save sources configuration to YAML"""
        with open(self.config.SOURCES_YAML, 'w') as f:
            yaml.dump(sources, f, sort_keys=False)
    
    # ========================================================================
    # SOURCE INJECTION
    # ========================================================================
    
    async def inject_source(self,
                           archetype: str,
                           url: str,
                           method: str,
                           category: str = "") -> str:
        """
        Inject knowledge source into system.
        
        Args:
            archetype: Target archetype
            url: Source URL
            method: Ingestion method
            category: Optional category tag
        
        Returns:
            Status message
        """
        if not url or not archetype:
            return "❌ Error: Missing URL or Archetype"
        
        # Validate URL
        if not url.startswith('http'):
            return "❌ Error: Invalid URL (must start with http:// or https://)"
        
        # Create source entry
        source_entry = {
            'url': url.strip(),
            'method': method,
            'added': datetime.now().isoformat()
        }
        
        if category:
            source_entry['category'] = category
        
        # Add to sources
        sources = self._load_sources()
        
        if archetype in sources['archetypes']:
            sources['archetypes'][archetype].append(source_entry)
            self._save_sources(sources)
            
            # Fetch and compress (if components available)
            if COMPONENTS_AVAILABLE:
                try:
                    content = await self._fetch_source(url, method)
                    compressed = self.compressor.compress_text(content)
                    ratio = len(compressed) / len(content.encode('utf-8'))
                    
                    # Cache compressed content
                    cache_key = f"source:{archetype}:{hash(url)}"
                    await self.state_manager.set(
                        CacheType.GRAPH,
                        cache_key,
                        compressed
                    )
                    
                    return (f"✅ Success: Added to {archetype}!\n"
                           f"URL: {url}\n"
                           f"Size: {len(content):,} → {len(compressed):,} bytes ({ratio:.1%})")
                except Exception as e:
                    return f"⚠️ Added to config, but fetch failed: {str(e)}"
            else:
                return f"✅ Success: Added to {archetype}!\nURL: {url}\n(Compression unavailable)"
        else:
            return f"❌ Error: Archetype '{archetype}' not found"
    
    async def _fetch_source(self, url: str, method: str) -> str:
        """
        Fetch source content.
        
        Args:
            url: Source URL
            method: Ingestion method
        
        Returns:
            Content text
        """
        # Mock implementation - in production, use appropriate fetcher
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    raise Exception(f"HTTP {resp.status}")
    
    # ========================================================================
    # VOICE PROCESSING
    # ========================================================================
    
    async def process_voice(self, audio_file) -> str:
        """
        Process voice command.
        
        Args:
            audio_file: Audio file path or data
        
        Returns:
            Transcription or command result
        """
        if not TRANSCRIPTION_AVAILABLE or not self.transcription_engine:
            return "⚠️ Voice transcription unavailable (Whisper not installed)"
        
        try:
            # Convert audio to AudioChunk
            import wave
            with wave.open(audio_file, 'rb') as wav:
                audio_data = wav.readframes(wav.getnframes())
                chunk = AudioChunk(
                    data=audio_data,
                    sample_rate=wav.getframerate(),
                    channels=wav.getnchannels()
                )
            
            # Transcribe
            result = await self.transcription_engine.transcribe([chunk])
            text = result.text
            
            # Parse command
            if 'add' in text.lower() and 'source' in text.lower():
                # Extract archetype
                archetype = self._extract_archetype_from_text(text)
                if archetype:
                    return f"🎯 Ready to inject into {archetype}\n📋 Paste URL in the form above"
                else:
                    return f"📝 Transcribed: {text}\n⚠️ No archetype detected"
            
            return f"📝 Transcribed: {text}"
        
        except Exception as e:
            return f"❌ Voice processing error: {str(e)}"
    
    def _extract_archetype_from_text(self, text: str) -> Optional[str]:
        """Extract archetype name from voice command"""
        text_lower = text.lower()
        
        # Check for archetype keywords
        for archetype in self.config.ARCHETYPES:
            arch_keywords = archetype.lower().split('_')
            if any(keyword in text_lower for keyword in arch_keywords):
                return archetype
        
        return None
    
    # ========================================================================
    # METRICS & MONITORING
    # ========================================================================
    
    async def get_metrics(self) -> Dict:
        """Get system metrics"""
        if not COMPONENTS_AVAILABLE:
            return {'error': 'Metrics unavailable'}
        
        sys_metrics = self.metrics.calculate_system_metrics()
        vertex = self.metrics.calculate_vertex_criteria()
        
        return {
            'queries_total': sys_metrics.total_queries,
            'qps': sys_metrics.queries_per_second,
            'avg_latency': sys_metrics.avg_latency,
            'cache_hit_rate': sys_metrics.cache_hit_rate,
            'collapse_ratio': sys_metrics.collapse_ratio,
            'avg_quality': sys_metrics.avg_quality_score,
            'vertex_status': vertex.status.value,
            'criteria_met': f"{vertex.criteria_met}/{vertex.criteria_total}"
        }
    
    async def get_compression_stats(self) -> Dict:
        """Get compression statistics"""
        if not COMPONENTS_AVAILABLE:
            return {'error': 'Compression unavailable'}
        
        return self.compressor.get_stats()
    
    async def get_source_list(self) -> str:
        """Get formatted source list"""
        sources = self._load_sources()
        
        output = []
        for archetype, source_list in sources['archetypes'].items():
            if source_list:
                output.append(f"\n**{archetype}** ({len(source_list)} sources)")
                for i, src in enumerate(source_list[:3], 1):
                    output.append(f"  {i}. {src['url'][:60]}...")
                if len(source_list) > 3:
                    output.append(f"  ... and {len(source_list) - 3} more")
        
        return "\n".join(output) if output else "No sources configured"
    
    # ========================================================================
    # INTERFACE CREATION
    # ========================================================================
    
    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface"""
        
        with gr.Blocks(
            title="Vertex Command Console",
            theme=gr.themes.Monochrome()
        ) as app:
            
            gr.Markdown("# 🧠 Vertex Knowledge Graph Controller")
            gr.Markdown("*Mobile-friendly admin dashboard via Tailscale*")
            
            with gr.Tabs():
                # ============================================================
                # TAB 1: Knowledge Injection
                # ============================================================
                with gr.Tab("📝 Knowledge Injection"):
                    gr.Markdown("### Add New Sources")
                    
                    with gr.Row():
                        arch_dropdown = gr.Dropdown(
                            choices=self.config.ARCHETYPES,
                            label="Target Archetype",
                            info="Select institutional archetype"
                        )
                        method_dropdown = gr.Dropdown(
                            choices=self.config.METHODS,
                            value="direct_download",
                            label="Ingestion Method"
                        )
                    
                    url_input = gr.Textbox(
                        label="Source URL",
                        placeholder="https://arxiv.org/abs/...",
                        info="Paste URL from mobile browser"
                    )
                    
                    category_input = gr.Textbox(
                        label="Category (Optional)",
                        placeholder="e.g., quantum_mechanics"
                    )
                    
                    inject_btn = gr.Button("🚀 Inject Source", variant="primary")
                    status_output = gr.Textbox(label="Status", lines=3)
                    
                    inject_btn.click(
                        fn=self.inject_source,
                        inputs=[arch_dropdown, url_input, method_dropdown, category_input],
                        outputs=status_output
                    )
                
                # ============================================================
                # TAB 2: Voice Control
                # ============================================================
                with gr.Tab("🎙️ Voice Control"):
                    gr.Markdown("### Voice Commands")
                    gr.Markdown("*Say: 'Add physics source' to prepare injection*")
                    
                    audio_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Record Command"
                    )
                    
                    transcribe_btn = gr.Button("Process Voice")
                    voice_output = gr.Textbox(label="Transcription", lines=3)
                    
                    transcribe_btn.click(
                        fn=self.process_voice,
                        inputs=audio_input,
                        outputs=voice_output
                    )
                
                # ============================================================
                # TAB 3: System Metrics
                # ============================================================
                with gr.Tab("📊 System Metrics"):
                    gr.Markdown("### Vertex Criteria Status")
                    
                    metrics_display = gr.JSON(label="Live Metrics")
                    refresh_btn = gr.Button("🔄 Refresh Metrics")
                    
                    refresh_btn.click(
                        fn=self.get_metrics,
                        outputs=metrics_display
                    )
                    
                    # Auto-refresh on load
                    app.load(fn=self.get_metrics, outputs=metrics_display)
                
                # ============================================================
                # TAB 4: Compression Stats
                # ============================================================
                with gr.Tab("💾 Storage Efficiency"):
                    gr.Markdown("### Compression Analytics")
                    
                    compress_display = gr.JSON(label="Compression Statistics")
                    compress_btn = gr.Button("📈 Analyze Compression")
                    
                    compress_btn.click(
                        fn=self.get_compression_stats,
                        outputs=compress_display
                    )
                
                # ============================================================
                # TAB 5: Source Manager
                # ============================================================
                with gr.Tab("📚 Source Manager"):
                    gr.Markdown("### Configured Sources")
                    
                    source_display = gr.Markdown(label="Source List")
                    list_btn = gr.Button("📋 List Sources")
                    
                    list_btn.click(
                        fn=self.get_source_list,
                        outputs=source_display
                    )
                    
                    # Load on startup
                    app.load(fn=self.get_source_list, outputs=source_display)
            
            # Footer
            gr.Markdown("---")
            gr.Markdown("*Secure access via Tailscale | Vertex Ambient Intelligence*")
        
        return app
    
    # ========================================================================
    # LAUNCH
    # ========================================================================
    
    async def connect(self):
        """Connect to backend services"""
        if COMPONENTS_AVAILABLE:
            await self.state_manager.connect()
            print("✓ Backend services connected")
    
    def launch(self):
        """Launch Gradio server"""
        if not GRADIO_AVAILABLE:
            print("ERROR: Gradio not available")
            return
        
        print("\n" + "=" * 60)
        print("VERTEX ADMIN DASHBOARD - STARTING")
        print("=" * 60)
        print(f"Local: http://localhost:{self.config.PORT}")
        print(f"Tailscale: http://<tailscale-ip>:{self.config.PORT}")
        print("=" * 60)
        
        # Create interface
        app = self.create_interface()
        
        # Launch
        app.launch(
            server_name=self.config.HOST,
            server_port=self.config.PORT,
            share=False  # No public tunnel (use Tailscale)
        )


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point"""
    dashboard = AdminDashboard()
    await dashboard.connect()
    dashboard.launch()


if __name__ == "__main__":
    asyncio.run(main())
