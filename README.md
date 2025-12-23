# PDFChat

PDFChat is a **production-grade, multi-user, project-based PDF Chat platform** that allows users to upload multiple PDFs into a project and chat with them using Retrieval-Augmented Generation (RAG).

This repository is designed with **SaaS readiness**, **scalability**, and **engineering discipline** from day one.

---

## 🎯 Vision

Build a secure, scalable system where:

- Users create projects
- Each project contains multiple PDFs
- Users can chat with their project as a unified knowledge base
- Answers are accurate, traceable, and isolated per user/project

This is **not a demo** — it is an engineering-first foundation for a real product.

---

## 🧠 Core Concepts
```
User
└── Project
    ├── PDF
    ├── PDF
    └── Chat (RAG across all PDFs in the project)
```

- **Multi-user**: authenticated users only
- **Project isolation**: no data leakage across users or projects
- **Project-level chat**: retrieval spans all PDFs in the project
- **Cloud-first**: designed for production deployment

---

## 🚀 MVP Scope

### Included

- Multi-user authentication
- Project-based organization
- Multiple PDFs per project
- Project-scoped chat
- RAG with source citations
- Async document ingestion
- Observability-ready architecture
- CI/CD-first mindset

### Explicitly Out of Scope (for MVP)

- Cross-project chat
- Team/shared projects
- Billing & subscriptions
- Fine-tuned models
- Real-time collaboration

---

## 🏗 High-Level Architecture

- **API**: Python (FastAPI)
- **Workers**: background ingestion & indexing
- **Core**: shared domain logic
- **Storage**:
  - PDFs → Object storage (e.g., S3)
  - Metadata → PostgreSQL
  - Embeddings → Vector DB (e.g., Qdrant)
- **LLM**: Abstracted provider (initially OpenAI)
- **Observability**: logs, metrics, tracing (OpenTelemetry)

> Implementation details are intentionally deferred until later phases.

---

## 🧰 Tech Stack (Locked Decisions)

- **Python**: 3.12.3 (required)
- **Repository**: mono-repo
- **Config**: environment variables only (12-factor)
- **CI/CD**: enforced before feature work
- **Code Quality**: formatter, linter, type checking, tests (CI-gated)

---

## 📂 Repository Structure (High-Level)
```
PDFChat/
├── api/        # API service (FastAPI)
├── workers/    # Background workers
├── core/       # Shared domain & business logic
├── infra/      # CI/CD, Docker, IaC
├── docs/       # Architecture & ADRs
├── tests/      # Test suite
└── README.md
```

---

## 🧭 Project Status

- ✅ Phase 0 — Scope & Architecture decisions locked
- ✅ Phase 1 — Engineering foundations
- ⏭ Phase 2 — CI/CD & code quality enforcement (next)

---

## ⚠️ Important Principles

- No shortcuts
- No production secrets in the repo
- No feature work without CI
- Architecture before implementation

---

## 📄 License

TBD
