"""Tests for utility functions: tools, PDF loader."""
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestGetTime:
    def test_returns_formatted_time(self):
        from app.utils.tools import get_time

        result = get_time("%Y-%m-%d")
        # Should match today's date format
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result == expected

    def test_custom_format(self):
        from app.utils.tools import get_time

        result = get_time("%H:%M")
        assert ":" in result  # basic format check


class TestSearch:
    def test_text_search(self):
        from app.utils.tools import search

        mock_results = [
            {"title": "Result 1", "href": "https://example.com", "body": "text"},
        ]

        with patch("app.utils.tools.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.return_value = mock_results
            result = search("test query", max_results=1)

        assert len(result) == 1
        assert result[0]["title"] == "Result 1"

    def test_news_search(self):
        from app.utils.tools import search

        mock_results = [{"title": "News 1", "url": "https://news.com"}]

        with patch("app.utils.tools.DDGS") as mock_ddgs:
            mock_ddgs.return_value.news.return_value = mock_results
            result = search("breaking news", source="news")

        assert len(result) == 1


class TestRag:
    def test_rag_with_results(self):
        from app.utils.tools import rag

        mock_chunks = [
            {"text": "chunk text 1", "filename": "doc.txt"},
            {"text": "chunk text 2", "filename": "doc.txt"},
        ]

        with patch("app.utils.tools.retrieve_from_knowledgestore", return_value=mock_chunks):
            result = rag("test query", user_id="user1")

        assert "chunk text 1" in result
        assert "chunk text 2" in result
        assert "doc.txt" in result

    def test_rag_no_results(self):
        from app.utils.tools import rag

        with patch("app.utils.tools.retrieve_from_knowledgestore", return_value=[]):
            result = rag("obscure query", user_id="user1")

        assert result == "No Relevant Context Found"


class TestLoadPdf:
    def test_load_pdf_extracts_text(self):
        from app.utils.loadpdf import load_pdf

        mock_page = MagicMock()
        mock_page.get_textpage.return_value.get_text_range.return_value = "Page 1 text"

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

        with patch("app.utils.loadpdf.pdfium.PdfDocument", return_value=mock_doc):
            result = load_pdf(b"fake-pdf-bytes")

        assert "Page 1 text" in result

    def test_load_pdf_multiple_pages(self):
        from app.utils.loadpdf import load_pdf

        pages = []
        for text in ["Page 1", "Page 2", "Page 3"]:
            mock_page = MagicMock()
            mock_page.get_textpage.return_value.get_text_range.return_value = text
            pages.append(mock_page)

        mock_doc = MagicMock()
        mock_doc.__iter__ = MagicMock(return_value=iter(pages))

        with patch("app.utils.loadpdf.pdfium.PdfDocument", return_value=mock_doc):
            result = load_pdf(b"fake-pdf-bytes")

        assert "Page 1" in result
        assert "Page 2" in result
        assert "Page 3" in result
        assert result == "Page 1\nPage 2\nPage 3"


class TestToolSchema:
    def test_schema_has_three_tools(self):
        from app.utils.tools import tool_schema

        assert len(tool_schema) == 3

    def test_schema_tool_names(self):
        from app.utils.tools import tool_schema

        names = [t["function"]["name"] for t in tool_schema]
        assert "get_time" in names
        assert "search" in names
        assert "rag" in names

    def test_each_tool_has_required_fields(self):
        from app.utils.tools import tool_schema

        for tool in tool_schema:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert "required" in func["parameters"]
