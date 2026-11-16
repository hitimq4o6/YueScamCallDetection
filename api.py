"""Development FastAPI stub. Layer-1 rules plus Layer-2 lexicon model. Advisory, not a legal finding."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from layer1_score import load_all, score_text
from layer2_score import MODEL_PATH, load_model, score_text as score_layer2

app = FastAPI(title="Suspicious message scorer", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_CONCEPTS, _DIGITS, _RULES = load_all()
_LAYER2 = load_model(MODEL_PATH) if MODEL_PATH.exists() else None


class ScoreRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class ScoreResponse(BaseModel):
    score: float
    risk: str
    concepts: list[str]
    advisory: bool = True
    layer2_score: float | None = None
    layer2_risk: str | None = None
    layer2_proba: float | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "layer": 2 if _LAYER2 else 1}


@app.post("/score", response_model=ScoreResponse)
def score(body: ScoreRequest) -> ScoreResponse:
    result = score_text(body.text, _CONCEPTS, _DIGITS, _RULES)
    if _LAYER2 is None:
        return ScoreResponse(**result)
    layer2 = score_layer2(body.text, _CONCEPTS, _DIGITS, _RULES, _LAYER2)
    return ScoreResponse(
        **result,
        layer2_score=layer2["score"],
        layer2_risk=layer2["risk"],
        layer2_proba=layer2["proba"],
    )
