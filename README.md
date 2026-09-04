# Titan / HAL - Orquestrador Agêntico

O **Titan** é um orquestrador/diretor de pipeline focado em criar uma esteira de produção ágil usando **Agentes de IA locais** operados com contas pessoais (como Antigravity, Claude Code, Cursor, etc.). 

Diferente de sistemas que gastam tokens de APIs pagas automatizando tudo no backend, o Titan atua como um "maestro". Ele orienta o desenvolvedor sobre qual agente utilizar em cada etapa e organiza as instruções contextuais (skills, rules) de forma centralizada e padronizada.

## Estrutura do Projeto

- `core/`: O motor de leitura e execução dos pipelines.
- `cli.py`: A interface de linha de comando.
- `profiles/`: Diretório contendo os `.yml` que ditam o passo a passo de cada esteira (ex: Engenharia de Dados, Backend).
- `shared_context/`: Repositório central de conhecimento (rules, skills) que qualquer agente (Claude, Antigravity) pode consumir.

## Como Executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute um perfil desejado (por ID ou por um prompt de intenção):
   ```bash
   python cli.py run data_engineering
   python cli.py run "app android com jetpack compose"
   ```

## Comandos

| Comando | O que faz |
|---|---|
| `run <perfil\|prompt> [--auto] [--resume] [--reset]` | Executa o pipeline passo a passo |
| `list` | Lista os perfis disponíveis |
| `agents` | Lista o registry de agentes (papéis) |
| `status <perfil>` | Estado do pipeline: etapas, duração, gates travados |
| `approve <perfil> <n>` | Aprova um gate (`approval_required`) |
| `verdict <perfil> <n> aprova\|rejeita [--motivo ...]` | Veredito do revisor; `rejeita` devolve o pipeline para a implementação |
| `report <perfil> [-o arquivo.md]` | Relatório de telemetria em Markdown |
