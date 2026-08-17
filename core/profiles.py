"""Профили карточек товара."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CardProfile:
    key: str
    display_name: str
    output_width: int
    output_height: int
    min_width: int
    max_width: int
    max_file_size_mb: int
    image_format: str
    jpeg_quality: int
    ai_style: str
    background_styles: tuple[str, ...]


UNIVERSAL = CardProfile(
    key="universal",
    display_name="Универсальная карточка",
    output_width=1200,
    output_height=1200,
    min_width=1000,
    max_width=2048,
    max_file_size_mb=10,
    image_format="JPEG",
    jpeg_quality=88,
    ai_style="premium product photography, studio lighting, soft shadow",
    background_styles=("studio_white", "soft_gradient", "neutral_beige"),
)

CLASSIFIEDS = CardProfile(
    key="classifieds",
    display_name="Карточка для объявлений",
    output_width=1600,
    output_height=1200,
    min_width=1000,
    max_width=2048,
    max_file_size_mb=20,
    image_format="JPEG",
    jpeg_quality=90,
    ai_style="clean marketplace listing photo, bright neutral background",
    background_styles=("white", "light_gray", "neutral_beige"),
)

SLONITA = CardProfile(
    key="slonita",
    display_name="Resale-карточка",
    output_width=1200,
    output_height=1200,
    min_width=1000,
    max_width=2048,
    max_file_size_mb=10,
    image_format="JPEG",
    jpeg_quality=88,
    ai_style="premium resale product card, realistic studio scene",
    background_styles=("studio_white", "concrete", "marble"),
)

PROFILES: dict[str, CardProfile] = {
    "universal": UNIVERSAL,
    "classifieds": CLASSIFIEDS,
    "slonita": SLONITA,
}


def get_profile(key: str) -> CardProfile:
    if key not in PROFILES:
        raise KeyError(f"Неизвестный профиль: {key}")
    return PROFILES[key]