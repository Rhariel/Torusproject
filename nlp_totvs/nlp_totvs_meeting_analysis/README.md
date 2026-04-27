# NLP TOTVS Meeting Analysis

Projeto em Python para analise de transcricoes de reunioes com FastAPI, SQLite e tecnicas de NLP. O sistema processa mensagens individuais e reunioes completas, identificando sentimento, entidades, intencoes e sinais de churn.

## Estrutura

```text
nlp_totvs_meeting_analysis/
│
├── main.py
├── nlp_pipeline.py
├── model.py
├── meeting_analysis.py
├── database.py
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10+
- pip atualizado

## Instalacao

```bash
pip install -r requirements.txt
python -m spacy download pt_core_news_sm
```

## Como rodar

No PyCharm, abra a pasta `nlp_totvs_meeting_analysis` como projeto e execute:

```bash
uvicorn main:app --reload
```

A API ficara disponivel em:

- `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

## Endpoints

### POST `/analyze`

Analisa uma mensagem unica.

Exemplo de entrada:

```json
{
  "speaker": "cliente",
  "text": "Estou achando caro e talvez eu cancele."
}
```

Exemplo de saida:

```json
{
  "speaker": "cliente",
  "original_text": "Estou achando caro e talvez eu cancele.",
  "processed_text": "estou achando caro e talvez eu cancele.",
  "intent": "churn_risk",
  "sentiment": {
    "label": "negative",
    "score": 0.15
  },
  "entities": [],
  "features": {
    "churn_signal": true,
    "price_signal": false,
    "upsell_signal": false,
    "satisfaction_signal": false,
    "token_count": 7
  }
}
```

### POST `/analyze_meeting`

Analisa uma reuniao completa.

Exemplo de entrada:

```json
{
  "meeting_id": 1,
  "conversation": [
    {"speaker": "vendedor", "text": "Bom dia, como posso ajudar?"},
    {"speaker": "cliente", "text": "Estou achando caro."},
    {"speaker": "cliente", "text": "Talvez eu cancele."},
    {"speaker": "vendedor", "text": "Posso montar uma proposta melhor e incluir outro modulo."}
  ]
}
```

Exemplo de saida:

```json
{
  "meeting_id": 1,
  "summary": {
    "average_customer_sentiment": 0.5,
    "churn_signals": 2,
    "upsell_opportunities": 1,
    "objections": [
      "Estou achando caro."
    ],
    "speech_ratio": {
      "cliente": 0.42,
      "vendedor": 0.58
    },
    "churn_risk_score": 55.0
  },
  "message_analysis": []
}
```

## Banco de dados

O arquivo SQLite `meeting_analysis.db` e criado automaticamente na inicializacao da API. A tabela `analyses` armazena:

- `text`
- `intent`
- `sentiment`
- `churn_signal`

## Observacoes

- O projeto usa `transformers` para sentimento e `spaCy` para entidades.
- Se o modelo de sentimento nao estiver disponivel localmente, o sistema usa fallback heuristico para continuar funcionando sem quebrar a API.
- O `spaCy` usa `pt_core_news_sm`; se ele nao estiver instalado, a extracao de entidades retorna lista vazia em vez de interromper a execucao.
