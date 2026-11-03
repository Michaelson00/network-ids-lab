# SentinelNIDS / Network IDS Lab

A small Network Intrusion Detection System (NIDS) built as a 4-week collaborative
mock project. Network traffic is captured, cleaned, classified, risk-scored, and
displayed as alerts on a dashboard.

Educational project only — not a commercial SOC/IDS product.

## Pipeline

Network Traffic → Packet Capture / Dataset → Preprocessing → Feature Extraction
→ Detection Engine (ML + Rules) → Classification → Risk Scoring → Security Alert
→ API → Database → Dashboard

## Team Roles

| Role | Person | Owns |
|---|---|---|
| Network Engineer | Benjamin | `lab/` |
| Data Analyst 1 (Data Eng & EDA) | Serene | `notebooks/01_eda.ipynb`, `src/preprocessing/`, `src/features/` |
| ML Engineer | Kelvin | `notebooks/02_model_comparison.ipynb`, `src/models/` |
| Cybersecurity Engineer | Eugene | `docs/threat-model.md`, `rules/`, `src/scoring/` |
| DevOps / Software Engineer | Bright | `src/api/`, `dashboard/` |

## Branching

- `main` — stable, tested, presentation-ready
- `dev` — integration/staging
- `feature/...` — individual task branches

Nobody develops directly on `main`. Start work with:

```
git switch dev
git pull
git switch -c feature/your-task
```

Save work with:

```
git status
git add .
git commit -m "Describe the change clearly"
git push -u origin feature/your-task
```

Open a Pull Request from your feature branch into `dev`. Explain what changed,
why, and how it was tested. Get one review, fix requested changes, get approval,
merge. Only move stable, tested work from `dev` into `main`.

## Setup and first detection

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.api.app
```

Open http://127.0.0.1:5000/, then click **Detection demo → Port scan**.
It processes validated simulated features through benchmark ML when available,
otherwise transparent rules-only DEMO MODE, then risk/storage and the dashboard. No packets or network attacks are generated.
The selected CICIDS2017 model/scaler are still an external ML-owner handoff;
the demo never replaces them or claims benchmark accuracy. Existing lab captures
can now be read offline through packet-header rules (not invented ML features).

[RUN_AND_TEST.md](RUN_AND_TEST.md) covers four demos, manual flow submission,
readiness, analytics, safe demo-only reset and tests. Raw PCAP-to-flow export
remains external; no automatic network monitoring is implemented.

## Project Structure

See each subfolder's README for details on that component.

## Final audit

See [Weeks 1–4 completion matrix](docs/FINAL_ISSUE_AUDIT.md) and
[consolidated final report](docs/final-report.md). Completion percentages describe
verified checklist evidence, not real-model readiness; missing artifacts and data
remain explicit blockers.

## Functional implementation

See [current input-path and verification notes](docs/FUNCTIONAL_IMPLEMENTATION.md).
Dashboard icons are official locally bundled Lucide SVGs; charts use Chart.js.
Licenses are preserved under `dashboard/vendor/`.

Current mode and role handoffs: [FINAL_BLOCKERS.md](docs/FINAL_BLOCKERS.md) and
[MISSING_ARTIFACTS.md](docs/MISSING_ARTIFACTS.md).
