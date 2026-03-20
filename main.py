"""
BibleDeepDive
=============
A web-based Bible study tool delivering 8-layer deep analysis.
Access-controlled — 7 unique user codes.

Author: Segun Omojola
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os

app = FastAPI(title="BibleDeepDive")

# ── Access Codes ───────────────────────────────────────────────────────────────
VALID_CODES = {
    "SEGUN001": "Segun",
    "STUDY002": "User 2",
    "STUDY003": "User 3",
    "STUDY004": "User 4",
    "STUDY005": "User 5",
    "STUDY006": "User 6",
    "STUDY007": "User 7",
}

# ── Input Models ───────────────────────────────────────────────────────────────

class AccessRequest(BaseModel):
    code: str

class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class StudyRequest(BaseModel):
    code: str
    reference: str
    mode: str  # "quick" or "deep"

class FollowUpRequest(BaseModel):
    code: str
    question: str
    mode: str           # "passage" or "open"
    reference: str      # original passage
    history: List[Message]  # full conversation so far

# ── Prompts ────────────────────────────────────────────────────────────────────

def build_quick_prompt(reference: str) -> str:
    return f"""You are BibleDeepDive — a serious Bible study tool.
Deliver a 3-layer study of {reference}. Be precise, deep, and scholarly.
Do not skip any layer. Do not be superficial.

LAYER 1 — CHAPTER BREAKDOWN
- What is the passage actually communicating?
- Surface key original language terms (Hebrew/Greek) — explain what is lost in English
- Establish the historical and political world the text assumes
- What would the original hearers have understood that modern readers miss?

LAYER 5 — CHRISTOCENTRIC READING
- How does this passage point to, find fulfilment in, or illuminate Jesus Christ?
- For OT passages: where is Christ as antitype, fulfilment, or embodiment?
- For NT passages: what does this deepen about who Christ is and what he has done?
- What would be lost in our understanding of Christ if this passage did not exist?

LAYER 8 — CURRENT SCENARIO
- What present-day situations does this passage directly address?
- Genuine structural parallels — not superficial application
- Be specific and concrete. Name real situations. No vague spiritual clichés.
- What does this passage demand of the person who takes it seriously in 2026?

Reference: {reference}
"""

def build_deep_prompt(reference: str) -> str:
    return f"""You are BibleDeepDive — a serious, seminary-level Bible study tool.
Deliver the full 8-layer study of {reference}.
Do not skip, abbreviate, or merge any layer. Each is theologically distinct and essential.
Be precise, deep, and scholarly throughout.

LAYER 1 — CHAPTER BREAKDOWN
- What is the passage actually communicating? What argument or narrative is being built?
- Surface key original language terms (Hebrew/Greek) — explain exactly what is lost in English
- Establish the historical and political world the text assumes
- Trace the structure and movement — how does the passage build?
- What would the original hearers have understood that modern readers miss entirely?

LAYER 2 — STRUCTURAL AND LITERARY CRAFT
- What literary genre is this — poetry, narrative, prophecy, epistle, apocalyptic?
- Identify structural features: chiasm, parallelism, inclusio, refrain, acrostic, narrative arc
- How does the structure itself make a theological argument?
- What does the form demand of the reader that prose could not achieve?

LAYER 3 — COVENANTAL FRAMEWORK
- Which covenant is the primary context — Noahic, Abrahamic, Mosaic, Davidic, or New Covenant?
- What covenant obligations, promises, and consequences are in view?
- How does this passage advance, fulfil, tension, or renew that covenant?
- What does this passage reveal about God as covenant-keeper?

LAYER 4 — CROSS-LINKAGES
- What earlier scriptures does this passage echo, fulfil, quote, or subvert?
- What later scriptures does it anticipate, explain, or find fulfilment in?
- Trace specific verbal echoes and thematic threads across both Testaments
- Identify type and antitype, promise and fulfilment, shadow and substance

LAYER 5 — CHRISTOCENTRIC READING
- How does this passage point to, find fulfilment in, or illuminate Jesus Christ?
- For OT passages: where is Christ as antitype, fulfilment, or embodiment?
- For NT passages: what does this deepen about who Christ is and what he has done?
- What does this passage reveal about Christ's person, work, or offices (prophet, priest, king)?
- What would be lost in our understanding of Christ if this passage did not exist?

LAYER 6 — DOCTRINAL THEOLOGY
- What attributes of God are on display — holiness, justice, mercy, sovereignty, faithfulness?
- What does this passage contribute to the doctrine of humanity, sin, or redemption?
- What does it teach about salvation, the Spirit, the church, or last things?
- What heresy or error does this passage directly correct or prevent?

LAYER 7 — COMMENTARY INSIGHTS
- What have the great commentators seen in this passage?
- Draw on Spurgeon, Calvin, Matthew Henry, N.T. Wright, and William Barclay where relevant
- Where do the voices of the tradition agree or see different things?
- What is the most important interpretive move for the serious student to grasp?

LAYER 8 — CURRENT SCENARIO
- What present-day situations does this passage directly address?
- Genuine structural parallels — not superficial application
- Be specific and concrete. Name real situations. No vague spiritual clichés.
- Where is the world today in a situation structurally identical to the world of this text?
- What does this passage demand of the person who takes it seriously in 2026?

Reference: {reference}
"""

def build_system_prompt(reference: str, mode: str) -> str:
    if mode == "passage":
        return (
            f"You are BibleDeepDive — a serious, scholarly Bible study assistant. "
            f"The user is studying {reference}. All follow-up questions relate to this passage. "
            f"Be precise, deep, and theological in all responses. "
            f"Draw on original languages, historical context, and the tradition of Spurgeon, Calvin, "
            f"Matthew Henry, N.T. Wright, and Barclay where relevant."
        )
    else:
        return (
            f"You are BibleDeepDive — a serious, scholarly Bible study assistant. "
            f"The user began by studying {reference} but may ask about any biblical topic. "
            f"Be precise, deep, and theological in all responses. "
            f"Draw on original languages, historical context, and the tradition of Spurgeon, Calvin, "
            f"Matthew Henry, N.T. Wright, and Barclay where relevant."
        )

# ── Claude API call ────────────────────────────────────────────────────────────

async def call_claude(messages: list, system: str = "", max_tokens: int = 4000) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        payload["system"] = system

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timed out — try again")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── API Routes ─────────────────────────────────────────────────────────────────

@app.post("/verify")
async def verify_code(request: AccessRequest):
    code = request.code.strip().upper()
    if code in VALID_CODES:
        return {"valid": True, "name": VALID_CODES[code]}
    raise HTTPException(status_code=401, detail="Invalid access code")


@app.post("/study")
async def study(request: StudyRequest):
    code = request.code.strip().upper()
    if code not in VALID_CODES:
        raise HTTPException(status_code=401, detail="Invalid access code")
    if not request.reference.strip():
        raise HTTPException(status_code=400, detail="Reference required")

    if request.mode == "quick":
        prompt = build_quick_prompt(request.reference.strip())
    else:
        prompt = build_deep_prompt(request.reference.strip())

    result = await call_claude(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000
    )
    return {"result": result}


@app.post("/followup")
async def followup(request: FollowUpRequest):
    code = request.code.strip().upper()
    if code not in VALID_CODES:
        raise HTTPException(status_code=401, detail="Invalid access code")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question required")

    system = build_system_prompt(request.reference, request.mode)

    # Build messages from history + new question
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.question.strip()})

    result = await call_claude(messages=messages, system=system, max_tokens=4000)
    return {"result": result}


@app.get("/health")
async def health():
    return {"status": "ok", "tool": "BibleDeepDive", "author": "Segun Omojola"}


# ── Serve Frontend ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
