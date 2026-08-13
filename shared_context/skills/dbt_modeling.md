# Skill Directive: dbt Transformation Modeling

This document specifies standards and modeling patterns for dbt (data build tool) projects in data engineering pipelines.

## 1. Dimensional Layering Structure
- **Staging Models (`models/staging/`)**:
  - Naming pattern: `stg_<source>__<table_name>.sql`.
  - Responsibilities: 1-to-1 mapping with raw source tables, light column renaming, explicit data type casting, and basic cleanup.
- **Intermediate Models (`models/intermediate/`)**:
  - Naming pattern: `int_<entity>_<action>.sql`.
  - Responsibilities: Complex business logic, multi-table joins, CTE aggregations, and reusable logic built on staging models.
- **Marts Models (`models/marts/`)**:
  - **Fact Tables (`fct_<domain>_<action>.sql`)**: Quantitative measurements, event records, and metrics with foreign keys.
  - **Dimension Tables (`dim_<domain>_<entity>.sql`)**: Contextual descriptors, entities, and lookup attributes.

## 2. SQL Coding Standards & CTE Patterns
- **CTE Structure**:
  - Use modular Common Table Expressions (CTEs) at the start of every file: `import` CTEs, `logical` CTEs, and a final `select` statement.
  - Avoid nested subqueries in `WHERE` or `JOIN` clauses.
- **Ref & Source Macros**:
  - Always reference upstream dbt models using `{{ ref('stg_model_name') }}` and raw sources using `{{ source('source_name', 'table_name') }}` to preserve DAG dependency tracking.
- **Formatting**:
  - Use lower-case SQL keywords (`select`, `from`, `join`, `where`, `group by`). Align fields and comma placements cleanly.

## 3. Schema Documentation & Data Testing
- **Documentation (`schema.yml`)**:
  - Document all staging models, facts, and dimensions in corresponding `schema.yml` files, including model definitions and column descriptions.
- **Automated Tests**:
  - Apply `unique` and `not_null` tests to all primary key columns.
  - Use `relationships` tests for foreign key integrity in fact tables.
  - Add `accepted_values` tests for enumerated status or category columns.
