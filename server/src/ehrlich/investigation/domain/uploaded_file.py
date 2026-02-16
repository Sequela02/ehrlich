from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TabularData:
    """Parsed tabular file data (CSV or Excel)."""

    columns: tuple[str, ...]
    dtypes: tuple[str, ...]
    row_count: int
    summary_stats: dict[str, dict[str, float]]
    sample_rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class DocumentData:
    """Parsed document data (PDF)."""

    text: str
    page_count: int


@dataclass(frozen=True)
class UploadedFile:
    """A user-uploaded file with parsed content."""

    filename: str
    content_type: str
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tabular: TabularData | None = None
    document: DocumentData | None = None

    def __post_init__(self) -> None:
        if not self.filename:
            msg = "filename is required"
            raise ValueError(msg)
        if self.tabular is None and self.document is None:
            msg = "UploadedFile must have either tabular or document data"
            raise ValueError(msg)
