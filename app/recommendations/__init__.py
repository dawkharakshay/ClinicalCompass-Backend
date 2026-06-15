"""Server-side recommendation engines ported 1:1 from the legacy *Logic.ts.

Public surface:
    get_assessor(logic_key) -> Callable[[dict], dict] | None
    coerce_submission(data, form) -> dict
"""

from app.recommendations.coerce import coerce_submission
from app.recommendations.registry import (
    get_assessor,
    get_evidence,
    get_presenter,
    present_result,
)

__all__ = [
    "coerce_submission",
    "get_assessor",
    "get_evidence",
    "get_presenter",
    "present_result",
]
