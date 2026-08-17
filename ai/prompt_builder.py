"""Построение промптов для генерации фона."""
from __future__ import annotations

CATEGORY_PROMPTS = {
    "clothes": "soft beige studio backdrop for clothing product photo, minimal, clean catalog style",
    "shoes": "concrete podium background for sneakers product photo, minimal studio, soft shadows",
    "electronics": "dark gradient studio background for electronics product photo, premium tech style, subtle reflection",
    "bags": "marble and warm leather tones background for handbag product photo, premium minimal studio",
    "furniture": "bright scandinavian interior background for furniture product photo, daylight, minimal",
    "other": "clean neutral studio background for product photography, soft light, minimal",
}


def build_background_prompt(category: str, style: str, extra: str = "") -> str:
    base = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["other"])
    prompt = (
        f"{base}, "
        "empty scene without product, no text, no watermark, "
        "no people, no logos, square composition"
    )
    if extra:
        prompt += f", {extra}"
    return prompt