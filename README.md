# SlashSure

**The AI-Powered Trust, Slashing, and Insurance Layer for Decentralized Networks.**

Powered by [GenLayer](https://genlayer.com) Intelligent Contracts on StudioNet.

- **Live App:** https://slash-sure.vercel.app
- **API:** https://slashsure-backend-prod.fly.dev
- **API Docs:** https://slashsure-backend-prod.fly.dev/api/docs
- **Intelligent Contract:** `0x8565ecca2743945e4020aEB8D6F4a69f088329c8` on GenLayer StudioNet

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
│   slashsure-backend-prod.fly.dev        │
│   - PostgreSQL (persistent data)        │
│   - Redis (pub/sub, caching)            │
│   - Background monitoring worker       │
│   - JWT auth + wallet generation        │
└────────────────┬────────────────────────┘
                 │ GenLayer Python SDK
┌────────────────▼────────────────────────┐
│   GenLayer StudioNet                    │
│   Intelligent Contract                  │
│   0x8565ecca2743945e4020aEB8D6F4a69f088329c8 │
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

1. Open [GenLayer Studio](https://explorer-studio.genlayer.com/)
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

---

## Test Data

Use these values for end-to-end testing:

### Operator registration

| Field | Value |
|---|---|
| Operator name | `Chorus One` |
| Wallet address | `0xF8809b368bCBa4E3eD2a4AddEe93A191F9Ab70e9` |
| Network | `eigenlayer` |
| Total stake (GEN) | `1000` |
| Commission (%) | `5` |
| Description | `Chorus One is a staking and infrastructure operator focused on uptime, monitoring, and validator reliability.` |
| Website | `https://chorus.one/` |

### Incident report

| Field | Value |
|---|---|
| Title | `Validator downtime detected on EigenLayer` |
| Incident type | `downtime` |
| Network | `eigenlayer` |
| Severity | `medium` |
| Operator | `0xF8809b368bCBa4E3eD2a4AddEe93A191F9Ab70e9` |
| Description | `The operator missed participation for a short period during normal network operation.` |
| Evidence title | `Monitoring dashboard snapshot` |
| Evidence URL | `https://blog.base.dev/postmortem-june-25th-block-production-outage` |
| Evidence block number | `4288927` |

### Insurance claim

| Field | Value |
|---|---|
| Incident | select the incident created above |
| Claimant wallet address | `0x97E12226f47FFEB552FAb16882f475c620bF8554` |
| Coverage amount | `10000` |
| Claimed amount | `7500` |
| Policy ID | `POL-EIGEN-2026-001` |

---

## Frontend Errors and What They Mean

### `POST /api/v1/operators/ 400 (Bad Request)`
The backend rejected the operator registration payload.

Common causes:
- missing required form values
- invalid website URL
- website content does not mention the operator name/address
- stake is zero or negative
- GEN amount is lower than the amount required for on-chain registration

How to fix:
- fill every required field
- use a reachable HTTPS website
- make sure the site contains the operator name or address in visible text or metadata
- enter a positive stake amount in GEN

### `POST /api/v1/operators/ 401 (Unauthorized)`
The user is not authenticated or the token expired.

How to fix:
- log in again
- refresh the browser
- make sure the frontend is pointed at the correct backend URL

### `GET /api/v1/auth/me 401 (Unauthorized)`
The session token is missing or stale.

How to fix:
- re-authenticate
- clear local storage if the app is stuck on an old session

### `GET /api/v1/auth/me/balance 401 (Unauthorized)`
The wallet balance endpoint is blocked by the same auth problem as above.

How to fix:
- log in again
- confirm the access token is valid

### `ERR_NAME_NOT_RESOLVED`
The frontend is trying to call a backend hostname that does not exist.

How to fix:
- update `NEXT_PUBLIC_API_URL`
- redeploy the frontend after changing environment variables
- confirm the backend hostname is the current Fly app URL

### `Unable to reach operator website`
The backend/contract tried to fetch the operator website, but the URL could not be resolved or connected to.

How to fix:
- use a real public website URL
- avoid placeholder domains or local-only hosts
- ensure the website is reachable from the public internet

### `Website verification failed: site must reference the operator name, address, or matching metadata`
The website was reachable, but it did not contain enough evidence that it belongs to the operator.

How to fix:
- add the operator name or wallet address to the page
- add matching metadata like description or author
- make sure the visible text is not just a generic landing page

### `Evidence source returned client error`
The contract fetched the evidence URL and received a 4xx response.

How to fix:
- use a valid evidence URL that returns HTTP 200
- make sure the URL is public and does not require login

### `This page couldn’t load` on settings
The frontend could not load data for the page, usually because the backend request failed or the session expired.

How to fix:
- refresh login
- verify the backend is running
- check browser console for the exact API request that failed

### Detail drawer shows dashes only
The record detail panel opened before the full backend response arrived, or the backend record is missing fields.

How to fix:
- wait a moment for the detail request to finish
- confirm the backend route returns the expected record fields
- use the latest frontend build

---

## Recommended Test Flow

1. Register the operator using the test data above.
2. Wait for the on-chain transaction to finalize.
3. Open the operator details drawer and confirm the metadata appears.
4. Report the incident using the operator above.
5. Wait for the incident transaction to finalize.
6. Submit the insurance claim tied to that incident.
7. Wait for the claim transaction to finalize.
8. Check the dashboard, incidents, insurance, and admin pages for populated details.

If any transaction fails, inspect the API response first, then the browser console, then the contract result on the explorer.
