import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "preembed_kb_questions",
    ROOT / "preembed-kb-questions.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_normalize_questions_accepts_strings_and_records():
    assert MODULE.normalize_questions(
        [
            "What is the Injeel?",
            {"id": "abrogation", "question": " Are earlier verses abrogated? "},
        ]
    ) == [
        {"id": "q1", "question": "What is the Injeel?"},
        {"id": "abrogation", "question": "Are earlier verses abrogated?"},
    ]


def test_normalize_questions_discards_stale_embeddings():
    assert MODULE.normalize_questions(
        {"questions": [{"question": "Question", "embedding": [0.0]}]}
    ) == [{"id": "q1", "question": "Question"}]


@pytest.mark.parametrize(
    "payload",
    [[], {}, [" "], [{"id": "missing"}], [42]],
)
def test_normalize_questions_rejects_invalid_input(payload):
    with pytest.raises(ValueError):
        MODULE.normalize_questions(payload)
