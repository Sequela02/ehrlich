import logging
from pathlib import Path

import pandas as pd

from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.kernel.types import SMILES

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parents[5] / "data" / "datasets"

TOX21_ENDPOINTS = [
    "NR-AR",
    "NR-AR-LBD",
    "NR-AhR",
    "NR-Aromatase",
    "NR-ER",
    "NR-ER-LBD",
    "NR-PPAR-gamma",
    "SR-ARE",
    "SR-ATAD5",
    "SR-HSE",
    "SR-MMP",
    "SR-p53",
]


class Tox21Loader:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or _DATA_DIR

    async def load(self, assay: str = "NR-AhR") -> Dataset:
        csv_path = self._data_dir / "tox21.csv"
        if not csv_path.exists():
            logger.warning("Tox21 dataset not found at %s", csv_path)
            return Dataset(name="Tox21", target=assay)
        df = pd.read_csv(csv_path)
        if assay not in df.columns:
            logger.warning("Assay %s not found in Tox21 data", assay)
            return Dataset(name="Tox21", target=assay)
        subset = df[["smiles", assay]].dropna()
        return Dataset(
            name=f"Tox21 {assay}",
            target=assay,
            smiles_list=[SMILES(s) for s in subset["smiles"].tolist()],
            activities=subset[assay].tolist(),
            metadata={
                "source": "Tox21",
                "endpoint": assay,
                "size": str(len(subset)),
            },
        )

    async def cross_reference(self, dataset: Dataset) -> Dataset:
        tox_data = await self.load()
        if tox_data.size == 0:
            return dataset
        tox_smiles = set(tox_data.smiles_list)
        overlap_indices = [i for i, s in enumerate(dataset.smiles_list) if s in tox_smiles]
        if not overlap_indices:
            return dataset
        metadata = dict(dataset.metadata)
        metadata["tox21_overlap"] = str(len(overlap_indices))
        metadata["tox21_overlap_pct"] = f"{100 * len(overlap_indices) / dataset.size:.1f}%"
        return Dataset(
            name=dataset.name,
            target=dataset.target,
            smiles_list=dataset.smiles_list,
            activities=dataset.activities,
            metadata=metadata,
        )
