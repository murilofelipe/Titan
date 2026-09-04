# 📋 Backlog — Titan / HAL

**Titan (HAL)** é um orquestrador agêntico: um "maestro" que não gasta tokens de
API — ele decide qual esteira de produção usar a partir do pedido, e para cada
etapa diz ao desenvolvedor qual agente acionar (Perplexity, Claude Code, Cursor,
Antigravity, Codex CLI) e injeta o contexto (rules/skills) certo. O
desenvolvedor continua sendo o decisor em cada gate.

Formato conforme `Github/.agents/rules/backlog_format.md` (Épico → Story com
Fibonacci + justificativa + subtarefas).

**Placar:** 4 épicos · 20 stories · 10 concluídas (✅) · 2 parciais (🟡) · 8 pendentes (⬜) · peso total 101.

| Épico | Stories | Concluídas | Peso |
|---|---|---|---|
| 1 · Orquestrador (Titan/HAL) | 4 | 4 ✅ | 24 |
| 2 · Perfis de Engenharia | 7 | 5 ✅ / 2 🟡 | 31 |
| 3 · Adapters de Agentes | 6 | 0 | 21 |
| 4 · Gates de Qualidade & HITL | 3 | 0 (1 🟡) | 18 |

Legenda: ✅ feito · 🟡 parcial · ⬜ pendente.

> Limite deste backlog: cobre o motor de orquestração e os perfis. Não cobre
> distribuição (empacotar como pip/brew), nem uma UI além da CLI.

---

## 🗂️ Épico 1 — Orquestrador (Titan / HAL)

O núcleo: classifica o trabalho, lê a esteira do `.yml`, executa passo a passo e
mantém o estado. Issues originais #1–#3 (fechadas).

### 🎫 Story 1.1: Classificador de trabalho de IA ✅
- **Descrição:** Identifica se o pedido inicial requer um pipeline de Engenharia
  de Dados, Backend, DevOps etc. e carrega o `.yml` correspondente.
  `core/classifier.py`: `PROFILE_KEYWORDS` cobre os 6 perfis; um gate de
  disponibilidade garante que nunca retorna um perfil sem `.yml` (keywords de
  perfis futuros ficam inertes até o arquivo existir). Score normalizado com
  `CONFIDENCE_THRESHOLD` de margem e fallback interativo (`click.prompt`) quando
  a confiança é baixa.
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** A base (scoring por keyword) já existe; o trabalho
  restante é ampliar o dicionário de termos por perfil e tratar ambiguidade sem
  virar um classificador ML. Risco baixo, escopo médio.
- **Tarefas:**
  - [x] Dicionário de keywords por perfil (`PROFILE_KEYWORDS`)
  - [x] Score normalizado + limiar de confiança (margem sobre o 2º colocado)
  - [x] Fallback: pergunta o perfil (`click.prompt`) quando a confiança é baixa
  - [x] Testes (perfil dormente cai no default, fallback interativo)

### 🎫 Story 1.2: Parser e Engine do Pipeline ✅
- **Descrição:** Lê os `.yml` de perfil (Pydantic), descobre qual agente executar
  em cada etapa e percorre os steps imprimindo Agente / Tarefa / Contexto /
  Saída esperada. Entregue em `core/parser.py` + `core/orchestrator.py` (issue
  #2, fechada).
- **Complexidade:** Média | **Peso:** 8
- **Justificativa do Peso:** Registro do que já foi feito. Envolveu modelagem
  Pydantic do schema de step, o loop de execução e a integração com estado.
- **Tarefas:**
  - [x] Modelos Pydantic do perfil e do step
  - [x] Loop de execução com pausa por `input()`
  - [x] Impressão formatada da etapa

### 🎫 Story 1.3: Gerenciador de Estado ✅
- **Descrição:** Mantém os artefatos e a posição do pipeline; suporta
  resume/reset/status. Entregue em `core/state.py` + `.titan_state/*.json`
  (issue #3, fechada).
- **Complexidade:** Média | **Peso:** 8
- **Justificativa do Peso:** Registro do que já foi feito. Persistência em JSON,
  máquina de estados de etapa (PENDING/RUNNING/COMPLETED) e retomada.
- **Tarefas:**
  - [x] `StateManager` com persistência JSON
  - [x] `run --resume` / `run --reset`
  - [x] `titan status`

### 🎫 Story 1.4: Telemetria de execução ✅
- **Descrição:** `StepState` grava `agent`, `duration_seconds` (de
  started_at/completed_at) e `advanced_by` (`auto`/`human`). `titan status`
  mostra agente/duração/liberação por etapa; `titan report <perfil>` exporta o
  resumo em Markdown (`.reports/telemetria-<perfil>.md` + stdout) via
  `core/telemetry.py`.
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Extensão do estado já existente com timestamps e um
  agregador de leitura. Sem lógica nova de orquestração.
- **Tarefas:**
  - [x] Campos de tempo/agente/liberação no modelo de etapa
  - [x] Agregador para `titan status`
  - [x] Export do resumo em Markdown (`titan report`)
  - Aprovação real (quem/quando) e contagem de ciclos de review ficam nas
    stories 4.1 (#11) e 4.2 (#12) — aqui só o fato `auto`/`human`.

---

## 🗂️ Épico 2 — Perfis de Engenharia

Esteiras pré-prontas que definem o padrão de trabalho para cada tipo de software.
Cada perfil: pipeline + agentes + `context_files` + critérios de aceite.

### 🎫 Story 2.1: Perfil "Engenharia de Dados" 🟡
- **Descrição:** Hoje `profiles/data_engineering.yml` tem 3 steps (Levantamento →
  Inferência/DDL → Modelagem dbt). Expandir para a esteira completa: Discovery →
  Data Contracts → Modelagem Conceitual/Física → Bronze/Silver/Gold → Qualidade
  → Observabilidade → Governança/LGPD → CI/CD → Entrega. (issue #4)
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Trabalho de curadoria (definir steps, agentes e
  `context_files` de cada fase) mais do que de código. Precisa de skills novas em
  `shared_context/` para as fases de qualidade/governança.
- **Tarefas:**
  - [ ] Redesenhar os steps do `.yml` conforme a esteira completa
  - [ ] Mapear agente por fase (Perplexity/Claude/Antigravity/Codex)
  - [ ] Skills em `shared_context/skills/` para qualidade e governança
  - [ ] `approval_required` nos gates de modelagem física e de entrega

### 🎫 Story 2.2: Perfil "Backend (Clean Arch)" 🟡
- **Descrição:** Hoje `profiles/backend_clean_arch.yml` tem 3 steps. Expandir
  para Pesquisa → DDD → Arquitetura → Implementação → Testes → Review → CI.
  (issue #5)
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Mesmo tipo de curadoria da Story 2.1; parte das
  rules já existe (`clean_architecture.md`, `python_clean_code.md`).
- **Tarefas:**
  - [ ] Redesenhar steps (7 fases)
  - [ ] Mapear agente por fase
  - [ ] Gate de aprovação após Arquitetura
  - [ ] Skill de DDD em `shared_context/`

### 🎫 Story 2.3: Injeção automática de contexto ✅
- **Descrição:** Ao selecionar um perfil, carregar os `context_files` de cada
  step e formatá-los no prompt sem o usuário pedir. Entregue em
  `core/context_loader.py` (issue #6).
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Registro do que já foi feito. Leitura de arquivos +
  formatação; a correção de `os.path.isabs` foi o único ajuste pós-entrega.
- **Tarefas:**
  - [x] Ler `context_files` por step
  - [x] Formatar bloco de contexto no output da etapa

### 🎫 Story 2.4: Perfil "Mobile / Android (Compose)" ✅
- **Descrição:** Esteira: Pesquisa → Arquitetura (MVVM/Clean) → UI Compose →
  Testes → Review. Agentes: Perplexity, Claude Code, Junie (quando JetBrains),
  Antigravity.
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Perfil novo do zero + skills de Compose/MVVM e
  offline-first em `shared_context/`.
- **Tarefas:**
  - [x] `profiles/mobile_android.yml` (5 steps, gates em Arquitetura e Review)
  - [x] Skill `compose_mvvm.md` (Compose + MVVM + offline-first num arquivo só)
  - [x] Keywords já no classificador (dormentes até este `.yml`)

### 🎫 Story 2.5: Perfil "Embarcados" ✅
- **Descrição:** Esteira: Pesquisa de datasheet → Driver → Firmware → Análise de
  consumo → Testes → Flash.
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Perfil novo; a fase de datasheet e a de consumo
  precisam de skills próprias e de um gate humano forte (hardware).
- **Tarefas:**
  - [x] `profiles/embedded.yml` (6 steps)
  - [x] Skill `datasheet_reading.md`
  - [x] Gate humano (`approval_required`) na Pesquisa de Datasheet e no Flash

### 🎫 Story 2.6: Perfil "IA / ML" ✅
- **Descrição:** Esteira: Pesquisa → Dataset → Treinamento → Avaliação → Deploy →
  Monitoramento.
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Perfil novo; fases de avaliação e monitoramento
  exigem critérios de aceite quantitativos nas skills.
- **Tarefas:**
  - [x] `profiles/ai_ml.yml` (6 steps, gate na Avaliação)
  - [x] Skill `ml_evaluation.md` (métricas + monitoring/drift num arquivo só)
  - [x] Keywords já no classificador

### 🎫 Story 2.7: Perfil "Game" ✅
- **Descrição:** Esteira: Pesquisa → Arquitetura → Implementação → Review.
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Perfil mais enxuto; reaproveita boa parte das skills
  de backend/arquitetura.
- **Tarefas:**
  - [x] `profiles/game.yml` (4 steps, reusa clean_architecture + code_review)
  - [x] Keywords já no classificador

---

## 🗂️ Épico 3 — Adapters de Agentes

Formalizar como cada papel de agente é referenciado nos steps. Hoje `agent:` é
uma string livre no `.yml`; os 6 perfis já usam os nomes canônicos previstos
para o registry ("Claude Code", "Antigravity", "Perplexity", "Codex CLI"), mas
sem validação.

### 🎫 Story 3.1: Registry de agentes + mapa dos 5 papéis ⬜
- **Descrição:** Um catálogo (`agents.yml` ou enum) com os papéis: Perplexity =
  pesquisa, Claude Code = arquitetura/implementação, Cursor = implementação
  diária, Antigravity = review, Codex CLI = CI/CD. O parser valida `agent:`
  contra o registry e o orchestrator imprime instruções específicas do agente.
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Toca parser (validação), schema de step e output do
  orchestrator; é a fundação das stories 3.2–3.6.
- **Tarefas:**
  - [ ] `shared_context/agents.yml` com papel, ponto forte, quando usar
  - [ ] Validação de `agent:` no parser
  - [ ] Mensagem de etapa por agente no orchestrator
  - [ ] Validar os 6 perfis existentes contra o registry (nomes já canônicos)

### 🎫 Story 3.2: Adapter Pesquisador (Perplexity) ⬜
- **Descrição:** Instruções e prompts para as etapas de descoberta, levantamento
  tecnológico e documentação; saída esperada padronizada em `docs/research.md`.
  (issue #7)
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Requer um template de prompt de pesquisa reutilizável
  e a convenção de artefato que as etapas seguintes consomem.
- **Tarefas:**
  - [ ] Template de prompt de pesquisa
  - [ ] Convenção `docs/research.md`
  - [ ] Usar nas fases de Discovery dos perfis

### 🎫 Story 3.3: Adapter Arquiteto (Claude Code) ⬜
- **Descrição:** Instruções para projetar arquitetura, diagramas e implementar o
  grosso do código. (issue #8)
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Já é o agente mais usado; o trabalho é formalizar o
  que já se faz na prática num bloco de instrução.
- **Tarefas:**
  - [ ] Bloco de instrução do papel Arquiteto
  - [ ] Convenção `docs/architecture.md`

### 🎫 Story 3.4: Adapter Revisor (Antigravity) ⬜
- **Descrição:** Checklist de review técnico: gargalo, acoplamento, risco,
  performance, custo. (issue #9)
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Reaproveita `shared_context/skills/code_review.md`;
  falta o checklist arquitetural e o formato de veredito (aprova/rejeita).
- **Tarefas:**
  - [ ] Checklist arquitetural
  - [ ] Formato de veredito consumível pela Story 4.2

### 🎫 Story 3.5: Adapter DevOps (Codex CLI) ⬜
- **Descrição:** Instruções para Docker, Terraform, GitHub Actions, Makefile,
  scripts bash. (issue #10)
- **Complexidade:** Baixa | **Peso:** 3
- **Justificativa do Peso:** Bloco de instrução + apontar para skills de infra;
  sem código no motor.
- **Tarefas:**
  - [ ] Bloco de instrução do papel DevOps
  - [ ] Skill de infra em `shared_context/`

### 🎫 Story 3.6: Adapter Cursor (implementação na IDE) ⬜
- **Descrição:** Papel de implementação incremental dentro da IDE (Controller →
  Service → Repository → DTO), complementar ao Claude Code.
- **Complexidade:** Baixa | **Peso:** 2
- **Justificativa do Peso:** Menor dos adapters; só um bloco de instrução e
  entrada no registry.
- **Tarefas:**
  - [ ] Bloco de instrução do papel Cursor
  - [ ] Entrada no registry (Story 3.1)

---

## 🗂️ Épico 4 — Gates de Qualidade e Human-in-the-Loop

Garantir que o pipeline não produza lixo autonomamente.

### 🎫 Story 4.1: Approval gates reais 🟡
- **Descrição:** O schema já tem `approval_required` por step. Falta o gate de
  fato: pausar, pedir OK explícito do humano, e registrar a aprovação (quem/
  quando) no estado antes de liberar a próxima etapa. (issue #11)
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Toca orchestrator (fluxo de pausa) e state (registro
  da aprovação); a flag já existe, então metade do caminho está feito.
- **Tarefas:**
  - [ ] Pausa dura quando `approval_required` e sem aprovação registrada
  - [ ] `titan approve <run> <step>` grava aprovação no estado
  - [ ] `titan status` mostra etapas travadas aguardando aprovação

### 🎫 Story 4.2: Self-healing / review loop ⬜
- **Descrição:** O Agente Revisor avalia o código gerado; se encontrar débito
  técnico (acoplamento/risco), rejeita e devolve para a etapa de implementação,
  até N ciclos. (issue #12)
- **Complexidade:** Alta | **Peso:** 8
- **Justificativa do Peso:** Introduz um ciclo (não-linear) na máquina de estados,
  contador de iterações, condição de parada e formato de veredito do revisor.
  É a mudança mais estrutural do épico.
- **Tarefas:**
  - [ ] Transição "review → implementação" no state manager
  - [ ] Contador de ciclos + teto configurável
  - [ ] Parser do veredito do revisor (aprova/rejeita + motivos)
  - [ ] Testes do loop (rejeita 2x, aprova na 3ª)

### 🎫 Story 4.3: Validadores de etapa automáticos ⬜
- **Descrição:** Antes de liberar a próxima etapa, checar se o `expected_output`
  da etapa atual existe (arquivo criado, testes passando, `dbt parse` ok).
- **Complexidade:** Média | **Peso:** 5
- **Justificativa do Peso:** Precisa de validadores plugáveis por tipo de saída
  (arquivo/comando/teste) e integração no loop do orchestrator.
- **Tarefas:**
  - [ ] Tipos de validador: arquivo existe, comando sai 0, glob não vazio
  - [ ] Campo `validation:` opcional no schema de step
  - [ ] Bloquear avanço se a validação falhar
