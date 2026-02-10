from ehrlich.kernel.types import SMILES
from ehrlich.simulation.domain.admet_profile import ADMETProfile
from ehrlich.simulation.domain.docking_result import DockingResult
from ehrlich.simulation.domain.resistance_assessment import ResistanceAssessment


class SimulationService:
    async def dock(self, smiles: SMILES, target_id: str) -> DockingResult:
        raise NotImplementedError

    async def predict_admet(self, smiles: SMILES) -> ADMETProfile:
        raise NotImplementedError

    async def assess_resistance(self, smiles: SMILES, target_id: str) -> ResistanceAssessment:
        raise NotImplementedError
