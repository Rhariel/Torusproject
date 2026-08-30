"""API da plataforma Torus Meeting Intelligence."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.intent_classifier import get_model_evaluation
from app.meeting_analysis import analyze_meeting
from app.storage import (
    authenticate_user,
    count_meetings,
    create_session,
    delete_session,
    get_meeting,
    get_user,
    get_user_by_token,
    init_db,
    list_meetings,
    list_sellers,
    save_meeting,
    save_message_analysis,
)
from app.text_processing import process_text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = PROJECT_ROOT / "index.html"
MAX_UPLOAD_BYTES = 1_000_000


class LoginPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., min_length=3, max_length=254)
    password: str = Field(..., min_length=1, max_length=256)


class MessagePayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    speaker: str = Field(
        default="unknown", min_length=1, max_length=80, examples=["cliente"]
    )
    text: str = Field(..., min_length=1, examples=["Estou pensando em cancelar."])


class MeetingPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    meeting_id: int = Field(..., examples=[101])
    title: str | None = Field(default=None, max_length=120)
    customer_name: str | None = Field(default=None, max_length=120)
    seller_id: int | None = None
    conversation: list[MessagePayload] = Field(..., min_length=1)


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    return authorization.removeprefix("Bearer ").strip()


def current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    token = _extract_token(authorization)
    user = get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")
    return user


def manager_user(
    user: Annotated[dict[str, Any], Depends(current_user)],
) -> dict[str, Any]:
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Acesso exclusivo para gerentes.")
    return user


def _resolve_seller(user: dict[str, Any], requested_seller_id: int | None) -> int:
    if user["role"] == "seller":
        return int(user["id"])
    if requested_seller_id is None:
        raise HTTPException(status_code=422, detail="Selecione o vendedor responsável.")
    seller = get_user(requested_seller_id)
    if seller is None or seller["role"] != "seller":
        raise HTTPException(status_code=422, detail="Vendedor responsável inválido.")
    return requested_seller_id


def _analyze_and_save(
    payload: dict[str, Any], user: dict[str, Any], requested_seller_id: int | None
) -> dict[str, Any]:
    seller_id = _resolve_seller(user, requested_seller_id)
    result = analyze_meeting(payload)
    record_id = save_meeting(
        payload=payload,
        analysis=result,
        seller_id=seller_id,
        created_by=int(user["id"]),
    )
    result["record_id"] = record_id
    result["seller"] = get_user(seller_id)
    return result


def _seed_demo_meetings() -> None:
    if count_meetings() > 0:
        return
    manager = authenticate_user("manager@torus.ai", "Torus@2026")
    sellers = list_sellers()
    if manager is None or len(sellers) < 2:
        return
    seller_by_email = {seller["email"]: seller for seller in sellers}
    demos = (
        (
            seller_by_email["ana@torus.ai"]["id"],
            {
                "meeting_id": 301,
                "title": "Renovação ERP",
                "customer_name": "Grupo Horizonte",
                "conversation": [
                    {
                        "speaker": "vendedor",
                        "text": "Vamos revisar a renovação do Protheus.",
                    },
                    {
                        "speaker": "cliente",
                        "text": "O valor ficou muito alto para nosso orçamento.",
                    },
                    {
                        "speaker": "cliente",
                        "text": (
                            "Se não houver ajuste, podemos cancelar no próximo mês."
                        ),
                    },
                ],
            },
        ),
        (
            seller_by_email["ana@torus.ai"]["id"],
            {
                "meeting_id": 302,
                "title": "Expansão do Fluig",
                "customer_name": "Nova Energia",
                "conversation": [
                    {
                        "speaker": "vendedor",
                        "text": "Quais são os planos para as novas filiais?",
                    },
                    {
                        "speaker": "cliente",
                        "text": "Queremos expandir o Fluig e contratar mais licenças.",
                    },
                    {
                        "speaker": "cliente",
                        "text": "A equipe está satisfeita com o resultado.",
                    },
                ],
            },
        ),
        (
            seller_by_email["carlos@torus.ai"]["id"],
            {
                "meeting_id": 303,
                "title": "Acompanhamento do RM",
                "customer_name": "Alimentos Brasil",
                "conversation": [
                    {
                        "speaker": "vendedor",
                        "text": "Como está a operação depois da implantação?",
                    },
                    {
                        "speaker": "cliente",
                        "text": "O RM está funcionando muito bem para a equipe.",
                    },
                    {
                        "speaker": "cliente",
                        "text": "Os indicadores melhoraram bastante.",
                    },
                ],
            },
        ),
    )
    for seller_id, payload in demos:
        result = analyze_meeting(payload)
        save_meeting(payload, result, int(seller_id), int(manager["id"]))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    _seed_demo_meetings()
    yield


app = FastAPI(
    title="Torus Meeting Intelligence",
    version="1.0.0",
    description="Análise de reuniões comerciais para vendedores e gerentes.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard() -> str:
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="Dashboard não encontrado.")
    return INDEX_PATH.read_text(encoding="utf-8")


@app.get("/health", tags=["Saúde"])
def healthcheck() -> dict[str, str]:
    evaluation = get_model_evaluation()
    return {
        "status": "ok",
        "model": str(evaluation.get("selected_model", "not_trained")),
    }


@app.post("/auth/login", tags=["Autenticação"])
def login(payload: LoginPayload) -> dict[str, Any]:
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return {
        "access_token": create_session(int(user["id"])),
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me", tags=["Autenticação"])
def auth_me(user: Annotated[dict[str, Any], Depends(current_user)]) -> dict[str, Any]:
    return user


@app.post("/auth/logout", tags=["Autenticação"])
def logout(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, bool]:
    token = _extract_token(authorization)
    delete_session(token)
    return {"logged_out": True}


@app.get("/users/sellers", tags=["Equipe"])
def sellers(
    _: Annotated[dict[str, Any], Depends(manager_user)],
) -> list[dict[str, Any]]:
    return list_sellers()


@app.get("/meetings", tags=["Reuniões"])
def meetings(
    user: Annotated[dict[str, Any], Depends(current_user)],
) -> list[dict[str, Any]]:
    return list_meetings(user)


@app.get("/meetings/{record_id}", tags=["Reuniões"])
def meeting_detail(
    record_id: int,
    user: Annotated[dict[str, Any], Depends(current_user)],
) -> dict[str, Any]:
    record = get_meeting(record_id, user)
    if record is None:
        raise HTTPException(status_code=404, detail="Reunião não encontrada.")
    return record


@app.get("/model_metrics", tags=["Modelo"])
def model_metrics(
    _: Annotated[dict[str, Any], Depends(current_user)],
) -> dict[str, Any]:
    return get_model_evaluation()


@app.post("/analyze", tags=["Análise"])
def analyze_message(
    payload: MessagePayload,
    _: Annotated[dict[str, Any], Depends(current_user)],
) -> dict[str, Any]:
    result = process_text(payload.model_dump())
    save_message_analysis(
        text=result["original_text"],
        intent=result["intent"],
        sentiment=result["sentiment"]["label"],
        churn_signal=result["features"]["churn_signal"],
    )
    return result


@app.post("/analyze_meeting", tags=["Análise"])
def analyze_complete_meeting(
    payload: MeetingPayload,
    user: Annotated[dict[str, Any], Depends(current_user)],
) -> dict[str, Any]:
    values = payload.model_dump()
    return _analyze_and_save(values, user, payload.seller_id)


@app.post("/analyze_meeting_file", tags=["Análise"])
async def analyze_meeting_file(
    user: Annotated[dict[str, Any], Depends(current_user)],
    file: Annotated[UploadFile, File()],
    seller_id: Annotated[int | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
    customer_name: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    if not (file.filename or "").lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Envie um arquivo JSON válido.")
    try:
        file_content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(file_content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="O arquivo excede o limite de 1 MB.",
            )
        raw_payload = json.loads(file_content.decode("utf-8"))
        if title:
            raw_payload["title"] = title
        if customer_name:
            raw_payload["customer_name"] = customer_name
        if seller_id is not None:
            raw_payload["seller_id"] = seller_id
        payload = MeetingPayload(**raw_payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValidationError,
        TypeError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail="JSON inválido ou fora do formato esperado.",
        ) from exc
    values = payload.model_dump()
    return _analyze_and_save(values, user, payload.seller_id)
