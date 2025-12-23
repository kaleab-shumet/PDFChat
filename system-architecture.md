# Phase 3 — System Architecture & Service Boundary Definition

## 📄 Document Purpose

This document defines explicit service boundaries for the PDFChat system.

The goal is to establish clear responsibilities, ownership, and interaction rules before any implementation begins, ensuring scalability, security, and maintainability.

**This document intentionally contains no implementation details.**

---

## 🎯 High-Level System Overview

PDFChat is a multi-user, multi-project PDF Chat (RAG) system where:

- Users create projects
- Projects contain multiple PDFs
- Users chat with their PDFs using Retrieval-Augmented Generation (RAG)

The system is designed using separated services with clear responsibilities to avoid tight coupling and future rewrites.

---

## 🏗 Service Boundary Definitions

### 1. API Gateway / Backend API

#### Responsibility

Acts as the single entry point for all client requests

#### Key Responsibilities

- User authentication (token validation)
- Authorization (user → project → resource access)
- Project lifecycle management
- PDF upload request handling
- Chat request routing
- Rate limiting (future)
- Audit logging (future)

#### Inputs

- HTTP requests from clients (REST)
- Auth tokens

#### Outputs

- HTTP responses to clients
- Events or tasks for background processing
- Requests to RAG Service

#### Explicitly Does NOT

- Parse PDFs
- Generate embeddings
- Perform vector searches
- Call LLMs directly

---

### 2. PDF Worker Service

#### Responsibility

Asynchronous background processing of uploaded PDFs

#### Key Responsibilities

- Retrieve uploaded PDF from object storage
- Parse PDF content
- Chunk extracted text
- Generate embeddings
- Store embeddings and metadata in Vector DB
- Update PDF processing status

#### Trigger

Event or job created after a successful PDF upload

#### Inputs

- PDF file reference (object storage)
- Project and PDF metadata

#### Outputs

- Embeddings stored in Vector DB
- Processing status updates

#### Explicitly Does NOT

- Handle HTTP requests
- Authenticate users
- Serve chat responses
- Manage project access control

---

### 3. RAG Service

#### Responsibility

Handle Retrieval-Augmented Generation logic

#### Key Responsibilities

- Receive validated chat queries
- Retrieve relevant context from Vector DB
- Construct prompts
- Call LLM provider
- Produce final chat responses

#### Inputs

- User query
- Project identifier
- Context retrieval parameters

#### Outputs

- Generated chat response
- Optional metadata (sources, confidence, etc.)

#### Explicitly Does NOT

- Authenticate users
- Validate project ownership
- Parse PDFs
- Manage embeddings lifecycle

---

### 4. Vector Database

#### Responsibility

Persistent storage and retrieval of embeddings

#### Key Responsibilities

- Store vector embeddings
- Perform similarity search
- Enforce logical isolation via namespaces (per project)

#### Inputs

- Embeddings from PDF Worker
- Search queries from RAG Service

#### Outputs

- Relevant document chunks

#### Explicitly Does NOT

- Store raw PDF files
- Perform authorization checks
- Handle user identity

---

### 5. Object Storage

#### Responsibility

Store raw uploaded PDF files

#### Key Responsibilities

- Secure storage of original PDFs
- Support versioning (future)
- Provide controlled access to PDFs for workers

#### Inputs

- PDF uploads from API

#### Outputs

- PDF file access for PDF Worker

#### Explicitly Does NOT

- Parse files
- Serve chat data
- Store embeddings

---

## 🔄 Service Interaction Summary

| Service        | Can Call                          | Cannot Call       |
|----------------|-----------------------------------|-------------------|
| API Gateway    | RAG Service, Object Storage       | Vector DB directly|
| PDF Worker     | Vector DB, Object Storage         | API Gateway       |
| RAG Service    | Vector DB, LLM Provider           | Object Storage    |
| Vector DB      | None                              | All               |
| Object Storage | None                              | All               |

---

## 🧭 Architecture Principles

- Single Responsibility per Service
- No shared databases across services
- Auth and authorization handled only at API layer
- Async processing for heavy workloads
- Project-level isolation enforced everywhere

---

# Phase 3 — Data Flow Architecture

## 📄 Document Purpose

This section defines end-to-end data flows across the system. Every flow is explicit, traceable, and deterministic, ensuring no hidden coupling between services.

---

## 🔄 High-Level Data Flow Categories

The system has two primary flows:

1. **PDF Ingestion & Indexing Flow**
2. **Chat Query & Response Flow**

Each flow is described step-by-step from request to completion.

---

## 📥 1. PDF Ingestion & Indexing Flow

### Goal

Safely ingest uploaded PDFs, process them asynchronously, and make them available for retrieval-augmented chat.

### Step-by-Step Flow

#### 1. User Uploads PDF

- User sends a `POST /projects/{project_id}/pdfs` request
- Request is authenticated and authorized at the API layer

#### 2. Request Validation

API validates:
- User owns or has access to the project
- File type and size constraints

Invalid requests are rejected immediately.

#### 3. PDF Storage

- API stores the raw PDF file in Object Storage
- Storage location is private and inaccessible to clients

#### 4. Metadata Creation

API creates a PDF metadata record:
- Project ID
- File name
- Upload timestamp
- Initial status: `UPLOADED`

#### 5. Background Job Trigger

API emits a background task/event for the PDF Worker.

Event includes:
- PDF identifier
- Storage reference
- Project namespace

#### 6. PDF Retrieval

- PDF Worker retrieves the PDF from Object Storage
- No direct client interaction occurs

#### 7. PDF Parsing

- PDF Worker extracts raw text from the document
- Parsing failures are captured and reported

#### 8. Text Chunking

Extracted text is split into semantic chunks.

Chunk metadata includes:
- PDF ID
- Chunk index
- Project ID

#### 9. Embedding Generation

- PDF Worker generates embeddings for each chunk
- Embeddings are associated with the project namespace

#### 10. Vector Storage

- Embeddings and metadata are stored in Vector DB
- Logical isolation enforced per project

#### 11. Status Update

PDF metadata status is updated:
- `INDEXED` on success
- `FAILED` on error

### Failure Handling

**Parsing or embedding errors:**
- Do not impact other PDFs
- Are isolated to the affected document

**Failed PDFs** can be retried or deleted.

---

## 💬 2. Chat Query & Response Flow

### Goal

Provide accurate, context-aware chat responses scoped to a project's PDFs.

### Step-by-Step Flow

#### 1. User Sends Chat Message

User sends `POST /projects/{project_id}/chat`

Request contains:
- Chat message
- Optional session context

#### 2. Authentication & Authorization

API validates:
- User identity
- Access to the project

Unauthorized requests are rejected.

#### 3. Chat Session Handling

- API creates or resumes a chat session
- Message is stored as part of chat history

#### 4. Query Forwarding

API forwards the validated query to RAG Service.

Includes:
- Project ID
- User query
- Retrieval parameters

#### 5. Context Retrieval

- RAG Service queries Vector DB
- Search is restricted to the project namespace
- Relevant chunks are retrieved

#### 6. Prompt Construction

RAG Service builds a prompt using:
- User query
- Retrieved document context
- System instructions

#### 7. LLM Invocation

- RAG Service sends prompt to LLM provider
- Response is generated

#### 8. Response Post-Processing

RAG Service may:
- Attach source references
- Truncate or format output

#### 9. Response Return

- RAG Service returns response to API

#### 10. Persistence

API stores:
- User message
- Assistant response
- Optional metadata

#### 11. Client Response

- API returns final response to user

### Failure Handling

**Vector DB unavailable:**
- Request fails gracefully
- No partial responses returned

**LLM failures:**
- Errors are surfaced cleanly
- No internal details leaked

---

## ✅ Data Flow Guarantees

- No direct client access to internal services
- All authorization enforced at API layer
- Project-level isolation preserved
- Asynchronous processing for heavy workloads
- Stateless RAG service

---

## 📊 Traceability Summary

| Flow Stage  | Service        |
|-------------|----------------|
| Upload      | API Gateway    |
| Storage     | Object Storage |
| Processing  | PDF Worker     |
| Retrieval   | Vector DB      |
| Generation  | RAG Service    |
| Response    | API Gateway    |

---

# Phase 3 — API Contract Design (Revised)

## 📄 Document Purpose

This section defines the **external REST API contracts** for the PDFChat system.

It explicitly documents **chat session behavior**, lifecycle ownership, and request semantics to avoid ambiguity during implementation.

This document defines **what the API does**, not how it is implemented.

---

## 🎯 API Design Principles

- RESTful, resource-oriented endpoints
- JSON request/response bodies
- Stateless requests from the client
- Backend-controlled lifecycle management
- Explicit HTTP status codes
- Strong project-level isolation
- No internal service leakage

---

## 🌐 Base URL
```
/api/v1
```

---

## 🔐 Authentication

All endpoints require authentication via:
```
Authorization: Bearer <access_token>
```

Unauthorized requests return `401 Unauthorized`.

---

## 📦 Core Resources

- User
- Project
- PDF
- ChatSession
- ChatMessage

---

## 1️⃣ Project Management

### Create Project

**Endpoint**
```http
POST /api/v1/projects
```

**Request Body**
```json
{
  "name": "My Research Project",
  "description": "Optional description"
}
```

**Response — 201 Created**
```json
{
  "id": "project_123",
  "name": "My Research Project",
  "description": "Optional description",
  "created_at": "2025-01-01T10:00:00Z"
}
```

---

### List Projects

**Endpoint**
```http
GET /api/v1/projects
```

**Response — 200 OK**
```json
[
  {
    "id": "project_123",
    "name": "My Research Project",
    "created_at": "2025-01-01T10:00:00Z"
  }
]
```

---

## 2️⃣ PDF Management

### Upload PDF

**Endpoint**
```http
POST /api/v1/projects/{project_id}/pdfs
```

**Request**

- `multipart/form-data`
- File field: `file`

**Response — 202 Accepted**
```json
{
  "pdf_id": "pdf_456",
  "status": "UPLOADED"
}
```

**Notes**

- PDF processing is asynchronous
- Indexing status is updated independently

---

### List PDFs

**Endpoint**
```http
GET /api/v1/projects/{project_id}/pdfs
```

**Response — 200 OK**
```json
[
  {
    "id": "pdf_456",
    "filename": "document.pdf",
    "status": "INDEXED",
    "uploaded_at": "2025-01-01T10:10:00Z"
  }
]
```

---

## 3️⃣ Chat & Session Management

### Chat Session Concept

- A **Project can contain multiple Chat Sessions**
- Each Chat Session represents an isolated conversation
- Sessions group messages to preserve context and relevance
- Session lifecycle is **owned by the backend**

**Clients are not required to explicitly create chat sessions.**

---

### Send Chat Message (Create or Continue Session)

**Endpoint**
```http
POST /api/v1/projects/{project_id}/chat
```

**Request Body**
```json
{
  "message": "What is this document about?",
  "session_id": "optional_session_id"
}
```

---

### `session_id` Semantics (IMPORTANT)

**If `session_id` is omitted:**
- The backend creates a **new Chat Session**
- A new `session_id` is generated and returned

**If `session_id` is provided:**
- The backend continues the existing session
- Previous messages may be used as context

This design allows a **single endpoint** to support both:
- Starting a new conversation
- Continuing an existing one

Without requiring extra API calls.

---

### Response — 200 OK
```json
{
  "session_id": "session_789",
  "reply": "This document discusses...",
  "sources": [
    {
      "pdf_id": "pdf_456",
      "page": 3
    }
  ]
}
```

---

### Error Cases

- `401 Unauthorized`
- `403 Forbidden`
- `404 Project not found`
- `404 Session not found` (if invalid `session_id`)
- `409 No indexed PDFs available`

---

### Get Chat History

**Endpoint**
```http
GET /api/v1/projects/{project_id}/chat/{session_id}
```

**Response — 200 OK**
```json
{
  "session_id": "session_789",
  "messages": [
    {
      "role": "user",
      "content": "What is this document about?"
    },
    {
      "role": "assistant",
      "content": "This document discusses..."
    }
  ]
}
```

---

## 4️⃣ Standard Error Response Format

All error responses follow a consistent structure:
```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "The requested project does not exist"
  }
}
```

---

## 🔒 Security Guarantees

- All endpoints require authentication
- Authorization enforced at project level
- Session access scoped to project ownership
- No cross-project data access possible
- No internal services exposed

---

# Phase 3 — Data Model & Storage Strategy

## 📄 Document Purpose

This section defines the **core data entities**, their **relationships**, **ownership**, **lifecycle**, and **storage strategy** for the PDFChat system.

The goal is to ensure:

- Clear ownership and isolation
- No ambiguous data responsibilities
- Scalable storage decisions
- Alignment with previously defined API and data flows

This section defines **logical models**, not physical schemas.

---

## 🎯 Core Design Principles

- Strong ownership hierarchy: **User → Project → Resources**
- Project-level isolation across all data stores
- Clear lifecycle for every entity
- Separation of concerns across storage systems
- No shared mutable state between services

---

## 🗂 Entity Overview

High-level entity relationship:
```
User
 └── Project
      ├── PDF
      │    └── PDFChunk (logical)
      └── ChatSession
           └── ChatMessage
```

---

## 1️⃣ User

### Description

Represents an authenticated account in the system.

### Key Attributes

- `id`
- `email`
- `created_at`
- `status`

### Ownership

- Root entity

### Storage

- Relational database (primary DB)

### Lifecycle

- Created on signup
- Soft-deleted or disabled if required

---

## 2️⃣ Project

### Description

Logical workspace created by a user to group PDFs and chat sessions.

### Key Attributes

- `id`
- `owner_user_id`
- `name`
- `description`
- `created_at`

### Ownership

- Belongs to a User
- All downstream data is scoped to a Project

### Storage

- Relational database

### Lifecycle

- Created by user
- Active while user owns it
- Deleting a project cascades deletion of all related data

---

## 3️⃣ PDF

### Description

Represents a single uploaded PDF document within a project.

### Key Attributes

- `id`
- `project_id`
- `filename`
- `storage_path`
- `status` (`UPLOADED`, `PROCESSING`, `INDEXED`, `FAILED`)
- `uploaded_at`

### Ownership

- Belongs to a Project

### Storage

- Metadata: relational database
- File content: object storage

### Lifecycle

- Created on upload
- Processed asynchronously
- Can be retried or deleted

---

## 4️⃣ PDFChunk (Logical Entity)

### Description

Represents a chunk of text extracted from a PDF for embedding and retrieval.

### Key Attributes

- `pdf_id`
- `project_id`
- `chunk_index`
- `text`
- `embedding_vector`
- `metadata` (page, offsets, etc.)

### Ownership

- Belongs to a PDF and Project

### Storage

- Vector DB (embeddings + metadata)

### Notes

- Not stored in relational DB
- Exists primarily for retrieval purposes

---

## 5️⃣ ChatSession

### Description

Represents a single, isolated conversation within a project.

### Key Attributes

- `id`
- `project_id`
- `created_at`
- `last_activity_at`

### Ownership

- Belongs to a Project

### Storage

- Relational database

### Lifecycle

- Created implicitly on first chat message
- Active while user interacts
- Can be archived or deleted (future)

---

## 6️⃣ ChatMessage

### Description

Represents an individual message within a chat session.

### Key Attributes

- `id`
- `session_id`
- `role` (`user`, `assistant`)
- `content`
- `created_at`

### Ownership

- Belongs to a ChatSession

### Storage

- Relational database

### Lifecycle

- Immutable once created
- Deleted when session or project is deleted

---

## 💾 Storage Strategy Summary

| Entity         | Storage Type   |
|----------------|----------------|
| User           | Relational DB  |
| Project        | Relational DB  |
| PDF (metadata) | Relational DB  |
| PDF (file)     | Object Storage |
| PDFChunk       | Vector DB      |
| ChatSession    | Relational DB  |
| ChatMessage    | Relational DB  |

---

## 🔒 Data Isolation Strategy

- All data is scoped by `project_id`
- Vector DB uses **per-project namespaces**
- Object storage paths are project-scoped
- Authorization enforced at API layer

---

## 🗑 Data Deletion & Cleanup

### Project Deletion

Deletes:
- Project record
- All PDFs
- All chat sessions and messages
- Vector DB embeddings
- Object storage files

### PDF Deletion

Deletes:
- PDF metadata
- Related embeddings
- Stored PDF file

---

## 🔮 Future-Proofing Considerations

- Soft deletes for auditability
- Usage metrics per project
- Chat session metadata (titles, tags)
- PDF versioning

---

# Phase 3 — Security & Isolation Architecture

## 📄 Document Purpose

This section defines the security model, authorization rules, and data isolation guarantees for the PDFChat system.

The objective is to ensure:

- No cross-user or cross-project data access
- Clear ownership enforcement
- Secure handling of sensitive data
- Explicit trust boundaries between services

This section focuses on architecture-level security, not implementation details.

---

## 🎯 Security Design Principles

- Zero trust between services
- Authentication at the edge
- Authorization before data access
- Project-level isolation everywhere
- Least privilege access
- No implicit trust based on network location

---

## 🔐 Authentication Architecture

### Authentication Scope

- All external requests must be authenticated
- Authentication is handled only at the API Gateway

### Authentication Mechanism (Abstract)

- Token-based authentication (e.g., JWT or opaque tokens)
- Tokens represent a verified user identity
- Tokens are validated on every request

### Guarantees

- No unauthenticated access to any endpoint
- Downstream services never authenticate users directly

---

## 🛡 Authorization Model

### Authorization Rules

Authorization is enforced strictly at the API layer before any downstream call.

**Rules:**

- A user can only access projects they own or are authorized for
- All project-scoped resources require project access validation
- Chat sessions must belong to the same project
- PDFs must belong to the same project

### Authorization Flow

1. Request received at API Gateway
2. Token validated → user identified
3. Project ownership/access verified
4. Only then is the request forwarded to internal services

---

## 🔗 Service-to-Service Security

### Trust Boundaries

- Internal services (PDF Worker, RAG Service) are not exposed publicly
- Only the API Gateway can receive external traffic

### Service Authentication

Services authenticate with each other using:

- Service credentials
- Internal tokens

**No user tokens are forwarded to internal services**

---

## 🔒 Data Isolation Strategy

### Project-Level Isolation (Critical)

Isolation is enforced at every layer:

#### Relational Database

- All records include `project_id`
- Queries are always scoped by `project_id`

#### Vector Database

- Separate namespace per project
- No cross-project vector search possible

#### Object Storage

- Files stored under project-scoped paths
- Buckets are private
- No public access to raw PDFs

### Chat Session Isolation

- Chat sessions belong to a single project
- A session ID is only valid within its project
- Accessing a session from another project is rejected

---

## 🔑 Secrets Management

### Principles

- No secrets committed to source control
- Secrets injected via environment variables
- Separate secrets per environment (local, staging, production)

### Examples of Secrets

- Database credentials
- Object storage keys
- LLM API keys
- Vector DB credentials

---

## 📝 Logging & Error Safety

### Logging Rules

Logs must not contain:

- Tokens
- Secrets
- Raw PDF content
- User-sensitive data

### Error Handling

- Internal errors are not exposed to clients
- Standardized error responses
- No stack traces returned externally

---

## 🛡️ Threat Mitigation Summary

| Threat                  | Mitigation                        |
|-------------------------|-----------------------------------|
| Cross-user data leak    | Project-scoped authorization      |
| Cross-project access    | Namespace isolation               |
| Unauthorized access     | Token validation                  |
| Secret leakage          | Env-based secrets                 |
| Data exfiltration       | Private storage & strict access   |

---

## 🚫 Out of Scope (This Phase)

- Fine-grained role-based access control (RBAC)
- Rate limiting enforcement
- Audit logs
- End-to-end encryption

**These may be added in future phases.**

---

## 📊 Status

- ✅ Security model defined
- ✅ Authorization rules explicit
- ✅ Data isolation guaranteed

---

## 🎉 Phase 3 Completion Summary

- ✅ Service boundaries defined
- ✅ Data flow traceable end-to-end
- ✅ API contracts finalized
- ✅ Data model complete
- ✅ Security & isolation architecture explicit

---

## 🏆 Phase 3 is now COMPLETE ✅