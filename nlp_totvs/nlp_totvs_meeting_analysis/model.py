"""Rule-based intent classification for meeting transcripts."""

from __future__ import annotations


INTENT_KEYWORDS = {
    "churn_risk": {
        "cancelar",
        "cancele",
        "cancelamento",
        "encerrar",
        "trocar de fornecedor",
        "desistir",
        "sair",
        "não vou continuar",
        "nao vou continuar",
    },
    "price_objection": {
        "caro",
        "preço",
        "preco",
        "valor alto",
        "muito caro",
        "desconto",
        "orçamento",
        "orcamento",
        "fora do orçamento",
    },
    "upsell_opportunity": {
        "upgrade",
        "mais usuários",
        "mais usuarios",
        "novo módulo",
        "novo modulo",
        "ampliar",
        "expandir",
        "contratar mais",
        "mais licenças",
        "mais licencas",
    },
    "satisfaction": {
        "gostei",
        "ótimo",
        "otimo",
        "excelente",
        "satisfeito",
        "satisfeita",
        "funcionando bem",
        "deu certo",
        "muito bom",
    },
}


def classify_intent(text: str) -> str:
    """Classify text intent using simple keyword rules."""
    normalized_text = (text or "").strip().lower()
    if not normalized_text:
        return "neutral"

    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            return intent

    return "neutral"
