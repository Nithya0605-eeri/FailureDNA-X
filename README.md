# FailureDNA X
### Autonomous GPU Failure Investigation using NVIDIA Nemotron and Nebius Token Factory

FailureDNA X is an AI-powered GPU failure investigation platform that identifies potential root causes of GPU performance problems through intelligent diagnostic testing.

Instead of running a fixed checklist, the AI selects diagnostic tools based on available evidence, evaluates the results, and produces an explainable diagnosis.

Built for the NVIDIA × Nebius Global AI Hackathon.

## The Problem

GPU infrastructure failures can be difficult to diagnose. Engineers often spend time running multiple diagnostic tests without knowing which ones are most relevant.

FailureDNA X demonstrates how AI-guided investigation can reduce unnecessary testing while helping identify the root cause of GPU performance degradation.

## Our Solution

FailureDNA X uses NVIDIA Nemotron through Nebius Token Factory to guide GPU investigations.

The system:
1. Simulates GPU performance failures.
2. Presents symptoms to the AI investigator.
3. Uses AI to select diagnostic tests.
4. Executes simulated diagnostic tools.
5. Updates probabilities for possible root causes.
6. Produces a diagnosis with supporting evidence.
7. Compares AI-guided investigation with a fixed checklist.

## Features

- AI-powered diagnostic test selection
- Hidden GPU fault simulation
- NVIDIA Nemotron integration
- Nebius Token Factory API integration
- Interactive React dashboard
- Investigation timeline
- Root-cause probability visualization
- Confidence and evidence tracking
- Diagnostic test cost comparison
- Fixed-checklist and information-gain baselines

## Technology Stack

**Frontend**
- React
- JavaScript
- Vite
- Tailwind CSS

**Backend**
- Python
- FastAPI
- Pydantic
- Pytest

**AI**
- NVIDIA Nemotron
- Nebius Token Factory
- OpenAI-compatible API client

**Version Control**
- Git
- GitHub

## System Architecture

React Dashboard
    |
    v
FastAPI Backend
    |
    +-- GPU Failure Simulator
    |
    +-- AI Investigation Engine
    |       |
    |       v
    |   NVIDIA Nemotron
    |   via Nebius Token Factory
    |
    +-- Diagnostic Tools
    |
    +-- Evidence and Belief Updates
    |
    v
Diagnosis and Visualization

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Nithya0605-eeri/FailureDNA-X.git
cd FailureDNA-X
```

### 2. Set Up the Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

### 3. Configure Nebius Token Factory

Create a file named `backend/.env`:

```env
NEBIUS_API_KEY=your_nebius_api_key
NEBIUS_MODEL=nvidia/nemotron-3-super-120b-a12b
```

Use a valid model available to your Nebius account. Never commit API keys or `.env` files.

### 4. Start the Backend

From the project root:

```bash
python -m uvicorn backend.main:app --env-file backend/.env --port 8000
```

Backend health check:

http://127.0.0.1:8000/health

### 5. Start the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite.

### 6. Run the Dashboards

**GPU Investigation Dashboard**

Open the frontend homepage and select:

Run Demo Investigation

**Live Hidden-Fault Investigation**

Open:

http://localhost:5173/live

Replace port 5173 with the port displayed by Vite if different.

Select the Nemotron agent and click:

Inject Hidden Failure

## Testing

Run backend tests from the project root:

```bash
python -m pytest -v
```

Build the frontend:

```bash
cd frontend
npm run build
```

During local integration testing:
- 24 backend tests passed.
- Frontend production build succeeded.
- Both investigation dashboards were exercised.
- A live Nemotron investigation correctly identified a simulated memory-pressure fault.

## Example Investigation

In one demonstration:

| Metric | Nemotron Agent | Fixed Checklist |
|---|---|---|
| Diagnostic tests | 5 | 6 |
| Simulated test cost | 10 | 18 |
| Diagnosis | Memory pressure | Memory pressure |
| Correct | Yes | Yes |

The AI-guided investigation used approximately 44% less simulated diagnostic cost in this example.

This result represents a single demonstration, not a statistically validated benchmark.

## Limitations

FailureDNA X currently uses simulated GPU failures and diagnostic measurements.

It is a research prototype and does not claim to diagnose physical GPU hardware or production infrastructure.

## Future Improvements

- Real GPU telemetry integration
- NVIDIA DCGM monitoring
- Multi-GPU cluster investigations
- Historical incident analysis
- Automated incident reporting
- Production deployment and observability

## License

MIT License.