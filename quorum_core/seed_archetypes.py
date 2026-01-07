#!/usr/bin/env python3
"""Seed all 26 archetypes into Neon PostgreSQL database"""

import asyncio
import sys
sys.path.insert(0, '/home/ubuntu/quorum_universe/quorum_core')

from config import ARCHETYPES, NEON_CONNECTION_STRING

async def seed_archetypes():
    import asyncpg
    
    print("Connecting to Neon database...")
    pool = await asyncpg.create_pool(NEON_CONNECTION_STRING, min_size=1, max_size=5)
    
    async with pool.acquire() as conn:
        count = 0
        for name, config in ARCHETYPES.items():
            try:
                await conn.execute(
                    """
                    INSERT INTO quorum.archetypes (id, name, cluster, corpus_size_gb, temperature, style, domains, sources)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (name) DO UPDATE SET
                        cluster = $3,
                        corpus_size_gb = $4,
                        temperature = $5,
                        style = $6,
                        domains = $7,
                        sources = $8,
                        updated_at = NOW()
                    """, 
                    config['id'],
                    name,
                    config['cluster'],
                    config['corpus_size_gb'],
                    config['temperature'],
                    config['style'],
                    config['domains'],
                    config.get('training_sources', [])
                )
                count += 1
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    
    await pool.close()
    print(f"\n✅ Seeded {count}/{len(ARCHETYPES)} archetypes")

if __name__ == "__main__":
    asyncio.run(seed_archetypes())
