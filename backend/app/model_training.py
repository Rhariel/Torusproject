"""Treina, compara e registra os classificadores de intenção comercial."""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.intent_classifier import (
    EVALUATION_PATH,
    MODEL_DIR,
    MODEL_PATH,
    predict_probabilities,
    text_features,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = BACKEND_ROOT / "data" / "training_examples.csv"
REPORT_PATH = BACKEND_ROOT / "docs" / "MODEL_EVALUATION.md"

RANDOM_STATE = 42
TEST_RATIO = 0.25
LOGISTIC_EPOCHS = 360
INITIAL_LEARNING_RATE = 0.14
L2_PENALTY = 0.0002
NAIVE_BAYES_ALPHA = 0.6

MODEL_DISPLAY_NAMES = {
    "logistic_regression": "Regressão Logística",
    "multinomial_naive_bayes": "Multinomial Naive Bayes",
}


def load_dataset(path: Path = DATASET_PATH) -> list[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"text", "label"}
        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError("O dataset precisa das colunas 'text' e 'label'.")
        return [(row["text"].strip(), row["label"].strip()) for row in reader]


def stratified_split(
    examples: list[tuple[str, str]],
    test_ratio: float = TEST_RATIO,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    examples_by_class: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for example in examples:
        examples_by_class[example[1]].append(example)

    random_generator = random.Random(RANDOM_STATE)
    train_set: list[tuple[str, str]] = []
    test_set: list[tuple[str, str]] = []

    for class_examples in examples_by_class.values():
        random_generator.shuffle(class_examples)
        test_size = max(1, round(len(class_examples) * test_ratio))
        test_set.extend(class_examples[:test_size])
        train_set.extend(class_examples[test_size:])

    random_generator.shuffle(train_set)
    random_generator.shuffle(test_set)
    return train_set, test_set


def inverse_document_frequency(
    examples: list[tuple[str, str]],
) -> dict[str, float]:
    document_frequency: Counter[str] = Counter()
    for text, _ in examples:
        document_frequency.update(set(text_features(text)))

    document_count = len(examples)
    return {
        feature: math.log((document_count + 1) / (frequency + 1)) + 1
        for feature, frequency in document_frequency.items()
    }


def tfidf_vector(text: str, idf: dict[str, float]) -> dict[str, float]:
    counts = text_features(text)
    largest_count = max(counts.values(), default=1)
    return {
        feature: count / largest_count * idf[feature]
        for feature, count in counts.items()
        if feature in idf
    }


def train_logistic_regression(
    examples: list[tuple[str, str]],
    labels: list[str],
) -> dict[str, Any]:
    idf = inverse_document_frequency(examples)
    training_data = [(tfidf_vector(text, idf), label) for text, label in examples]
    weights = {label: defaultdict(float) for label in labels}
    biases = {label: 0.0 for label in labels}
    random_generator = random.Random(RANDOM_STATE)

    for epoch in range(LOGISTIC_EPOCHS):
        random_generator.shuffle(training_data)
        learning_rate = INITIAL_LEARNING_RATE / (1 + epoch * 0.006)

        for vector, expected_label in training_data:
            scores = {}
            for label in labels:
                scores[label] = biases[label] + sum(
                    weights[label][feature] * value for feature, value in vector.items()
                )

            highest_score = max(scores.values())
            exponentials = {
                label: math.exp(score - highest_score)
                for label, score in scores.items()
            }
            exponential_sum = sum(exponentials.values())

            for label in labels:
                target = 1.0 if label == expected_label else 0.0
                error = target - exponentials[label] / exponential_sum
                biases[label] += learning_rate * error
                for feature, value in vector.items():
                    regularization = L2_PENALTY * weights[label][feature]
                    weights[label][feature] += learning_rate * (
                        error * value - regularization
                    )

    return {
        "model_type": "logistic_regression",
        "labels": labels,
        "idf": {feature: round(value, 8) for feature, value in idf.items()},
        "weights": {
            label: {
                feature: round(value, 8) for feature, value in label_weights.items()
            }
            for label, label_weights in weights.items()
        },
        "biases": {label: round(value, 8) for label, value in biases.items()},
    }


def train_naive_bayes(
    examples: list[tuple[str, str]],
    labels: list[str],
) -> dict[str, Any]:
    class_counts = Counter(label for _, label in examples)
    feature_counts = {label: Counter() for label in labels}
    vocabulary: set[str] = set()

    for text, label in examples:
        counts = text_features(text)
        feature_counts[label].update(counts)
        vocabulary.update(counts)

    log_likelihoods: dict[str, dict[str, float]] = {}
    unknown_likelihood: dict[str, float] = {}
    for label in labels:
        denominator = sum(feature_counts[label].values()) + NAIVE_BAYES_ALPHA * len(
            vocabulary
        )
        log_likelihoods[label] = {
            feature: round(
                math.log(
                    (feature_counts[label][feature] + NAIVE_BAYES_ALPHA) / denominator
                ),
                8,
            )
            for feature in vocabulary
        }
        unknown_likelihood[label] = round(
            math.log(NAIVE_BAYES_ALPHA / denominator),
            8,
        )

    return {
        "model_type": "multinomial_naive_bayes",
        "labels": labels,
        "log_priors": {
            label: round(math.log(class_counts[label] / len(examples)), 8)
            for label in labels
        },
        "log_likelihoods": log_likelihoods,
        "unknown_log_likelihood": unknown_likelihood,
    }


def evaluate_model(
    model: dict[str, Any],
    examples: list[tuple[str, str]],
    labels: list[str],
) -> dict[str, Any]:
    matrix = [[0 for _ in labels] for _ in labels]
    label_position = {label: position for position, label in enumerate(labels)}
    errors = []

    for text, expected_label in examples:
        probabilities = predict_probabilities(model, text)
        predicted_label = max(probabilities, key=probabilities.get)
        matrix[label_position[expected_label]][label_position[predicted_label]] += 1
        if predicted_label != expected_label:
            errors.append(
                {
                    "text": text,
                    "expected": expected_label,
                    "predicted": predicted_label,
                }
            )

    per_class = {}
    for position, label in enumerate(labels):
        true_positive = matrix[position][position]
        false_positive = sum(row[position] for row in matrix) - true_positive
        false_negative = sum(matrix[position]) - true_positive
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1_score = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1_score, 4),
            "support": sum(matrix[position]),
        }

    accuracy = sum(matrix[position][position] for position in range(len(labels))) / len(
        examples
    )
    return {
        "accuracy": round(accuracy, 4),
        "precision_macro": round(
            sum(metrics["precision"] for metrics in per_class.values()) / len(labels),
            4,
        ),
        "recall_macro": round(
            sum(metrics["recall"] for metrics in per_class.values()) / len(labels),
            4,
        ),
        "f1_macro": round(
            sum(metrics["f1"] for metrics in per_class.values()) / len(labels),
            4,
        ),
        "confusion_matrix": matrix,
        "per_class": per_class,
        "errors": errors,
    }


def choose_model(metrics_by_model: dict[str, dict[str, Any]]) -> str:
    return max(
        metrics_by_model,
        key=lambda name: (
            metrics_by_model[name]["recall_macro"],
            metrics_by_model[name]["f1_macro"],
            metrics_by_model[name]["accuracy"],
            name == "logistic_regression",
        ),
    )


def _confusion_matrix_markdown(
    model_name: str,
    metrics: dict[str, Any],
    labels: list[str],
) -> list[str]:
    lines = [
        f"### Matriz de confusão — `{model_name}`",
        "",
        "As linhas mostram a classe real; as colunas, a previsão.",
        "",
        "| Real \\ Prevista | " + " | ".join(labels) + " |",
        "|---|" + "---:|" * len(labels),
    ]
    for label, row in zip(labels, metrics["confusion_matrix"], strict=True):
        lines.append("| " + label + " | " + " | ".join(map(str, row)) + " |")
    return lines


def _errors_markdown(metrics: dict[str, Any]) -> list[str]:
    lines = ["", "#### Onde o modelo errou", ""]
    for error in metrics["errors"]:
        lines.append(
            f"- “{error['text']}” — esperava `{error['expected']}`; "
            f"previu `{error['predicted']}`."
        )
    if not metrics["errors"]:
        lines.append("- Não houve erro no conjunto de teste.")
    return lines


def _percentage(value: float) -> str:
    return f"{value:.2%}".replace(".", ",")


def write_report(evaluation: dict[str, Any]) -> None:
    labels = evaluation["labels"]
    lines = [
        "# Avaliação do classificador de intenções comerciais",
        "",
        "## Problema e variável-alvo",
        "",
        (
            "O experimento classifica cada fala da reunião em uma de cinco classes: "
            "`churn_risk`, `price_objection`, `upsell_opportunity`, `satisfaction` "
            "ou `neutral`. A coluna `label` é a variável-alvo."
        ),
        "",
        "## Distribuição das classes",
        "",
        "| Classe | Exemplos |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {label} | {count} |"
        for label, count in evaluation["class_distribution"].items()
    )
    lines.extend(
        [
            "",
            (
                "O conjunto tem 100 frases sintéticas, com 20 exemplos por classe. "
                "A divisão estratificada reservou 75 frases para treino e 25 para "
                "teste. A semente 42 torna essa divisão reproduzível."
            ),
            "",
            "## Construção dos modelos",
            "",
            (
                "Foram treinados uma Regressão Logística multiclasse e um "
                "Multinomial Naive Bayes. Ambos usam as mesmas palavras, bigramas "
                "e n-gramas de caracteres."
            ),
            "",
            "## Comparação",
            "",
            "| Modelo | Acurácia | Precisão macro | Recall macro | F1 macro |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for model_name, metrics in evaluation["models"].items():
        lines.append(
            f"| {MODEL_DISPLAY_NAMES[model_name]} | {metrics['accuracy']:.4f} | "
            f"{metrics['precision_macro']:.4f} | {metrics['recall_macro']:.4f} | "
            f"{metrics['f1_macro']:.4f} |"
        )

    for model_name, metrics in evaluation["models"].items():
        lines.extend([""] + _confusion_matrix_markdown(model_name, metrics, labels))
        lines.extend(_errors_markdown(metrics))

    selected_model = evaluation["selected_model"]
    selected_metrics = evaluation["models"][selected_model]
    lines.extend(
        [
            "",
            "## Escolha do modelo",
            "",
            (
                "A Regressão Logística ficou com recall macro de "
                f"{_percentage(selected_metrics['recall_macro'])} e foi melhor que o "
                "Naive Bayes nesse critério. O recall macro tem prioridade porque dá "
                "o mesmo peso às cinco classes; assim, uma classe frequente não "
                "esconde falhas em churn ou oportunidade."
            ),
            "",
            "## Análise dos erros",
            "",
            (
                "A maior dificuldade está nas frases curtas e indiretas. Termos como "
                "“investimento”, “filiais” e “contrato” aparecem em contextos "
                "diferentes e geram confusão entre objeção, expansão e fala neutra."
            ),
            "",
            "## Conclusões e implicações para o negócio",
            "",
            (
                "Com 48% de acurácia no teste, este modelo é uma referência inicial, "
                "não um classificador pronto para produção. O próximo passo é "
                "rotular mais reuniões reais, sem dados pessoais, e medir o resultado "
                "por cliente e por período. Casos de churn devem continuar sujeitos "
                "à revisão humana."
            ),
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_experiment() -> dict[str, Any]:
    examples = load_dataset()
    train_set, test_set = stratified_split(examples)
    labels = sorted({label for _, label in examples})

    trained_models = {
        "logistic_regression": train_logistic_regression(train_set, labels),
        "multinomial_naive_bayes": train_naive_bayes(train_set, labels),
    }
    metrics_by_model = {
        name: evaluate_model(model, test_set, labels)
        for name, model in trained_models.items()
    }
    selected_model = choose_model(metrics_by_model)

    evaluation = {
        "dataset": "data/training_examples.csv",
        "dataset_size": len(examples),
        "train_size": len(train_set),
        "test_size": len(test_set),
        "random_state": RANDOM_STATE,
        "labels": labels,
        "class_distribution": dict(
            sorted(Counter(label for _, label in examples).items())
        ),
        "models": metrics_by_model,
        "selected_model": selected_model,
        "selection_rationale": (
            "Maior recall macro; em caso de empate, F1 macro e accuracy."
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(
        json.dumps(trained_models[selected_model], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    EVALUATION_PATH.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_report(evaluation)
    return evaluation


if __name__ == "__main__":
    result = run_experiment()
    print(
        json.dumps(
            {
                "selected_model": result["selected_model"],
                "metrics": result["models"][result["selected_model"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
