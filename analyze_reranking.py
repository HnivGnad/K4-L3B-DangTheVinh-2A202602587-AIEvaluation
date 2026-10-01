"""Measure lexical reranking on saved retrieval traces for Exercise 3.5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from template import RAGASEvaluator, rerank_by_overlap


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    golden = _load_object(Path("golden_dataset.json"))
    actual = _load_object(Path("artifacts/actual_answers.json"))
    gold_by_id = {record["id"]: record for record in golden["qa_pairs"]}
    evaluator = RAGASEvaluator()
    rows: list[dict[str, Any]] = []

    for answer_record in actual["answers"]:
        pair = gold_by_id[answer_record["id"]]
        contexts = [item["text"] for item in answer_record["retrieved_contexts"]]
        reranked = rerank_by_overlap(contexts, pair["question"])
        recall_before = evaluator.evaluate_context_recall(
            contexts, pair["expected_answer"]
        )
        precision_before = evaluator.evaluate_context_precision(
            contexts, pair["expected_answer"]
        )
        recall_after = evaluator.evaluate_context_recall(
            reranked, pair["expected_answer"]
        )
        precision_after = evaluator.evaluate_context_precision(
            reranked, pair["expected_answer"]
        )
        rows.append(
            {
                "id": pair["id"],
                "recall_before": recall_before,
                "recall_after": recall_after,
                "precision_before": precision_before,
                "precision_after": precision_after,
                "delta": precision_after - precision_before,
            }
        )

    rows.sort(key=lambda row: (-row["delta"], row["id"]))
    selected = rows[:5]
    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |")
    print("|---|---:|---:|---:|---:|---:|")
    for row in selected:
        print(
            f"| {row['id']} | {row['recall_before']:.3f} | "
            f"{row['recall_after']:.3f} | {row['precision_before']:.3f} | "
            f"{row['precision_after']:.3f} | {row['delta']:+.3f} |"
        )
    count = len(selected)
    print(
        "| **Avg** | "
        f"{sum(row['recall_before'] for row in selected) / count:.3f} | "
        f"{sum(row['recall_after'] for row in selected) / count:.3f} | "
        f"{sum(row['precision_before'] for row in selected) / count:.3f} | "
        f"{sum(row['precision_after'] for row in selected) / count:.3f} | "
        f"{sum(row['delta'] for row in selected) / count:+.3f} |"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
