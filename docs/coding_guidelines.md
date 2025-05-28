# Techstack and Coding Guidelines

## Common Guidelines (for all services)

- Keep It Simple, Stupid (KISS): Prefer the simplest solution that works.
- You Ain't Gonna Need It (YAGNI): Don't over-engineer or add features that aren't currently required.

- Non-ascii characters are not allowed in source code (e.g. emoji, non-english characters, etc.)
- Hardcoded values in the code are not allowed, instead use:
  - YAML files: Non-sensitive values
  - Environment variables: Sensitive values
- Config must be consistent across all services.

## Go

- Web Framework: Gin
- ORM: Gorm
- Logging: Zap
- Configuration Management: Viper
- Redis Client: Go-redis
- Testing: Go-test

## Python

- Web Framework: Flask
- WSGI: Gunicorn
- ORM: SQLAlchemy
- Redis Client: redis-py
- Database Migration: Alembic
- Testing: PyTest
- Validation: Pydantic
- Configuration Management: OmegaConf
- Note: Do not use marshmallow (overlap with Pydantic)

- Use N-tier architecture for Flask (route -> service -> repository -> model)
- Global variables are not allowed.
- Use dependency injection instead of global variables (inject in constructor)
- All variables must be typed, using `Any` is not recommended but allowed.
- Merge environment variables to config by directly setting the fields.

## API Guidelines

- For HTTP API, every routes must be in the format of `/api/v1/...` unless otherwise specified like `/.well-known/jwks.json` (JWKS) or `/health` (health check)
- Success response must be in the format: `{ data: <data> }`
- Error response must be in the format: `{ error: { code: <error_name>, message: <error_message>, details (optional): [<detail_1>, <detail_2>, ...] } }`
- Error code and error message should be implemented with enum or constants, don't use string literals.

## Comment Guidelines

- Explain Why, Not What: Clarify intent for complex or non-obvious code
- Document Public APIs: Briefly describe purpose, params, and returns
- Keep Current: Update or remove comments when code changes
- Write Self-Documenting Code: Prefer clear code over excessive comments
- Use `TODO` to mark the code that needs to be improved or refactored

## Source Code Structure

- `src/auth-service/`: Auth service
- `src/user-service/`: User service
- `src/chat-service/`: Chat service
