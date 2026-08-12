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
2. Execute um perfil desejado:
   ```bash
   python cli.py run data_engineering
   ```
