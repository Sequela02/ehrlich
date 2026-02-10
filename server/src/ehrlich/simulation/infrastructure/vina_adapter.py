class VinaAdapter:
    async def dock(
        self,
        mol_block: str,
        target_pdbqt: str,
        center: tuple[float, float, float],
        box_size: float,
    ) -> dict[str, float]:
        raise NotImplementedError
