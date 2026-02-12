from ehrlich.investigation.domain.events import PositiveControlRecorded
from ehrlich.investigation.domain.investigation import Investigation
from ehrlich.investigation.domain.negative_control import NegativeControl
from ehrlich.investigation.domain.positive_control import PositiveControl


class TestPositiveControl:
    def test_creation_with_defaults(self) -> None:
        pc = PositiveControl(identifier="CC(=O)O")
        assert pc.identifier == "CC(=O)O"
        assert pc.identifier_type == ""
        assert pc.name == ""
        assert pc.known_activity == ""
        assert pc.source == ""
        assert pc.score == 0.0
        assert pc.expected_active is True

    def test_creation_with_all_fields(self) -> None:
        pc = PositiveControl(
            identifier="CC1CC2(CC(=O)N1)C(=O)N(S2(=O)=O)O",
            identifier_type="smiles",
            name="Avibactam",
            known_activity="Ki ~1 nM vs Class A beta-lactamase",
            source="FDA-approved BLI",
            score=0.92,
        )
        assert pc.name == "Avibactam"
        assert pc.known_activity == "Ki ~1 nM vs Class A beta-lactamase"
        assert pc.score == 0.92

    def test_correctly_classified_above_threshold(self) -> None:
        pc = PositiveControl(identifier="CC(=O)O", score=0.85)
        assert pc.correctly_classified is True

    def test_correctly_classified_at_threshold(self) -> None:
        pc = PositiveControl(identifier="CC(=O)O", score=0.5)
        assert pc.correctly_classified is True

    def test_correctly_classified_below_threshold(self) -> None:
        pc = PositiveControl(identifier="CC(=O)O", score=0.3)
        assert pc.correctly_classified is False


class TestNegativeControlClassification:
    def test_correctly_classified_below_threshold(self) -> None:
        nc = NegativeControl(identifier="CCO", score=0.1, threshold=0.5)
        assert nc.correctly_classified is True

    def test_incorrectly_classified_above_threshold(self) -> None:
        nc = NegativeControl(identifier="CCO", score=0.8, threshold=0.5)
        assert nc.correctly_classified is False


class TestInvestigationPositiveControls:
    def test_add_positive_control(self) -> None:
        investigation = Investigation(prompt="Test")
        pc = PositiveControl(identifier="CC(=O)O", name="Test active")
        investigation.add_positive_control(pc)
        assert len(investigation.positive_controls) == 1
        assert investigation.positive_controls[0].name == "Test active"

    def test_positive_controls_default_empty(self) -> None:
        investigation = Investigation(prompt="Test")
        assert investigation.positive_controls == []

    def test_positive_controls_independent_lists(self) -> None:
        inv1 = Investigation(prompt="Test 1")
        inv2 = Investigation(prompt="Test 2")
        inv1.add_positive_control(PositiveControl(identifier="A"))
        assert len(inv1.positive_controls) == 1
        assert len(inv2.positive_controls) == 0


class TestPositiveControlRecordedEvent:
    def test_creation_with_all_fields(self) -> None:
        event = PositiveControlRecorded(
            identifier="CC(=O)O",
            identifier_type="smiles",
            name="Avibactam",
            known_activity="Ki ~1 nM",
            score=0.92,
            correctly_classified=True,
            investigation_id="inv-1",
        )
        assert event.identifier == "CC(=O)O"
        assert event.name == "Avibactam"
        assert event.known_activity == "Ki ~1 nM"
        assert event.score == 0.92
        assert event.correctly_classified is True
        assert event.investigation_id == "inv-1"

    def test_defaults(self) -> None:
        event = PositiveControlRecorded()
        assert event.identifier == ""
        assert event.known_activity == ""
        assert event.score == 0.0
        assert event.correctly_classified is True
