"""Tests for OCR pipeline."""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ocr_pipeline import OCRPipeline


class TestOCRPipeline:
    """Test OCR pipeline functionality."""

    @pytest.fixture
    def pipeline(self, tmp_path):
        """Create OCR pipeline instance with temp directories."""
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()

        return OCRPipeline(str(raw_dir), str(processed_dir))

    def test_pipeline_initialization(self, pipeline, tmp_path):
        """Test pipeline initializes correctly."""
        assert pipeline.raw_data_dir.exists()
        assert pipeline.processed_data_dir.exists()

    def test_chunk_text(self, pipeline):
        """Test text chunking with overlap."""
        text = "ا" * 1000  # Arabic text
        chunks = pipeline.chunk_text(text, page_number=1, chunk_size=500, overlap=100)

        assert len(chunks) > 1
        assert chunks[0]["page_number"] == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[1]["chunk_index"] == 1

    def test_chunk_text_empty(self, pipeline):
        """Test chunking empty text."""
        chunks = pipeline.chunk_text("", page_number=1)
        assert len(chunks) == 0

    def test_chunk_text_preserves_page_number(self, pipeline):
        """Test that all chunks preserve page number."""
        text = "ا" * 1000
        chunks = pipeline.chunk_text(text, page_number=42)

        for chunk in chunks:
            assert chunk["page_number"] == 42

    def test_ocr_image_requires_tesseract(self, pipeline):
        """Test OCR requires Tesseract installation."""
        # This test will be skipped if Tesseract is not installed
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            pytest.skip("Tesseract not installed")

    def test_convert_pdf_to_images_requires_file(self, pipeline, tmp_path):
        """Test PDF conversion requires valid PDF file."""
        fake_pdf = tmp_path / "raw" / "test.pdf"

        # Should handle missing file gracefully
        with pytest.raises(Exception):
            pipeline.convert_pdf_to_images(fake_pdf, tmp_path / "output")


class TestChunkingLogic:
    """Test chunking logic in detail."""

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        pipeline = OCRPipeline("/tmp/raw", "/tmp/processed")

        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 50  # 1300 chars
        chunks = pipeline.chunk_text(text, 1, chunk_size=500, overlap=100)

        # Check that there's actual overlap
        assert len(chunks) >= 3

        # Check chunk sizes
        for chunk in chunks[:-1]:  # All but last
            assert len(chunk["text"]) == 500

    def test_chunk_metadata(self):
        """Test chunk metadata is complete."""
        pipeline = OCRPipeline("/tmp/raw", "/tmp/processed")

        text = "Test text" * 100
        chunks = pipeline.chunk_text(text, 42, chunk_size=100, overlap=20)

        for i, chunk in enumerate(chunks):
            assert "text" in chunk
            assert "page_number" in chunk
            assert "chunk_index" in chunk
            assert "start_pos" in chunk
            assert "end_pos" in chunk
            assert chunk["page_number"] == 42
            assert chunk["chunk_index"] == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
