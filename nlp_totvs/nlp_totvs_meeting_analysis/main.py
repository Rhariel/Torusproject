"""FastAPI entrypoint for meeting transcript analysis."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from database import init_db, insert_data
from meeting_analysis import analyze_meeting
from nlp_pipeline import process_text


class MessagePayload(BaseModel):
    speaker: str = Field(
        default="unknown",
        title="Falante",
        description="Quem enviou a mensagem, por exemplo cliente ou vendedor.",
        examples=["cliente"],
    )
    text: str = Field(
        ...,
        min_length=1,
        title="Texto",
        description="Conteudo textual da mensagem a ser analisada.",
        examples=["Estou achando caro."],
    )


class MeetingPayload(BaseModel):
    meeting_id: int = Field(
        ...,
        title="ID da reuniao",
        description="Identificador unico da reuniao.",
        examples=[1],
    )
    conversation: list[MessagePayload] = Field(
        ...,
        title="Conversa",
        description="Lista de falas da reuniao em ordem cronologica.",
    )


tags_metadata = [
    {
        "name": "Dashboard",
        "description": "Interface visual para upload e analise de reunioes.",
    },
    {
        "name": "Saude",
        "description": "Endpoints para verificar se a API esta online.",
    },
    {
        "name": "Analise NLP",
        "description": "Endpoints para analise de mensagens e reunioes.",
    },
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Analise de Reunioes TOTVS com NLP",
    version="1.0.0",
    description=(
        "API REST para analisar transcricoes de reunioes, identificar sentimento, "
        "entidades, intencoes e sinais de churn."
    ),
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "docExpansion": "list",
        "displayRequestDuration": True,
        "filter": True,
    },
)


@app.get(
    "/",
    response_class=HTMLResponse,
    tags=["Dashboard"],
    summary="Abrir dashboard",
    description="Abre o painel visual para envio de arquivo JSON e visualizacao dos resultados.",
)
def dashboard() -> str:
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Dashboard de Analise de Reunioes</title>
        <style>
            :root {
                --bg: #f5f1e8;
                --panel: #fffdf8;
                --ink: #1f2937;
                --muted: #6b7280;
                --line: #d8cfc2;
                --brand: #0f766e;
                --brand-soft: #dff5f2;
                --warn: #b45309;
                --danger: #b91c1c;
                --success: #166534;
                --shadow: 0 12px 30px rgba(31, 41, 55, 0.08);
            }

            * { box-sizing: border-box; }
            body {
                margin: 0;
                font-family: "Segoe UI", Tahoma, sans-serif;
                background:
                    radial-gradient(circle at top left, #efe3cc 0, transparent 35%),
                    linear-gradient(135deg, #f5f1e8 0%, #f3f7f4 100%);
                color: var(--ink);
            }

            .page {
                max-width: 1300px;
                margin: 0 auto;
                padding: 32px 20px 60px;
            }

            .hero {
                display: grid;
                grid-template-columns: 1.2fr 0.8fr;
                gap: 20px;
                margin-bottom: 24px;
            }

            .panel {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 20px;
                box-shadow: var(--shadow);
            }

            .hero-card {
                padding: 28px;
            }

            h1, h2, h3 { margin: 0 0 12px; }

            .hero p, .helper, .legend, .empty-state, .status {
                color: var(--muted);
                line-height: 1.5;
            }

            .badge-row {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 18px;
            }

            .badge {
                padding: 10px 14px;
                border-radius: 999px;
                background: var(--brand-soft);
                color: var(--brand);
                font-weight: 600;
                font-size: 14px;
            }

            .upload-box {
                padding: 24px;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }

            label {
                font-weight: 600;
                font-size: 14px;
            }

            input[type="file"] {
                width: 100%;
                padding: 12px;
                border: 1px dashed var(--line);
                border-radius: 14px;
                background: #fff;
            }

            button {
                border: none;
                border-radius: 14px;
                background: var(--brand);
                color: white;
                padding: 14px 18px;
                font-size: 15px;
                font-weight: 700;
                cursor: pointer;
            }

            button:hover { filter: brightness(1.05); }
            button:disabled { opacity: 0.7; cursor: wait; }

            .grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 16px;
                margin-bottom: 20px;
            }

            .metric {
                padding: 20px;
            }

            .metric span {
                display: block;
                font-size: 13px;
                color: var(--muted);
                margin-bottom: 10px;
            }

            .metric strong {
                font-size: 30px;
            }

            .metric small {
                display: block;
                margin-top: 8px;
                color: var(--muted);
            }

            .sections {
                display: grid;
                grid-template-columns: 0.8fr 1.2fr;
                gap: 20px;
            }

            .section {
                padding: 22px;
            }

            .bar-wrap {
                margin-top: 14px;
            }

            .bar-label {
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                margin-bottom: 6px;
            }

            .bar {
                width: 100%;
                height: 14px;
                background: #ece7dd;
                border-radius: 999px;
                overflow: hidden;
                margin-bottom: 14px;
            }

            .fill {
                height: 100%;
                border-radius: 999px;
            }

            .fill-cliente { background: #0f766e; }
            .fill-vendedor { background: #d97706; }
            .fill-risco { background: linear-gradient(90deg, #16a34a, #f59e0b, #dc2626); }

            .objection-list, .message-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-top: 14px;
            }

            .pill {
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
                margin-right: 8px;
            }

            .pill-negative { background: #fee2e2; color: var(--danger); }
            .pill-positive { background: #dcfce7; color: var(--success); }
            .pill-neutral { background: #e5e7eb; color: #374151; }
            .pill-intent { background: #e0f2fe; color: #075985; }

            .message-card {
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 16px;
                background: #fff;
            }

            .message-head {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 8px;
                flex-wrap: wrap;
            }

            .message-text {
                margin: 10px 0;
                line-height: 1.5;
            }

            .helper-box {
                margin-bottom: 20px;
                padding: 18px 20px;
            }

            .code {
                font-family: Consolas, monospace;
                background: #f8fafc;
                border: 1px solid var(--line);
                border-radius: 12px;
                padding: 12px;
                font-size: 13px;
                white-space: pre-wrap;
            }

            @media (max-width: 980px) {
                .hero, .sections, .grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="page">
            <div class="hero">
                <div class="panel hero-card">
                    <h1>Dashboard de Analise de Reunioes</h1>
                    <p>
                        Envie um arquivo JSON com a transcricao da reuniao. O sistema analisa
                        sentimento, intencao, risco de churn, objecoes e oportunidades de upsell.
                    </p>
                    <div class="badge-row">
                        <div class="badge">Entrada por arquivo JSON</div>
                        <div class="badge">Analise consolidada</div>
                        <div class="badge">Detalhe por mensagem</div>
                    </div>
                </div>
                <div class="panel upload-box">
                    <div>
                        <label for="meetingFile">Arquivo da reuniao</label>
                        <p class="helper">Use um JSON com `meeting_id` e `conversation`.</p>
                    </div>
                    <input id="meetingFile" type="file" accept=".json,application/json" />
                    <button id="analyzeButton">Analisar arquivo</button>
                    <div class="status" id="statusText">Aguardando envio de arquivo.</div>
                    <div class="legend">
                        Exemplo de caminho de teste: `sample_meeting.json`
                    </div>
                </div>
            </div>

            <div class="panel helper-box">
                <h3>Como usar este dashboard</h3>
                <div class="legend">
                    1. Selecione um arquivo JSON da reuniao.
                    2. Clique em <strong>Analisar arquivo</strong>.
                    3. Veja os indicadores principais nos cards.
                    4. Veja abaixo o detalhe por fala e os sinais encontrados.
                </div>
                <div class="code">{
  "meeting_id": 1,
  "conversation": [
    {"speaker": "vendedor", "text": "Bom dia"},
    {"speaker": "cliente", "text": "Estou achando caro"},
    {"speaker": "cliente", "text": "Talvez eu cancele"}
  ]
}</div>
            </div>

            <div id="results" style="display:none;">
                <div class="grid">
                    <div class="panel metric">
                        <span>Risco consolidado</span>
                        <strong id="riskScore">0</strong>
                        <small>Score final de 0 a 100</small>
                    </div>
                    <div class="panel metric">
                        <span>Sentimento Global</span>
                        <strong id="avgSentiment">0</strong>
                        <small>Media das falas do cliente</small>
                    </div>
                    <div class="panel metric">
                        <span>Mensagens Processadas</span>
                        <strong id="churnSignals">0</strong>
                        <small>Total de mensagens analisadas</small>
                    </div>
                    <div class="panel metric">
                        <span>Total de Entidades</span>
                        <strong id="upsellCount">0</strong>
                        <small>Entidades identificadas no texto</small>
                    </div>
                </div>

                <div class="sections">
                    <div class="panel section">
                        <h2>Métricas e Sinais</h2>
                        <p class="legend">
                            Este bloco resume os indicadores mais importantes da reuniao para uso gerencial.
                        </p>
                        <div class="bar-wrap">
                            <div class="bar-label">
                                <span>Participacao do cliente</span>
                                <span id="clientShareLabel">0%</span>
                            </div>
                            <div class="bar"><div id="clientShareBar" class="fill fill-cliente" style="width:0%;"></div></div>
                            <div class="bar-label">
                                <span>Participacao do vendedor</span>
                                <span id="sellerShareLabel">0%</span>
                            </div>
                            <div class="bar"><div id="sellerShareBar" class="fill fill-vendedor" style="width:0%;"></div></div>
                            <div class="bar-label">
                                <span>Risco consolidado</span>
                                <span id="riskBarLabel">0%</span>
                            </div>
                            <div class="bar"><div id="riskBar" class="fill fill-risco" style="width:0%;"></div></div>
                        </div>
                        <h3>Objecoes encontradas</h3>
                        <div id="objectionList" class="objection-list"></div>
                    </div>

                    <div class="panel section">
                        <h2>Histórico da Conversa</h2>
                        <p class="legend">
                            Cada card mostra quem falou, o texto analisado, a intencao detectada,
                            o sentimento e os sinais relevantes para a reuniao.
                        </p>
                        <div id="messageList" class="message-list"></div>
                    </div>
                </div>
            </div>

            <div id="emptyState" class="panel section empty-state">
                Nenhuma reuniao analisada ainda. Envie um arquivo JSON para preencher o dashboard.
            </div>
        </div>

        <script>
            const analyzeButton = document.getElementById("analyzeButton");
            const meetingFile = document.getElementById("meetingFile");
            const statusText = document.getElementById("statusText");
            const results = document.getElementById("results");
            const emptyState = document.getElementById("emptyState");

            function sentimentClass(label) {
                if (label === "positive") return "pill-positive";
                if (label === "negative") return "pill-negative";
                return "pill-neutral";
            }

            function formatPercent(value) {
                return `${Math.round(value * 100)}%`;
            }

            function renderObjections(objections) {
                const container = document.getElementById("objectionList");
                container.innerHTML = "";
                if (!objections.length) {
                    container.innerHTML = "<div class='legend'>Nenhuma objecao comercial encontrada.</div>";
                    return;
                }

                objections.forEach((item) => {
                    const div = document.createElement("div");
                    div.className = "message-card";
                    div.textContent = item;
                    container.appendChild(div);
                });
            }

            function renderMessages(messages) {
                const container = document.getElementById("messageList");
                container.innerHTML = "";

                let totalEntities = 0;

                messages.forEach((message, index) => {
                    totalEntities += message.entities.length;
                    const entities = message.entities.length
                        ? message.entities.map((entity) => `${entity.text} (${entity.label})`).join(", ")
                        : "Nenhuma entidade relevante.";

                    const features = Object.entries(message.features)
                        .filter(([key, value]) => typeof value === "boolean" && value)
                        .map(([key]) => key)
                        .join(", ") || "Nenhum sinal especial.";

                    const card = document.createElement("div");
                    card.className = "message-card";
                    card.innerHTML = `
                        <div class="message-head">
                            <strong>Fala ${index + 1} - ${message.speaker}</strong>
                            <div>
                                <span class="pill pill-intent">${message.intent}</span>
                                <span class="pill ${sentimentClass(message.sentiment.label)}">${message.sentiment.label}</span>
                            </div>
                        </div>
                        <div class="message-text">${message.original_text}</div>
                        <div class="legend"><strong>Entidades:</strong> ${entities}</div>
                        <div class="legend"><strong>Sinais:</strong> ${features}</div>
                    `;
                    container.appendChild(card);
                });
                return totalEntities;
            }

            function renderDashboard(data) {
                const summary = data.summary;
                document.getElementById("riskScore").textContent = summary.churn_risk_score;
                document.getElementById("avgSentiment").textContent = summary.average_customer_sentiment;
                document.getElementById("churnSignals").textContent = data.message_analysis.length;

                document.getElementById("clientShareLabel").textContent = formatPercent(summary.speech_ratio.cliente);
                document.getElementById("sellerShareLabel").textContent = formatPercent(summary.speech_ratio.vendedor);
                document.getElementById("riskBarLabel").textContent = `${summary.churn_risk_score}%`;
                document.getElementById("clientShareBar").style.width = formatPercent(summary.speech_ratio.cliente);
                document.getElementById("sellerShareBar").style.width = formatPercent(summary.speech_ratio.vendedor);
                document.getElementById("riskBar").style.width = `${summary.churn_risk_score}%`;

                renderObjections(summary.objections);
                const totalEntities = renderMessages(data.message_analysis);
                document.getElementById("upsellCount").textContent = totalEntities;

                emptyState.style.display = "none";
                results.style.display = "block";
            }

            analyzeButton.addEventListener("click", async () => {
                const file = meetingFile.files[0];
                if (!file) {
                    statusText.textContent = "Selecione um arquivo JSON antes de analisar.";
                    return;
                }

                const formData = new FormData();
                formData.append("file", file);
                analyzeButton.disabled = true;
                statusText.textContent = "Processando arquivo e gerando dashboard...";

                try {
                    const response = await fetch("/analyze_meeting_file", {
                        method: "POST",
                        body: formData
                    });

                    const data = await response.json();
                    if (!response.ok) {
                        throw new Error(data.detail || "Falha ao analisar o arquivo.");
                    }

                    renderDashboard(data);
                    statusText.textContent = `Reuniao ${data.meeting_id} analisada com sucesso.`;
                } catch (error) {
                    statusText.textContent = error.message;
                } finally {
                    analyzeButton.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """


@app.get(
    "/health",
    tags=["Saude"],
    summary="Verificar status da API",
    description="Retorna um status simples para confirmar que a API esta online.",
)
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/analyze",
    tags=["Analise NLP"],
    summary="Analisar mensagem",
    description="Recebe uma unica mensagem e retorna a analise completa de NLP.",
)
def analyze_message(payload: MessagePayload) -> dict:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="O campo text nao pode ser vazio.")

    result = process_text(payload.model_dump())
    insert_data(
        text=result["original_text"],
        intent=result["intent"],
        sentiment=result["sentiment"]["label"],
        churn_signal=result["features"]["churn_signal"],
    )
    return result


@app.post(
    "/analyze_meeting",
    tags=["Analise NLP"],
    summary="Analisar reuniao completa",
    description=(
            "Recebe uma reuniao com varias falas e retorna a analise consolidada "
            "e o detalhamento por mensagem."
    ),
)
def analyze_complete_meeting(payload: MeetingPayload) -> dict:
    if not payload.conversation:
        raise HTTPException(status_code=400, detail="A conversa nao pode ser vazia.")

    return analyze_meeting(payload.model_dump())


@app.post(
    "/analyze_meeting_file",
    tags=["Analise NLP"],
    summary="Analisar reuniao por arquivo",
    description="Recebe um arquivo JSON de reuniao e retorna a analise consolidada em formato estruturado.",
)
async def analyze_meeting_file(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Envie um arquivo JSON valido.")

    raw_content = await file.read()
    try:
        payload = json.loads(raw_content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Nao foi possivel ler o JSON enviado.") from exc

    if not isinstance(payload, dict) or "conversation" not in payload:
        raise HTTPException(
            status_code=400,
            detail="O arquivo precisa conter meeting_id e conversation.",
        )

    meeting_payload = MeetingPayload(**payload)
    return analyze_meeting(meeting_payload.model_dump())