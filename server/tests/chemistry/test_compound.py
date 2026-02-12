from ehrlich.chemistry.domain.compound import Compound
from ehrlich.kernel.types import SMILES, InChIKey


class TestCompound:
    def test_create_with_defaults(self) -> None:
        c = Compound(smiles=SMILES("CCO"))
        assert c.smiles == "CCO"
        assert c.name == ""
        assert c.inchi_key == ""
        assert c.metadata == {}

    def test_create_with_all_fields(self) -> None:
        c = Compound(
            smiles=SMILES("CC(=O)Oc1ccccc1C(=O)O"),
            name="Aspirin",
            inchi_key=InChIKey("BSYNRYMUTXBXSQ-UHFFFAOYSA-N"),
            metadata={"source": "pubchem"},
        )
        assert c.name == "Aspirin"
        assert c.inchi_key == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert c.metadata["source"] == "pubchem"
