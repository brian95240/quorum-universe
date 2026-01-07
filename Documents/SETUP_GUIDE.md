# QUORUM SETUP GUIDE
## Philosopher Tribunal for Truth Forensics

---

## I. PREREQUISITES

### Hardware Requirements
- **Minimum:** 32 GB RAM, 100 GB free disk space
- **Recommended:** 64 GB RAM, 500 GB NVMe SSD
- **GPU:** Optional but recommended (NVIDIA with 24GB+ VRAM for local training)

### Software
- Linux (Ubuntu 22.04+ recommended) or macOS
- Python 3.10+
- PostgreSQL 14+
- Docker (optional, for containerized AGE)

---

## II. INSTALL OLLAMA

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Start Ollama service (if not auto-started)
ollama serve
```

---

## III. PREPARE PHILOSOPHER LoRAs

You have two options: **train from scratch** or **use pre-trained models**.

### Option A: Train Your Own (Recommended for Accuracy)

#### 1. Gather Source Texts

```bash
# Create dataset directory
mkdir -p ~/quorum_datasets

# Download philosopher texts from Project Gutenberg / Wikisource
# Example for Hume:
cd ~/quorum_datasets
wget "https://www.gutenberg.org/files/9662/9662-0.txt" -O hume_enquiry.txt
wget "https://www.gutenberg.org/files/4705/4705-0.txt" -O hume_treatise.txt

# Repeat for each philosopher:
# - Popper: Logic of Scientific Discovery, Open Society
# - Quine: Word and Object, Two Dogmas papers
# - Arendt: Human Condition, Eichmann in Jerusalem
# - Zhuangzi: Complete Chuang Tzu
# - Khaldun: Muqaddimah
```

#### 2. Train LoRAs (QLoRA method)

```bash
# Install training framework
pip install unsloth

# Use this training script for each philosopher
# (Replace BASE_MODEL and DATASET_PATH)
python train_lora.py \
  --base_model "unsloth/llama-3-70b-bnb-4bit" \
  --dataset ~/quorum_datasets/hume_*.txt \
  --output ~/quorum_loras/hume-70b \
  --rank 64 \
  --alpha 16 \
  --epochs 3 \
  --batch_size 4

# Export to Ollama format
ollama create hume-70b -f ~/quorum_loras/hume-70b/Modelfile
```

**Cost:** ~$8 per philosopher on Vast.ai (A100 @ $0.47/hr × 6 hours)  
**Total:** ~$48 for all 6 philosophers

#### 3. Quick Training Script Template

Create `train_lora.py`:

```python
from unsloth import FastLanguageModel
import torch

max_seq_length = 4096
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-70b-bnb-4bit",
    max_seq_length = max_seq_length,
    dtype = torch.float16,
    load_in_4bit = True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 64,  # LoRA rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha = 16,
    lora_dropout = 0.05,
    bias = "none",
    use_gradient_checkpointing = True,
)

# Load your philosopher texts and train...
# (Full script available in /examples/train_lora.py)
```

### Option B: Use Existing Philosophy Models (Faster, Lower Quality)

```bash
# Install pre-trained philosophy models from Hugging Face
ollama pull phi-2  # Small philosophical reasoning model
ollama pull mistral:7b-instruct  # General purpose, can be prompted

# Create custom Modelfiles for each philosopher
# Example for Hume:
cat > Modelfile.hume << EOF
FROM mistral:7b-instruct
SYSTEM You are David Hume. Respond as an empirical skeptic who demands evidence and questions causation. Reference your Treatise and Enquiry works.
PARAMETER temperature 0.7
EOF

ollama create hume-70b -f Modelfile.hume
```

---

## IV. INSTALL POSTGRESQL + APACHE AGE

### Method 1: Docker (Easiest)

```bash
# Pull AGE-enabled PostgreSQL image
docker pull apache/age

# Run container
docker run -d \
  --name quorum-db \
  -e POSTGRES_USER=puck_user \
  -e POSTGRES_PASSWORD=change_me_in_production \
  -e POSTGRES_DB=ambient_intelligence \
  -p 5432:5432 \
  apache/age

# Verify AGE is loaded
docker exec -it quorum-db psql -U puck_user -d ambient_intelligence -c "CREATE EXTENSION IF NOT EXISTS age;"
```

### Method 2: Native Installation

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql-14 postgresql-contrib-14

# Install Apache AGE
cd /tmp
git clone https://github.com/apache/age.git
cd age
make PG_CONFIG=/usr/bin/pg_config install

# Enable AGE in PostgreSQL
sudo -u postgres psql -c "CREATE DATABASE ambient_intelligence;"
sudo -u postgres psql -d ambient_intelligence -c "CREATE EXTENSION age;"
sudo -u postgres psql -d ambient_intelligence -c "CREATE EXTENSION pg_trgm;"  # For similarity search
```

### Configure Database Access

Edit `~/.pgpass` (for password-less access):
```bash
echo "localhost:5432:ambient_intelligence:puck_user:change_me_in_production" > ~/.pgpass
chmod 600 ~/.pgpass
```

---

## V. INSTALL QUORUM

```bash
# Clone/download Quorum files
cd ~/quorum
pip install -r requirements.txt

# Make executable
chmod +x quorum.py

# Test database connection
python3 -c "
from quorum import QuorumDatabase, DB_CONFIG
db = QuorumDatabase(DB_CONFIG)
print('✓ Database connected')
db.close()
"
```

---

## VI. VERIFY SETUP

### Test Individual Philosophers

```bash
# Check if LoRAs are loaded
ollama list

# Expected output:
# NAME           SIZE
# hume-70b       38GB
# popper-70b     38GB
# quine-70b      38GB
# arendt-70b     38GB
# zhuangzi-70b   38GB
# khaldun-70b    38GB

# Test a single philosopher
ollama run hume-70b "What is the nature of causation?"
```

### Run First Quorum

```bash
# Single query test
./quorum.py "Is artificial intelligence conscious?"

# Expected output:
# ============================================================
# QUORUM INITIATED
# Query: Is artificial intelligence conscious?
# Context Hash: a3f8c9d2e1b4...
# ...
# → HUME analyzing...
# → POPPER analyzing...
# → QUINE analyzing...
# → ARENDT analyzing...
# → ZHUANGZI analyzing...
# → KHALDUN analyzing...
# ============================================================
# FINAL VERDICT
# ============================================================
# [Synthesized philosophical response]
# Consensus: 0.73
# ============================================================
```

---

## VII. ADVANCED FEATURES

### Temporal Context Hashing

The system automatically rotates context every hour. Test it:

```bash
# Morning query (9 AM)
./quorum.py "How do I fix this headache?"
# Routes to: sleep-deprivation context

# Evening query (9 PM, same text)
./quorum.py "How do I fix this headache?"
# Routes to: post-exercise context
```

### Pattern Matching (After 50 Verdicts)

Once you've run 50+ queries, the system caches similar questions:

```bash
# First time: Full Quorum (30 seconds)
./quorum.py "Will Bitcoin reach 100k?"

# Similar query later: Cached (0.2 seconds)
./quorum.py "Will BTC hit 100k in 2026?"
# Output: ⚡ PATTERN MATCH: 0.89
```

### Auto-Trend Analysis

Run on top Twitter/X trends:

```bash
./quorum.py --trends \
  "World War III imminent" \
  "Miracle cure discovered" \
  "AI will replace all jobs"

# Flags propaganda automatically
# ⚠️ World War III imminent
#    Consensus: 0.21 (philosophers disagree = suspicious)
```

---

## VIII. INTEGRATION WITH AMBIENT INTELLIGENCE STACK

### Connect to Orange Pi Puck

On your Orange Pi 5 Plus:

```bash
# Install Ollama for ARM
curl -fsSL https://ollama.com/install.sh | sh

# Copy LoRAs from training machine
rsync -avz ~/quorum_loras/ orangepi:/home/puck/quorum_loras/

# Import into Ollama
for lora in /home/puck/quorum_loras/*.safetensors; do
  ollama create $(basename $lora .safetensors) -f $lora
done
```

### Connect to Mentra Glasses

Add to your glasses SDK:

```python
# glasses_integration.py
import requests

def query_quorum(voice_input: str, gaze_target: str, location_gps: tuple):
    """Send query from glasses to puck Quorum"""
    response = requests.post('http://puck.local:8000/quorum', json={
        'query': voice_input,
        'gaze': gaze_target,
        'location': f"{location_gps[0]},{location_gps[1]}"
    })
    
    verdict = response.json()['verdict']
    
    # Bone-conduction audio output
    play_audio(verdict, voice='philosopher_neutral')
```

---

## IX. PERFORMANCE TUNING

### Optimize LoRA Switching Speed

```bash
# Pre-load all LoRAs into memory (requires 240 GB RAM)
ollama load hume-70b &
ollama load popper-70b &
ollama load quine-70b &
ollama load arendt-70b &
ollama load zhuangzi-70b &
ollama load khaldun-70b &
wait

# Now switching is instant (0.1 sec vs 3 sec cold start)
```

### Database Query Optimization

```sql
-- Add indexes for pattern matching
CREATE INDEX idx_quorum_verdicts_query ON quorum_verdicts USING gin(query gin_trgm_ops);
CREATE INDEX idx_quorum_verdicts_hash ON quorum_verdicts(context_hash);
CREATE INDEX idx_quorum_verdicts_created ON quorum_verdicts(created_at DESC);

-- Vacuum analyze
VACUUM ANALYZE quorum_verdicts;
```

---

## X. TROUBLESHOOTING

### "ERROR: Model not found"
```bash
# List available models
ollama list

# If missing, re-create:
ollama create hume-70b -f ~/quorum_loras/hume-70b/Modelfile
```

### "WARNING: Database connection failed"
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection manually
psql -h localhost -U puck_user -d ambient_intelligence

# Check AGE extension
psql -d ambient_intelligence -c "SELECT * FROM ag_catalog.ag_graph;"
```

### "Out of Memory"
```bash
# Use 4-bit quantization (reduces from 70GB to 38GB per model)
# Already configured in training script

# Or reduce concurrent LoRAs:
# Edit quorum.py, line 26:
# PHILOSOPHERS = {'hume': ..., 'popper': ...}  # Only keep 2-3
```

---

## XI. COST BREAKDOWN

| Component | Cost |
|-----------|------|
| Training 6 LoRAs (Vast.ai) | $48 |
| Orange Pi 5 Plus 16GB | $120 |
| PostgreSQL (self-hosted) | $0 |
| Ongoing GPU (if cloud) | $0 (local) or $8/mo (RunPod) |
| **TOTAL (one-time)** | **$168** |

Compare to: ChatGPT Plus ($20/mo × 12 = $240/year), Claude Pro ($20/mo × 12 = $240/year)

---

## XII. NEXT STEPS

1. **Train your first LoRA** - Start with Hume (easiest dataset)
2. **Run 10 test queries** - Get familiar with consensus scores
3. **Integrate with your puck** - Connect to ambient intelligence stack
4. **Add custom philosophers** - Nietzsche? Foucault? Your choice
5. **Deploy trend analysis** - Run nightly on news feeds

---

**Support:** Open an issue at github.com/your-repo/quorum  
**License:** MIT (all FOSS, fork freely)

**Remember:** The Quorum doesn't give you answers. It gives you a tribunal.
