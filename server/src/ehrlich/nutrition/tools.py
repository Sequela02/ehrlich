"""Nutrition Science tools for the investigation engine.

4 tools for evidence-based nutrition research: supplement evidence
search, supplement label lookup, nutrient data search, and
supplement safety monitoring.
"""

from __future__ import annotations

import json

from ehrlich.literature.infrastructure.semantic_scholar import SemanticScholarClient
from ehrlich.nutrition.application.nutrition_service import NutritionService
from ehrlich.nutrition.infrastructure.dsld_client import DSLDClient
from ehrlich.nutrition.infrastructure.fooddata_client import FoodDataClient
from ehrlich.nutrition.infrastructure.openfda_client import OpenFDAClient

_client = SemanticScholarClient()
_dsld_client = DSLDClient()
_food_client = FoodDataClient()
_fda_client = OpenFDAClient()
_service = NutritionService(
    paper_repo=_client,
    supplements=_dsld_client,
    nutrients=_food_client,
    adverse_events=_fda_client,
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
