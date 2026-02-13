from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngredientEntry:
    name: str
    amount: str
    unit: str
    daily_value_pct: float | None = None


@dataclass(frozen=True)
class SupplementLabel:
    report_id: str
    product_name: str
    brand: str
    ingredients: tuple[IngredientEntry, ...]
    serving_size: str


@dataclass(frozen=True)
class NutrientEntry:
    name: str
    amount: float
    unit: str
    nutrient_number: str


@dataclass(frozen=True)
class NutrientProfile:
    fdc_id: int
    description: str
    brand: str
    category: str
    nutrients: tuple[NutrientEntry, ...]


@dataclass(frozen=True)
class AdverseEvent:
    report_id: str
    date: str
    products: tuple[str, ...]
    reactions: tuple[str, ...]
    outcomes: tuple[str, ...]
    consumer_age: str
    consumer_gender: str


@dataclass(frozen=True)
class DrugInteraction:
    drug_a: str
    drug_b: str
    severity: str
    description: str
    source: str


@dataclass(frozen=True)
class NutrientRatio:
    name: str
    value: float
    optimal_min: float
    optimal_max: float
    status: str


@dataclass(frozen=True)
class AdequacyResult:
    nutrient: str
    intake: float
    unit: str
    rda: float
    ear: float
    ul: float
    pct_rda: float
    status: str


@dataclass(frozen=True)
class InteractionResult:
    interactions: tuple[DrugInteraction, ...]
    query_substance: str
