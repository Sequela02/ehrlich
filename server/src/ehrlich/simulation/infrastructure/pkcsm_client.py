from ehrlich.simulation.domain.admet_profile import ADMETProfile


class PkCSMClient:
    async def predict(self, smiles: str) -> ADMETProfile:
        raise NotImplementedError
