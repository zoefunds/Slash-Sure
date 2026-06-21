# SlashSure

**The AI-Powered Trust, Slashing, and Insurance Layer for Decentralized Networks.**

Powered by [GenLayer](https://genlayer.com) Intelligent Contracts on StudioNet.

- **Live App:** https://slash-sure.vercel.app
- **API:** https://slashsure-api.fly.dev
- **API Docs:** https://slashsure-api.fly.dev/api/docs
- **Intelligent Contract:** `0x9A91eBfC28832E70c541De5EF46BE99714691922` on GenLayer StudioNet

---

## What is SlashSure?

Operators in decentralized networks (EigenLayer, Symbiotic, Babylon, and beyond) face constant exposure to slashing — punitive penalties triggered by missed attestations, double signing, equivocation, and other faults. Today, there is no automated, trust-minimized system that monitors these events in real time, evaluates fault probability, and coordinates insurance payouts — leaving billions in staked assets unprotected.

SlashSure fixes this. It is an intelligent slashing monitoring, risk assessment, and insurance coordination platform that combines a live backend with GenLayer's AI-native smart contracts to protect validator operators end to end.

---

## Core Features

### Real-Time Incident Detection
A background monitoring worker continuously polls registered operators across EigenLayer and Symbiotic networks, detecting slashing events and generating alerts the moment they occur. Incidents are created automatically with severity classification.

### AI Fault Assessment (GenLayer Intelligent Contract)
When an incident is flagged, SlashSure's GenLayer intelligent contract uses on-chain AI to:
- Evaluate the **fault probability** (0–100%) for the incident type
- Compute the **slash severity in basis points** deterministically from the AI's numeric output (no categorical outputs — prevents UNDETERMINED)
- Return a **confidence score** verified by GenLayer's full validator network

### Slashing Case Management
Confirmed faults are escalated to on-chain slashing cases. The contract executes sequentially — each transaction reaches FINALIZED before the next fires — ensuring reliable on-chain state across the full lifecycle: register → analyze → slash → claim.

### Insurance Adjudication
Operators and stakeholders can submit insurance claims. The AI contract evaluates coverage eligibility, damage assessment, and payout recommendation in a single trustless transaction. Claims are tracked through full lifecycle: submitted → ai_adjudication → approved/rejected → paid.

### Governance
Active proposals for slashing appeals, claim reviews, and operator whitelisting are voted on-chain via GenLayer. Proposals display live vote tallies with progress bars, and voting triggers on-chain consensus.

### Risk Scoring
Per-operator risk scores are computed from uptime history, slash count, stake size, and network type. A risk trend (improving / stable / worsening) is derived and displayed for each operator.

### Admin Dashboard
A superadmin-only dashboard gives full system visibility: all users, operators, incidents, AI reviews, with real-time stats including network distribution and 24-hour incident activity.

---

## Architecture

```
┌─────────────────────────────────────────┐
│   Frontend (Next.js → Vercel)           │
│   slash-sure.vercel.app                 │
│   - Dashboard, Operators, Incidents     │
│   - Risk Scores, Slashing, Insurance    │
│   - Governance, Monitoring, Admin       │
└────────────────┬────────────────────────┘
                 │ REST + WebSockets
┌────────────────▼────────────────────────┐
│   Backend (FastAPI → Fly.io)            │
│   slashsure-api.fly.dev                 │
│   - PostgreSQL (persistent data)        │
│   - Redis (pub/sub, caching)            │
│   - Background monitoring worker       │
│   - JWT auth + wallet generation        │
└────────────────┬────────────────────────┘
                 │ GenLayer Python SDK
┌────────────────▼────────────────────────┐
│   GenLayer StudioNet                    │
│   Intelligent Contract                  │
│   0x9A91eBfC28832E70c541De5EF46BE99714691922 │
│   - register_operator                   │
│   - analyze_incident (AI)               │
│   - execute_slash                       │
│   - process_insurance_claim (AI)        │
│   - create_governance_proposal          │
│   - vote_on_proposal                    │
└─────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Intelligent Contract | Python on GenLayer StudioNet |
| Backend | FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis |
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Recharts |
| Hosting | Fly.io (backend, 24/7), Vercel (frontend) |
| Auth | JWT (access + refresh tokens), per-user blockchain wallet generation |
| Email | Brevo transactional email |

---

## Network Coverage

- **EigenLayer** — ETH restaking operators
- **Symbiotic** — cross-protocol restaking
- **Babylon** — BTC staking (monitoring ready)
- **Cosmos / IBC** — validator networks (monitoring ready)

---

## GenLayer Integration Details

The intelligent contract (`intelligent-contracts/slash_sure.py`) uses GenLayer's `eq_principle` for AI-driven functions:

- **`analyze_incident`** — prompts the AI with incident type, network, and evidence hash. Returns `fault_probability` (float) and `confidence_score` (float). `slash_bps` is computed deterministically as `round(fault_probability * 100)` to avoid non-determinism from categorical outputs.
- **`process_insurance_claim`** — AI evaluates coverage eligibility and recommended payout ratio. Returns structured JSON parsed with a numeric `coverage_ratio`.
- All write functions follow strict sequential execution: each transaction must reach **FINALIZED** before the next is sent.

---

## E2E Tests Completed On-Chain

| Test | Operator | Network | Fault Type | Result |
|---|---|---|---|---|
| Test 1 | `0xAAAA...0001` | EigenLayer | double_signing | ✅ All 4 functions FINALIZED |
| Test 2 | `0xBBBB...0002` | Symbiotic | missed_attestation | ✅ All 4 functions FINALIZED |

---

## Local Development

### Prerequisites
- Docker + Docker Compose
- Python 3.11+ + Poetry
- Node.js 20+

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
5. Set `GENLAYER_CONTRACT_ADDRESS` in your environment / Fly.io secrets

---

## Backend Deployment (Fly.io)

```bash
cd backend
fly deploy
```

The backend is configured with `auto_stop_machines = "off"` and `min_machines_running = 1` for 24/7 uptime. Health checks run every 15 seconds at `/health`.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string |
| `DATABASE_SYNC_URL` | PostgreSQL sync connection string (Alembic) |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |
| `SECRET_KEY` | App secret key |
| `WALLET_MASTER_KEY` | Master key for HD wallet derivation |
| `GENLAYER_CONTRACT_ADDRESS` | Deployed intelligent contract address |
| `GENLAYER_RPC_URL` | GenLayer StudioNet RPC endpoint |
| `BREVO_API_KEY` | Brevo API key for transactional email |
| `FRONTEND_URL` | Frontend URL for email links |
| `ALLOWED_ORIGINS` | CORS allowed origins |
