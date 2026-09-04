# Skill Directive: Governança e LGPD

Para a fase de Governança de um pipeline de dados. Gate humano obrigatório —
dado pessoal exposto é incidente, não bug.

## 1. Classificação de dados
- Marque cada coluna: `publico`, `interno`, `pessoal`, `pessoal_sensivel`
  (origem racial, saúde, biometria, orientação sexual, etc. — art. 5º II LGPD).
- Registre a **base legal** de cada dado pessoal tratado (consentimento,
  execução de contrato, legítimo interesse, obrigação legal).

## 2. Minimização e mascaramento
- Camada de consumo (Gold) não expõe `pessoal_sensivel` sem necessidade provada.
- PII em Silver: hash com salt ou tokenização quando o caso de uso permite.
- CPF/e-mail em logs e amostras: sempre mascarado.

## 3. Retenção e direitos do titular
- Defina prazo de retenção por tabela; job de expurgo agendado.
- O modelo permite localizar e apagar todos os registros de um titular
  (direito de eliminação, art. 18 V).

## 4. Saída esperada
`docs/governanca.md`: tabela coluna → classificação → base legal → tratamento
(mascaramento/retenção). Aprovação humana registrada antes da entrega.
