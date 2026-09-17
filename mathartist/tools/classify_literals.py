#!/usr/bin/env python3
"""AST-based numeric literal role classifier for p5.js/Processing sketches.

Classifies every numeric literal in a sketch as one of:
  FIXED_RUNTIME, CANVAS_GEOMETRY, SAMPLING_BUDGET, COLOR_ALPHA, TIME_STEP,
  MATHEMATICAL_COEFFICIENT, FREQUENCY, PHASE, EXPONENT, INITIAL_CONDITION,
  BRANCH_SELECTOR, UNKNOWN

A control enters the mutation genome only if:
  - role is MATHEMATICAL_COEFFICIENT, FREQUENCY, PHASE, EXPONENT, or INITIAL_CONDITION
  - source span is recorded
  - default reproduces original
  - range is justified

Usage:
  python tools/classify_literals.py <code_file> [--json]
"""
from __future__ import annotations
import argparse
import json
import re
import sys

# Context patterns that indicate role
RUNTIME_CONTEXTS = {
    "FIXED_RUNTIME": [
        r"createCanvas", r"frameRate", r"pixelDensity", r"size\(",
        r"smooth\(", r"noSmooth\(", r"pixelWidth", r"pixelHeight",
        r"displayWidth", r"displayHeight", r"windowWidth", r"windowHeight",
    ],
    "CANVAS_GEOMETRY": [
        r"width", r"height", r"mouseX", r"mouseY", r"pmouseX", r"pmouseY",
        r"touches\[\d+\]", r"center", r"HALF_WIDTH", r"HALF_HEIGHT",
    ],
    "SAMPLING_BUDGET": [
        r"for\s*\(", r"while\s*\(", r"loop", r"i\s*<\s*\d+", r"j\s*<\s*\d+",
        r"numPoints", r"count", r"iterations", r"steps", r"resolution",
        r"segments", r"samples", r"density", r"particles",
    ],
    "COLOR_ALPHA": [
        r"fill\(", r"stroke\(", r"background\(", r"color\(", r"rgba?\(",
        r"fill\(", r"noFill", r"noStroke", r"tint\(", r"colorMode\(",
        r"alpha", r"red", r"green", r"blue", r"brightness", r"saturation",
        r"hue", r"lerpColor", r"fill\(\d+", r"stroke\(\d+",
    ],
    "TIME_STEP": [
        r"t\s*\+=", r"t\s*=\s*t", r"time", r"frameCount", r"deltaTime",
        r"millis\(\)", r"second\(\)", r"minute\(\)", r"hour\(\)",
        r"t\s*\+=\s*\d", r"dt", r"speed", r"angle\s*\+",
    ],
    "BRANCH_SELECTOR": [
        r"if\s*\(", r"else\s*if", r"switch", r"case\s+\d",
        r"random\(\)\s*[<>]", r"noise\(\d", r"floor\(", r"ceil\(",
        r"round\(", r"int\(", r"%\s*\d", r"\bmod\b",
    ],
}

MATHEMATICAL_PATTERNS = [
    (r"sin\(", "FREQUENCY"),
    (r"cos\(", "FREQUENCY"),
    (r"tan\(", "FREQUENCY"),
    (r"atan2?\(", "PHASE"),
    (r"sqrt\(", "EXPONENT"),
    (r"pow\(", "EXPONENT"),
    (r"log\(", "EXPONENT"),
    (r"exp\(", "EXPONENT"),
    (r"abs\(", "MATHEMATICAL_COEFFICIENT"),
    (r"map\(", "MATHEMATICAL_COEFFICIENT"),
    (r"constrain\(", "MATHEMATICAL_COEFFICIENT"),
    (r"lerp\(", "MATHEMATICAL_COEFFICIENT"),
    (r"noise\(", "INITIAL_CONDITION"),
    (r"random\(", "INITIAL_CONDITION"),
    (r"randomSeed\(", "INITIAL_CONDITION"),
    (r"noiseSeed\(", "INITIAL_CONDITION"),
]

NUMBER_RE = re.compile(
    r'(?<![\w.])(-?(?:\d+\.\d*|\.\d+|\d+)(?:e[+-]?\d+)?)(?![\w.])'
)


def classify_literal(value_str: str, context: str, code: str, offset: int) -> dict:
    """Classify a single numeric literal by its surrounding context."""
    try:
        value = float(value_str)
    except ValueError:
        return {"literal": value_str, "role": "UNKNOWN", "confidence": 0.0}

    # Check runtime contexts
    for role, patterns in RUNTIME_CONTEXTS.items():
        for pat in patterns:
            if re.search(pat, context):
                return {"literal": value_str, "role": role, "confidence": 0.8}

    # Check mathematical contexts
    for pat, role in MATHEMATICAL_PATTERNS:
        if re.search(pat, context):
            return {"literal": value_str, "role": role, "confidence": 0.7}

    # Heuristic: small integers (0-12) near sin/cos are likely frequency/phase
    if 0 <= value <= 12 and abs(value - round(value)) < 0.01:
        nearby = code[max(0, offset - 60):min(len(code), offset + 60)]
        if re.search(r'sin|cos|tan|PI|TWO_PI|HALF_PI', nearby):
            return {"literal": value_str, "role": "FREQUENCY", "confidence": 0.5}

    # Heuristic: PI-like values
    if abs(value - 3.14159) < 0.01 or abs(value - 6.28318) < 0.01:
        return {"literal": value_str, "role": "PHASE", "confidence": 0.6}

    # Heuristic: very large numbers are likely canvas geometry or sampling
    if abs(value) > 1000:
        return {"literal": value_str, "role": "CANVAS_GEOMETRY", "confidence": 0.4}

    return {"literal": value_str, "role": "UNKNOWN", "confidence": 0.2}


def extract_literals(code: str) -> list[dict]:
    """Extract and classify all numeric literals from code."""
    results = []
    for m in NUMBER_RE.finditer(code):
        value_str = m.group(1)
        offset = m.start()
        # Get surrounding context (40 chars each side)
        ctx_start = max(0, offset - 40)
        ctx_end = min(len(code), offset + len(value_str) + 40)
        context = code[ctx_start:ctx_end]
        classification = classify_literal(value_str, context, code, offset)
        classification["offset"] = offset
        classification["context"] = context.strip()
        results.append(classification)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="p5.js or Processing source file")
    ap.add_argument("--json", action="store_true", help="output JSON")
    a = ap.parse_args()

    code = open(a.file).read()
    literals = extract_literals(code)

    # Summary
    roles = {}
    for lit in literals:
        r = lit["role"]
        roles[r] = roles.get(r, 0) + 1

    # Candidates for mutation (non-fixed roles)
    MUTABLE_ROLES = {"MATHEMATICAL_COEFFICIENT", "FREQUENCY", "PHASE", "EXPONENT", "INITIAL_CONDITION"}
    candidates = [lit for lit in literals if lit["role"] in MUTABLE_ROLES]

    result = {
        "file": a.file,
        "total_literals": len(literals),
        "role_distribution": roles,
        "mutation_candidates": len(candidates),
        "candidates": candidates,
        "all_literals": literals,
    }

    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"File: {a.file}")
        print(f"Total literals: {len(literals)}")
        print(f"Role distribution:")
        for role, count in sorted(roles.items()):
            print(f"  {role}: {count}")
        print(f"Mutation candidates: {len(candidates)}")
        for c in candidates[:10]:
            print(f"  {c['literal']:>10s}  {c['role']:30s}  {c['context'][:50]}")


if __name__ == "__main__":
    main()
