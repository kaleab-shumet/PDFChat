# Phase 4 — Observability Strategy

> Complete observability architecture for the PDFChat system covering logging, metrics, tracing, LLM observability, and error handling.

---

## Table of Contents

1. [Logging Strategy](#1-logging-strategy)
2. [Metrics & Monitoring](#2-metrics--monitoring)
3. [Distributed Tracing](#3-distributed-tracing)
4. [LLM Observability](#4-llm-observability)
5. [Error Tracking & Alerting](#5-error-tracking--alerting)
6. [Phase 4 Summary](#6-phase-4-summary)

---

## 1. Logging Strategy

### 1.1 Purpose

This section defines a consistent, structured logging strategy for all services in the PDFChat system to ensure:

- Debuggability
- Traceability
- Production safety
- Privacy compliance

Logging is designed before implementation to avoid unstructured logs and blind debugging later.

### 1.2 Design Principles

- Logs are structured, not free-text
- Logs are machine-readable
- Logs never contain sensitive data
- Logs are correlated across services
- Logs are useful for both humans and monitoring systems

### 1.3 Log Levels

All services must use the same log levels:

| Level    | Usage                                      |
|----------|---------------------------------------------|
| DEBUG    | Detailed internal state (local/dev only)    |
| INFO     | Normal system behavior                      |
| WARN     | Recoverable or suspicious situations        |
| ERROR    | Failed operations requiring attention       |
| CRITICAL | System-wide failure or data loss risk       |

### 1.4 Log Format

All logs must be emitted in structured JSON format with the following required fields:

```json
{
  "timestamp": "ISO-8601",
  "level": "INFO | WARN | ERROR",
  "service": "api-gateway | rag-service | pdf-worker",
  "environment": "local | staging | production",
  "message": "Human-readable summary",
  "request_id": "uuid",
  "project_id": "uuid (if applicable)",
  "user_id": "uuid (if applicable)"
}
```

### 1.5 Correlation & Traceability

- Every incoming request generates a `request_id`
- `request_id` is propagated across all internal services
- Logs across services can be correlated using `request_id`

This enables:

- End-to-end request tracing
- Faster root cause analysis
- Cross-service debugging

### 1.6 What Must Be Logged

#### API Gateway

- Incoming requests (method, path)
- Authorization success/failure (without token data)
- Request duration
- Error responses

#### PDF Worker

- PDF upload received
- Parsing started/completed
- Chunking success/failure
- Processing duration

#### RAG Service

- Retrieval started
- Number of chunks retrieved
- LLM request initiated
- Response received
- Latency metrics

### 1.7 What Must NOT Be Logged

> **Critical Privacy Constraints**

- ❌ Raw PDF content
- ❌ User prompts or full chat messages
- ❌ Authentication tokens
- ❌ API keys or secrets
- ❌ Personally identifiable information (PII)

### 1.8 Log Aggregation Strategy

- Logs written to `stdout`/`stderr`
- Centralized aggregation via logging backend (TBD)
- Environment-based retention policies:
  - **Dev**: Short retention
  - **Prod**: Longer retention with rotation

### 1.9 Environment-Specific Behavior

| Environment | Logging Behavior         |
|-------------|--------------------------|
| Local       | DEBUG enabled            |
| Staging     | INFO and above           |
| Production  | INFO and above (no DEBUG)|

### 1.10 Failure Safety

- Logging must never crash a service
- Logging failures are non-blocking
- No synchronous external log calls in request path

---

## 2. Metrics & Monitoring

### 2.1 Purpose

This section defines the metrics, KPIs, and monitoring strategy for the PDFChat system to ensure:

- System health is visible at all times
- Performance regressions are detected early
- Business-critical workflows are measurable
- Scaling decisions are data-driven

Metrics are defined before implementation to avoid incomplete or misleading monitoring.

### 2.2 Design Principles

- Metrics must be actionable
- Metrics must be low-overhead
- Metrics must reflect user experience
- Metrics must align with service boundaries
- Metrics must support alerting and dashboards

### 2.3 Metric Categories

Metrics are grouped into four categories:

1. Infrastructure Metrics
2. Service-Level Metrics
3. Business Metrics
4. LLM-Specific Metrics

### 2.4 Infrastructure Metrics

Tracked for all services:

| Metric       | Description                |
|--------------|----------------------------|
| CPU usage    | Service CPU consumption    |
| Memory usage | RAM utilization            |
| Disk I/O     | Read/write activity        |
| Network I/O  | Request/response throughput|

**Purpose**: Detect resource exhaustion and support scaling decisions.

### 2.5 Service-Level Metrics

#### API Gateway

| Metric          | Description              |
|-----------------|--------------------------|
| Request count   | Total incoming requests  |
| Request latency | p50 / p95 / p99          |
| Error rate      | 4xx / 5xx ratio          |
| Auth failures   | Authorization rejections |

#### PDF Worker

| Metric           | Description            |
|------------------|------------------------|
| PDFs uploaded    | Count per time window  |
| Processing time  | PDF ingestion duration |
| Parsing failures | Failed PDF jobs        |
| Queue depth      | Pending PDF jobs       |

#### RAG Service

| Metric            | Description                |
|-------------------|----------------------------|
| Retrieval latency | Vector search duration     |
| Chunks retrieved  | Number of retrieved chunks |
| LLM latency       | Time to generate response  |
| RAG failures      | End-to-end failures        |

### 2.6 Business Metrics

These reflect product health, not infrastructure.

| Metric              | Description            |
|---------------------|------------------------|
| Projects created    | New projects           |
| PDFs per project    | Average usage          |
| Chat sessions created| Conversations started |
| Messages per session| Engagement indicator   |
| Time to first answer| User-perceived latency |

### 2.7 LLM Cost & Usage Metrics

| Metric            | Description          |
|-------------------|----------------------|
| Token usage       | Tokens per request   |
| Cost per request  | Estimated spend      |
| Cost per project  | Budget tracking      |
| Requests per model| Model usage patterns |

**Purpose**: Cost control, budget forecasting, and model optimization.

### 2.8 Dashboards

#### Operational Dashboard

- Service health
- Error rates
- Latency percentiles

#### Product Dashboard

- User activity
- Project growth
- PDF ingestion trends

#### LLM Dashboard

- Latency
- Token usage
- Cost trends

### 2.9 Alerting Thresholds

| Metric         | Alert Condition           |
|----------------|---------------------------|
| API error rate | > 2% for 5 min            |
| LLM latency    | p95 > threshold           |
| PDF failures   | Spike above baseline      |
| Cost anomaly   | Sudden usage increase     |

> Thresholds will be refined post-launch.

### 2.10 Metric Collection Strategy

- Metrics emitted by services
- Collected asynchronously
- Aggregated centrally
- No blocking calls in request path

### 2.11 Retention Policy

| Environment | Retention               |
|-------------|-------------------------|
| Local       | Minimal                 |
| Staging     | Short-term              |
| Production  | Long-term (policy-driven)|

### 2.12 Privacy Considerations

- No raw prompts stored
- No user-identifiable content in metrics
- Metrics are numeric and aggregated

---

## 3. Distributed Tracing

### 3.1 Purpose

This section defines the distributed tracing architecture for the PDFChat system to ensure:

- End-to-end request visibility across services
- Fast root cause analysis for failures
- Clear understanding of latency sources
- Traceable user journeys from request to response

Tracing is designed before implementation to prevent fragmented or unusable traces.

### 3.2 Design Principles

- Every external request is traceable end-to-end
- Traces span all service boundaries
- Tracing must have minimal performance overhead
- Tracing must not expose sensitive data
- Sampling is configurable per environment

### 3.3 Trace Scope

Traces cover the full lifecycle of:

- API requests
- PDF ingestion workflows
- Chat/RAG requests
- Internal service calls

### 3.4 Trace Identifiers

Each trace includes:

| Identifier       | Description              |
|------------------|--------------------------|
| `trace_id`       | Unique per request       |
| `span_id`        | Unique per operation     |
| `parent_span_id` | Hierarchical relationship|

These identifiers are propagated across services.

### 3.5 Trace Propagation Flow

1. External request arrives at API Gateway
2. API Gateway creates a `trace_id`
3. `trace_id` is attached to:
   - Internal HTTP headers
   - Logs
   - Metrics
4. Downstream services create child spans
5. Entire request can be visualized as a trace graph

### 3.6 Span Definition by Service

#### API Gateway

- Request received
- Authentication
- Authorization
- Downstream call initiation

#### PDF Worker

- PDF validation
- Parsing
- Chunking
- Vector storage

#### RAG Service

- Query received
- Vector retrieval
- Prompt construction
- LLM invocation
- Response generation

### 3.7 Error & Latency Attribution

- Errors are recorded at the span level
- Slow spans are highlighted
- Failed spans include error metadata (no sensitive data)

This enables:

- Identification of slow components
- Clear blame assignment (API vs RAG vs LLM)

### 3.8 Sampling Strategy

| Environment | Sampling                   |
|-------------|----------------------------|
| Local       | 100%                       |
| Staging     | 100%                       |
| Production  | Configurable (e.g., 5–10%) |

Sampling decisions are made at the entry point (API Gateway).

### 3.9 Trace Storage & Retention

- Traces stored centrally
- Retention varies by environment
- High-cardinality traces rotated regularly

### 3.10 Privacy & Security Constraints

- No raw PDF content in traces
- No user prompts stored verbatim
- No authentication data captured
- Trace access restricted to authorized operators

### 3.11 Performance Considerations

- Tracing must be asynchronous
- Tracing failures must not impact request execution
- No blocking trace exporters in request path

---

## 4. LLM Observability

### 4.1 Purpose

This section defines how LLM usage, performance, cost, reliability, and quality signals are observed in the PDFChat system.

LLMs are:

- External dependencies
- Probabilistic
- Cost-sensitive
- Latency-dominant

Therefore, they require explicit, dedicated observability design.

This strategy applies whether LLM calls are made directly by the RAG Service or via an LLM Gateway service.

### 4.2 Design Principles

- Observe metadata, not content
- Treat LLMs as critical infrastructure
- Cost attribution must be accurate and auditable
- Observability must not affect request latency
- Privacy and security are non-negotiable

### 4.3 LLM Call Architecture

```
User Request
     ↓
API Gateway
     ↓
RAG Service
     ↓
[ Optional LLM Gateway ]
     ↓
LLM Provider
```

Observability applies regardless of gateway presence.

### 4.4 LLM Request Lifecycle

Each LLM interaction consists of:

1. Context retrieval completed
2. Prompt constructed (not logged)
3. LLM request sent
4. LLM response generated
5. Response post-processed

Observability hooks exist at steps 3–5.

### 4.5 Performance Metrics

| Metric              | Description                  |
|---------------------|------------------------------|
| LLM latency         | End-to-end LLM call duration |
| Time to first token | Initial response delay       |
| Generation duration | Total completion time        |
| Timeout rate        | Requests exceeding limits    |

**Purpose**: Detect slow responses and identify provider or model regressions.

### 4.6 Usage & Cost Metrics

| Metric            | Description          |
|-------------------|----------------------|
| Tokens in         | Prompt token count   |
| Tokens out        | Completion token count|
| Tokens per request| Total usage          |
| Cost per request  | Monetary cost        |
| Cost per project  | Aggregated billing unit|
| Cost per user     | Account-level aggregation|

### 4.7 Cost Attribution Model

**Primary Billing Boundary**: Project

Every LLM request is tagged with:

- `project_id`
- `user_id`
- `request_id`
- `model`

Cost is calculated per request. Requests are aggregated per project.

**User cost** = sum(cost of all owned projects)

#### Why Project-Level First

- Strong isolation boundary
- Future-ready for shared/team projects
- Clean SaaS billing semantics

### 4.8 Reliability Metrics

| Metric              | Description           |
|---------------------|-----------------------|
| Error rate          | LLM API failures      |
| Retry count         | Automatic retries     |
| Fallback usage      | Secondary model usage |
| Provider availability| Upstream health      |

### 4.9 Quality Proxy Metrics

> Raw prompts and responses are never stored.

Instead, quality is inferred via proxies:

| Metric               | Purpose                    |
|----------------------|----------------------------|
| Retrieved chunk count| Context relevance          |
| Context token size   | Prompt richness            |
| Answer length        | Response completeness      |
| Regeneration rate    | User dissatisfaction signal|

These are signals, not absolute judgments.

### 4.10 LLM Gateway Integration

If an LLM Gateway is used:

#### Gateway Responsibilities

- Token counting
- Cost calculation
- Provider routing
- Retry and fallback logic
- Rate limiting/quotas

#### RAG Service Responsibilities

- Provide request metadata
- Consume response + usage data
- Remain provider-agnostic

#### Observability Impact

Gateway becomes the source of truth for tokens, cost, and latency. Existing aggregation logic remains unchanged. No architectural redesign is required.

### 4.11 Trace Integration

- Each LLM call is a dedicated span
- Spans include: model name, provider, latency, status
- Linked to full request trace via `trace_id`

### 4.12 Privacy & Security Constraints

- ❌ No raw prompts
- ❌ No LLM responses
- ❌ No PII
- ❌ No authentication data

Only numeric and categorical metadata is recorded.

### 4.13 Alerting

| Condition           | Severity |
|---------------------|----------|
| Error rate spike    | Critical |
| Latency regression  | Warning  |
| Cost anomaly        | Alert    |
| Provider outage     | Critical |

### 4.14 Environment-Specific Behavior

| Environment | Observability       |
|-------------|---------------------|
| Local       | Full metrics        |
| Staging     | Full metrics        |
| Production  | Metrics + sampling  |

---

## 5. Error Tracking & Alerting

### 5.1 Purpose

This section defines how errors, failures, and abnormal system behavior are detected, categorized, and escalated in the PDFChat system.

The objective is to:

- Detect issues early
- Minimize user impact
- Enable fast root cause analysis
- Establish clear incident response signals

Error tracking is designed before implementation to avoid blind production failures.

### 5.2 Error Management Principles

- Errors must be visible
- Errors must be actionable
- Errors must be classified consistently
- Alerts must be signal-based, not noise-based
- Human intervention should be required only when necessary

### 5.3 Error Categories

#### 1️⃣ Client Errors (4xx)

**Examples**: Unauthorized access, invalid requests, missing parameters

**Handling**:
- Logged at WARN level
- Not alert-worthy
- Counted for metrics

#### 2️⃣ Service Errors (5xx)

**Examples**: Internal service failures, timeouts, dependency failures

**Handling**:
- Logged at ERROR level
- Included in traces
- Alerted based on rate and impact

#### 3️⃣ Dependency Errors

**Examples**: LLM provider failures, vector DB unavailability, object storage failures

**Handling**:
- Logged at ERROR level
- Tagged with dependency name
- Elevated alert priority

#### 4️⃣ Data Integrity Errors

**Examples**: Corrupted PDFs, failed vector writes, inconsistent state

**Handling**:
- Logged at CRITICAL level
- Immediate alert
- Requires human intervention

### 5.4 Error Metadata

Every error log includes:

```json
{
  "error_type": "client | service | dependency | data",
  "service": "api-gateway | rag-service | pdf-worker",
  "request_id": "uuid",
  "trace_id": "uuid",
  "project_id": "uuid (if applicable)",
  "severity": "WARN | ERROR | CRITICAL"
}
```

### 5.5 Alert Severity Levels

| Severity | Meaning        | Action             |
|----------|----------------|--------------------|
| Info     | Informational  | No action          |
| Warning  | Potential issue| Monitor            |
| Alert    | User-impacting | Investigate        |
| Critical | System failure | Immediate response |

### 5.6 Alert Triggers

| Condition              | Severity |
|------------------------|----------|
| API error rate > threshold | Alert    |
| LLM failure spike      | Alert    |
| PDF ingestion failures | Warning  |
| Data integrity error   | Critical |
| Cost anomaly           | Alert    |

> Thresholds are refined post-launch.

### 5.7 Alert Routing

- Alerts routed to on-call engineer and team notification channel
- Critical alerts bypass batching
- Alert deduplication enabled

### 5.8 Incident Response Flow

1. Alert triggered
2. Engineer inspects: metrics, logs, traces
3. Mitigation applied
4. Incident resolved
5. Post-incident review (future)

### 5.9 Error Tracking Integration

Errors are linked to logs, traces, and metrics. A single `request_id` allows full correlation.

### 5.10 Noise Reduction Strategy

- Rate-based alerting
- Alert suppression during known maintenance
- Aggregation over time windows

### 5.11 Privacy & Security Constraints

- ❌ No sensitive data in error logs
- ❌ No tokens or secrets logged
- ❌ No raw user input captured

---

## 6. Phase 4 Summary

| Component                 | Status |
|---------------------------|--------|
| Logging Strategy          | ✅ Complete |
| Metrics & Monitoring      | ✅ Complete |
| Distributed Tracing       | ✅ Complete |
| LLM Observability         | ✅ Complete |
| Error Tracking & Alerting | ✅ Complete |

### Key Achievements

- ✅ Logging standards defined with privacy constraints enforced
- ✅ Key metrics defined and KPIs aligned with business goals
- ✅ End-to-end tracing defined with explicit span boundaries
- ✅ LLM performance observable with gateway-compatible design
- ✅ Error taxonomy defined with alerting rules established

---

*Document Version: 1.0*  
*Last Updated: Phase 4 Completion*
