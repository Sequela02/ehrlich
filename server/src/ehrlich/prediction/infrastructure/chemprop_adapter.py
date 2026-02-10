class ChempropAdapter:
    async def train(self, smiles_list: list[str], activities: list[float]) -> object:
        raise NotImplementedError

    async def predict(self, smiles_list: list[str], model: object) -> list[float]:
        raise NotImplementedError
