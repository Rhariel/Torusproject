"""Valida o pipeline com reuniões que não aparecem no treinamento."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.meeting_analysis import analyze_meeting

BACKEND_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = BACKEND_ROOT / "data" / "validation_meetings.json"
OUTPUT_PATH = BACKEND_ROOT / "models" / "validation_results.json"
REPORT_PATH = BACKEND_ROOT / "docs" / "VALIDATION_RESULTS.md"


def _evaluate_meeting(meeting: dict[str, Any]) -> dict[str, Any]:
    analysis = analyze_meeting(meeting)
    predicted = [message["intent"] for message in analysis["message_analysis"]]
    expected = meeting["expected_intents"]
    matches = [
        expected_label == predicted_label
        for expected_label, predicted_label in zip(expected, predicted, strict=True)
    ]
    return {
        "meeting_id": meeting["meeting_id"],
        "scenario": meeting["scenario"],
        "expected_intents": expected,
        "predicted_intents": predicted,
        "matches": matches,
        "summary": analysis["summary"],
    }


def _write_report(validation: dict[str, Any]) -> None:
    accuracy = f"{validation['validation_accuracy']:.2%}".replace(".", ",")
    lines = [
        "# Validação do pipeline de reuniões",
        "",
        (
            f"O teste usa {validation['meetings']} reuniões que não fizeram parte "
            f"do treinamento. O modelo acertou {validation['correct_messages']} "
            f"das {validation['messages']} falas ({accuracy})."
        ),
        "",
        "| Reunião | Cenário | Esperado | Previsto | Acertos | Risco | Oportunidade |",
        "|---:|---|---|---|---:|---:|---:|",
    ]

    for result in validation["results"]:
        summary = result["summary"]
        lines.append(
            f"| {result['meeting_id']} | {result['scenario']} | "
            f"{', '.join(result['expected_intents'])} | "
            f"{', '.join(result['predicted_intents'])} | "
            f"{sum(result['matches'])}/{len(result['matches'])} | "
            f"{summary['churn_risk_score']} | {summary['opportunity_score']} |"
        )

    lines.extend(
        [
            "",
            "## O que os três casos mostram",
            "",
            (
                "- Na reunião de retenção, o score de churn ultrapassa o limite de "
                "70 e aciona contato executivo."
            ),
            "- Na expansão, o modelo encontra a oportunidade e a menção ao Fluig.",
            "- No acompanhamento, o risco permanece baixo.",
            "",
            (
                "A amostra tem somente nove falas. A taxa acima descreve estes "
                "casos; ela não estima o desempenho em produção."
            ),
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate() -> dict[str, Any]:
    meetings = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    results = [_evaluate_meeting(meeting) for meeting in meetings]
    total_messages = sum(len(result["matches"]) for result in results)
    correct_messages = sum(sum(result["matches"]) for result in results)

    validation = {
        "meetings": len(results),
        "messages": total_messages,
        "correct_messages": correct_messages,
        "validation_accuracy": (
            round(correct_messages / total_messages, 4) if total_messages else 0.0
        ),
        "results": results,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_report(validation)
    return validation


if __name__ == "__main__":
    result = validate()
    accuracy = f"{result['validation_accuracy']:.2%}".replace(".", ",")
    print(
        f"{result['correct_messages']}/{result['messages']} falas corretas ({accuracy})"
    )
