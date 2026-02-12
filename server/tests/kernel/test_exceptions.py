from ehrlich.kernel.exceptions import (
    DatasetNotFoundError,
    ModelNotTrainedError,
)


class TestModelNotTrainedError:
    def test_message(self) -> None:
        err = ModelNotTrainedError("xgboost")
        assert err.model_type == "xgboost"
        assert "xgboost" in str(err)


class TestDatasetNotFoundError:
    def test_message(self) -> None:
        err = DatasetNotFoundError("ds-123")
        assert err.dataset_id == "ds-123"
        assert "ds-123" in str(err)
