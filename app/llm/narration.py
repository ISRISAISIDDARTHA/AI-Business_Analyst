import requests
import json
import math
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

PROMPT_TEMPLATE = """You are a business analyst assistant. You will be given a precomputed, 
verified finding about a change in revenue. Your only job is to explain 
this finding in 1-2 clear, plain-English sentences.

STRICT RULES:
- Only use the numbers and facts given below. Do not estimate, guess, or 
  add any numbers not explicitly provided.
- Do not mention any category, region, or seller that is not named below.
- Do not speculate about causes beyond what the data shows.
- If contribution_pct is over 100%, note that other factors partially 
  offset this change.
- Write in a neutral, professional tone.
- Use this sentence shape: "Revenue from [the driver] fell or rose by $X, which
  accounts for Y% of the total change between the two periods."
- NEVER use causal words such as "due to", "because", "caused by", "as a
  result of", "led to", or "driven by".

FINDING:
Comparison period: {period}
Primary driver dimension: {dimension}
Primary driver value: {value}
Dollar change: {change}
Contribution to total change: {contribution_pct}%

Now write the explanation.
"""


def build_prompt(finding: dict) -> str:
    """Fills the prompt template with a real finding from find_root_cause()."""
    driver = finding["primary_driver"]
    return PROMPT_TEMPLATE.format(
        period=finding["period"],
        dimension=driver["dimension"],
        value=describe_driver(driver),
        change=driver["change"],
        contribution_pct=driver["contribution_pct"],
    )


def call_ollama(prompt: str) -> str:
    """Sends the prompt to the local Ollama API and returns the generated text."""
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

def _extract_numbers(text: str) -> list[float]:
    # Whole numbers only: "133,228.05" -> 133228.05, "102.8" -> 102.8
    return [float(m.replace(",", "")) for m in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]

def check_grounding(finding: dict, narration_text: str) -> dict:
    driver = finding["primary_driver"]
    sources = _extract_numbers(finding["period"]) + [
        abs(driver["change"]),
        abs(driver["contribution_pct"]),
    ]
    # Accept exact values plus 1-decimal and whole-number roundings
    allowed = set()
    for v in sources:
        allowed.update({round(v, 2), round(v, 1), float(round(v))})

    unexpected = [
        n for n in _extract_numbers(narration_text)
        if not any(math.isclose(n, a, abs_tol=1e-6) for a in allowed)
    ]
    causal = check_no_causal_language(narration_text)
    missing_offset = (
    abs(driver["contribution_pct"]) > 100
    and "offset" not in narration_text.lower())
    
    return {
        "passed": not unexpected and not causal and not missing_offset,
        "unexpected_numbers": unexpected,
        "causal_phrases": causal,
    }

def narrate_finding(finding: dict, max_attempts: int = 2) -> dict:
    if "error" in finding:
        return {"narration": None, "error": finding["error"], "message": finding["message"]}

    prompt = build_prompt(finding)
    rejected = []
    for _ in range(max_attempts):
        text = call_ollama(prompt)
        check = check_grounding(finding, text)
        if check["passed"]:
            return {"narration": text, "source": "llm", "grounding_check": check}
        rejected.append({"text": text, "unexpected_numbers": check["unexpected_numbers"]})

    return {
        "narration": template_narration(finding),
        "source": "template_fallback",
        "rejected_llm_outputs": rejected,
    }

STATE_NAMES = {
    "SP": "São Paulo", "RJ": "Rio de Janeiro", "MG": "Minas Gerais",
    "GO": "Goiás", "SC": "Santa Catarina", "PR": "Paraná",
    "RS": "Rio Grande do Sul", "BA": "Bahia", "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    # extend as needed
}

def describe_driver(driver: dict) -> str:
    dim, value = driver["dimension"], driver["value"]
    name = STATE_NAMES.get(value, value)
    if dim == "seller":
        return f"sellers based in {name} ({value})"
    if dim == "region":
        return f"customers in {name} ({value})"
    return f"the {value.replace('_', ' ')} category"

def template_narration(finding: dict) -> str:
    d = finding["primary_driver"]
    direction = "fell" if d["change"] < 0 else "rose"
    text = (
        f"Between {finding['period']}, revenue from {describe_driver(d)} "
        f"{direction} by ${abs(d['change']):,.2f}, which is "
        f"{abs(d['contribution_pct'])}% of the total change."
    )
    if abs(d["contribution_pct"]) > 100:
        text += " Other factors partially offset this change."
    return text
CAUSAL_PHRASES = ["due to", "because", "caused by", "as a result",
                  "led to", "resulting from", "thanks to", "owing to"]

def check_no_causal_language(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in CAUSAL_PHRASES if p in lowered]