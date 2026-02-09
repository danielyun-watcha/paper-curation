from __future__ import annotations

import io
from typing import Optional

import httpx
from pypdf import PdfReader


class PdfServiceError(Exception):
    pass


class PdfService:
    """Service for downloading and extracting text from PDFs"""

    async def download_pdf(self, url: str) -> bytes:
        """Download PDF from URL"""
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    raise PdfServiceError(f"Failed to download PDF: {response.status_code}")
                return response.content
            except httpx.TimeoutException:
                raise PdfServiceError("PDF download timed out")
            except httpx.RequestError as e:
                raise PdfServiceError(f"Failed to download PDF: {e}")

    def extract_text(self, pdf_bytes: bytes, max_pages: int = 20) -> str:
        """Extract text from PDF bytes"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []

            # Limit pages to prevent too much text
            pages_to_read = min(len(reader.pages), max_pages)

            for i in range(pages_to_read):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise PdfServiceError(f"Failed to extract text from PDF: {e}")

    def extract_title_from_pdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract title from PDF (first page, first significant line)"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            if not reader.pages:
                return None

            # Try PDF metadata first
            if reader.metadata and reader.metadata.title:
                title = reader.metadata.title.strip()
                if title and len(title) > 5:
                    return title

            # Extract from first page text
            first_page = reader.pages[0]
            text = first_page.extract_text()
            if not text:
                return None

            lines = [line.strip() for line in text.split('\n') if line.strip()]

            # Find title: skip non-title lines, find first substantial line
            for line in lines[:15]:  # Check first 15 lines
                lower = line.lower()
                # Skip very short lines or lines that look like headers/page numbers
                if len(line) < 10:
                    continue
                # Skip lines that are likely authors (contain @, university, etc.)
                if '@' in line or 'university' in lower or 'institute' in lower:
                    continue
                # Skip lines that look like "arXiv:" or dates
                if lower.startswith('arxiv') or line.startswith('20'):
                    continue
                # Skip lines containing URLs or DOIs
                if 'http' in lower or 'doi.org' in lower or 'doi:' in lower or '10.' in line[:4]:
                    continue
                # Skip journal/publisher headers and article type labels
                if any(kw in lower for kw in [
                    'journal', 'proceedings', 'conference', 'transactions',
                    'research article', 'review article', 'original article',
                    'open access', 'vol.', 'volume', 'issn', 'isbn',
                    'published', 'accepted', 'received', 'revised',
                    'latest update', 'copyright', 'license', 'creative commons',
                    'springer', 'elsevier', 'wiley', 'ieee', 'acm',
                    'preprint', 'submitted',
                ]):
                    continue
                # This is likely the title
                return line

            return None
        except Exception:
            return None

    async def get_paper_text(
        self,
        arxiv_id: Optional[str] = None,
        paper_url: Optional[str] = None,
        pdf_path: Optional[str] = None,
        max_pages: int = 20
    ) -> str:
        """Get text from a paper (arXiv, URL, or local file)"""
        if pdf_path:
            # Read from local file
            import os
            if not os.path.exists(pdf_path):
                raise PdfServiceError(f"PDF file not found: {pdf_path}")
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
            return self.extract_text(pdf_bytes, max_pages)
        elif arxiv_id:
            url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        elif paper_url:
            url = paper_url
        else:
            raise PdfServiceError("No PDF source available")

        pdf_bytes = await self.download_pdf(url)
        return self.extract_text(pdf_bytes, max_pages)


_pdf_service: Optional[PdfService] = None


def get_pdf_service() -> PdfService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PdfService()
    return _pdf_service
