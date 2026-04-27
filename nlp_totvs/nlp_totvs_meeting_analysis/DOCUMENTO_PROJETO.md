# Documento do Projeto

## O que e

O projeto atual e uma aplicacao em Python para analise de reunioes comerciais a partir de transcricoes em texto. Ele recebe falas de uma conversa entre cliente e vendedor, processa cada mensagem com tecnicas de NLP e devolve uma leitura estruturada da reuniao.

Na pratica, o sistema transforma uma conversa bruta em informacoes acionaveis, como:

- intencao da fala
- sentimento
- entidades identificadas
- sinais de churn
- objecoes
- oportunidades de upsell
- score consolidado de risco da reuniao

O projeto possui:

- uma API FastAPI para analise automatica
- um dashboard web para envio de arquivos JSON
- persistencia em SQLite para registrar resultados de analise

## Para quem e e qual problema resolve

O projeto faz sentido para times que dependem de reunioes para manter clientes, vender mais e antecipar riscos. Os principais perfis beneficiados sao:

- times de Customer Success
- times comerciais e de pre-venda
- liderancas de operacao comercial
- gestores de carteira e retencao

O problema que ele resolve e simples: hoje, boa parte do valor de uma reuniao fica escondido dentro de uma transcricao longa, subjetiva e dificil de revisar em escala. Ler tudo manualmente consome tempo e torna a identificacao de risco lenta e inconsistente.

Com isso, o projeto ajuda a responder perguntas como:

- o cliente demonstrou risco de cancelamento?
- houve objecao de preco?
- apareceu espaco para expansao de conta?
- o sentimento medio do cliente foi positivo, neutro ou negativo?
- quem falou mais na reuniao, cliente ou vendedor?

## Como funciona

O fluxo atual do sistema segue estas etapas:

1. A reuniao e enviada em JSON com `meeting_id` e `conversation`.
2. Cada fala e processada individualmente.
3. O texto passa por preprocessamento, classificacao de intencao, analise de sentimento e extracao de entidades.
4. O sistema gera features de negocio, como `churn_signal`, `price_signal`, `upsell_signal` e `satisfaction_signal`.
5. Ao final, a aplicacao consolida a reuniao em um resumo executivo.

Hoje, a classificacao de intencao e feita por regras e palavras-chave. As categorias implementadas sao:

- `churn_risk`
- `price_objection`
- `upsell_opportunity`
- `satisfaction`
- `neutral`

A analise de sentimento usa um modelo de `transformers` quando disponivel. Se o modelo nao estiver carregado, o sistema usa um fallback heuristico para nao interromper a operacao. A extracao de entidades usa `spaCy`, tambem com fallback seguro.

Ao final da reuniao, o sistema calcula indicadores consolidados como:

- sentimento medio do cliente
- quantidade de sinais de churn
- quantidade de oportunidades de upsell
- lista de objecoes
- proporcao de fala entre cliente e vendedor
- `churn_risk_score` de 0 a 100

Esse score de risco e calculado combinando:

- sinais de churn
- objecoes de preco
- piora no sentimento medio do cliente
- reducao por sinais de upsell

## Por que isso e diferente de uma transcricao

Uma transcricao apenas registra o que foi dito. Este projeto interpreta o que foi dito.

Essa diferenca e central. Em vez de entregar um bloco de texto para leitura humana, o sistema entrega uma camada analitica sobre a conversa. Isso significa sair de um material passivo para um resultado operacional.

Em termos praticos:

- transcricao mostra frases
- analise mostra significado
- transcricao exige leitura manual
- analise destaca risco, objecao e oportunidade
- transcricao nao prioriza acao
- analise ajuda a decidir proximo passo

Exemplo:

- transcricao: "Estamos usando bem, mas estou achando o valor um pouco caro."
- analise: satisfacao parcial, objecao de preco e aumento de risco comercial

Portanto, o valor do projeto nao esta em registrar a reuniao, mas em traduzir a reuniao em sinais de negocio.

## Tipos de risco detectados

Pelo que esta implementado hoje, o projeto detecta principalmente riscos comerciais e de relacionamento.

### 1. Risco de churn

O sistema identifica termos ligados a cancelamento, saida ou encerramento da relacao, como:

- cancelar
- encerrar
- trocar de fornecedor
- nao vou continuar

Esse e o principal tipo de risco tratado pelo projeto e impacta diretamente o `churn_risk_score`.

### 2. Objecao de preco

Quando o cliente menciona percepcao de custo alto, desconto ou limite de orcamento, a reuniao recebe sinal de objecao comercial.

Exemplos:

- caro
- preco
- valor alto
- fora do orcamento

Esse tipo de risco indica vulnerabilidade da conta, mesmo quando o cliente ainda nao verbalizou cancelamento.

### 3. Deterioracao de sentimento

Mesmo sem uma palavra explicita de cancelamento, o sistema considera sentimento negativo como um sinal relevante. Isso permite capturar desgaste antes que ele vire uma declaracao direta de churn.

### 4. Baixo equilibrio da conversa

O sistema calcula a proporcao de fala entre cliente e vendedor. Isso nao e classificado isoladamente como um alerta automatico, mas e um indicador importante de qualidade da reuniao. Quando o vendedor domina demais a conversa, pode haver menos descoberta real do contexto do cliente.

### 5. Risco de perda de oportunidade

Quando nao ha escuta adequada ou quando sinais de expansao aparecem sem tratamento, a reuniao pode indicar risco indireto de perda comercial. O sistema nao chama isso de risco explicitamente no modelo, mas ja identifica oportunidades de upsell para apoiar essa leitura.

## O valor da comparacao entre reunioes

Comparar reunioes e o passo que transforma analise pontual em inteligencia de acompanhamento.

Uma reuniao isolada mostra um retrato. A comparacao entre reunioes mostra tendencia.

Esse valor aparece em varios cenarios:

- verificar se o risco aumentou ou diminuiu ao longo do tempo
- observar se a objecao de preco foi resolvida ou repetida
- medir evolucao do sentimento do cliente
- perceber se a participacao do cliente cresceu ou caiu
- identificar se uma conta saiu de reclamacao para expansao

Para operacoes de CS e vendas, isso permite:

- acompanhar contas de forma menos subjetiva
- priorizar follow-ups com base em evidencias
- identificar padroes recorrentes em clientes com maior risco
- avaliar qualidade de conducao de reunioes

No estado atual do projeto, ja existe uma base para esse caminho porque os resultados sao armazenados em SQLite. Porem, e importante separar expectativa de implementacao real:

- o sistema ja analisa reunioes individualmente
- o sistema ja persiste dados de analise
- o sistema ainda nao oferece um modulo explicito de comparacao historica entre reunioes

Ou seja, o valor da comparacao entre reunioes esta claramente alinhado ao projeto, mas hoje ele aparece mais como proximo passo evolutivo do que como funcionalidade completa exposta na API.

## Conclusao

O projeto atual e uma camada de inteligencia aplicada a reunioes. Ele nao substitui apenas o trabalho de transcrever, mas organiza a conversa em sinais de negocio que ajudam a tomar decisao.

Seu diferencial esta em transformar texto em leitura operacional: risco de churn, objecoes, sentimento, equilibrio da conversa e oportunidades de expansao.

Para uma evolucao futura, o caminho mais valioso seria ampliar o uso do historico salvo no banco para comparar reunioes de uma mesma conta e gerar visao de tendencia, o que aumentaria bastante o valor analitico da solucao.
