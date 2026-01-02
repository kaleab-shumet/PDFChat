# Claude Development Guidelines

## Python/FastAPI Development Rules

### 1. Use Async/Await for I/O Operations
- **ALL** database operations must use async (AsyncSession, async ORM methods)
- **ALL** HTTP client calls should be async
- **ALL** file I/O should be async when possible
- **ALL** middleware functions should be async
- **ALL** API endpoint functions should be `async def`
- **SYNC OK**: Pure computational functions (password hashing, data validation, etc.)

### 2. Database Operations
- Use `AsyncSession` for all database connections
- Use `await session.execute()` for queries
- Use `await session.commit()` for transactions
- Use `await session.refresh()` for object reloading
- **SECURITY**: Always use UUIDs for primary keys, never sequential integers
- **SECURITY**: UUIDs prevent enumeration attacks and business intelligence leaks

### 3. API Endpoints
- All endpoint functions should be `async def`
- Use `Depends(get_db)` for async database dependency injection
- Use proper error handling with async context

### 4. Middleware
- Use `@app.middleware("http")` with `async def` functions
- Properly await `call_next(request)`
- Handle exceptions asynchronously

### 5. Testing
- Use `pytest-asyncio` for async test functions
- Mark async tests with `@pytest.mark.asyncio`
- Use async test clients (`AsyncClient` from httpx)

## Reasoning
- FastAPI is built for async - using sync operations blocks the event loop
- Async provides better performance and scalability
- Consistency prevents bugs and confusion
- Modern Python best practices favor async for I/O operations

## Commands
- Lint: `ruff check`
- Format: `ruff format`
- Test: `pytest`
- Run: `uvicorn main:app --reload`