# Integration: [Name of External System/Service]

## 1. Overview
- **Purpose:** Why does this integration exist? What business or technical need does it fulfill?
- **External System:** [Name of the system we are integrating with]
    - Link to their documentation (if any):
    - Contact at their end (if applicable):

## 2. Integration Type & Pattern
- e.g., REST API (Client), REST API (Provider), Webhook, Message Queue, Batch File Transfer, Database Link, SDK.
- e.g., Request-Response, Publish-Subscribe, Event-Driven.

## 3. Data Flow
- **Direction:** Uni-directional (Our System -> External) / Uni-directional (External -> Our System) / Bi-directional.
- **Data Exchanged:** What key data entities or messages are exchanged?
    - e.g., "User profiles," "Order updates," "Payment confirmations."
- **Format:** JSON, XML, CSV, Protobuf, etc.
- **Frequency/Trigger:** Real-time, On-demand, Scheduled (e.g., hourly, daily).

## 4. Authentication & Authorization
- How does our system authenticate with the external system (and vice-versa if applicable)?
    - e.g., API Key, OAuth 2.0, Basic Auth, Mutual TLS.
- What permissions are required?

## 5. Error Handling & Resilience
- How are errors from the external system handled?
- Retry mechanisms?
- Fallback behavior if the integration fails?
- Alerting/Monitoring for failures?

## 6. Key Endpoints / Configuration (If applicable)
- **API Base URL:**
- **Key Endpoints used:** (e.g., `POST /v1/orders`, `GET /v1/users/{id}`)
- **Configuration Parameters:** (e.g., API keys, queue names - store actual secrets securely, not here)

## 7. Monitoring & Logging
- What key metrics are monitored for this integration? (e.g., success rate, latency, error count)
- Where are logs related to this integration stored?

## 8. Risks & Dependencies
- What are the risks associated with this integration? (e.g., external system downtime, API changes)
- Are there any specific versions of the external system we depend on?