# Urban Safety AI — Real-Time Anomaly Detection System

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-FF6B35?style=flat)
![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?style=flat&logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Deployed-0B0D0E?style=flat&logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

AI-powered urban safety monitoring system that detects anomalies in real-time video feeds using computer vision and machine learning.

**[🚀 Live Demo](https://urban-safety-ai.vercel.app)** &nbsp;|&nbsp; **[📖 API Docs](https://urban-safety-ai-production.up.railway.app/docs)**

---

## Live Demo

![Dashboard Demo](docs/demo.gif)

> Upload a video → Watch AI detect anomalies in real time → Alerts stream to dashboard

---

## System Architecture

```
Video Input → YOLOv8 Detection → Anomaly Classifier → FastAPI Backend → React Dashboard
                                                             ↓                    ↓
                                                       SQLite DB          WebSocket Alerts
                                                             ↓
                                                      Email Notifications
```

---

## Key Features

- [x] Real-time object detection using YOLOv8n (6.2MB model, 97.2% detection rate)
- [x] Two-layer anomaly detection: rule-based scorer + Random Forest classifier
- [x] False positive calibration: reduced from 96% to 12.2% through resolution-aware thresholds
- [x] 11 REST API endpoints with async Celery task processing
- [x] WebSocket real-time alert streaming to dashboard
- [x] Multi-camera grid view simulating operations centre
- [x] Email alerts via Gmail SMTP when anomaly threshold exceeded
- [x] Fully containerised with Docker, deployed on Railway + Vercel

---

## Tech Stack

| Layer | Technology |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| Anomaly Classification | Random Forest (scikit-learn) |
| Backend API | FastAPI + SQLAlchemy |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Task Queue | Celery + Redis |
| Frontend | React 18 + Vite + Recharts |
| Deployment | Docker + Railway + Vercel |

---

## Performance Metrics

| Metric | Value |
|---|---|
| Detection Rate | 97.2% of frames |
| Classifier Accuracy | 98% (3-class) |
| False Positive Rate | 12.2% (down from 96%) |
| API Response Time | <50ms (async processing) |
| Model Size | 6.2MB (YOLOv8n) |

---

## Local Setup

```bash
git clone https://github.com/faheem0704/urban-safety-ai
cd urban-safety-ai
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# Frontend
cd frontend && npm install && npm run dev
```

Or run the full stack with Docker:

```bash
docker compose up --build
# Backend: http://localhost:8080
# Frontend: http://localhost:80
```

---

## Project Structure

```
urban-safety-ai/
├── ai_core/
│   ├── anomaly_classifier.py   # Random Forest classifier (3-class)
│   ├── anomaly_scorer.py       # Rule-based scoring engine
│   ├── combined_detector.py    # Orchestrates YOLOv8 + scorer + classifier
│   ├── detector.py             # YOLOv8 inference wrapper
│   └── utils.py
├── alerts/
│   ├── alert_engine.py         # Threshold evaluation & trigger logic
│   └── email_templates.py      # Gmail SMTP alert templates
├── api/
│   ├── routes/
│   │   ├── analysis.py         # /api/analyze, /api/jobs/* endpoints
│   │   └── events.py           # Event history endpoints
│   ├── schemas.py              # Pydantic request/response models
│   └── websocket.py            # WebSocket broadcast manager
├── cache/
│   └── redis_cache.py          # Redis / FakeRedis abstraction
├── config/
│   └── settings.py             # Environment-based config (pydantic-settings)
├── database/
│   ├── database.py             # SQLAlchemy engine & session
│   └── models.py               # ORM models (Job, Event, Alert)
├── frontend/
│   ├── src/
│   │   ├── components/         # Dashboard UI components
│   │   ├── hooks/              # useWebSocket, useJobPoller
│   │   └── config.js           # Runtime API/WS URL detection
│   ├── Dockerfile
│   └── nginx.conf
├── tasks/
│   ├── analysis_tasks.py       # Celery task: run video analysis
│   └── celery_app.py           # Celery app configuration
├── models/
│   └── anomaly_classifier.pkl  # Trained Random Forest model
├── main.py                     # FastAPI app entry point
├── start.py                    # Dynamic PORT entry point (Railway)
├── Dockerfile                  # Backend container
├── docker-compose.yml          # Local full-stack orchestration
└── railway.json                # Railway deployment config
```

---

## Engineering Decisions & Technical Depth

### The False Positive Calibration Story

The most significant engineering challenge was reducing an initial **96% false positive rate** to a production-viable **12.2%**.

**Root Cause Analysis**

The anomaly scorer used a hardcoded `80px` movement threshold to flag suspicious motion. This worked on one test video but completely broke on footage from a different camera — because pixel displacement is meaningless without knowing the frame resolution. An 80px movement in a 4K feed is negligible; in a 360p feed it's a sprint.

**Fix 1 — Resolution-relative threshold**

Replaced the hardcoded pixel value with a threshold relative to the frame diagonal:

```python
# Before: hardcoded, resolution-dependent
MOVEMENT_THRESHOLD = 80  # px — breaks on any non-standard resolution

# After: 4% of frame diagonal, resolution-invariant
frame_diagonal = (frame_w**2 + frame_h**2) ** 0.5
movement_threshold = 0.04 * frame_diagonal
```

**Fix 2 — Temporal smoothing**

Single-frame detections were causing spurious spikes. Added a 10-frame rolling window: only flag an anomaly if it persists across the majority of the window, filtering out motion blur, lighting changes, and compression artefacts.

**Fix 3 — 3-class rebalancing**

The Random Forest was trained on an imbalanced dataset (normal events dominated). Re-framed the problem as a 3-class classification (`normal` / `suspicious` / `anomaly`) and used `class_weight='balanced'` during training, giving the model equal sensitivity across all outcome types.

**Result**

| Stage | False Positive Rate | Classifier Accuracy |
|---|---|---|
| Baseline (hardcoded threshold) | 96% | — |
| After resolution-relative threshold | 38% | — |
| After temporal smoothing | 21% | — |
| After 3-class rebalancing | **12.2%** | **98%** |

---

## License

MIT © 2024 Faheem

---

*Built by [Faheem](https://github.com/faheem0704) — [LinkedIn](https://linkedin.com/in/faheem0704)*

*Built as a portfolio project targeting AI/ML engineering roles in smart city and surveillance AI.*
