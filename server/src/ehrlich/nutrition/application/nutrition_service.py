from __future__ import annotations

from typing import TYPE_CHECKING

from ehrlich.nutrition.domain.dri import get_dri
from ehrlich.nutrition.domain.entities import AdequacyResult, NutrientRatio

if TYPE_CHECKING:
    from ehrlich.literature.domain.paper import Paper
    from ehrlich.literature.domain.repository import PaperSearchRepository
    from ehrlich.nutrition.domain.entities import (
        AdverseEvent,
        DrugInteraction,
        NutrientEntry,
        NutrientProfile,
        SupplementLabel,
    )
    from ehrlich.nutrition.domain.repository import (
        AdverseEventRepository,
        InteractionRepository,
        NutrientRepository,
        SupplementRepository,
    )

# Nutrient name -> DRI key mapping (case-insensitive substring match).
_NUTRIENT_TO_DRI: dict[str, str] = {
    "vitamin a": "vitamin_a",
    "vitamin c": "vitamin_c",
    "ascorbic acid": "vitamin_c",
    "vitamin d": "vitamin_d",
    "vitamin e": "vitamin_e",
    "vitamin k": "vitamin_k",
    "thiamin": "thiamin",
    "riboflavin": "riboflavin",
    "niacin": "niacin",
    "pantothenic acid": "pantothenic_acid",
    "vitamin b-6": "vitamin_b6",
    "vitamin b6": "vitamin_b6",
    "biotin": "biotin",
    "folate": "folate",
    "folic acid": "folate",
    "vitamin b-12": "vitamin_b12",
    "vitamin b12": "vitamin_b12",
    "calcium": "calcium",
    "iron": "iron",
    "magnesium": "magnesium",
    "zinc": "zinc",
    "copper": "copper",
    "selenium": "selenium",
    "phosphorus": "phosphorus",
    "potassium": "potassium",
    "sodium": "sodium",
    "manganese": "manganese",
    "chromium": "chromium",
    "molybdenum": "molybdenum",
    "iodine": "iodine",
    "fluoride": "fluoride",
    "choline": "choline",
    "fiber": "fiber",
    "protein": "protein",
}

# Ratio definitions: (name, numerator_terms, denominator_terms, optimal_min, optimal_max).
_RATIO_DEFS: list[tuple[str, list[str], list[str], float, float]] = [
    ("omega6_to_omega3", ["18:2", "linoleic"], ["18:3", "linolenic"], 1.0, 4.0),
    ("calcium_to_magnesium", ["calcium"], ["magnesium"], 1.5, 2.5),
    ("sodium_to_potassium", ["sodium"], ["potassium"], 0.3, 0.6),
    ("zinc_to_copper", ["zinc"], ["copper"], 8.0, 15.0),
    ("calcium_to_phosphorus", ["calcium"], ["phosphorus"], 1.0, 2.0),
    ("iron_to_copper", ["iron"], ["copper"], 10.0, 20.0),
]

# DII classification: pro-inflammatory nutrients score +1, anti-inflammatory -1.
_PRO_INFLAMMATORY = [
    "saturated",
    "trans fat",
    "trans-fat",
    "cholesterol",
    "carbohydrate",
    "protein",
    "iron",
    "vitamin b-12",
    "vitamin b12",
]
_ANTI_INFLAMMATORY = [
    "fiber",
    "omega-3",
    "omega 3",
    "18:3",
    "linolenic",
    "vitamin a",
    "vitamin c",
    "ascorbic acid",
    "vitamin d",
    "vitamin e",
    "magnesium",
    "zinc",
    "selenium",
    "folate",
    "folic acid",
]


def _match_dri_key(nutrient_name: str) -> str | None:
    lower = nutrient_name.lower()
    for term, key in _NUTRIENT_TO_DRI.items():
        if term in lower:
            return key
    return None


def _find_nutrient(nutrients: list[NutrientEntry], terms: list[str]) -> float | None:
    lower_terms = [t.lower() for t in terms]
    for n in nutrients:
        name_lower = n.name.lower()
        if any(t in name_lower for t in lower_terms):
            return n.amount
    return None


class NutritionService:
    def __init__(
        self,
        paper_repo: PaperSearchRepository,
        supplements: SupplementRepository | None = None,
        nutrients: NutrientRepository | None = None,
        adverse_events: AdverseEventRepository | None = None,
        interactions: InteractionRepository | None = None,
    ) -> None:
        self._papers = paper_repo
        self._supplements = supplements
        self._nutrients = nutrients
        self._adverse_events = adverse_events
        self._interactions = interactions

    async def search_supplement_evidence(
        self, supplement: str, outcome: str = "performance", limit: int = 8
    ) -> list[Paper]:
        query = f"{supplement} {outcome} meta-analysis systematic review"

        # Fetch extra papers to compensate for filtering
        papers = await self._papers.search(query, limit=limit * 2)

        # Filter out retracted papers
        retracted_keywords = {"[retracted]", "retracted:", "retraction"}
        non_retracted = [
            p for p in papers if not any(kw in p.title.lower() for kw in retracted_keywords)
        ]

        # Sort by study type rank, then year descending
        def get_study_type_rank(paper: Paper) -> int:
            text = (paper.title + " " + paper.abstract).lower()
            if "meta-analysis" in text:
                return 0
            if "systematic review" in text:
                return 1
            if "rct" in text or "randomized" in text:
                return 2
            return 3

        non_retracted.sort(key=lambda p: (get_study_type_rank(p), -p.year))

        return non_retracted[:limit]

    async def search_supplement_labels(
        self, ingredient: str, max_results: int = 10
    ) -> list[SupplementLabel]:
        if not self._supplements:
            return []
        return await self._supplements.search_labels(ingredient, max_results)

    async def search_nutrient_data(self, query: str, max_results: int = 5) -> list[NutrientProfile]:
        if not self._nutrients:
            return []
        return await self._nutrients.search(query, max_results)

    async def search_supplement_safety(
        self, product_name: str, max_results: int = 10
    ) -> list[AdverseEvent]:
        if not self._adverse_events:
            return []
        return await self._adverse_events.search(product_name, max_results)

    async def compare_nutrients(
        self, food_queries: list[str], max_nutrients: int = 20
    ) -> list[NutrientProfile]:
        if not self._nutrients:
            return []
        results: list[NutrientProfile] = []
        for q in food_queries:
            profiles = await self._nutrients.search(q.strip(), 1)
            if profiles:
                p = profiles[0]
                trimmed = type(p)(
                    fdc_id=p.fdc_id,
                    description=p.description,
                    brand=p.brand,
                    category=p.category,
                    nutrients=p.nutrients[:max_nutrients],
                )
                results.append(trimmed)
        return results

    def assess_nutrient_adequacy(
        self,
        nutrients: list[NutrientEntry],
        age_group: str = "adult",
        sex: str = "male",
    ) -> list[AdequacyResult]:
        results: list[AdequacyResult] = []
        for n in nutrients:
            dri_key = _match_dri_key(n.name)
            if not dri_key:
                continue
            dri = get_dri(dri_key, age_group, sex)
            if not dri:
                continue
            ref = dri.rda or dri.ai or 0.0
            if ref <= 0:
                continue
            pct_rda = round((n.amount / ref) * 100, 1)
            if pct_rda >= 100:
                status = "adequate"
            elif pct_rda >= 70:
                status = "marginal"
            else:
                status = "deficient"
            results.append(
                AdequacyResult(
                    nutrient=n.name,
                    intake=n.amount,
                    unit=n.unit,
                    rda=dri.rda or 0.0,
                    ear=dri.ear or 0.0,
                    ul=dri.ul or 0.0,
                    pct_rda=pct_rda,
                    status=status,
                )
            )
        return results

    def check_intake_safety(
        self,
        nutrients: list[NutrientEntry],
        age_group: str = "adult",
        sex: str = "male",
    ) -> list[AdequacyResult]:
        results: list[AdequacyResult] = []
        for n in nutrients:
            dri_key = _match_dri_key(n.name)
            if not dri_key:
                continue
            dri = get_dri(dri_key, age_group, sex)
            if not dri or not dri.ul or dri.ul <= 0:
                continue
            pct_ul = (n.amount / dri.ul) * 100
            if pct_ul < 80:
                continue
            ref = dri.rda or dri.ai or 0.0
            pct_rda = round((n.amount / ref) * 100, 1) if ref > 0 else 0.0
            status = "exceeds_ul" if pct_ul >= 100 else "approaching_ul"
            results.append(
                AdequacyResult(
                    nutrient=n.name,
                    intake=n.amount,
                    unit=n.unit,
                    rda=dri.rda or 0.0,
                    ear=dri.ear or 0.0,
                    ul=dri.ul,
                    pct_rda=pct_rda,
                    status=status,
                )
            )
        return results

    async def check_interactions(
        self, substance: str, max_results: int = 10
    ) -> list[DrugInteraction]:
        if not self._interactions:
            return []
        return await self._interactions.search_interactions(substance, max_results)

    def analyze_nutrient_ratios(self, nutrients: list[NutrientEntry]) -> list[NutrientRatio]:
        results: list[NutrientRatio] = []
        for name, num_terms, den_terms, opt_min, opt_max in _RATIO_DEFS:
            numerator = _find_nutrient(nutrients, num_terms)
            denominator = _find_nutrient(nutrients, den_terms)
            if numerator is None or denominator is None or denominator <= 0:
                continue
            value = round(numerator / denominator, 2)
            if opt_min <= value <= opt_max:
                status = "optimal"
            elif value < opt_min * 0.5 or value > opt_max * 2:
                status = "problematic"
            else:
                status = "suboptimal"
            results.append(
                NutrientRatio(
                    name=name,
                    value=value,
                    optimal_min=opt_min,
                    optimal_max=opt_max,
                    status=status,
                )
            )
        return results

    def compute_inflammatory_index(self, nutrients: list[NutrientEntry]) -> dict[str, object]:
        components: dict[str, float] = {}
        for n in nutrients:
            name_lower = n.name.lower()
            if any(term in name_lower for term in _PRO_INFLAMMATORY):
                components[n.name] = 1.0
            elif any(term in name_lower for term in _ANTI_INFLAMMATORY):
                components[n.name] = -1.0
        total = len(components)
        if total == 0:
            return {
                "dii_score": 0.0,
                "classification": "neutral",
                "components": {},
            }
        raw_score = sum(components.values())
        dii_score = round(raw_score / total * total, 2)
        if dii_score < -1.5:
            classification = "anti-inflammatory"
        elif dii_score > 1.5:
            classification = "pro-inflammatory"
        else:
            classification = "neutral"
        return {
            "dii_score": dii_score,
            "classification": classification,
            "components": components,
        }
