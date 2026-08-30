# Validação do pipeline de reuniões

O teste usa 3 reuniões que não fizeram parte do treinamento. O modelo acertou 7 das 9 falas (77,78%).

| Reunião | Cenário | Esperado | Previsto | Acertos | Risco | Oportunidade |
|---:|---|---|---|---:|---:|---:|
| 201 | retenção | neutral, churn_risk, price_objection | churn_risk, churn_risk, price_objection | 2/3 | 72.0 | 8 |
| 202 | expansão | neutral, upsell_opportunity, satisfaction | churn_risk, upsell_opportunity, satisfaction | 2/3 | 0.0 | 53.0 |
| 203 | acompanhamento | neutral, neutral, satisfaction | neutral, neutral, satisfaction | 3/3 | 0.0 | 8 |

## O que os três casos mostram

- Na reunião de retenção, o score de churn ultrapassa o limite de 70 e aciona contato executivo.
- Na expansão, o modelo encontra a oportunidade e a menção ao Fluig.
- No acompanhamento, o risco permanece baixo.

A amostra tem somente nove falas. A taxa acima descreve estes casos; ela não estima o desempenho em produção.
