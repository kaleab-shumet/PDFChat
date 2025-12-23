# Contributing to PDFChat

This project follows **strict engineering discipline**.  
Please read this document carefully before contributing.

---

## 🧠 Engineering Philosophy

- Quality > speed
- CI before features
- Decisions are documented
- Code must be production-ready
- No undocumented changes

This repo is intended to **scale with contributors**, not collapse under them.

---

## 🧾 Repository Model

- **Mono-repo**
- Single source of truth
- Shared standards across all services

---

## 🌿 Branching Strategy

### Default Branch

- `main` → always stable & deployable

### Working Branches

All work must happen on feature branches:
```
feature/<short-description>
fix/<short-description>
chore/<short-description>
```

Examples:
```
feature/project-model
fix/token-refresh
chore/update-docs
```

---

## 🔀 Pull Request Rules

- No direct commits to `main`
- Pull Request required for all changes
- CI must be green
- At least one review required (can be self-review for now)
- Small, focused PRs preferred

---

## 🐍 Python & Environment

### Required Python Version

- **Python 3.12.3**
- This is mandatory across local, CI, and production environments

A `.python-version` file should be respected if present.

---

## ⚙️ Environment Configuration

- Environment variables only
- No secrets committed to the repo
- Use `.env.example` as reference
- `.env` files must never be committed

Environments:

- `local`
- `staging`
- `production`

---

## 🧪 Code Quality (CI-Enforced)

The following tools are **mandatory** and will be enforced via CI:

| Category       | Tool   |
|----------------|--------|
| Formatting     | black  |
| Import sorting | isort  |
| Linting        | ruff   |
| Type checking  | mypy   |
| Testing        | pytest |

> Do not bypass or disable checks.

---

## 🧱 Repository Structure Rules

- `api/` → HTTP layer only
- `workers/` → background processing only
- `core/` → shared domain logic
- `infra/` → deployment, CI/CD, IaC
- `docs/` → architecture & decisions
- `tests/` → all tests

No business logic in API routes.

---

## 🚫 What NOT to Do

- Do not add features without CI
- Do not mix concerns (API ↔ core ↔ infra)
- Do not introduce new dependencies casually
- Do not commit secrets
- Do not skip documentation

---

## ✅ Definition of Done

A change is considered **done** only if:

- Code compiles
- Tests pass
- CI is green
- Docs are updated (if applicable)

---

## 🙏 Final Note

This project prioritizes **long-term maintainability**.  
If you are unsure about a change, document it first.

Welcome, and build responsibly 🚀
