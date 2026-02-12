"""Molecular Science domain configuration."""

from __future__ import annotations

from ehrlich.investigation.domain.domain_config import DomainConfig, ScoreDefinition

MOLECULAR_SCIENCE = DomainConfig(
    name="molecular_science",
    display_name="Molecular Science",
    identifier_type="smiles",
    identifier_label="SMILES",
    candidate_label="Candidate Molecules",
    tool_tags=frozenset(
        {
            "chemistry",
            "analysis",
            "prediction",
            "simulation",
            "literature",
        }
    ),
    score_definitions=(
        ScoreDefinition(
            key="prediction_score",
            label="Prediction",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.7,
            ok_threshold=0.4,
        ),
        ScoreDefinition(
            key="docking_score",
            label="Docking",
            format_spec=".1f",
            higher_is_better=False,
            good_threshold=-8.0,
            ok_threshold=-6.0,
        ),
        ScoreDefinition(
            key="admet_score",
            label="ADMET",
            format_spec=".2f",
            higher_is_better=True,
            good_threshold=0.7,
            ok_threshold=0.4,
        ),
    ),
    attribute_keys=("resistance_risk",),
    negative_control_threshold=0.5,
    visualization_type="molecular",
    hypothesis_types=(
        "mechanistic",
        "structural",
        "pharmacological",
        "toxicological",
    ),
    valid_domain_categories=(
        "antimicrobial",
        "neurodegenerative",
        "oncology",
        "environmental",
        "cardiovascular",
        "metabolic",
        "immunology",
    ),
    template_prompts=(
        {
            "title": "MRSA Drug Discovery",
            "description": "Find novel antimicrobial compounds effective against MRSA",
            "prompt": "Find novel antimicrobial compounds effective against "
            "methicillin-resistant Staphylococcus aureus (MRSA). Focus on "
            "beta-lactamase inhibitors and PBP2a binding agents. Evaluate "
            "resistance risk and ADMET profiles.",
            "icon": "shield",
        },
        {
            "title": "Alzheimer's BACE1 Inhibitors",
            "description": "Identify BACE1 inhibitors for Alzheimer's disease",
            "prompt": "Identify novel BACE1 (beta-secretase 1) inhibitors for "
            "Alzheimer's disease. Focus on compounds with blood-brain barrier "
            "penetration potential (TPSA < 90, MW < 500) and selectivity over "
            "BACE2. Evaluate using docking against known BACE1 crystal structures.",
            "icon": "brain",
        },
        {
            "title": "Environmental Toxicity",
            "description": "Assess environmental toxicity of industrial compounds",
            "prompt": "Assess the environmental toxicity and ecological risk of "
            "common PFAS (per- and polyfluoroalkyl substances). Evaluate "
            "bioaccumulation potential, aquatic toxicity, and persistence using "
            "EPA CompTox data. Compare with known safe alternatives.",
            "icon": "leaf",
        },
        {
            "title": "Oncology Drug Candidates",
            "description": "Discover kinase inhibitors for targeted cancer therapy",
            "prompt": "Discover novel kinase inhibitors targeting EGFR mutations "
            "(T790M, L858R) for non-small cell lung cancer. Focus on third-gen "
            "inhibitors with selectivity over wild-type EGFR. Evaluate drug-likeness "
            "and compare with known inhibitors (osimertinib, rociletinib).",
            "icon": "target",
        },
    ),
    director_examples="""\
<examples>
<example>
<research_question>
Find novel beta-lactamase inhibitors to combat MRSA resistance
</research_question>
<literature_findings>
- Beta-lactamase enzymes (Class A, C, D) hydrolyze beta-lactam \
ring; PBP2a confers methicillin resistance in MRSA
- Avibactam (diazabicyclooctane) inhibits Class A/C with Ki \
~1 nM; clavulanate is first-gen but weak vs Class C
- Boronic acid scaffolds show broad-spectrum inhibition; \
vaborbactam approved 2017
</literature_findings>
<output>
{
  "hypotheses": [
    {
      "statement": "Diazabicyclooctane derivatives with C2 \
sulfonamide substituents will show dual Class A/C beta-lactamase \
inhibition with Ki below 50 nM",
      "rationale": "Avibactam's DBO core achieves covalent \
reversible inhibition; C2 sulfonamide groups enhance Ser70 binding",
      "prediction": "Docking < -7 kcal/mol for 3+ DBO derivatives; \
ML model predicts Ki < 50 nM",
      "null_prediction": "DBO derivatives show no preferential \
binding vs controls; Ki > 500 nM",
      "success_criteria": ">=3 candidates with docking < -7 AND Ki < 100 nM",
      "failure_criteria": "<2 compounds meet threshold OR all fail ADMET",
      "scope": "MRSA beta-lactamases Class A/C; MW < 500",
      "hypothesis_type": "mechanistic",
      "prior_confidence": 0.7
    }
  ],
  "negative_controls": [
    {"identifier": "CC(=O)Oc1ccccc1C(=O)O", "name": "Aspirin", \
"source": "Non-antimicrobial NSAID"}
  ],
  "positive_controls": [
    {"identifier": "CC1CC2(CC(=O)N1)C(=O)N(S2(=O)=O)O", "name": "Avibactam", \
"known_activity": "Ki ~1 nM vs Class A beta-lactamase", \
"source": "FDA-approved BLI, gold standard"}
  ]
}
</output>
</example>

<example>
<research_question>
Identify BACE1 inhibitors for Alzheimer's disease treatment
</research_question>
<literature_findings>
- BACE1 cleaves APP to produce amyloid-beta; key target for Alzheimer's
- Verubecestat reached Phase III but failed due to toxicity
- Macrocyclic BACE1 inhibitors show improved selectivity over BACE2
</literature_findings>
<output>
{
  "hypotheses": [
    {
      "statement": "Macrocyclic aminohydantoin derivatives with \
12-14 membered rings will achieve BACE1 IC50 below 10 nM while \
maintaining TPSA below 90 for BBB penetration",
      "rationale": "Macrocyclization constrains pharmacophore into \
bioactive conformation, reducing entropic penalty",
      "prediction": "Docking < -8 kcal/mol; TPSA < 90 and MW < 500",
      "null_prediction": "No binding improvement over linear analogs; TPSA > 100",
      "success_criteria": ">=2 candidates with docking < -8 AND TPSA < 90",
      "failure_criteria": "No macrocycles achieve docking < -6 OR all exceed MW 600",
      "scope": "BACE1 aspartyl protease; CNS-penetrant",
      "hypothesis_type": "structural",
      "prior_confidence": 0.6
    }
  ],
  "negative_controls": [
    {"identifier": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "name": "Caffeine", \
"source": "Zero BACE1 activity in published screens"}
  ],
  "positive_controls": [
    {"identifier": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)N2CCC(CC2)N3C(=O)N(C3=O)C", \
"name": "Verubecestat", "known_activity": "IC50 = 2.2 nM vs BACE1", \
"source": "Reached Phase III, confirmed potent inhibitor"}
  ]
}
</output>
</example>
</examples>""",
    experiment_examples="""\
<examples>
<example>
<hypothesis>DBO derivatives inhibit Class A/C beta-lactamases \
with Ki below 50 nM</hypothesis>
<output>
{
  "description": "Search ChEMBL for DBO-scaffold compounds, \
train model, dock top predictions against beta-lactamase",
  "tool_plan": ["search_bioactivity", "compute_descriptors", \
"train_model", "predict_candidates", "dock_against_target"],
  "independent_variable": "C2 substituent pattern on DBO scaffold",
  "dependent_variable": "Predicted Ki (nM) and docking score (kcal/mol)",
  "controls": ["positive: Avibactam (Ki ~1 nM)", \
"negative: Aspirin (non-antimicrobial)"],
  "confounders": ["ChEMBL dataset bias toward published actives", \
"Docking may not capture covalent binding"],
  "analysis_plan": "Primary: model AUC >0.7; secondary: docking \
<-7 kcal/mol for top 3; expect N>=50 training compounds",
  "success_criteria": ">=3 DBO derivatives with P>0.7 AND docking <-7",
  "failure_criteria": "<2 compounds meet thresholds OR AUC <0.7"
}
</output>
</example>
</examples>

<tool_examples>
Example: Docking a compound against a protein target
1. search_protein_targets(query="BACE1 human", limit=3)
2. get_protein_annotation(uniprot_id="P56817")
3. dock_against_target(smiles="CC1=CC(=O)...", target_id="4ivt")

Example: Training a predictive model
1. search_bioactivity(target="beta-lactamase", organism="S. aureus")
2. train_model(smiles_list=[...], activity_list=[...], model_type="xgboost")
3. predict_candidates(smiles_list=[...], model_id="model_xyz")

Example: Identifying disease-target associations
1. search_disease_targets(disease="Alzheimer", limit=10)
2. get_protein_annotation(uniprot_id="P56817")
3. search_bioactivity(target="BACE1", assay_type="IC50")
</tool_examples>""",
    synthesis_scoring_instructions="""\
Scoring fields for candidates:
- prediction_score: ML model probability (0-1)
- docking_score: binding affinity in kcal/mol (negative = better)
- admet_score: overall drug-likeness (0-1)
Attributes:
- resistance_risk: mutation risk ("low", "medium", "high")
Use 0.0 or "unknown" if a score was not computed.""",
)
