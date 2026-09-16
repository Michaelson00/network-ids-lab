# Network IDS Lab

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
| Network Engineer | TBD | `lab/` |
| Data Analyst 1 (Data Eng & EDA) | TBD | `notebooks/01_eda.ipynb`, `src/preprocessing/`, `src/features/` |
| ML Engineer | TBD | `notebooks/02_model_comparison.ipynb`, `src/models/` |
| Cybersecurity Engineer | TBD | `docs/threat-model.md`, `rules/`, `src/scoring/` |
| DevOps / Software Engineer | TBD | `src/api/`, `dashboard/`, `Dockerfile`, `docker-compose.yml` |

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

## Setup

```
pip install -r requirements.txt
```

## Project Structure

See each subfolder's README for details on that component.
