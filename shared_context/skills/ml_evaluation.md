# Skill Directive: Avaliação e Monitoramento de Modelos (IA / ML)

Critérios de aceite quantitativos para as fases de Avaliação e Monitoramento.

## 1. Avaliação (gate antes do deploy)
- **Split honesto**: train/val/test separados por tempo ou por entidade — nunca aleatório quando há vazamento temporal.
- **Métrica primária declarada antes do treino**, com baseline (modelo trivial / regra de negócio atual).
- **Classificação**: reportar precision/recall/F1 por classe + matriz de confusão; AUC só como secundária.
- **Regressão**: MAE e RMSE + erro relativo; comparar contra baseline de média/último valor.
- **Corte por segmento**: a métrica não pode cair abaixo do baseline em nenhum segmento crítico (ex.: região, faixa de valor).
- **Aprovação humana obrigatória** antes de promover o modelo.

## 2. Monitoramento (pós-deploy)
- **Data drift**: PSI ou KS nas features de entrada vs. janela de treino; alerta em PSI > 0.2.
- **Prediction drift**: distribuição das predições ao longo do tempo.
- **Métrica online**: quando o label chega com atraso, medir a métrica primária em janela móvel e comparar com a de avaliação.
- **Fallback**: regra de negócio ou modelo anterior acionável se a métrica online degradar além do limiar.
