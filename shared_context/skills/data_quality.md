# Skill Directive: Qualidade de Dados

Critérios para a fase de Qualidade de um pipeline de dados. Ponto de partida:
o revisor amplia conforme o domínio.

## 1. Testes obrigatórios (dbt ou equivalente)
- `not_null` e `unique` em toda chave primária.
- `relationships` (FK) em todo `fct_*` que referencia `dim_*`.
- `accepted_values` em colunas de status/categoria enumerada.
- Teste de contagem: linha do Silver não pode ser menor que o Bronze sem regra explícita.

## 2. Expectativas de conteúdo
- Faixa numérica plausível (ex.: idade 0–130, valor ≥ 0).
- Formato de data/CPF/e-mail validado onde a coluna alimenta decisão.
- Cardinalidade esperada por partição (alerta se cair > 30% vs. média móvel).

## 3. Gate
- A fase de Qualidade **falha o pipeline** se qualquer teste de PK/FK quebrar.
- Testes de expectativa que quebram viram aviso + item no relatório, não bloqueio,
  salvo se o contrato de dados marcar a coluna como crítica.

## 4. Saída esperada
`docs/data_quality.md`: lista de testes, o que cada um cobre, e os que ficaram
como aviso com justificativa.
