# SlashSure

**The AI-Powered Trust, Slashing, and Insurance Layer for Decentralized Networks.**

Powered by [GenLayer](https://genlayer.com) Intelligent Contracts on StudioNet.

---

## Quick Start (Local Development)

### Prerequisites
- Docker + Docker Compose
- Python 3.11+ + Poetry
- Node.js 20+
- GenLayer Studio account

### 1. Clone & configure

```bash
git clone https://github.com/zoefunds/Slash-Sure.git
cd Slash-Sure
cp backend/.env.example backend/.env
# Fill in your secrets in backend/.env
```

### 2. Start infrastructure

```bash
docker-compose up -d postgres redis
```

### 3. Start backend

```bash
cd backend
poetry install
uvicorn app.main:app --reload --port 8000
```

### 4. Start frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Deploy Intelligent Contract

1. Open [GenLayer Studio](https://studio.genlayer.com)
2. Upload `intelligent-contracts/slash_sure.py`
3. Deploy to StudioNet
4. Copy the deployed contract address
5. Add it to `backend/.env` as `GENLAYER_CONTRACT_ADDRESS=0x...`

---

## Architecture

```
frontend (Next.js → Vercel)
    ↕ REST + GraphQL + WebSockets
backend (FastAPI → Fly.io)
    ↕ PostgreSQL + Redis Streams
    ↕ GenLayer StudioNet (Intelligent Contract)
        → AI Fault Analysis
        → Slashing Recommendations
        → Insurance Adjudication
        → Reputation Scoring
        → Predictive Risk
```

## Network Coverage
- EigenLayer / ETH Restaking
- Symbiotic
- Babylon (BTC Staking)
- Cosmos / IBC Validators
