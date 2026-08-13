# Directives: DDD & Clean Architecture Guidelines

This document outlines architectural principles, layer organization, and domain modeling directives for backend modules in Titan.

## 1. Core Architecture Layers
- **Domain Layer (Entities & Value Objects)**:
  - Contains enterprise business rules, entities, and value objects.
  - Must remain strictly independent of external frameworks, databases, or UI modules (pure Python).
- **Application Layer (Use Cases & Application Services)**:
  - Contains application business rules and orchestrates domain entities to execute business scenarios.
  - Defines repository interfaces (ports) and application DTOs.
- **Interface Adapters Layer (Controllers, Repositories, Presenters)**:
  - Adapts data between application entities and external delivery mechanisms (e.g., converting database rows or API JSON into domain entities).
- **Frameworks & Infrastructure Layer (DB, Frameworks, CLI)**:
  - Outer layer containing framework-specific code (FastAPI, Click, SQLALchemy, file storage adapters).

## 2. Domain-Driven Design (DDD) Principles
- **Bounded Contexts**:
  - Keep domain boundaries clear and explicitly isolated. Avoid tight cross-domain couplings.
- **Ubiquitous Language**:
  - Use domain terminology consistently across code symbols, documentation, test names, and specifications.
- **Entities vs. Value Objects**:
  - **Entities**: Objects possessing unique identity that persists across state changes.
  - **Value Objects**: Immutable objects defined solely by their attribute values.

## 3. Dependency Inversion & Interfaces
- **Dependency Rule**:
  - Code dependencies must point strictly inward toward higher-level policies (Domain). Outer layers depend on inner layers; inner layers never depend on outer layers.
- **Ports & Adapters (Interfaces)**:
  - Use Abstract Base Classes (`abc.ABC`) to define repository or gateway contracts in the application layer.
- **Dependency Injection**:
  - Inject concrete implementations into use cases or controllers at runtime rather than instantiating infrastructure dependencies directly inside core logic.
