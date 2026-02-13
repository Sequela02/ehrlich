"""Nutrition Science tools for the investigation engine.

10 tools for evidence-based nutrition research: supplement evidence
search, supplement label lookup, nutrient data search, supplement
safety monitoring, nutrient comparison, DRI adequacy assessment,
intake safety checks, drug-nutrient interactions, nutrient ratio
analysis, and dietary inflammatory index computation.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient
from ehrlich.nutrition.application.nutrition_service import NutritionService
from ehrlich.nutrition.infrastructure.dsld_client import DSLDClient
from ehrlich.nutrition.infrastructure.fooddata_client import FoodDataClient
from ehrlich.nutrition.infrastructure.openfda_client import OpenFDAClient
from ehrlich.nutrition.infrastructure.rxnav_client import RxNavClient

_client = SemanticScholarClient()
_dsld_client = DSLDClient()
_food_client = FoodDataClient()
_fda_client = OpenFDAClient()
_rxnav_client = RxNavClient()
_service = NutritionService(
    paper_repo=_client,
    supplements=_dsld_client,
    nutrients=_food_client,
    adverse_events=_fda_client,
    interactions=_rxnav_client,
)


async def search_supplement_evidence(
    supplement: str,
    outcome: str = "performance",
    limit: int = 8,
) -> str:
    """Search for evidence on supplement efficacy for athletic performance.

    Queries Semantic Scholar for meta-analyses and systematic reviews
    on supplement effects.

    Args:
        supplement: Supplement name (e.g. 'creatine', 'caffeine', 'beta-alanine')
        outcome: Performance outcome (e.g. 'strength', 'endurance', 'recovery')
        limit: Maximum papers to return (default: 8)
    """
    papers = await _service.search_supplement_evidence(supplement, outcome, limit)

    results = []
    for p in papers:
        results.append(
            {
                "title": p.title,
                "authors": ", ".join(p.authors),
                "year": p.year,
                "doi": p.doi,
                "abstract": p.abstract[:500] if p.abstract else "",
                "citations": p.citations,
            }
        )

    return json.dumps(
        {
            "supplement": supplement,
            "outcome": outcome,
            "count": len(results),
            "papers": results,
        }
    )


async def search_supplement_labels(
    ingredient: str,
    max_results: int = 10,
) -> str:
    """Search NIH DSLD for supplement products containing an ingredient.

    Queries the NIH Dietary Supplement Label Database for commercial
    supplement products. Returns product name, brand, ingredient list
    with amounts and daily value percentages, and serving size.

    Args:
        ingredient: Ingredient name (e.g. 'creatine', 'caffeine', 'vitamin D')
        max_results: Maximum number of products to return (default: 10)
    """
    labels = await _service.search_supplement_labels(ingredient, max_results)
    return json.dumps(
        {
            "ingredient": ingredient,
            "count": len(labels),
            "products": [
                {
                    "report_id": lb.report_id,
                    "product_name": lb.product_name,
                    "brand": lb.brand,
                    "serving_size": lb.serving_size,
                    "ingredients": [
                        {
                            "name": ing.name,
                            "amount": ing.amount,
                            "unit": ing.unit,
                            "daily_value_pct": ing.daily_value_pct,
                        }
                        for ing in lb.ingredients
                    ],
                }
                for lb in labels
            ],
        }
    )


async def search_nutrient_data(
    food_query: str,
    max_results: int = 5,
) -> str:
    """Search USDA FoodData Central for nutrient profiles.

    Queries the USDA FoodData Central database for food nutrient
    information including macronutrients, vitamins, and minerals.

    Args:
        food_query: Food search query (e.g. 'chicken breast', 'whey protein', 'salmon')
        max_results: Maximum number of food items to return (default: 5)
    """
    profiles = await _service.search_nutrient_data(food_query, max_results)
    return json.dumps(
        {
            "query": food_query,
            "count": len(profiles),
            "foods": [
                {
                    "fdc_id": p.fdc_id,
                    "description": p.description,
                    "brand": p.brand,
                    "category": p.category,
                    "nutrients": [
                        {
                            "name": n.name,
                            "amount": n.amount,
                            "unit": n.unit,
                            "nutrient_number": n.nutrient_number,
                        }
                        for n in p.nutrients
                    ],
                }
                for p in profiles
            ],
        }
    )


async def search_supplement_safety(
    product_name: str,
    max_results: int = 10,
) -> str:
    """Search OpenFDA CAERS for supplement adverse event reports.

    Queries the FDA Center for Food Safety adverse event reporting
    system for supplement-related adverse events. Returns report date,
    products involved, reactions, outcomes, and consumer demographics.

    Args:
        product_name: Supplement product name (e.g. 'creatine', 'pre-workout', 'fat burner')
        max_results: Maximum number of reports to return (default: 10)
    """
    events = await _service.search_supplement_safety(product_name, max_results)
    return json.dumps(
        {
            "product_name": product_name,
            "count": len(events),
            "adverse_events": [
                {
                    "report_id": e.report_id,
                    "date": e.date,
                    "products": list(e.products),
                    "reactions": list(e.reactions),
                    "outcomes": list(e.outcomes),
                    "consumer_age": e.consumer_age,
                    "consumer_gender": e.consumer_gender,
                }
                for e in events
            ],
        }
    )


async def compare_nutrients(
    food_queries: str,
    max_nutrients: int = 20,
) -> str:
    """Compare nutrient profiles of multiple foods side by side.

    Searches USDA FoodData Central for each food and returns nutrient
    profiles for comparison. Useful for comparing protein sources,
    vitamin content, or mineral density across foods.

    Args:
        food_queries: Comma-separated food names (e.g. 'chicken breast, salmon, tofu')
        max_nutrients: Maximum nutrients per food (default: 20)
    """
    queries = [q.strip() for q in food_queries.split(",") if q.strip()]
    profiles = await _service.compare_nutrients(queries, max_nutrients)
    return json.dumps(
        {
            "queries": queries,
            "count": len(profiles),
            "foods": [
                {
                    "fdc_id": p.fdc_id,
                    "description": p.description,
                    "brand": p.brand,
                    "category": p.category,
                    "nutrients": [
                        {
                            "name": n.name,
                            "amount": n.amount,
                            "unit": n.unit,
                            "nutrient_number": n.nutrient_number,
                        }
                        for n in p.nutrients
                    ],
                }
                for p in profiles
            ],
        }
    )


async def assess_nutrient_adequacy(
    food_query: str,
    age_group: str = "adult",
    sex: str = "male",
) -> str:
    """Assess nutrient adequacy of a food against DRI recommendations.

    Searches for a food in USDA FoodData Central, then compares each
    nutrient against Dietary Reference Intake (DRI) values to determine
    adequacy status (adequate, marginal, or deficient).

    Args:
        food_query: Food to assess (e.g. 'spinach', 'beef liver', 'milk')
        age_group: Age group for DRI lookup (infant/child/teen/adult/elderly/pregnant/lactating)
        sex: Biological sex for DRI lookup (male/female)
    """
    profiles = await _service.search_nutrient_data(food_query, 1)
    if not profiles:
        return json.dumps({"food_query": food_query, "count": 0, "assessments": []})
    nutrients = list(profiles[0].nutrients)
    assessments = _service.assess_nutrient_adequacy(nutrients, age_group, sex)
    return json.dumps(
        {
            "food_query": food_query,
            "food": profiles[0].description,
            "age_group": age_group,
            "sex": sex,
            "count": len(assessments),
            "assessments": [asdict(a) for a in assessments],
        }
    )


async def check_intake_safety(
    food_query: str,
    age_group: str = "adult",
    sex: str = "male",
) -> str:
    """Check if nutrient intake from a food approaches or exceeds safe upper limits.

    Searches for a food in USDA FoodData Central, then checks each
    nutrient against Tolerable Upper Intake Levels (UL). Returns only
    nutrients at 80%+ of UL or exceeding UL.

    Args:
        food_query: Food to check (e.g. 'beef liver', 'brazil nuts', 'fortified cereal')
        age_group: Age group for UL lookup (infant/child/teen/adult/elderly/pregnant/lactating)
        sex: Biological sex for UL lookup (male/female)
    """
    profiles = await _service.search_nutrient_data(food_query, 1)
    if not profiles:
        return json.dumps({"food_query": food_query, "count": 0, "warnings": []})
    nutrients = list(profiles[0].nutrients)
    warnings = _service.check_intake_safety(nutrients, age_group, sex)
    return json.dumps(
        {
            "food_query": food_query,
            "food": profiles[0].description,
            "age_group": age_group,
            "sex": sex,
            "count": len(warnings),
            "warnings": [asdict(w) for w in warnings],
        }
    )


async def check_interactions(
    substance: str,
    max_results: int = 10,
) -> str:
    """Check drug-nutrient or drug-supplement interactions via RxNav.

    Queries the NIH RxNav interaction API for known interactions
    between a substance and other drugs or supplements.

    Args:
        substance: Drug or supplement name (e.g. 'warfarin', 'metformin', 'St. John\\'s Wort')
        max_results: Maximum interactions to return (default: 10)
    """
    interactions = await _service.check_interactions(substance, max_results)
    return json.dumps(
        {
            "substance": substance,
            "count": len(interactions),
            "interactions": [asdict(i) for i in interactions],
        }
    )


async def analyze_nutrient_ratios(
    food_query: str,
) -> str:
    """Analyze key nutrient ratios in a food for nutritional balance.

    Searches for a food in USDA FoodData Central, then computes 6
    clinically relevant nutrient ratios: omega-6:omega-3, Ca:Mg,
    Na:K, Zn:Cu, Ca:P, and Fe:Cu. Reports optimal ranges and status.

    Args:
        food_query: Food to analyze (e.g. 'salmon', 'walnuts', 'beef')
    """
    profiles = await _service.search_nutrient_data(food_query, 1)
    if not profiles:
        return json.dumps({"food_query": food_query, "count": 0, "ratios": []})
    nutrients = list(profiles[0].nutrients)
    ratios = _service.analyze_nutrient_ratios(nutrients)
    return json.dumps(
        {
            "food_query": food_query,
            "food": profiles[0].description,
            "count": len(ratios),
            "ratios": [asdict(r) for r in ratios],
        }
    )


async def compute_inflammatory_index(
    food_query: str,
) -> str:
    """Compute simplified Dietary Inflammatory Index (DII) for a food.

    Searches for a food in USDA FoodData Central, then scores each
    nutrient as pro-inflammatory (+1) or anti-inflammatory (-1) based
    on the DII framework. Returns total score and classification.

    Args:
        food_query: Food to score (e.g. 'salmon', 'bacon', 'kale')
    """
    profiles = await _service.search_nutrient_data(food_query, 1)
    if not profiles:
        return json.dumps(
            {
                "food_query": food_query,
                "dii_score": 0.0,
                "classification": "neutral",
                "components": {},
            }
        )
    nutrients = list(profiles[0].nutrients)
    result = _service.compute_inflammatory_index(nutrients)
    return json.dumps(
        {
            "food_query": food_query,
            "food": profiles[0].description,
            **result,
        }
    )
