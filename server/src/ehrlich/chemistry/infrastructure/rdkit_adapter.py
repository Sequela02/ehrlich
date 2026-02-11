from rdkit import Chem
from rdkit.Chem import (
    QED,
    AllChem,
    Descriptors,
    MACCSkeys,
    rdFingerprintGenerator,
    rdMolDescriptors,
)
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.inchi import MolToInchi
from rdkit.Chem.Scaffolds.MurckoScaffold import GetScaffoldForMol
from rdkit.DataStructs import TanimotoSimilarity
from rdkit.ML.Cluster import Butina

from ehrlich.chemistry.domain.conformer import Conformer3D
from ehrlich.chemistry.domain.descriptors import MolecularDescriptors
from ehrlich.chemistry.domain.fingerprint import Fingerprint
from ehrlich.kernel.exceptions import InvalidSMILESError
from ehrlich.kernel.types import SMILES, InChIKey, MolBlock


class RDKitAdapter:
    def _to_mol(self, smiles: SMILES) -> Chem.Mol:
        mol = Chem.MolFromSmiles(str(smiles))
        if mol is None:
            raise InvalidSMILESError(str(smiles))
        return mol

    def validate_smiles(self, smiles: SMILES) -> bool:
        return Chem.MolFromSmiles(str(smiles)) is not None

    def canonicalize(self, smiles: SMILES) -> SMILES:
        mol = self._to_mol(smiles)
        return SMILES(Chem.MolToSmiles(mol))

    def to_inchikey(self, smiles: SMILES) -> InChIKey:
        mol = self._to_mol(smiles)
        inchi = MolToInchi(mol)
        if inchi is None:
            raise InvalidSMILESError(str(smiles), "Cannot compute InChI")
        key = Chem.inchi.InchiToInchiKey(inchi)
        if key is None:
            raise InvalidSMILESError(str(smiles), "Cannot compute InChIKey")
        return InChIKey(key)

    def compute_descriptors(self, smiles: SMILES) -> MolecularDescriptors:
        mol = self._to_mol(smiles)
        return MolecularDescriptors(
            molecular_weight=Descriptors.MolWt(mol),
            logp=Descriptors.MolLogP(mol),
            tpsa=Descriptors.TPSA(mol),
            hbd=rdMolDescriptors.CalcNumHBD(mol),
            hba=rdMolDescriptors.CalcNumHBA(mol),
            rotatable_bonds=rdMolDescriptors.CalcNumRotatableBonds(mol),
            qed=QED.qed(mol),
            num_rings=rdMolDescriptors.CalcNumRings(mol),
        )

    _morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    def compute_fingerprint(self, smiles: SMILES, fp_type: str = "morgan") -> Fingerprint:
        mol = self._to_mol(smiles)
        if fp_type == "maccs":
            fp = MACCSkeys.GenMACCSKeys(mol)
            on_bits = tuple(fp.GetOnBits())
            return Fingerprint(bits=on_bits, fp_type="maccs", radius=0, n_bits=167)
        fp = self._morgan_gen.GetFingerprint(mol)
        on_bits = tuple(fp.GetOnBits())
        return Fingerprint(bits=on_bits, fp_type="morgan", radius=2, n_bits=2048)

    def tanimoto_similarity(self, fp1: Fingerprint, fp2: Fingerprint) -> float:
        bv1 = self._fingerprint_to_bitvect(fp1)
        bv2 = self._fingerprint_to_bitvect(fp2)
        return float(TanimotoSimilarity(bv1, bv2))

    def _fingerprint_to_bitvect(self, fp: Fingerprint) -> Chem.DataStructs.ExplicitBitVect:
        from rdkit.DataStructs import ExplicitBitVect

        bv = ExplicitBitVect(fp.n_bits)
        for bit in fp.bits:
            bv.SetBit(bit)
        return bv

    def generate_conformer(self, smiles: SMILES) -> Conformer3D:
        mol = self._to_mol(smiles)
        mol = Chem.AddHs(mol)
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        result = AllChem.EmbedMolecule(mol, params)
        if result == -1:
            raise InvalidSMILESError(str(smiles), "Cannot generate 3D conformer")
        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
            energy = float(AllChem.MMFFGetMoleculeForceField(mol).CalcEnergy())
        except Exception:
            energy = 0.0
        mol_block = Chem.MolToMolBlock(mol)
        return Conformer3D(
            mol_block=MolBlock(mol_block),
            energy=energy,
            num_atoms=mol.GetNumAtoms(),
        )

    def substructure_match(self, smiles: SMILES, pattern: str) -> tuple[bool, tuple[int, ...]]:
        mol = self._to_mol(smiles)
        pattern_mol = Chem.MolFromSmarts(pattern)
        if pattern_mol is None:
            pattern_mol = Chem.MolFromSmiles(pattern)
        if pattern_mol is None:
            return (False, ())
        match = mol.GetSubstructMatch(pattern_mol)
        if match:
            return (True, tuple(match))
        return (False, ())

    def depict_2d(self, smiles: SMILES, width: int = 300, height: int = 200) -> str:
        mol = self._to_mol(smiles)
        AllChem.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return str(drawer.GetDrawingText())

    def murcko_scaffold(self, smiles: SMILES) -> str:
        mol = self._to_mol(smiles)
        scaffold = GetScaffoldForMol(mol)
        return str(Chem.MolToSmiles(scaffold))

    def butina_cluster(
        self, fingerprints: list[Fingerprint], cutoff: float = 0.35
    ) -> list[list[int]]:
        n = len(fingerprints)
        if n == 0:
            return []
        if n == 1:
            return [[0]]
        bvs = [self._fingerprint_to_bitvect(fp) for fp in fingerprints]
        dists = []
        for i in range(1, n):
            for j in range(i):
                dists.append(1.0 - float(TanimotoSimilarity(bvs[i], bvs[j])))
        clusters = Butina.ClusterData(dists, n, cutoff, isDistData=True)
        return [list(c) for c in clusters]
