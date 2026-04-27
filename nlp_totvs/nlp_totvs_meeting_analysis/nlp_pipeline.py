"""NLP pipeline for transcript analysis."""

from __future__ import annotations

from typing import Any

import spacy
from transformers import pipeline

from model import classify_intent


_SENTIMENT_PIPELINE = None
_SPACY_MODEL = None

POSITIVE_LABELS = {"positive", "positivo", "pos"}
NEGATIVE_LABELS = {"negative", "negativo", "neg"}


def _load_sentiment_pipeline():
    global _SENTIMENT_PIPELINE
    if _SENTIMENT_PIPELINE is not None:
        return _SENTIMENT_PIPELINE

    try:
        _SENTIMENT_PIPELINE = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            tokenizer="cardiffnlp/twitter-xlm-roberta-base-sentiment",
        )
    except Exception:
        # Fallback keeps the API functional when the transformer model is unavailable locally.
        _SENTIMENT_PIPELINE = False
    return _SENTIMENT_PIPELINE


def _load_spacy_model():
    global _SPACY_MODEL
    if _SPACY_MODEL is not None:
        return _SPACY_MODEL

    try:
        _SPACY_MODEL = spacy.load("pt_core_news_sm")
    except Exception:
        # Blank Portuguese pipeline avoids runtime failure when the model was not downloaded yet.
        _SPACY_MODEL = spacy.blank("pt")
    return _SPACY_MODEL


def preprocess_text(text: str) -> str:
    return (text or "").strip().lower()


def _heuristic_sentiment(text: str) -> dict[str, Any]:
    positive_terms = {"bom", "ótimo", "otimo", "excelente", "gostei", "feliz", "satisfeito"}
    negative_terms = {"caro", "ruim", "cancelar", "problema", "insatisfeito", "cancelamento"}

    score = 0.5
    text_lower = preprocess_text(text)

    if any(term in text_lower for term in positive_terms):
        score = 0.85
        label = "positive"
    elif any(term in text_lower for term in negative_terms):
        score = 0.15
        label = "negative"
    else:
        label = "neutral"

    return {"label": label, "score": score}


def analyze_sentiment(text: str) -> dict[str, Any]:
    sentiment_model = _load_sentiment_pipeline()
    if sentiment_model:
        try:
            result = sentiment_model(text[:512])[0]
            label = str(result.get("label", "neutral")).lower()
            score = float(result.get("score", 0.5))

            if label.endswith("0") or "negative" in label:
                label = "negative"
            elif label.endswith("1") or "neutral" in label:
                label = "neutral"
            elif label.endswith("2") or "positive" in label:
                label = "positive"

            return {"label": label, "score": score}
        except Exception:
            pass

    return _heuristic_sentiment(text)


def extract_entities(text: str) -> list[dict[str, str]]:
    nlp = _load_spacy_model()
    doc = nlp(text)
    if not doc.ents:
        return []

    return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]


def build_features(processed_text: str, intent: str, sentiment: dict[str, Any]) -> dict[str, Any]:
    negative_sentiment = sentiment["label"] in NEGATIVE_LABELS or sentiment["score"] < 0.4
    positive_sentiment = sentiment["label"] in POSITIVE_LABELS or sentiment["score"] > 0.7

    return {
        "churn_signal": intent == "churn_risk" or negative_sentiment,
        "price_signal": intent == "price_objection",
        "upsell_signal": intent == "upsell_opportunity",
        "satisfaction_signal": intent == "satisfaction" or positive_sentiment,
        "token_count": len(processed_text.split()),
    }


def process_text(data: dict) -> dict:
    """Run full NLP processing for a single message payload."""
    original_text = data.get("text", "")
    processed_text = preprocess_text(original_text)
    intent = classify_intent(processed_text)
    sentiment = analyze_sentiment(processed_text)
    entities = extract_entities(original_text)
    features = build_features(processed_text, intent, sentiment)

    return {
        "speaker": data.get("speaker", "unknown"),
        "original_text": original_text,
        "processed_text": processed_text,
        "intent": intent,
        "sentiment": sentiment,
        "entities": entities,
        "features": features,
    }
