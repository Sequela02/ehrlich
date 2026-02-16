from __future__ import annotations

import io

import pytest

from ehrlich.investigation.application.file_processor import FileProcessor


@pytest.fixture
def processor() -> FileProcessor:
    return FileProcessor()


class TestCSVProcessing:
    def test_valid_csv(self, processor: FileProcessor) -> None:
        content = b"name,age,score\nAlice,30,85.5\nBob,25,92.0\nCharlie,35,78.3"
        result = processor.process("data.csv", content)
        assert result.filename == "data.csv"
        assert result.content_type == "text/csv"
        assert result.tabular is not None
        assert result.document is None
        assert result.tabular.columns == ("name", "age", "score")
        assert result.tabular.row_count == 3
        assert len(result.tabular.sample_rows) == 3

    def test_csv_dtypes(self, processor: FileProcessor) -> None:
        content = b"x,y\n1,hello\n2,world"
        result = processor.process("types.csv", content)
        assert result.tabular is not None
        assert len(result.tabular.dtypes) == 2
        assert "int" in result.tabular.dtypes[0]
        assert "object" in result.tabular.dtypes[1]

    def test_csv_summary_stats(self, processor: FileProcessor) -> None:
        content = b"value\n1\n2\n3\n4\n5"
        result = processor.process("stats.csv", content)
        assert result.tabular is not None
        stats = result.tabular.summary_stats
        assert "value" in stats
        assert stats["value"]["mean"] == 3.0
        assert stats["value"]["count"] == 5.0

    def test_csv_sample_rows_limited(self, processor: FileProcessor) -> None:
        lines = ["x"] + [str(i) for i in range(20)]
        content = "\n".join(lines).encode()
        result = processor.process("big.csv", content)
        assert result.tabular is not None
        assert len(result.tabular.sample_rows) <= 10

    def test_csv_sample_rows_as_strings(self, processor: FileProcessor) -> None:
        content = b"a,b\n1,2.5\n3,4.0"
        result = processor.process("nums.csv", content)
        assert result.tabular is not None
        for row in result.tabular.sample_rows:
            for val in row:
                assert isinstance(val, str)

    def test_csv_file_id_generated(self, processor: FileProcessor) -> None:
        content = b"col\n1"
        result = processor.process("id.csv", content)
        assert result.file_id
        assert len(result.file_id) == 36  # UUID format


class TestXLSXProcessing:
    def test_valid_xlsx(self, processor: FileProcessor) -> None:
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws is not None
        ws.append(["name", "value"])
        ws.append(["A", 1])
        ws.append(["B", 2])
        buf = io.BytesIO()
        wb.save(buf)
        content = buf.getvalue()

        result = processor.process("data.xlsx", content)
        assert result.filename == "data.xlsx"
        assert result.tabular is not None
        assert result.tabular.columns == ("name", "value")
        assert result.tabular.row_count == 2

    def test_xlsx_content_type(self, processor: FileProcessor) -> None:
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        assert ws is not None
        ws.append(["x"])
        ws.append([1])
        buf = io.BytesIO()
        wb.save(buf)

        result = processor.process("test.xlsx", buf.getvalue())
        assert "spreadsheetml" in result.content_type


class TestPDFProcessing:
    def test_valid_pdf(self, processor: FileProcessor) -> None:
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Hello world test document")
        content = doc.tobytes()
        doc.close()

        result = processor.process("report.pdf", content)
        assert result.filename == "report.pdf"
        assert result.content_type == "application/pdf"
        assert result.document is not None
        assert result.tabular is None
        assert "Hello world" in result.document.text
        assert result.document.page_count >= 1

    def test_pdf_text_truncation(self, processor: FileProcessor) -> None:
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        # Insert a lot of text
        long_text = "A" * 500
        for y in range(50, 800, 15):
            page.insert_text((50, y), long_text)
        # Add more pages
        for _ in range(5):
            p = doc.new_page()
            for y in range(50, 800, 15):
                p.insert_text((50, y), long_text)
        content = doc.tobytes()
        doc.close()

        result = processor.process("long.pdf", content)
        assert result.document is not None
        assert len(result.document.text) <= 8001 + 3  # 8000 + "..."

    def test_pdf_multiple_pages(self, processor: FileProcessor) -> None:
        import pymupdf

        doc = pymupdf.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((50, 50), f"Page {i + 1} content")
        content = doc.tobytes()
        doc.close()

        result = processor.process("multi.pdf", content)
        assert result.document is not None
        assert result.document.page_count == 3


class TestValidation:
    def test_empty_file_raises(self, processor: FileProcessor) -> None:
        with pytest.raises(ValueError, match="empty"):
            processor.process("empty.csv", b"")

    def test_unsupported_extension_raises(self, processor: FileProcessor) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            processor.process("data.json", b'{"key": "value"}')

    def test_no_extension_raises(self, processor: FileProcessor) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            processor.process("noext", b"some data")

    def test_oversized_file_raises(self, processor: FileProcessor) -> None:
        huge = b"x" * (51 * 1024 * 1024)
        with pytest.raises(ValueError, match="50MB"):
            processor.process("huge.csv", huge)

    def test_txt_extension_raises(self, processor: FileProcessor) -> None:
        with pytest.raises(ValueError, match="Unsupported"):
            processor.process("notes.txt", b"some text")
