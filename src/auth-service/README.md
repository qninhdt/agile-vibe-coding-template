# Auth Service

A complete JWT-based authentication service built with Flask, featuring user registration, login, token management, and rate limiting.

## Features

- **User Registration**: Email/username and password registration with validation
- **User Login**: Authenticate with email or username and password
- **JWT Authentication**: RS256 JWT tokens with access and refresh token support
- **Rate Limiting**: Redis-based rate limiting for login attempts
- **Security**: Password hashing with bcrypt, timing attack prevention
- **JWKS**: Public key distribution for JWT signature verification
- **Session Management**: Multi-device session support with token rotation

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

## Configuration

The service uses YAML configuration files and environment variables:

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_PRIVATE_KEY`: RSA private key (PEM format, base64 encoded)
- `JWT_PUBLIC_KEY`: RSA public key (PEM format, base64 encoded)
- `JWT_KEY_ID`: JWT key identifier
- `JWT_ISSUER`: JWT issuer claim
- `BCRYPT_ROUNDS`: Password hashing rounds (default: 12)
- `DEBUG`: Enable debug mode

### Configuration File

See `app/config.yaml` for detailed configuration options.

## Installation

### Local Development

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up database:

```bash
# Create database
createdb notepot

# Run migrations
alembic upgrade head
```

3. Set environment variables:

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/notepot"
export REDIS_URL="redis://localhost:6379/0"
export DEBUG=True
```

4. Run the application:

```bash
python -m app.main
```

### Docker

```bash
docker-compose up --build
```

## Testing

The service includes comprehensive unit tests covering all authentication functionality.

### Running All Tests

```bash
# Run all tests with coverage
python run_tests.py

# Or use pytest directly
pytest tests/ -v --cov=app
```

### Running Specific Test Files

```bash
# Run authentication service tests
python run_tests.py test_auth_service

# Run JWT manager tests
python run_tests.py test_jwt_manager

# Run route tests
python run_tests.py test_auth_routes

# Run schema validation tests
python run_tests.py test_schemas

# Run password manager tests
python run_tests.py test_password_manager

# Run integration tests
python run_tests.py test_integration
```

### Test Coverage

The test suite includes:

- **Unit Tests**: Individual component testing

  - `test_auth_service.py`: AuthService business logic
  - `test_jwt_manager.py`: JWT token generation and validation
  - `test_password_manager.py`: Password hashing and verification
  - `test_schemas.py`: Pydantic schema validation
  - `test_auth_routes.py`: Flask route handlers

- **Integration Tests**: End-to-end testing
  - `test_integration.py`: Complete authentication flows

### Test Features Covered

- ✅ **User Registration**

  - Valid registration with all required fields
  - Email format validation
  - Username validation (length, characters, reserved words)
  - Password complexity requirements
  - Duplicate user prevention

- ✅ **User Login**

  - Login with email or username
  - Password verification
  - Invalid credentials handling
  - Account status validation
  - Rate limiting integration

- ✅ **JWT Token Management**

  - Access token generation and validation
  - Refresh token generation and validation
  - Token expiration handling
  - Token type validation
  - RSA key generation and management

- ✅ **JWKS (JSON Web Key Set)**

  - Public key distribution
  - Proper key format validation
  - Base64url encoding verification

- ✅ **Security Features**

  - Password hashing with bcrypt
  - Timing attack prevention
  - Token hash generation for storage
  - Case-insensitive email handling

- ✅ **API Routes**

  - All authentication endpoints
  - Error handling and response formats
  - Input validation
  - HTTP status codes

- ✅ **Integration Flows**
  - Complete registration → login → refresh → logout flow
  - Multi-device session management
  - Token rotation on refresh
  - Cross-service JWT validation

### Running Tests in CI/CD

The tests are designed to work in CI/CD environments:

```bash
# Set test environment variables
export TESTING=true
export DATABASE_URL=sqlite:///:memory:
export REDIS_URL=redis://localhost:6379/1

# Run tests with junit output for CI
pytest tests/ --junitxml=test-results.xml --cov=app --cov-report=xml
```

## API Endpoints

### Authentication

#### POST `/api/v1/auth/register`

Register a new user.

**Request:**

```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Response (201):**

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "john_doe",
      "created_at": "2024-01-15T10:30:00Z",
      "email_verified": false
    }
  }
}
```

#### POST `/api/v1/auth/login`

Authenticate user and return tokens.

**Request:**

```json
{
  "identifier": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**

```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "username": "john_doe",
      "email_verified": false
    },
    "tokens": {
      "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 900
    }
  }
}
```

#### POST `/api/v1/auth/refresh`

Refresh access and refresh tokens.

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

#### POST `/api/v1/auth/logout`

Logout user by revoking refresh token.

**Request:**

```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**

```json
{
  "data": null
}
```

### JWKS

#### GET `/.well-known/jwks.json`

Get JSON Web Key Set for JWT signature verification.

**Response (200):**

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "auth-service-key-1",
      "alg": "RS256",
      "n": "base64url-encoded-modulus",
      "e": "AQAB"
    }
  ]
}
```

### Health Check

#### GET `/health`

Health check endpoint.

**Response (200):**

```json
{
  "status": "healthy"
}
```

## Error Handling

All endpoints return consistent error formats:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Specific field error"
    }
  }
}
```

Common error codes:

- `VALIDATION_FAILED`: Input validation errors
- `USER_ALREADY_EXISTS`: Duplicate registration attempt
- `INVALID_CREDENTIALS`: Wrong email/username or password
- `ACCOUNT_INACTIVE`: User account is deactivated
- `INVALID_REFRESH_TOKEN`: Refresh token is invalid or expired
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Security Considerations

- Passwords are hashed using bcrypt with configurable rounds
- JWT tokens use RS256 algorithm with RSA key pairs
- Refresh tokens are stored as hashes in the database
- Rate limiting prevents brute force attacks
- Timing attack prevention in authentication flows
- Session management with configurable limits
- CORS support for cross-origin requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[License information here]
