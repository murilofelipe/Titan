[Português](README.md) · **English**

# Titan / HAL - Agentic Orchestrator

**Titan** is a pipeline orchestrator/director for building a lean production line with **local AI agents** run on personal accounts (Antigravity, Claude Code, Cursor, etc.).

Unlike systems that burn paid-API tokens automating everything in the backend, Titan acts as a "conductor". It tells the developer which agent to use at each step and keeps the contextual instructions (skills, rules) centralized and standardized.

## Project Structure

- `core/`: the engine that reads and runs pipelines (orchestrator, intent classifier, state, telemetry, validators).
- `cli.py`: the command-line interface.
- `profiles/`: `.yml` files defining each pipeline step by step (e.g. `data_engineering`, `backend_clean_arch`, `mobile_android`, `ai_ml`, `embedded`, `game`).
- `shared_context/`: central knowledge base (rules, skills) that any agent (Claude, Antigravity) can consume, plus the agent registry (`agents.yml`).
- `tests/`: tests (`pytest`).

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run a profile (by ID or by an intent prompt):
   ```bash
   python cli.py run data_engineering
   python cli.py run "android app with jetpack compose"
   ```

## Commands

| Command | What it does |
|---|---|
| `run <profile\|prompt> [--auto] [--resume] [--reset]` | Runs the pipeline step by step |
| `list` | Lists available profiles |
| `agents` | Lists the agent (role) registry |
| `status <profile>` | Pipeline state: steps, duration, blocked gates |
| `approve <profile> <n>` | Approves a gate (`approval_required`) |
| `verdict <profile> <n> aprova\|rejeita [--motivo ...]` | Reviewer verdict; `rejeita` sends the pipeline back to implementation |
| `report <profile> [-o file.md]` | Markdown telemetry report |
