# SYSTEM ARCHITECTURE DIAGRAM - Vertex-Complete Vision

## High-Level System Architecture

```mermaid
graph TB
    subgraph "USER INTERFACE LAYER"
        UI1[Mentra Live AR Glasses]
        UI2[CLI Interface]
        UI3[Web Dashboard - Optional]
        UI1 -->|Voice Input| VoiceProc[Voice Processing]
        UI1 -->|Bone Conduction| AudioOut[Audio Output]
    end
    
    subgraph "NETWORK LAYER"
        TailScale[Tailscale Mesh VPN]
        StarLink[Starlink Direct-to-Cell]
        UI1 -.->|Wireless| StarLink
        StarLink -->|Encrypted| TailScale
        TailScale -->|Zero-Trust| Puck
    end
    
    subgraph "ORANGE PI PUCK - Main Intelligence Unit"
        
        subgraph "API LAYER"
            Router[Archetype Router - FastAPI]
            WS[WebSocket - Streaming]
        end
        
        subgraph "INTELLIGENCE LAYER"
            QD[Query Decomposer]
            AS[Archetype Selector]
            WCO[Warm Circuit Optimizer]
            MBP[Micro-Batch Processor]
            QA[Quality Assessor]
            CAS[Cross-Archetype Synthesizer]
        end
        
        subgraph "EXECUTION LAYER"
            Exec[Archetype Executor]
            Ollama[Ollama Model Server]
            Models[20 Composite Models<br/>4 Base + 20 Voice]
        end
        
        subgraph "TRUTH VALIDATION"
            Quorum[Quorum Tribunal<br/>6 Philosophers]
            TruthFor[Truth Forensics]
        end
        
        subgraph "EXTERNAL RESEARCH"
            MetaAnalyst[Meta-Analyst Unified<br/>Web Research + Authority Discovery]
            Playwright[Playwright Browser]
        end
        
        subgraph "SPECIALIZED SYSTEMS"
            VoiceDebate[Voice Debate System<br/>L1/L2 Caching]
            BioWatch[Biomarker Watchdog<br/>Health Monitoring]
            CompEng[Comparison Engine]
        end
        
        subgraph "STORAGE LAYER"
            PG[(PostgreSQL + AGE<br/>Knowledge Graph)]
            Vec[(PGVector<br/>3.2GB Embeddings)]
            Redis[(Redis<br/>Multi-tier Cache)]
        end
        
        subgraph "ORCHESTRATION"
            N8N[n8n Workflows<br/>Nightly Annealing]
        end
        
        subgraph "MONITORING"
            Prom[Prometheus<br/>Metrics]
            Graf[Grafana<br/>Dashboards]
        end
    end
    
    subgraph "TRAINING PIPELINE - Vast.ai"
        DataDownload[Dataset Downloaders<br/>620 GB Corpus]
        BaseTrain[Base Model Trainer<br/>4 Models]
        VoiceaTrain[Voice Adapter Trainer<br/>20 Adapters]
        CompCreate[Composite Creator<br/>Ollama Modelfiles]
        
        DataDownload --> BaseTrain
        DataDownload --> VoiceaTrain
        BaseTrain --> CompCreate
        VoiceaTrain --> CompCreate
    end
    
    subgraph "BACKUP SYSTEMS"
        BackupPuck[Raspberry Pi 5<br/>Backup Puck]
        HomeMCP[Home MCP<br/>Laptop/NUC]
    end
    
    subgraph "WEARABLES - Data Sources"
        Watch[Apple Watch]
        CGM[Continuous Glucose Monitor]
        PolarH10[Polar H10 - Heart Rate]
    end
    
    %% Query Flow
    VoiceProc --> Router
    Router --> QD
    QD --> AS
    AS --> WCO
    WCO --> MBP
    MBP --> Exec
    Exec --> Ollama
    Ollama --> Models
    Models --> QA
    QA --> CAS
    CAS --> Router
    Router --> AudioOut
    
    %% Knowledge Access
    AS -.->|Domain Lookup| PG
    Exec -.->|Context Retrieval| PG
    Exec -.->|Semantic Search| Vec
    
    %% Caching
    AS -.->|Cache Check| Redis
    Exec -.->|Warm Models| Redis
    MetaAnalyst -.->|7-day Cache| Redis
    VoiceDebate -.->|L1/L2 Cache| Redis
    
    %% Special Flows
    QA -.->|Low Quality| AS
    QA -.->|Low Consensus| Quorum
    QA -.->|Low Confidence| MetaAnalyst
    MetaAnalyst -.->|Web Scraping| Playwright
    
    %% Health Monitoring
    Watch --> BioWatch
    CGM --> BioWatch
    PolarH10 --> BioWatch
    BioWatch -.->|Warnings| AS
    BioWatch -.->|Critical| Router
    
    %% Warm Circuits
    WCO -.->|Co-activation Matrix| N8N
    N8N -.->|Nightly Update| PG
    
    %% Training Flow
    CompCreate -.->|Deploy Models| Ollama
    
    %% Monitoring
    Router --> Prom
    Exec --> Prom
    PG --> Prom
    Prom --> Graf
    
    %% Failover
    Puck -.->|Failure| BackupPuck
    Puck -.->|Sync| HomeMCP
    
    %% Styling
    style UI1 fill:#339af0
    style Router fill:#ffa94d
    style QD fill:#ff6b6b
    style AS fill:#ff6b6b
    style Exec fill:#ff6b6b
    style Quorum fill:#845ef7
    style MetaAnalyst fill:#51cf66
    style PG fill:#20c997
    style Vec fill:#20c997
    style Redis fill:#20c997
    style Ollama fill:#845ef7
    style Models fill:#845ef7
```

---

## Data Flow: Query Lifecycle

```mermaid
sequenceDiagram
    participant User as 👤 User (Glasses)
    participant Router as 🎯 Archetype Router
    participant Decomp as 📊 Query Decomposer
    participant Select as 🎲 Archetype Selector
    participant Warm as 🔥 Warm Circuit Optimizer
    participant Batch as ⚡ Micro-Batch Processor
    participant Exec as 🤖 Archetype Executor
    participant KG as 📚 Knowledge Graph
    participant Ollama as 🧠 Ollama
    participant Quality as ✅ Quality Assessor
    participant Synth as 🔀 Synthesizer
    participant Quorum as ⚖️ Quorum Tribunal
    participant Meta as 🌐 Meta-Analyst
    
    User->>Router: Voice Query: "Design solar water purifier for rural India"
    
    Router->>Decomp: Decompose query
    Decomp->>Decomp: Parse dependencies (spaCy)
    Decomp->>Decomp: Extract key phrases
    Decomp->>Decomp: Cluster semantically (HDBSCAN)
    Decomp->>Router: Atoms: [solar_power, water_purification, rural_deployment, india_context]
    
    Router->>Select: Select archetypes for atoms
    Select->>KG: Query domain metadata
    KG-->>Select: Domain mappings
    Select->>Select: Collapse-to-zero (start with 1)
    Select->>Router: Initial: [mit_engineering]
    
    Router->>Warm: Check warm circuits
    Warm->>Warm: Lookup co-activation matrix
    Warm-->>Router: Predicted: [caltech_physics, chicago_economics]
    
    Router->>Batch: Create execution batches
    Batch->>Batch: Batch 1: [solar_power, water_purification]
    Batch->>Batch: Batch 2: [rural_deployment, india_context]
    
    loop For each batch
        Batch->>Exec: Execute batch with archetype
        Exec->>KG: Retrieve context chunks
        KG-->>Exec: Relevant knowledge
        Exec->>Ollama: Generate response (mit_engineering)
        Ollama-->>Exec: Response with citations
        Exec->>Quality: Assess response quality
        Quality->>Quality: Check relevance, specificity, structure
        
        alt Quality < 0.85
            Quality->>Select: Request additional archetype
            Select-->>Batch: Add caltech_physics
            Batch->>Exec: Re-execute with 2 archetypes
            Exec->>Ollama: Generate with caltech_physics
            Ollama-->>Exec: Enhanced response
        end
        
        Quality-->>Batch: Quality: 0.87 ✓
    end
    
    Batch->>Synth: Synthesize all responses
    Synth->>Synth: Extract claims
    Synth->>Synth: Resolve conflicts
    Synth->>Synth: Weave narrative
    Synth->>Synth: Map citations
    
    alt Conflicts detected
        Synth->>Quorum: Validate conflicting claims
        Quorum->>Quorum: Philosopher debate (6 LoRAs)
        Quorum-->>Synth: Consensus verdict
    end
    
    alt Confidence < 0.85
        Synth->>Meta: Trigger web research
        Meta->>Meta: Generate dork queries
        Meta->>Meta: Scrape authorities
        Meta->>Meta: Extract + cache (7 days)
        Meta-->>Synth: Additional evidence
        Synth->>Synth: Re-synthesize with web data
    end
    
    Synth->>Router: Final synthesis (coherence: 0.91)
    Router->>User: Stream response via bone conduction
    
    Router->>Warm: Update co-activation matrix
    Warm->>Warm: Record: [mit_engineering, caltech_physics] co-activated
```

---

## Training Pipeline Flow

```mermaid
graph LR
    subgraph "Phase 1: Data Collection"
        D1[MIT OCW<br/>160 GB]
        D2[arXiv<br/>180 GB]
        D3[PubMed<br/>185 GB]
        D4[SSRN + Books<br/>95 GB]
        
        D1 --> Filter[Quality Filter<br/>Dedup + Toxicity + PII]
        D2 --> Filter
        D3 --> Filter
        D4 --> Filter
    end
    
    subgraph "Phase 2: Preprocessing"
        Filter --> Clean[Clean Text<br/>620 GB → 590 GB]
        Clean --> Split[Split by Domain]
        
        Split --> STEM[STEM Combined<br/>301 GB]
        Split --> Life[Life Systems<br/>205 GB]
        Split --> Human[Human Systems<br/>105 GB]
        Split --> Creative[Creative Edge<br/>54 GB]
    end
    
    subgraph "Phase 3: Base Training"
        STEM --> Train1[Train Base 1<br/>Llama-3-70B-4bit<br/>12h, $12]
        Life --> Train2[Train Base 2<br/>12h, $12]
        Human --> Train3[Train Base 3<br/>12h, $12]
        Creative --> Train4[Train Base 4<br/>12h, $12]
        
        Train1 --> Base1[stem_reasoning<br/>18 GB]
        Train2 --> Base2[life_systems<br/>18 GB]
        Train3 --> Base3[human_systems<br/>18 GB]
        Train4 --> Base4[creative_edge<br/>18 GB]
    end
    
    subgraph "Phase 4: Voice Training"
        STEM --> StyleEx1[Style Extractor]
        Life --> StyleEx2[Style Extractor]
        Human --> StyleEx3[Style Extractor]
        Creative --> StyleEx4[Style Extractor]
        
        StyleEx1 --> VT1[Train 5 Voice Adapters<br/>MIT, Caltech, Princeton, Stanford, Complexity]
        StyleEx2 --> VT2[Train 4 Voice Adapters<br/>Harvard, Broad, Berkeley, Longevity]
        StyleEx3 --> VT3[Train 3 Voice Adapters<br/>Yale, Chicago, Oxford]
        StyleEx4 --> VT4[Train 8 Voice Adapters<br/>Beijing, Baghdad, Nalanda, Bauhaus, etc.]
        
        VT1 --> Adapt1[5 Adapters<br/>10 GB]
        VT2 --> Adapt2[4 Adapters<br/>8 GB]
        VT3 --> Adapt3[3 Adapters<br/>6 GB]
        VT4 --> Adapt4[8 Adapters<br/>16 GB]
    end
    
    subgraph "Phase 5: Composite Creation"
        Base1 --> Comp[Composite Creator]
        Base2 --> Comp
        Base3 --> Comp
        Base4 --> Comp
        Adapt1 --> Comp
        Adapt2 --> Comp
        Adapt3 --> Comp
        Adapt4 --> Comp
        
        Comp --> Model1[20 Modelfiles<br/>Ollama]
        Model1 --> Deploy[Deploy to Puck]
    end
    
    style Train1 fill:#ff6b6b
    style Train2 fill:#ff6b6b
    style Train3 fill:#ff6b6b
    style Train4 fill:#ff6b6b
    style VT1 fill:#845ef7
    style VT2 fill:#845ef7
    style VT3 fill:#845ef7
    style VT4 fill:#845ef7
    style Deploy fill:#51cf66
```

---

## Vertex Criteria Validation Flow

```mermaid
graph TB
    Start[Start Validation<br/>Week 15]
    
    Start --> Latency[Latency Tests]
    Latency --> L1{p99 < 5s?}
    L1 -->|Yes ✓| Efficiency[Efficiency Tests]
    L1 -->|No ✗| FixL[Optimize Warm Circuits]
    FixL --> Latency
    
    Efficiency --> E1{Collapse > 90%?}
    E1 -->|Yes ✓| Quality[Quality Tests]
    E1 -->|No ✗| FixE[Tune Selection Threshold]
    FixE --> Efficiency
    
    Quality --> Q1{Quality > 0.85?}
    Q1 -->|Yes ✓| Knowledge[Knowledge Tests]
    Q1 -->|No ✗| FixQ[Improve Training Data]
    FixQ --> Quality
    
    Knowledge --> K1{Coverage > 95%?}
    K1 -->|Yes ✓| Resource[Resource Tests]
    K1 -->|No ✗| FixK[Add More Archetypes]
    FixK --> Knowledge
    
    Resource --> R1{Memory < 128GB?}
    R1 -->|Yes ✓| Cost[Cost Tests]
    R1 -->|No ✗| FixR[Reduce Concurrent Models]
    FixR --> Resource
    
    Cost --> C1{Cost < $0.001?}
    C1 -->|Yes ✓| Privacy[Privacy Tests]
    C1 -->|No ✗| FixC[Optimize Inference]
    FixC --> Cost
    
    Privacy --> P1{Privacy = 100%?}
    P1 -->|Yes ✓| Reliability[Reliability Tests]
    P1 -->|No ✗| FixP[Fix Cloud Leaks]
    FixP --> Privacy
    
    Reliability --> Rel1{Uptime > 99.5%?}
    Rel1 -->|Yes ✓| Human[Human Evaluation]
    Rel1 -->|No ✗| FixRel[Improve Stability]
    FixRel --> Reliability
    
    Human --> H1{Score > 4.0/5?}
    H1 -->|Yes ✓| VertexPass[✨ VERTEX CERTIFIED ✨<br/>All 28 Criteria Met]
    H1 -->|No ✗| FixH[Refine User Experience]
    FixH --> Human
    
    VertexPass --> Report[Generate Certification Report]
    Report --> Publish[Publish Documentation]
    Publish --> End[System Ready for Production]
    
    style VertexPass fill:#51cf66
    style End fill:#51cf66
    style FixL fill:#ff6b6b
    style FixE fill:#ff6b6b
    style FixQ fill:#ff6b6b
    style FixK fill:#ff6b6b
    style FixR fill:#ff6b6b
    style FixC fill:#ff6b6b
    style FixP fill:#ff6b6b
    style FixRel fill:#ff6b6b
    style FixH fill:#ff6b6b
```

---

## Deployment Topology

```mermaid
graph TB
    subgraph "User Equipment"
        Glasses[Mentra Live AR Glasses<br/>Snapdragon XR2 Gen 2<br/>4h Battery]
        Watch[Apple Watch<br/>Health Sensors]
        CGM[Continuous Glucose Monitor]
        H10[Polar H10<br/>Heart Rate]
    end
    
    subgraph "Primary Puck - Orange Pi 5 Plus"
        CPU[RK3588 8-core<br/>4×A76 2.4GHz + 4×A55 1.8GHz]
        RAM[16 GB LPDDR4X]
        NVMe[512 GB NVMe SSD<br/>620 GB Data + 112 GB Models]
        
        CPU --> Services
        
        subgraph "Services"
            Router[Archetype Router<br/>FastAPI]
            Ollama[Ollama Server<br/>Model Serving]
            PG[(PostgreSQL<br/>+ AGE + PGVector)]
            Redis[(Redis<br/>Multi-tier Cache)]
            N8N[n8n Workflows]
            Monitoring[Prometheus + Grafana]
        end
    end
    
    subgraph "Backup Puck - Raspberry Pi 5"
        RPI[BCM2712 4-core<br/>2.4 GHz]
        RAM2[8 GB LPDDR4X]
        SSD2[256 GB SSD<br/>Essential Data Only]
    end
    
    subgraph "Home MCP - Laptop/NUC"
        HomeCPU[x86 CPU]
        HomeRAM[32+ GB RAM]
        HomeSSD[1 TB SSD<br/>Full Backup]
    end
    
    subgraph "Connectivity"
        StarLink[Starlink Direct-to-Cell<br/>Mobile Connectivity]
        TailScale[Tailscale VPN<br/>Zero-Trust Mesh]
    end
    
    Glasses -.->|Bone Conduction| Audio[Audio I/O]
    Watch --> TailScale
    CGM --> TailScale
    H10 --> TailScale
    
    Glasses --> StarLink
    StarLink --> TailScale
    TailScale --> CPU
    
    CPU -.->|Sync| RPI
    CPU -.->|Backup| HomeCPU
    
    Router --> PG
    Router --> Redis
    Ollama --> NVMe
    N8N --> PG
    
    style CPU fill:#ffa94d
    style NVMe fill:#20c997
    style Services fill:#339af0
    style TailScale fill:#845ef7
```

---

## Memory Architecture (128 GB Budget)

```mermaid
pie title Memory Allocation (Max 128 GB)
    "Base Models (3 concurrent)" : 54
    "Voice Adapters (3 concurrent)" : 6
    "PostgreSQL + AGE" : 16
    "PGVector Embeddings" : 8
    "Redis Cache" : 12
    "Ollama Server" : 8
    "Operating System" : 6
    "Archetype Router" : 4
    "Other Services" : 6
    "Buffer" : 8
```

---

## Storage Architecture (512 GB NVMe)

```mermaid
pie title Storage Allocation (512 GB Total)
    "Knowledge Graph Data" : 100
    "Vector Embeddings" : 20
    "Base Models (4)" : 72
    "Voice Adapters (20)" : 40
    "Co-activation Matrices" : 2
    "Redis Persistence" : 10
    "Application Code" : 5
    "Logs + Backups" : 50
    "Operating System" : 30
    "Free Space (Buffer)" : 183
```

---

**END OF SYSTEM ARCHITECTURE DIAGRAMS**

**Purpose:** Visual reference for system design, data flow, and deployment topology  
**Use:** Reference during development, onboarding, and debugging  
**Update:** After each major phase completion

---

*"A picture is worth a thousand lines of code, but a well-designed architecture is worth a million."*

— Graph Ontology | Ambient Intelligence Architecture
