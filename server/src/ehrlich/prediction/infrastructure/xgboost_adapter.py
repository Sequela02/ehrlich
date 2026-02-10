class XGBoostAdapter:
    async def train(self, fingerprints: list[list[int]], activities: list[float]) -> object:
        raise NotImplementedError

    async def predict(self, fingerprints: list[list[int]], model: object) -> list[float]:
        raise NotImplementedError
