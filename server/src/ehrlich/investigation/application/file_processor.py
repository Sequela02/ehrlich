from __future__ import annotations

import io

import pandas as pd

from ehrlich.investigation.domain.upload_limits import ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from ehrlich.investigation.domain.uploaded_file import (
    DocumentData,
    TabularData,
    UploadedFile,
)

_MAX_SAMPLE_ROWS = 10
_MAX_PDF_TEXT_LENGTH = 8000


class FileProcessor:
    """Parses uploaded files into domain entities."""

    def process(self, filename: str, content: bytes) -> UploadedFile:
        if not content:
            msg = "File is empty"
            raise ValueError(msg)
        if len(content) > MAX_FILE_SIZE:
            msg = f"File exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"
            raise ValueError(msg)

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            msg = f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            raise ValueError(msg)

        if ext == "csv":
            return self._process_csv(filename, content)
        if ext == "xlsx":
            return self._process_xlsx(filename, content)
        return self._process_pdf(filename, content)

    def _process_csv(self, filename: str, content: bytes) -> UploadedFile:
        df = pd.read_csv(io.BytesIO(content))
        return self._build_tabular(filename, "text/csv", df)

    def _process_xlsx(self, filename: str, content: bytes) -> UploadedFile:
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        return self._build_tabular(
            filename,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            df,
        )

    def _process_pdf(self, filename: str, content: bytes) -> UploadedFile:
        import pymupdf  # lazy import -- only needed for PDF

        doc: pymupdf.Document = pymupdf.open(stream=content, filetype="pdf")  # type: ignore[no-untyped-call]
        pages: list[str] = []
        for i in range(len(doc)):
            page = doc[i]
            text: str = page.get_text()  # type: ignore[attr-defined]
            if text.strip():
                pages.append(text)
        doc.close()  # type: ignore[no-untyped-call]

        full_text = "\n\n".join(pages)
        if len(full_text) > _MAX_PDF_TEXT_LENGTH:
            full_text = full_text[:_MAX_PDF_TEXT_LENGTH] + "..."

        return UploadedFile(
            filename=filename,
            content_type="application/pdf",
            document=DocumentData(text=full_text, page_count=len(pages)),
        )

    def _build_tabular(self, filename: str, content_type: str, df: pd.DataFrame) -> UploadedFile:
        columns = tuple(str(c) for c in df.columns)
        dtypes = tuple(str(d) for d in df.dtypes)
        row_count = len(df)

        # Summary statistics for numeric columns
        desc = df.describe()
        summary_stats: dict[str, dict[str, float]] = {}
        for col in desc.columns:
            summary_stats[str(col)] = {str(k): round(float(v), 4) for k, v in desc[col].items()}

        # Sample rows (first N, all values as strings)
        sample = df.head(_MAX_SAMPLE_ROWS)
        sample_rows = tuple(tuple(str(v) for v in row) for row in sample.values)

        return UploadedFile(
            filename=filename,
            content_type=content_type,
            tabular=TabularData(
                columns=columns,
                dtypes=dtypes,
                row_count=row_count,
                summary_stats=summary_stats,
                sample_rows=sample_rows,
            ),
        )
