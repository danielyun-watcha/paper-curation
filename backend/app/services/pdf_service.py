from __future__ import annotations

import io
import re
from typing import Optional

import httpx


class PdfServiceError(Exception):
    pass


class PdfService:
    """Service for downloading and extracting text from PDFs using PyMuPDF"""

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

    async def download_arxiv_pdf(self, arxiv_id: str) -> str:
        """Download arXiv PDF and save to temp file, return path"""
        import tempfile
        import os

        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        pdf_bytes = await self.download_pdf(url)

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, f"{arxiv_id.replace('/', '_')}.pdf")

        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        return pdf_path

    def extract_text(self, pdf_bytes: bytes, max_pages: int = 20) -> str:
        """Extract text from PDF bytes using PyMuPDF with 2-column layout handling"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            # Fallback to pypdf if PyMuPDF not available
            return self._extract_text_pypdf(pdf_bytes, max_pages)

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text_parts = []

            pages_to_read = min(len(doc), max_pages)

            for page_num in range(pages_to_read):
                page = doc[page_num]

                # Use block-based extraction for better 2-column handling
                text = self._extract_page_with_columns(page, page_num)

                if text:
                    text_parts.append(text)

            doc.close()

            # Join pages and do final cleanup
            full_text = "\n\n".join(text_parts)
            return self._post_process_text(full_text)

        except Exception as e:
            raise PdfServiceError(f"Failed to extract text from PDF: {e}")

    def _extract_page_with_columns(self, page, page_num: int) -> str:
        """Extract text from page handling 2-column layouts"""
        import fitz

        # Get page dimensions
        page_width = page.rect.width
        page_center = page_width / 2

        # Get text blocks with position info
        blocks = page.get_text("dict", sort=True)["blocks"]

        # Separate blocks into left and right columns
        left_blocks = []
        right_blocks = []
        full_width_blocks = []

        for block in blocks:
            if block["type"] != 0:  # Skip non-text blocks (images, etc.)
                continue

            bbox = block["bbox"]  # (x0, y0, x1, y1)
            block_left = bbox[0]
            block_right = bbox[2]
            block_width = block_right - block_left

            # Check if block spans full width (like title, abstract header)
            if block_width > page_width * 0.7:
                full_width_blocks.append(block)
            elif block_right < page_center + 20:  # Left column (with some tolerance)
                left_blocks.append(block)
            elif block_left > page_center - 20:  # Right column
                right_blocks.append(block)
            else:
                # Block spans both columns - treat as full width
                full_width_blocks.append(block)

        # Sort blocks by y position (top to bottom)
        def get_y(block):
            return block["bbox"][1]

        full_width_blocks.sort(key=get_y)
        left_blocks.sort(key=get_y)
        right_blocks.sort(key=get_y)

        # Extract text from blocks
        def extract_block_text(block):
            lines = []
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                if line_text.strip():
                    lines.append(line_text.strip())
            return "\n".join(lines)

        # Build output: full-width first, then left column, then right column
        text_parts = []

        # Add full-width blocks (usually title, author info at top)
        for block in full_width_blocks:
            text = extract_block_text(block)
            if text:
                text_parts.append(text)

        # Add left column
        for block in left_blocks:
            text = extract_block_text(block)
            if text:
                text_parts.append(text)

        # Add right column
        for block in right_blocks:
            text = extract_block_text(block)
            if text:
                text_parts.append(text)

        result = "\n\n".join(text_parts)

        # Clean up page-specific artifacts
        return self._clean_page_text(result, page_num)

    def _extract_text_pypdf(self, pdf_bytes: bytes, max_pages: int = 20) -> str:
        """Fallback extraction using pypdf"""
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            pages_to_read = min(len(reader.pages), max_pages)

            for i in range(pages_to_read):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise PdfServiceError(f"Failed to extract text from PDF: {e}")

    def _clean_page_text(self, text: str, page_num: int) -> str:
        """Clean up text from a single page"""
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                cleaned_lines.append('')
                continue

            # Skip page numbers (common patterns)
            if re.match(r'^[\d]+$', stripped):
                continue
            if re.match(r'^-\s*\d+\s*-$', stripped):
                continue
            if re.match(r'^Page\s+\d+', stripped, re.IGNORECASE):
                continue

            # Skip headers/footers (usually appear on every page)
            if page_num > 0:
                # arXiv ID in header
                if re.match(r'^arXiv:\d+\.\d+', stripped):
                    continue
                # Conference headers
                if re.match(r"^(WWW|KDD|SIGIR|AAAI|ICML|NeurIPS|ICLR|ACL|EMNLP|CVPR|ICCV|RecSys|WSDM|CIKM)\s*['\"]?\d{2}", stripped):
                    continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _post_process_text(self, text: str) -> str:
        """Post-process the full extracted text"""
        # Fix common PDF extraction issues

        # 1. Join hyphenated words across lines
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

        # 2. Join lines that were broken mid-sentence
        lines = text.split('\n')
        result_lines = []
        buffer = ""

        for line in lines:
            stripped = line.strip()

            if not stripped:
                # Empty line = paragraph break
                if buffer:
                    result_lines.append(buffer)
                    buffer = ""
                result_lines.append('')
                continue

            # Check if this looks like a section header
            if self._is_section_header(stripped):
                if buffer:
                    result_lines.append(buffer)
                    buffer = ""
                result_lines.append('')
                result_lines.append(stripped)
                result_lines.append('')
                continue

            # Check if we should join with previous line
            if buffer:
                # Join if: previous line doesn't end with sentence terminator
                # or current line starts with lowercase
                prev_ends_sentence = buffer.rstrip()[-1] in '.!?:' if buffer.rstrip() else False
                curr_starts_lower = stripped[0].islower() if stripped else False

                if not prev_ends_sentence or curr_starts_lower:
                    # Check if buffer ends with hyphen (word break)
                    if buffer.rstrip().endswith('-'):
                        buffer = buffer.rstrip()[:-1] + stripped
                    else:
                        buffer = buffer.rstrip() + ' ' + stripped
                else:
                    result_lines.append(buffer)
                    buffer = stripped
            else:
                buffer = stripped

        if buffer:
            result_lines.append(buffer)

        # Join and clean up excessive whitespace
        result = '\n'.join(result_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r' {2,}', ' ', result)

        return result.strip()

    def _is_section_header(self, line: str) -> bool:
        """Check if a line looks like a section header"""
        line_lower = line.lower().strip()

        # Common section patterns
        section_patterns = [
            r'^(abstract)\s*$',
            r'^(\d+\.?\s*)?(introduction|intro)\s*$',
            r'^(\d+\.?\s*)?(related\s+work|background)\s*$',
            r'^(\d+\.?\s*)?(method|methods|methodology|approach)\s*$',
            r'^(\d+\.?\s*)?(experiment|experiments|evaluation|results)\s*$',
            r'^(\d+\.?\s*)?(conclusion|conclusions|summary)\s*$',
            r'^(\d+\.?\s*)?(reference|references|bibliography)\s*$',
            r'^(\d+\.?\s*)?(acknowledgment|acknowledgments)\s*$',
            r'^(\d+\.?\s*)?(appendix)\s*$',
            r'^(\d+\.?\s*)?(discussion)\s*$',
            r'^(\d+\.?\s*)?(preliminar)',
            r'^(\d+\.?\s*)?(problem\s+definition|problem\s+statement)',
            # Numbered sections like "3 TIGER" or "3. Our Method"
            r'^\d+\.?\s+[A-Z][A-Za-z\s:]+$',
        ]

        for pattern in section_patterns:
            if re.match(pattern, line_lower, re.IGNORECASE):
                return True

        # Also check for ALL CAPS short lines (common for headers)
        if line.isupper() and len(line) < 50 and len(line.split()) <= 5:
            return True

        return False

    def extract_title_from_pdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract title from PDF (first page, first significant line)"""
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except ImportError:
            # Fallback
            return self._extract_title_pypdf(pdf_bytes)

        try:
            if not doc:
                return None

            # Try PDF metadata first
            metadata = doc.metadata
            if metadata and metadata.get('title'):
                title = metadata['title'].strip()
                if title and len(title) > 5 and not title.lower().startswith('microsoft'):
                    return title

            # Extract from first page
            first_page = doc[0]
            text = first_page.get_text("text")
            doc.close()

            if not text:
                return None

            return self._find_title_in_text(text)

        except Exception:
            return None

    def _extract_title_pypdf(self, pdf_bytes: bytes) -> Optional[str]:
        """Fallback title extraction using pypdf"""
        from pypdf import PdfReader

        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            if not reader.pages:
                return None

            if reader.metadata and reader.metadata.title:
                title = reader.metadata.title.strip()
                if title and len(title) > 5:
                    return title

            first_page = reader.pages[0]
            text = first_page.extract_text()
            if not text:
                return None

            return self._find_title_in_text(text)
        except Exception:
            return None

    def _find_title_in_text(self, text: str) -> Optional[str]:
        """Find title in first page text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        for line in lines[:15]:  # Check first 15 lines
            lower = line.lower()

            # Skip very short lines
            if len(line) < 10:
                continue
            # Skip author-like lines
            if '@' in line or 'university' in lower or 'institute' in lower:
                continue
            # Skip arXiv/date lines
            if lower.startswith('arxiv') or line.startswith('20'):
                continue
            # Skip URLs
            if 'http' in lower or 'doi.org' in lower:
                continue
            # Skip journal/publisher headers
            skip_keywords = [
                'journal', 'proceedings', 'conference', 'transactions',
                'research article', 'open access', 'vol.', 'issn',
                'published', 'accepted', 'received', 'copyright',
                'springer', 'elsevier', 'wiley', 'ieee', 'acm', 'preprint'
            ]
            if any(kw in lower for kw in skip_keywords):
                continue

            return line

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
