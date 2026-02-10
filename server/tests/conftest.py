import pytest

from ehrlich.kernel.types import SMILES


@pytest.fixture
def aspirin_smiles() -> SMILES:
    return SMILES("CC(=O)Oc1ccccc1C(=O)O")


@pytest.fixture
def penicillin_smiles() -> SMILES:
    return SMILES("CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)Cc3ccccc3)C(=O)O)C")


@pytest.fixture
def invalid_smiles() -> str:
    return "not_a_valid_smiles!!!"


@pytest.fixture
def sample_papers() -> list[dict[str, object]]:
    return [
        {
            "title": "Antimicrobial peptides: an emerging category of therapeutic agents",
            "authors": ["Bahar", "Ren"],
            "year": 2013,
            "doi": "10.2174/1389450113666120726002205",
            "abstract": "Review of antimicrobial peptides as therapeutic agents.",
        }
    ]
