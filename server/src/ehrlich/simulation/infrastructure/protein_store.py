class ProteinStore:
    async def get_pdbqt(self, pdb_id: str) -> str:
        raise NotImplementedError

    async def list_targets(self) -> list[str]:
        raise NotImplementedError
