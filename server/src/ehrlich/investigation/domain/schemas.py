"""JSON Schema definitions for Anthropic structured output responses.

Each schema is a valid JSON Schema (draft-07) dict suitable for passing to
``output_config={"format": {"type": "json_schema", "schema": SCHEMA}}``.

Only structural keywords are used (type, properties, required, additionalProperties,
items, enum).  Validation-only keywords (minimum, maximum, minItems, minLength,
pattern, format) are NOT supported by the Anthropic constrained-decoding grammar
and will cause 400 errors.  Value-range constraints are communicated via prompts.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "PICO_SCHEMA",
    "FORMULATION_SCHEMA",
    "EXPERIMENT_DESIGN_SCHEMA",
    "EVALUATION_SCHEMA",
    "SYNTHESIS_SCHEMA",
    "LITERATURE_GRADING_SCHEMA",
]

PICO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "domain": {
            "type": "array",
            "items": {"type": "string"},
        },
        "population": {"type": "string"},
        "intervention": {"type": "string"},
        "comparison": {"type": "string"},
        "outcome": {"type": "string"},
        "search_terms": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "domain",
        "population",
        "intervention",
        "comparison",
        "outcome",
        "search_terms",
    ],
    "additionalProperties": False,
}

FORMULATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "rationale": {"type": "string"},
                    "prediction": {"type": "string"},
                    "null_prediction": {"type": "string"},
                    "success_criteria": {"type": "string"},
                    "failure_criteria": {"type": "string"},
                    "scope": {"type": "string"},
                    "hypothesis_type": {"type": "string"},
                    "prior_confidence": {"type": "number"},
                },
                "required": [
                    "statement",
                    "rationale",
                    "prediction",
                    "null_prediction",
                    "success_criteria",
                    "failure_criteria",
                    "scope",
                    "hypothesis_type",
                    "prior_confidence",
                ],
                "additionalProperties": False,
            },
        },
        "negative_controls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "name": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["identifier", "name", "source"],
                "additionalProperties": False,
            },
        },
        "positive_controls": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "name": {"type": "string"},
                    "known_activity": {"type": "string"},
                    "source": {"type": "string"},
                },
                "required": ["identifier", "name", "known_activity", "source"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["hypotheses", "negative_controls", "positive_controls"],
    "additionalProperties": False,
}

EXPERIMENT_DESIGN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "tool_plan": {
            "type": "array",
            "items": {"type": "string"},
        },
        "independent_variable": {"type": "string"},
        "dependent_variable": {"type": "string"},
        "controls": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confounders": {
            "type": "array",
            "items": {"type": "string"},
        },
        "analysis_plan": {"type": "string"},
        "success_criteria": {"type": "string"},
        "failure_criteria": {"type": "string"},
        "statistical_test_plan": {
            "type": "object",
            "properties": {
                "test_type": {
                    "type": "string",
                    "enum": [
                        "run_statistical_test",
                        "run_categorical_test",
                    ],
                },
                "alpha": {"type": "number"},
                "effect_size_threshold": {"type": "string"},
                "data_source": {"type": "string"},
            },
            "required": [
                "test_type",
                "alpha",
                "effect_size_threshold",
                "data_source",
            ],
            "additionalProperties": False,
        },
    },
    "required": [
        "description",
        "tool_plan",
        "independent_variable",
        "dependent_variable",
        "controls",
        "confounders",
        "analysis_plan",
        "success_criteria",
        "failure_criteria",
    ],
    "additionalProperties": False,
}

EVALUATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["supported", "refuted", "revised"],
        },
        "confidence": {"type": "number"},
        "certainty_of_evidence": {
            "type": "string",
            "enum": ["high", "moderate", "low", "very_low"],
        },
        "evidence_convergence": {
            "type": "string",
            "enum": ["converging", "mixed", "contradictory"],
        },
        "reasoning": {"type": "string"},
        "key_evidence": {
            "type": "array",
            "items": {"type": "string"},
        },
        "revision": {"type": "string"},
        "action": {
            "type": "string",
            "enum": ["deepen", "prune", "branch"],
        },
    },
    "required": [
        "status",
        "confidence",
        "certainty_of_evidence",
        "evidence_convergence",
        "reasoning",
        "key_evidence",
        "action",
    ],
    "additionalProperties": False,
}

SYNTHESIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "identifier_type": {"type": "string"},
                    "name": {"type": "string"},
                    "rationale": {"type": "string"},
                    "rank": {"type": "integer"},
                    "priority": {"type": "integer"},
                    "scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "number"},
                            },
                            "required": ["name", "value"],
                            "additionalProperties": False,
                        },
                    },
                    "attributes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "required": ["name", "value"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "identifier",
                    "identifier_type",
                    "name",
                    "rationale",
                    "rank",
                    "priority",
                    "scores",
                    "attributes",
                ],
                "additionalProperties": False,
            },
        },
        "citations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "hypothesis_assessments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hypothesis_id": {"type": "string"},
                    "statement": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["supported", "refuted", "revised"],
                    },
                    "confidence": {"type": "number"},
                    "certainty": {
                        "type": "string",
                        "enum": ["high", "moderate", "low", "very_low"],
                    },
                    "certainty_reasoning": {"type": "string"},
                    "key_evidence": {"type": "string"},
                },
                "required": [
                    "hypothesis_id",
                    "statement",
                    "status",
                    "confidence",
                    "certainty",
                    "certainty_reasoning",
                    "key_evidence",
                ],
                "additionalProperties": False,
            },
        },
        "negative_control_summary": {"type": "string"},
        "model_validation_quality": {
            "type": "string",
            "enum": ["sufficient", "marginal", "insufficient"],
        },
        "confidence": {"type": "string"},
        "limitations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "methodology",
                            "data",
                            "scope",
                            "interpretation",
                        ],
                    },
                    "description": {"type": "string"},
                },
                "required": ["category", "description"],
                "additionalProperties": False,
            },
        },
        "knowledge_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "gap_type": {
                        "type": "string",
                        "enum": [
                            "evidence",
                            "quality",
                            "consistency",
                            "scope",
                            "temporal",
                        ],
                    },
                    "description": {"type": "string"},
                },
                "required": ["gap_type", "description"],
                "additionalProperties": False,
            },
        },
        "follow_up_experiments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "impact": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"],
                    },
                    "type": {
                        "type": "string",
                        "enum": ["computational", "experimental"],
                    },
                },
                "required": ["description", "impact", "type"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "summary",
        "candidates",
        "citations",
        "hypothesis_assessments",
        "negative_control_summary",
        "model_validation_quality",
        "confidence",
        "limitations",
        "knowledge_gaps",
        "follow_up_experiments",
    ],
    "additionalProperties": False,
}

LITERATURE_GRADING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "evidence_grade": {
            "type": "string",
            "enum": ["high", "moderate", "low", "very_low"],
        },
        "reasoning": {"type": "string"},
        "assessment": {"type": "string"},
    },
    "required": ["evidence_grade", "reasoning", "assessment"],
    "additionalProperties": False,
}
