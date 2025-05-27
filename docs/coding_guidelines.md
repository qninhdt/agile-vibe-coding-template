# Techstack and Coding Guidelines

This document outlines the primary technologies, frameworks, libraries, tools, and coding practices used in the **Notepot project**.

## 1. Programming Languages

- **Go:** Primary backend language for core services.
- **Python:** Secondary backend language, specifically for LLM-related services.
- **TypeScript:** Primary frontend language.
- **Shell Scripting (Bash/sh):** For automation, deployment, and utility scripts.

## 2. Backend Development

### 2.1. Go

- **Web Frameworks:**
  - **Gin:** For building complex APIs requiring rich features.
- **ORM:** **Gorm**
- **Logging:** **Zap**
- **Configuration Management:** **Viper**
- **Redis Client:** **Go-redis**

### 2.2. Python (LLM Services)

- **Web Framework:** **Flask**
- **ORM:** **SQLAlchemy**
- **Redis Client:** **redis-py**

### 2.3. API

- For HTTP API, every routes should be in the format of `/api/v1/...` unless otherwise specified like `/.well-known/jwks.json` (JWKS)

## 3. Frontend Development

- **Core Framework:** **Next.js** (utilizing **React** for UI components)
- **CSS Framework:** **Tailwind CSS**
- **UI Component Library:** **Shadcn UI**

## 4. Data Storage

- **Relational Database:** **CockroachDB**
- **NoSQL Database:** **ScyllaDB**
- **Key-Value Store/Cache:** **Redis**

## 5. Infrastructure & DevOps

- **Cloud Provider:** **AWS (Amazon Web Services)**
- **Containerization:** **Docker**
- **Orchestration:**
  - **Kubernetes (K8s):** For production environments.
  - **Docker Swarm:** For development and testing environments.
- **API Gateway:** **Kong**
- **CI/CD:** **GitHub Actions**

## 6. Development Tools & Practices

### 6.1. Version Control

- **Git** (hosted on GitHub)

### 6.2. Recommended IDEs

- **Visual Studio Code (VS Code)**
- **Cursor**

### 6.3. Code Formatting

- **Go:** `gofmt` (standard Go formatter)
- **Python:** **Black**
- **TypeScript:** **Prettier**

### 6.4. Linting

- **Go:** `golint` (or preferred linter like `golangci-lint`)
- **Python:** **Flake8**
- **TypeScript:** **ESLint**

### 6.5. Testing

- **Unit Testing:**
  - **Go:** Standard `testing` package (`go test`)
  - **Python:** **PyTest**
  - **TypeScript:** **Jest**
- **End-to-End (E2E) Testing:** **Playwright**
- **Testing Principle:** Each test case **must** use unique mock data or setup/teardown routines to ensure test isolation and prevent dependencies on the state left by previous tests. Avoid data duplication across tests where it can lead to ambiguity or shared state issues.

## 7. Coding Guidelines

- No hardcoded values in the code, use environment variables or configuration files.
