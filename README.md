# Torus Meeting Intelligence

O Torus recebe a transcrição de uma reunião em JSON e classifica cada fala como risco de cancelamento, objeção de preço, oportunidade de expansão, satisfação ou conversa neutra. Em seguida, consolida risco, oportunidade, sentimento, produtos TOTVS citados e a ação comercial recomendada para a conta.

O acesso é separado por perfil: vendedores consultam somente as próprias reuniões, enquanto gerentes visualizam a equipe inteira e podem atribuir novas análises a um vendedor.

## Recursos principais

- login com sessão temporária e senhas protegidas por PBKDF2;
- painéis distintos para vendedores e gerentes;
- envio de reunião por formulário ou arquivo JSON;
- classificação de intenção em cinco categorias comerciais;
- indicadores de churn, oportunidade, sentimento e participação na conversa;
- histórico persistido em SQLite;
- comparação reproduzível entre Regressão Logística e Naive Bayes;
- validação automatizada da API, das permissões e do pipeline analítico.

O projeto não envia transcrições para serviços externos e não depende de LLM. O classificador executado localmente é uma Regressão Logística treinada com a base disponível em `backend/data`.

## Organização

```text
Torusproject/
├── index.html                  # interface web
├── README.md                   # visão geral e execução
└── backend/
    ├── app/                    # API, autenticação e análise
    ├── data/                   # treino e validação
    ├── docs/                   # metodologia e resultados
    ├── examples/               # reunião de exemplo
    ├── models/                 # modelo e métricas versionadas
    ├── runtime/                # banco local, ignorado pelo Git
    ├── tests/                  # testes automatizados
    └── pyproject.toml          # dependências e ferramentas
```

## Como abrir no Windows

Dê dois cliques em `INICIAR_TORUS.cmd`. O inicializador mantém a API ativa em segundo plano e abre `http://127.0.0.1:8000` no navegador. Para encerrar, use `ENCERRAR_TORUS.cmd`.

Na primeira execução, o uv pode levar alguns segundos para preparar as dependências.

## Execução pelo terminal

No PowerShell, a partir da pasta do projeto:

```powershell
cd backend
uv sync --extra dev
uv run python -m uvicorn app.api:app --reload --port 8000
```

Abra `http://127.0.0.1:8000`. A documentação interativa da API fica em `http://127.0.0.1:8000/docs`.

### Acessos de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Gerente | `manager@torus.ai` | `Torus@2026` |
| Vendedora | `ana@torus.ai` | `Vendas@2026` |
| Vendedor | `carlos@torus.ai` | `Vendas@2026` |

Essas contas existem somente para demonstração. Em uma implantação real, substitua-as por usuários cadastrados e use HTTPS.

## Modelo e validação

Os artefatos prontos estão em `backend/models`. Para reproduzir o treinamento e a validação:

```powershell
uv run python -m app.model_training
uv run python -m app.model_validation
```

O treinamento usa divisão estratificada e semente fixa. Os relatórios resultantes ficam em `backend/docs`.

Para executar a verificação completa:

```powershell
uv run python -m unittest discover -s tests -v
uv run ruff check .
```

## Limites atuais

A base possui 100 frases sintéticas e serve como ponto de partida. A acurácia de teste do modelo selecionado é 48%, portanto os resultados não devem orientar decisões contratuais sem revisão humana. Antes de uso real, é necessário treinar com transcrições anonimizadas, separar a avaliação por cliente e período e calibrar os limites dos indicadores.
