#!/usr/bin/env python3
"""Pre-embed retrieval-evaluation questions without sharing the service key.

Run this only on Hein's authorized machine. The output contains questions and
gte-small vectors, not credentials, and can be handed to the kb_reader user.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import kb_client


def normalize_questions(payload: object) -> list[dict]:
    """Return question records from a list or {"questions": [...]} document."""
    if isinstance(payload, dict):
        payload = payload.get("questions")
    if not isinstance(payload, list) or not payload:
        raise ValueError("input must contain a non-empty questions list")

    questions: list[dict] = []
    for index, item in enumerate(payload, start=1):
        if isinstance(item, str):
            record = {"id": f"q{index}", "question": item}
        elif isinstance(item, dict):
            record = dict(item)
        else:
            raise ValueError(f"question {index} must be a string or object")

        question = record.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"question {index} has no non-empty 'question'")
        record["question"] = question.strip()
        record.setdefault("id", f"q{index}")
        record.pop("embedding", None)
        questions.append(record)
    return questions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="retrieval_questions.json")
    parser.add_argument("output", type=Path, help="non-secret embedded JSON")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    questions = normalize_questions(payload)

    embed_url = kb_client.env("SUPABASE_EMBED_URL")
    service_key = kb_client.env("SUPABASE_SERVICE_ROLE_KEY")
    vectors = kb_client.embed_texts(
        [item["question"] for item in questions],
        embed_url,
        service_key,
    )

    for item, vector in zip(questions, vectors, strict=True):
        if len(vector) != 384:
            raise RuntimeError(
                f"{item['id']}: expected a 384-dimensional gte-small vector, "
                f"got {len(vector)}"
            )
        item["embedding"] = vector

    output = {
        "model": "gte-small",
        "dimensions": 384,
        "questions": questions,
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"embedded {len(questions)} questions -> {args.output}")


if __name__ == "__main__":
    main()
