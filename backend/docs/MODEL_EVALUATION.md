# Avaliação do classificador de intenções comerciais

## Problema e variável-alvo

O experimento classifica cada fala da reunião em uma de cinco classes: `churn_risk`, `price_objection`, `upsell_opportunity`, `satisfaction` ou `neutral`. A coluna `label` é a variável-alvo.

## Distribuição das classes

| Classe | Exemplos |
|---|---:|
| churn_risk | 20 |
| neutral | 20 |
| price_objection | 20 |
| satisfaction | 20 |
| upsell_opportunity | 20 |

O conjunto tem 100 frases sintéticas, com 20 exemplos por classe. A divisão estratificada reservou 75 frases para treino e 25 para teste. A semente 42 torna essa divisão reproduzível.

## Construção dos modelos

Foram treinados uma Regressão Logística multiclasse e um Multinomial Naive Bayes. Ambos usam as mesmas palavras, bigramas e n-gramas de caracteres.

## Comparação

| Modelo | Acurácia | Precisão macro | Recall macro | F1 macro |
|---|---:|---:|---:|---:|
| Regressão Logística | 0.4800 | 0.5022 | 0.4800 | 0.4720 |
| Multinomial Naive Bayes | 0.4000 | 0.4429 | 0.4000 | 0.3965 |

### Matriz de confusão — `logistic_regression`

As linhas mostram a classe real; as colunas, a previsão.

| Real \ Prevista | churn_risk | neutral | price_objection | satisfaction | upsell_opportunity |
|---|---:|---:|---:|---:|---:|
| churn_risk | 2 | 1 | 0 | 1 | 1 |
| neutral | 0 | 4 | 0 | 0 | 1 |
| price_objection | 1 | 2 | 2 | 0 | 0 |
| satisfaction | 0 | 2 | 0 | 2 | 1 |
| upsell_opportunity | 0 | 0 | 2 | 1 | 2 |

#### Onde o modelo errou

- “O investimento não compensa para uma equipe pequena.” — esperava `price_objection`; previu `neutral`.
- “A nova unidade também precisa usar a plataforma.” — esperava `upsell_opportunity`; previu `price_objection`.
- “Tivemos muitos problemas e vamos sair.” — esperava `churn_risk`; previu `neutral`.
- “Não temos verba para contratar agora.” — esperava `price_objection`; previu `neutral`.
- “Quais opções existem para expandir nossa conta?” — esperava `upsell_opportunity`; previu `price_objection`.
- “A equipe está bem satisfeita com o Fluig.” — esperava `satisfaction`; previu `neutral`.
- “Precisamos negociar o reajuste do contrato.” — esperava `price_objection`; previu `churn_risk`.
- “Estamos interessados em aumentar o escopo do contrato.” — esperava `upsell_opportunity`; previu `satisfaction`.
- “Essa experiência foi péssima e não quero mais usar.” — esperava `churn_risk`; previu `satisfaction`.
- “Gostei muito da nova funcionalidade.” — esperava `satisfaction`; previu `upsell_opportunity`.
- “Nossa operação possui três filiais.” — esperava `neutral`; previu `upsell_opportunity`.
- “O diretor pediu para migrarmos para outro sistema.” — esperava `churn_risk`; previu `upsell_opportunity`.
- “Tudo está rodando bem depois da atualização.” — esperava `satisfaction`; previu `neutral`.

### Matriz de confusão — `multinomial_naive_bayes`

As linhas mostram a classe real; as colunas, a previsão.

| Real \ Prevista | churn_risk | neutral | price_objection | satisfaction | upsell_opportunity |
|---|---:|---:|---:|---:|---:|
| churn_risk | 2 | 0 | 1 | 1 | 1 |
| neutral | 1 | 1 | 2 | 0 | 1 |
| price_objection | 2 | 0 | 2 | 0 | 1 |
| satisfaction | 1 | 1 | 0 | 2 | 1 |
| upsell_opportunity | 1 | 0 | 1 | 0 | 3 |

#### Onde o modelo errou

- “Podem cancelar todas as licenças da conta.” — esperava `churn_risk`; previu `price_objection`.
- “A empresa cresceu e precisamos ampliar as licenças.” — esperava `upsell_opportunity`; previu `price_objection`.
- “A próxima reunião ficou marcada para segunda.” — esperava `neutral`; previu `price_objection`.
- “O investimento não compensa para uma equipe pequena.” — esperava `price_objection`; previu `upsell_opportunity`.
- “Não temos verba para contratar agora.” — esperava `price_objection`; previu `churn_risk`.
- “Precisamos negociar o reajuste do contrato.” — esperava `price_objection`; previu `churn_risk`.
- “Podemos agendar uma demonstração para amanhã?” — esperava `neutral`; previu `upsell_opportunity`.
- “Estamos interessados em aumentar o escopo do contrato.” — esperava `upsell_opportunity`; previu `churn_risk`.
- “Essa experiência foi péssima e não quero mais usar.” — esperava `churn_risk`; previu `satisfaction`.
- “Valeu a pena investir nessa melhoria.” — esperava `satisfaction`; previu `churn_risk`.
- “A versão atual foi instalada no mês passado.” — esperava `neutral`; previu `churn_risk`.
- “Gostei muito da nova funcionalidade.” — esperava `satisfaction`; previu `upsell_opportunity`.
- “Nossa operação possui três filiais.” — esperava `neutral`; previu `price_objection`.
- “O diretor pediu para migrarmos para outro sistema.” — esperava `churn_risk`; previu `upsell_opportunity`.
- “Tudo está rodando bem depois da atualização.” — esperava `satisfaction`; previu `neutral`.

## Escolha do modelo

A Regressão Logística ficou com recall macro de 48,00% e foi melhor que o Naive Bayes nesse critério. O recall macro tem prioridade porque dá o mesmo peso às cinco classes; assim, uma classe frequente não esconde falhas em churn ou oportunidade.

## Análise dos erros

A maior dificuldade está nas frases curtas e indiretas. Termos como “investimento”, “filiais” e “contrato” aparecem em contextos diferentes e geram confusão entre objeção, expansão e fala neutra.

## Conclusões e implicações para o negócio

Com 48% de acurácia no teste, este modelo é uma referência inicial, não um classificador pronto para produção. O próximo passo é rotular mais reuniões reais, sem dados pessoais, e medir o resultado por cliente e por período. Casos de churn devem continuar sujeitos à revisão humana.
