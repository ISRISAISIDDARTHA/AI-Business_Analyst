import calendar
import json
import math
import re

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

PROMPT_TEMPLATE = """You are a business analyst assistant. You will be given a precomputed,
verified finding about a change in revenue. Your only job is to restate this
finding as ONE plain-English sentence.

STRICT RULES:
- Only use the numbers and facts given below. Do not estimate, guess, or
  add any numbers not explicitly provided.
- Do not mention any category, region, or seller that is not named below.
- Write ONE sentence only. Do not mention other factors or offsetting;
  that is added separately.
- Write in a neutral, professional tone.
- Use this sentence shape: "Revenue from [the driver] fell or rose by $X, which
  accounts for Y% of the total change between [the two months]."
- NEVER use causal words such as "due to", "because", "caused by", "as a
  result of", "led to", or "driven by".

FINDING:
Comparison period: {period}
Primary driver: {value}
Dollar change: {change}
Contribution to total change: {contribution_pct}%

Now write the sentence.
"""

STATE_NAMES = {
    "SP": "São Paulo", "RJ": "Rio de Janeiro", "MG": "Minas Gerais",
    "GO": "Goiás", "SC": "Santa Catarina", "PR": "Paraná",
    "RS": "Rio Grande do Sul", "BA": "Bahia", "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    # extend as needed
}

CAUSAL_PHRASES = [
    "due to", "because", "caused by", "as a result", "led to",
    "resulting from", "thanks to", "owing to", "driven by",
]

OFFSET_NOTE = " Other factors partially offset this change."


# ---------- formatting helpers ----------

def format_period(period: str) -> str:
    """'5/2018 vs 6/2018' -> 'May 2018 and June 2018'"""
    a_m, a_y, b_m, b_y = map(int, re.match(r"(\d+)/(\d+) vs (\d+)/(\d+)", period).groups())
    return f"{calendar.month_name[a_m]} {a_y} and {calendar.month_name[b_m]} {b_y}"


def describe_driver(driver: dict) -> str:
    dim, value = driver["dimension"], driver["value"]
    name = STATE_NAMES.get(value, value)
    if dim == "seller":
        return f"sellers based in {name} ({value})"
    if dim == "region":
        return f"customers in {name} ({value})"
    return f"the {value.replace('_', ' ')} category"


def with_offset_note(finding: dict, text: str) -> str:
    """Deterministic: added in code, never left to the model."""
    if abs(finding["primary_driver"]["contribution_pct"]) > 100:
        return text + OFFSET_NOTE
    return text


def template_narration(finding: dict) -> str:
    d = finding["primary_driver"]
    direction = "fell" if d["change"] < 0 else "rose"
    text = (
        f"Between {format_period(finding['period'])}, revenue from "
        f"{describe_driver(d)} {direction} by ${abs(d['change']):,.2f}, "
        f"which is {abs(d['contribution_pct'])}% of the total change."
    )
    return with_offset_note(finding, text)


# ---------- prompt + LLM call ----------

def build_prompt(finding: dict) -> str:
    driver = finding["primary_driver"]
    return PROMPT_TEMPLATE.format(
        period=format_period(finding["period"]),
        value=describe_driver(driver),
        change=driver["change"],
        contribution_pct=driver["contribution_pct"],
    )


def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {"num_predict": 90, "temperature": 0.2},
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


# ---------- grounding checks ----------

def _extract_numbers(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def check_no_causal_language(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in CAUSAL_PHRASES if p in lowered]


def check_grounding(finding: dict, narration_text: str) -> dict:
    driver = finding["primary_driver"]
    sources = _extract_numbers(finding["period"]) + [
        abs(driver["change"]),
        abs(driver["contribution_pct"]),
    ]
    allowed = set()
    for v in sources:
        allowed.update({round(v, 2), round(v, 1), float(round(v))})

    unexpected = [
        n for n in _extract_numbers(narration_text)
        if not any(math.isclose(n, a, abs_tol=1e-6) for a in allowed)
    ]
    causal = check_no_causal_language(narration_text)

    return {
        "passed": not unexpected and not causal,
        "unexpected_numbers": unexpected,
        "causal_phrases": causal,
    }


# ---------- orchestrator ----------

def narrate_finding(finding: dict, max_attempts: int = 2) -> dict:
    if "error" in finding:
        return {"narration": None, "error": finding["error"], "message": finding["message"]}

    prompt = build_prompt(finding)
    rejected = []
    for _ in range(max_attempts):
        text = call_ollama(prompt)
        check = check_grounding(finding, text)
        if check["passed"]:
            return {
                "narration": with_offset_note(finding, text),
                "source": "llm",
                "grounding_check": check,
            }
        rejected.append({"text": text, **check})

    return {
        "narration": template_narration(finding),
        "source": "template_fallback",
        "rejected_llm_outputs": rejected,
    }