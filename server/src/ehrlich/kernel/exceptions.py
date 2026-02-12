class EhrlichError(Exception):
    pass


class InvalidSMILESError(EhrlichError):
    def __init__(self, smiles: str, reason: str = "Invalid SMILES string") -> None:
        self.smiles = smiles
        self.reason = reason
        super().__init__(f"{reason}: '{smiles}'")


class ModelNotTrainedError(EhrlichError):
    def __init__(self, model_type: str) -> None:
        self.model_type = model_type
        super().__init__(f"Model not trained: {model_type}")


class DatasetNotFoundError(EhrlichError):
    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Dataset not found: {dataset_id}")


class TargetNotFoundError(EhrlichError):
    def __init__(self, target_id: str) -> None:
        self.target_id = target_id
        super().__init__(f"Target not found: {target_id}")


class ExternalServiceError(EhrlichError):
    def __init__(self, service: str, detail: str) -> None:
        self.service = service
        self.detail = detail
        super().__init__(f"External service error ({service}): {detail}")
