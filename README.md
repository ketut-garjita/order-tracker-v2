# Order Tracker — Observability & Automated Incident Response

Order Tracker is a small FastAPI application extended into a fully observable, containerized service with automated incident response.

**Repository Version:** v2  
**Status:** Q1–Q6 completed and verified; the original incident scenario has been fixed.

The project demonstrates a complete operational workflow:

```text
Application
    │
    ├── Metrics
    ├── Logs
    └── Traces
          │
          ▼
 OpenTelemetry Collector
      │      │      │
      ▼      ▼      ▼
 Prometheus Loki   Tempo
      │      │      │
      └──────┼──────┘
             ▼
          Grafana
             │
       Alert / Webhook
             │
             ▼
    Incident Response
             │
             ▼
        Codex CLI
             │
             ▼
       Code Investigation
       and Bug Fix
```

---

## 1. Problem Statement

The original Order Tracker application was functional, but an application-level failure could be difficult to investigate because application health alone does not explain what happened during a request.

The project was therefore extended to answer three operational questions:

1. **What happened?** — metrics, logs, and traces.
2. **When should someone investigate?** — Grafana alerting on server errors.
3. **Can the incident investigation and remediation be automated?** — an incident responder that invokes a headless coding assistant.

The incident scenario exposed a bug in the express-order delivery-date calculation. The original implementation attempted to construct a date by directly replacing the day component:

```python
placed_at.replace(day=placed_at.day + 2)
```

For an order placed near the end of a month, the resulting day can be invalid.

---

## 2. Solution

Version 2 adds an end-to-end observability and incident-response workflow.

### Application observability

The FastAPI application is instrumented with OpenTelemetry for:

- **Metrics** — request counts and HTTP status codes.
- **Logs** — request and incident information.
- **Traces** — request execution flow.

The request metric includes the route and HTTP status code so successful requests and server-side failures can be distinguished.

### Telemetry pipeline

Telemetry is sent through an OpenTelemetry Collector and routed to:

- Prometheus for metrics.
- Loki for logs.
- Tempo for traces.
- Grafana for visualization and alerting.

### Automated incident response

Grafana can send an alert webhook to:

```text
POST http://localhost:8001/alerts
```

The `incident-response` service:

1. Receives the alert.
2. Stores incident information.
3. Collects relevant observability evidence.
4. Starts the coding assistant in headless mode.
5. Provides the repository workspace to the agent for investigation and remediation.

The coding assistant used for this project is **Codex CLI**.

### Bug resolution

The express-order date calculation was corrected to perform date arithmetic rather than manually replacing the calendar day:

```python
estimated_at = placed_at + timedelta(days=2)
```

This handles month boundaries correctly.

---

## 3. Data Sources

The project uses local application data rather than an external business data platform.

### Order data

Order data is stored in the application's SQLite database.

The seeded test orders include:

- `standard-1001`
- `express-1002`
- `standard-1003`

The `express-1002` order is used to exercise the incident scenario.

### Observability data

The observability layer produces three telemetry signals:

| Signal | Storage / Backend | Purpose |
|---|---|---|
| Metrics | Prometheus | Request counts and HTTP status metrics |
| Logs | Loki | Application and incident evidence |
| Traces | Tempo | Request execution and failure investigation |

Grafana provides a unified interface for querying these signals.

---

## 4. Architecture

The final architecture consists of the application, observability stack, alerting layer, and automated incident responder.

```text
                         ┌──────────────────┐
                         │      Client      │
                         │ curl / Browser   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    FastAPI App   │
                         │      :8000       │
                         └────────┬─────────┘
                                  │
                         OTLP metrics/logs/traces
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ OpenTelemetry Collector │
                    │        :4317/:4318      │
                    └──────┬──────┬──────┬────┘
                           │      │      │
                 metrics   │      │      │   traces
                           │      │      │
                           ▼      ▼      ▼
                     Prometheus Loki   Tempo
                        :9090   :3100  :3200
                           \      |      /
                            \     |     /
                             ▼    ▼    ▼
                           ┌─────────────┐
                           │   Grafana   │
                           │    :3000    │
                           └──────┬──────┘
                                  │
                            Alert Webhook
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │   Incident Response    │
                     │         :8001          │
                     └────────────┬───────────┘
                                  │
                         Evidence + prompt
                                  │
                                  ▼
                         ┌────────────────┐
                         │    Codex CLI   │
                         │    headless    │
                         └───────┬────────┘
                                 │
                         Repository workspace
                                 │
                                 ▼
                           Bug investigation
                           and code repair
```

### Incident flow

```text
HTTP 5xx
   │
   ▼
OpenTelemetry
   │
   ▼
Collector
   │
   ▼
Prometheus
   │
   ▼
Grafana Alert
   │
   ▼
POST /alerts
   │
   ▼
incident-response
   │
   ├── Save alert
   ├── Collect logs
   ├── Collect traces
   └── Start Codex
           │
           ▼
       Diagnose bug
           │
           ▼
        Fix code
           │
           ▼
      Restart / verify
```

---

## 5. Project Structure

```text
order-tracker/
├── app/
│   ├── main.py
│   └── telemetry.py
│
├── incident-response/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── responder.py
│   ├── evidence.py
│   ├── agent.py
│   ├── prompt.md
│   └── incidents/
│
├── observability/
│   ├── otel-collector-config.yaml
│   ├── prometheus.yml
│   ├── loki-config.yaml
│   ├── tempo-config.yaml
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── datasources.yaml
│       │   └── dashboards/
│       │       └── dashboards.yaml
│       └── dashboards/
│           └── order-tracker.json
│
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── orders/
└── README.md
```

### Main components

| Component | Responsibility |
|---|---|
| `app/main.py` | FastAPI application and order endpoints |
| `app/telemetry.py` | OpenTelemetry instrumentation |
| `incident-response/main.py` | HTTP service and `/alerts` endpoint |
| `incident-response/responder.py` | Incident-response orchestration |
| `incident-response/evidence.py` | Incident evidence collection |
| `incident-response/agent.py` | Headless coding-agent execution |
| `incident-response/prompt.md` | Investigation/remediation instructions |
| `observability/otel-collector-config.yaml` | Telemetry routing |
| `observability/prometheus.yml` | Prometheus configuration |
| `observability/loki-config.yaml` | Loki configuration |
| `observability/tempo-config.yaml` | Tempo configuration |
| `observability/grafana/` | Grafana data sources and dashboard |
| `compose.yaml` | Complete local stack |

---

## 6. Technology / Tools

### Application

- Python 3.12
- FastAPI
- Uvicorn
- SQLite
- `uv`

### Observability

- OpenTelemetry
- OpenTelemetry Collector Contrib `0.133.0`
- Prometheus `3.5.0`
- Loki `3.5.0`
- Tempo `2.7.2`
- Grafana `12.1.1`

### Incident Response

- FastAPI
- Docker
- Codex CLI
- Headless coding-agent execution

### Infrastructure

- Docker
- Docker Compose
- HTTP / REST
- OTLP

---

## 7. How to Run

### Prerequisites

Install or have available:

- Docker
- Docker Compose
- Python
- `uv`

For the automated incident-response workflow, Codex CLI must also be configured with valid authentication.

### Start the complete stack

From the repository root:

```bash
docker compose up --build -d
```

Check the containers:

```bash
docker compose ps
```

The main services expose:

| Service | URL |
|---|---|
| Order Tracker | http://localhost:8000 |
| Incident Response | http://localhost:8001 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100 |
| Tempo | http://localhost:3200 |

### Verify application health

```bash
curl http://localhost:8000/healthz
```

Expected:

```json
{"status":"ok"}
```

### Verify the incident responder

```bash
curl http://localhost:8001/healthz
```

### Test an order lookup

Successful order:

```bash
curl -i http://localhost:8000/api/orders/standard-1001
```

Missing order:

```bash
curl -i http://localhost:8000/api/orders/standard-1002
```

The missing order produces HTTP `404`, which can be observed through the telemetry stack.

### Test the repaired express-order path

```bash
curl -i http://localhost:8000/api/orders/express-1002
```

After the bug fix, the endpoint should complete without the previous date-calculation exception.

### Test the responder webhook

Start apps ( http://0.0.0.0:8001):

```bsh
./incident-response/run.sh
```

Open another terminal:

```bash
curl -X POST http://localhost:8001/alerts \
  -H 'Content-Type: application/json' \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},"annotations":{"summary":"Test notification; no incident to fix"}}]}'
```

Inspect the responder logs in the **./incident-response/incidents/** directory

### Stop the stack

```bash
docker compose down
```

---

## 8. Monitoring Dashboard

Grafana provides the main operational view for the application.

Open:

```text
http://localhost:3000
```

The dashboard brings together application request metrics and telemetry generated by the service.

### Metrics

The request metric records:

- HTTP route
- HTTP status code
- Request activity

This makes it possible to distinguish normal traffic from `5xx` server errors.

### Logs

Loki stores application logs received through the OpenTelemetry Collector.

Logs provide contextual information for an individual request and help correlate an alert with application behavior.

### Traces

Tempo stores distributed traces received through the Collector.

Traces provide the request execution path and help identify where an exception occurred.

### Alerting

Grafana monitors server-error responses.

The alert configuration includes:

- affected endpoint information
- evaluation time window
- dashboard reference
- handling for periods without `5xx` data

When the alert fires, Grafana can send a webhook to:

```text
http://incident-response:8001/alerts
```

This starts the automated incident-response workflow.

---

## 9. Improvements

Version 2 establishes the complete local observability and automated remediation loop, but several improvements would be appropriate for a production deployment.

### Security

- Store Codex/OpenAI credentials in a dedicated secret manager.
- Avoid exposing internal observability services unnecessarily.
- Authenticate and authorize the alert webhook.
- Restrict the coding agent's filesystem and network permissions.

### Reliability

- Add retry and timeout policies to the incident responder.
- Persist incident state in a durable database.
- Prevent duplicate processing of repeated Grafana notifications.
- Add responder health and readiness checks.

### Agent safety

- Add explicit approval policies for production changes.
- Run automated tests before accepting an agent-generated fix.
- Require verification after restart.
- Escalate incidents when the agent cannot produce a validated fix.

### Observability

- Add structured JSON logging.
- Add more business-level metrics.
- Add trace-to-log correlation.
- Add alert severity and incident lifecycle tracking.

### Deployment

- Separate development and production configurations.
- Add CI checks for telemetry configuration.
- Build immutable application images.
- Deploy the observability stack with infrastructure-as-code.

---

## 10. Acknowledgments

This project was developed as part of the **DataTalksClub AI Dev Tools Zoomcamp — Homework 4: DevOps and Observability for AI-Built Apps**.

The exercise provided the Order Tracker application and the incident scenario used to implement:

- OpenTelemetry metrics, logs, and traces
- OpenTelemetry Collector
- Prometheus
- Loki
- Tempo
- Grafana dashboards and alerting
- Automated incident response
- Headless coding-agent execution
- Agent-assisted debugging and remediation

Special thanks to **DataTalksClub** for the AI Dev Tools Zoomcamp and the practical learning-by-building approach.

---

## Verification Summary

The final v2 implementation successfully completed the six homework questions:

| Question | Verification |
|---|---|
| Q1 | `/healthz` returns `{"status":"ok"}` |
| Q2 | `standard-1001` records HTTP `200` |
| Q3 | `standard-1002` records HTTP `404` |
| Q4 | Grafana `5xx` alert behaves according to the configured rule |
| Q5 | `incident-response` receives `/alerts` and starts the coding agent |
| Q6 | `express-1002` incident is investigated and the date-calculation bug is fixed |

### Root cause of the original incident

The express delivery calculation attempted to create a date by incrementing the calendar day directly. When the order was created near the end of a month, that day could be outside the valid range for the month.

The corrected implementation uses date arithmetic:

```python
estimated_at = placed_at + timedelta(days=2)
```

This makes the calculation valid across month boundaries.

---

## Project Status

**Order Tracker v2 — Completed**

The repository now demonstrates a complete local DevOps and observability workflow:

```text
Application
    ↓
Telemetry
    ↓
OpenTelemetry Collector
    ↓
Prometheus / Loki / Tempo
    ↓
Grafana
    ↓
Alert
    ↓
Incident Responder
    ↓
Codex CLI
    ↓
Investigation
    ↓
Bug Fix
    ↓
Verification
```

The original incident has been resolved, and the application has been verified through the Q1–Q6 workflow.
