# Pipeline de análise de reuniões

## Fluxo de processamento

A entrada é um objeto JSON com a identificação da reunião e uma lista de falas. Cada fala informa o participante e o texto. O processamento segue uma sequência única:

1. normaliza espaços e caixa;
2. cria as mesmas características usadas no treinamento;
3. classifica a intenção e registra a confiança de cada classe;
4. identifica sentimento e nomes de produtos TOTVS;
5. consolida as falas em indicadores da reunião;
6. sugere uma próxima ação de acordo com os sinais encontrados.

`app/text_processing.py` cuida da análise de cada fala. `app/meeting_analysis.py` consolida os resultados da reunião.

## Classificador selecionado

Regressão Logística e Multinomial Naive Bayes foram comparados no mesmo conjunto de teste.

| Modelo | Acurácia | Precisão macro | Recall macro | F1 macro |
|---|---:|---:|---:|---:|
| Regressão Logística | 0,4800 | 0,5022 | 0,4800 | 0,4720 |
| Multinomial Naive Bayes | 0,4000 | 0,4429 | 0,4000 | 0,3965 |

A Regressão Logística foi selecionada pelo maior recall macro. Esse critério atribui o mesmo peso às cinco classes e reduz o risco de uma classe mais frequente esconder falhas em sinais de churn ou oportunidade. A API carrega `models/intent_classifier.json` uma vez e reutiliza o modelo nas próximas requisições.

## Informações produzidas

A resposta da análise inclui:

- risco de churn, de 0 a 100;
- oportunidade comercial, de 0 a 100;
- sentimento médio do cliente, de 0 a 100;
- sinais de churn, expansão e objeção de preço;
- participação do cliente e do vendedor na conversa;
- produtos TOTVS e termos mais frequentes;
- intenção, confiança e probabilidades de cada fala;
- recomendação de próxima ação.

O risco de churn combina confiança das falas classificadas como churn, objeções de preço e sentimento negativo. A oportunidade combina confiança de upsell e produtos citados. Os pesos são regras de negócio explícitas em `app/meeting_analysis.py`; não são parâmetros aprendidos pelo classificador.

## Recomendações comerciais

- risco a partir de 70: abrir plano de retenção e fazer contato executivo em até 24 horas;
- risco a partir de 40 com objeção: rever proposta de valor e condições;
- oportunidade a partir de 45: preparar proposta de expansão;
- risco a partir de 30: fazer acompanhamento sobre a insatisfação;
- demais casos: registrar próximos passos e manter o acompanhamento normal.

## Limitações

O conjunto de treinamento contém 100 frases sintéticas e não representa toda a variedade de segmentos, regiões e estilos de conversa. A avaliação atual caracteriza um baseline. Antes de uso real, o projeto precisa de transcrições anonimizadas e revisadas, avaliação separada por cliente e período, calibração das probabilidades e acompanhamento de falsos negativos de churn.
