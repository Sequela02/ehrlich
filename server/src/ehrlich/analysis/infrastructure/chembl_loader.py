import logging
import math
from pathlib import Path

import httpx
import pandas as pd

from ehrlich.analysis.domain.dataset import Dataset
from ehrlich.analysis.domain.repository import DatasetRepository
from ehrlich.kernel.exceptions import ExternalServiceError
from ehrlich.kernel.types import SMILES

logger = logging.getLogger(__name__)

_CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
_TIMEOUT = 30.0
_CACHE_DIR = Path(__file__).resolve().parents[5] / "data" / "datasets"


class ChEMBLLoader(DatasetRepository):
    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or _CACHE_DIR
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def load(self, target: str, threshold: float = 1.0) -> Dataset:
        cache_file = self._cache_dir / f"chembl_{target.replace(' ', '_').lower()}.parquet"
        if cache_file.exists():
            return self._load_from_cache(cache_file, target, threshold)
        return await self._load_from_api(target, threshold, cache_file)

    async def list_targets(self) -> list[str]:
        cached = list(self._cache_dir.glob("chembl_*.parquet"))
        targets = []
        for f in cached:
            name = f.stem.replace("chembl_", "").replace("_", " ").title()
            targets.append(name)
        if not targets:
            targets = [
                "Staphylococcus aureus",
                "Escherichia coli",
                "Pseudomonas aeruginosa",
                "Acinetobacter baumannii",
                "Mycobacterium tuberculosis",
            ]
        return targets

    async def _load_from_api(self, target: str, threshold: float, cache_file: Path) -> Dataset:
        try:
            activities = await self._fetch_activities(target)
            if not activities:
                return Dataset(name=f"ChEMBL {target}", target=target)
            df = self._process_activities(activities, threshold)
            df.to_parquet(cache_file, index=False)
            return self._df_to_dataset(df, target)
        except httpx.HTTPError as e:
            raise ExternalServiceError("ChEMBL", str(e)) from e

    async def _fetch_activities(self, target_organism: str) -> list[dict[str, object]]:
        all_activities: list[dict[str, object]] = []
        offset = 0
        limit = 1000
        while True:
            try:
                resp = await self._client.get(
                    f"{_CHEMBL_API}/activity.json",
                    params={
                        "target_organism__iexact": target_organism,
                        "standard_type__in": "MIC,IC50",
                        "standard_relation": "=",
                        "limit": limit,
                        "offset": offset,
                    },
                )
                if resp.status_code == 429:
                    raise ExternalServiceError("ChEMBL", "Rate limit exceeded")
                resp.raise_for_status()
                data = resp.json()
                activities = data.get("activities", [])
                if not activities:
                    break
                all_activities.extend(activities)
                if len(activities) < limit:
                    break
                offset += limit
                if offset >= 20000:
                    break
            except httpx.TimeoutException as e:
                logger.warning("ChEMBL timeout at offset %d: %s", offset, e)
                break
        return all_activities

    @staticmethod
    def _process_activities(activities: list[dict[str, object]], threshold: float) -> pd.DataFrame:
        rows = []
        for act in activities:
            smiles = act.get("canonical_smiles")
            value = act.get("standard_value")
            units = act.get("standard_units")
            if not smiles or value is None:
                continue
            try:
                value_float = float(str(value))
            except (ValueError, TypeError):
                continue
            if units == "nM":
                value_um = value_float / 1000.0
            elif units == "uM":
                value_um = value_float
            else:
                continue
            if value_um <= 0:
                continue
            p_activity = -math.log10(value_um * 1e-6)
            rows.append(
                {
                    "smiles": str(smiles),
                    "value_um": value_um,
                    "p_activity": p_activity,
                    "standard_type": str(act.get("standard_type", "")),
                    "assay_chembl_id": str(act.get("assay_chembl_id", "")),
                }
            )
        if not rows:
            return pd.DataFrame(columns=["smiles", "value_um", "p_activity"])
        df = pd.DataFrame(rows)
        df = df.groupby("smiles", as_index=False).agg(
            {
                "value_um": "median",
                "p_activity": "median",
                "standard_type": "first",
                "assay_chembl_id": "first",
            }
        )
        active = (df["p_activity"] >= threshold).astype(float)
        df["activity"] = active
        return df

    @staticmethod
    def _df_to_dataset(df: pd.DataFrame, target: str) -> Dataset:
        return Dataset(
            name=f"ChEMBL {target}",
            target=target,
            smiles_list=[SMILES(s) for s in df["smiles"].tolist()],
            activities=df["activity"].tolist(),
            metadata={
                "source": "ChEMBL",
                "size": str(len(df)),
                "active_count": str(int(df["activity"].sum())),
            },
        )

    def _load_from_cache(self, path: Path, target: str, threshold: float) -> Dataset:
        df = pd.read_parquet(path)
        if "p_activity" in df.columns:
            df["activity"] = (df["p_activity"] >= threshold).astype(float)
        return self._df_to_dataset(df, target)
