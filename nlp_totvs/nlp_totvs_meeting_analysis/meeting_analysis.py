"""Meeting-level analytics built on top of the NLP pipeline."""

from __future__ import annotations

from typing import Any

from database import insert_data
from nlp_pipeline import process_text


def _sentiment_to_numeric(sentiment: dict[str, Any]) -> float:
    label = sentiment.get("label", "neutral")
    score = float(sentiment.get("score", 0.5))

    if label == "positive":
        return score
    if label == "negative":
        return 1 - score
    return 0.5


def _compute_speech_proportion(conversation: list[dict[str, Any]]) -> dict[str, float]:
    total_words = 0
    customer_words = 0
    seller_words = 0

    for message in conversation:
        word_count = len(str(message.get("text", "")).split())
        total_words += word_count

        speaker = str(message.get("speaker", "")).lower()
        if speaker == "cliente":
            customer_words += word_count
        elif speaker == "vendedor":
            seller_words += word_count

    if total_words == 0:
        return {"cliente": 0.0, "vendedor": 0.0}

    return {
        "cliente": round(customer_words / total_words, 2),
        "vendedor": round(seller_words / total_words, 2),
    }


def analyze_meeting(data: dict) -> dict:
    conversation = data.get("conversation", [])
    message_analyses = []
    customer_sentiments = []
    churn_signals = 0
    upsell_opportunities = 0
    objections = []

    for message in conversation:
        analysis = process_text(message)
        message_analyses.append(analysis)

        insert_data(
            text=analysis["original_text"],
            intent=analysis["intent"],
            sentiment=analysis["sentiment"]["label"],
            churn_signal=analysis["features"]["churn_signal"],
        )

        speaker = str(analysis.get("speaker", "")).lower()
        if speaker == "cliente":
            customer_sentiments.append(_sentiment_to_numeric(analysis["sentiment"]))

        if analysis["features"]["churn_signal"]:
            churn_signals += 1

        if analysis["intent"] == "upsell_opportunity":
            upsell_opportunities += 1

        if analysis["intent"] == "price_objection":
            objections.append(analysis["original_text"])

    average_customer_sentiment = round(
        sum(customer_sentiments) / len(customer_sentiments), 2
    ) if customer_sentiments else 0.0

    speech_ratio = _compute_speech_proportion(conversation)

    churn_risk_score = (
        churn_signals * 25
        + len(objections) * 10
        + max(0.0, (0.5 - average_customer_sentiment)) * 100
        - upsell_opportunities * 10
    )
    churn_risk_score = round(max(0.0, min(100.0, churn_risk_score)), 2)

    return {
        "meeting_id": data.get("meeting_id"),
        "summary": {
            "average_customer_sentiment": average_customer_sentiment,
            "churn_signals": churn_signals,
            "upsell_opportunities": upsell_opportunities,
            "objections": objections,
            "speech_ratio": speech_ratio,
            "churn_risk_score": churn_risk_score,
        },
        "message_analysis": message_analyses,
    }
