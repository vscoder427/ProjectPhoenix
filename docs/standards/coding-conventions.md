# Coding Conventions (Python/FastAPI)

This standard defines coding conventions for all Employa services.

## General Style

- Follow PEP 8 for naming, imports, whitespace, and layout.
- Use explicit names; avoid single-letter variables outside loops
- Prefer composition over inheritance
- Keep functions under 50 lines where possible
- Favor small modules with clear responsibility

## Project Layout

- `api/app/` contains application code
- `api/app/main.py` contains app initialization only
- Feature code lives in `api/app/routes/`, `api/app/services/`, `api/app/models/`

## FastAPI Patterns

- Use dependency injection for auth and shared resources
- Use Pydantic models for all request/response bodies
- Return `JSONResponse` for error handling consistency
- Use explicit response models on endpoints

## Error Handling

- Use standard error schema for all non-2xx responses
- Raise typed HTTPExceptions with clear error codes
- Do not leak internal errors to clients

## Configuration

- All config access goes through `app.config.settings`
- Validate required config at startup

## Logging

- Use structured logs only
- Include `request_id` on request logs
- Never log PHI/PII

## Testing Conventions

- Tests mirror package layout
- Use fixtures for shared setup
- Prefer explicit assertions

## API Versioning

- Endpoints live under `/api/v1/`
- New versions require new route modules

> Any non-Python implementation must document its own coding conventions and link to this template or a decision record explaining the deviation.
