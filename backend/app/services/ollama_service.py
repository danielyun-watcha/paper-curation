from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class PaperSummary:
    one_line: str
    contribution: str
    methodology: str
    results: str


class OllamaServiceError(Exception):
    pass


class OllamaService:
    """Service for generating paper summaries using Ollama"""

    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    DEFAULT_MODEL = "gemma3:4b"

    SUMMARY_PROMPT = """You are a research paper summarizer. Given a paper's title and abstract, provide a summary in the following JSON format:

{{
    "one_line": "A single sentence (max 50 words) capturing the paper's main contribution",
    "contribution": "2-3 sentences describing the key contributions",
    "methodology": "2-3 sentences explaining the approach/method",
    "results": "2-3 sentences summarizing main results and findings"
}}

IMPORTANT:
- Respond ONLY with valid JSON, no other text
- Be concise and technical
- Focus on what's novel and important

Title: {title}

Abstract: {abstract}

JSON Response:"""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    async def generate_summary(self, title: str, abstract: str) -> PaperSummary:
        """Generate a structured summary for a paper"""
        prompt = self.SUMMARY_PROMPT.format(title=title, abstract=abstract)

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    self.OLLAMA_API_URL,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1024,
                        }
                    },
                )

                if response.status_code != 200:
                    raise OllamaServiceError(f"Ollama API error: {response.status_code}")

                result = response.json()
                generated_text = result.get("response", "")

                # Parse JSON from response
                summary_data = self._parse_json_response(generated_text)

                return PaperSummary(
                    one_line=summary_data.get("one_line", ""),
                    contribution=summary_data.get("contribution", ""),
                    methodology=summary_data.get("methodology", ""),
                    results=summary_data.get("results", ""),
                )

            except httpx.ConnectError:
                raise OllamaServiceError("Cannot connect to Ollama. Is it running? (ollama serve)")
            except httpx.TimeoutException:
                raise OllamaServiceError("Ollama request timed out")

    def _parse_json_response(self, text: str) -> dict:
        """Extract and parse JSON from the response"""
        text = text.strip()

        # Try to find JSON in the response
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            raise OllamaServiceError("No JSON found in response")

        json_str = text[start_idx:end_idx]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise OllamaServiceError(f"Failed to parse JSON: {e}")

    TRANSLATION_PROMPT = """You are a professional translator. Translate the following research paper content to Korean.

IMPORTANT:
- Translate naturally and accurately
- Keep technical terms in English with Korean explanation in parentheses if needed
- Maintain the original structure and meaning
- Output ONLY the Korean translation, no other text

Title: {title}

Abstract: {abstract}

Korean Translation:"""

    async def translate_to_korean(self, title: str, abstract: str) -> dict:
        """Translate paper title and abstract to Korean"""
        prompt = self.TRANSLATION_PROMPT.format(title=title, abstract=abstract)

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(
                    self.OLLAMA_API_URL,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 2048,
                        }
                    },
                )

                if response.status_code != 200:
                    raise OllamaServiceError(f"Ollama API error: {response.status_code}")

                result = response.json()
                translated_text = result.get("response", "").strip()

                # Try to split title and abstract from the translation
                lines = translated_text.split("\n\n", 1)
                if len(lines) >= 2:
                    return {
                        "title": lines[0].strip(),
                        "abstract": lines[1].strip(),
                    }
                else:
                    # If can't split, return all as abstract
                    return {
                        "title": "",
                        "abstract": translated_text,
                    }

            except httpx.ConnectError:
                raise OllamaServiceError("Cannot connect to Ollama. Is it running? (ollama serve)")
            except httpx.TimeoutException:
                raise OllamaServiceError("Ollama request timed out")

    async def check_health(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in models)
                return False
        except Exception:
            return False

    SECTION_TRANSLATION_PROMPT = """Translate the following academic paper text to Korean.

RULES:
- Translate the given text accurately and naturally into Korean
- Keep technical terms in English (add Korean explanation in parentheses if helpful)
- Preserve equations, formulas, and citations [1], [2] as-is
- Do NOT add any content not in the original text
- Do NOT add section headers, labels, or numbering
- Do NOT output anything except the Korean translation
- If text ends mid-sentence, just translate what is given

Text to translate:
{text}

Korean:"""

    def _clean_translation(self, text: str) -> str:
        """Clean up translated text to remove hallucinated content."""
        import re

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line_stripped = line.strip()

            # Skip chunk/part markers like "방법 (3/3)", "서론 (1/2)"
            if re.match(r'^[\w\s]+(하|론|록|법|과|론)\s*\(\d+/\d+\)', line_stripped):
                continue
            # Skip lines that indicate hallucinated section markers
            if re.match(r'^\*?\*?초록\s*\(\d+/\d+\)', line_stripped):
                continue
            if re.match(r'^\*?\*?(Section|Part|번역)\s*\d+', line_stripped, re.IGNORECASE):
                continue
            # Skip lines that look like the model is starting a new section
            if re.match(r'^(Korean Translation|영어 원문|Original|번역문|Korean|번역):?\s*$', line_stripped):
                continue
            # Skip template/placeholder text (hallucination)
            if re.search(r'\[.*?(목적|내용|요약|설명|언급|제시|작성).*?\]', line_stripped):
                continue
            # Skip conference reference lines (translated)
            if re.match(r"^(KDD|SIGKDD|SIGIR|WWW|AAAI|ICML|NeurIPS|ICLR|ACL|EMNLP)\s*['\"]?\d{2}", line_stripped):
                continue
            if re.search(r'\d{1,2}월\s+\d{1,2}일.*?(토론토|뉴욕|시애틀|밴쿠버|런던|파리|시드니)', line_stripped):
                continue
            # Skip lines that are just ** markers
            if re.match(r'^\*\*[\w\s]+\*\*\s*$', line_stripped) and len(line_stripped) < 20:
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    def _filter_abstract_authors(self, text: str) -> str:
        """Remove author names and affiliations that got mixed into abstract."""
        import re

        # Common patterns for author info that shouldn't be in abstract
        # Pattern 1: Name followed by affiliation (University, Google, etc.)
        # Pattern 2: Multiple names with asterisks (corresponding author markers)
        # Pattern 3: Email-like patterns

        lines = text.split('\n')
        filtered_lines = []

        author_patterns = [
            # Name + University/Company pattern
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+[\*†]?\s+(University|Google|DeepMind|Microsoft|Meta|Amazon|Apple|Alibaba|Tencent|Baidu|Huawei)',
            # Multiple names on same line (typical author list)
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+[\*†]?\s*,?\s*){3,}',
            # Email patterns
            r'@(gmail|google|edu|com|org|cn|ac\.|mail)',
            # Lines with mostly names (CamelCase words)
            r'^([A-Z][a-z]+\s+){4,}[A-Z][a-z]+$',
            # Affiliation-only lines
            r'^(University|Department|School|Institute|Lab|Google|DeepMind|Microsoft)\s+of',
            # Lines starting with asterisk (author notes)
            r'^\*\s*(Equal|Corresponding)',
        ]

        for line in lines:
            stripped = line.strip()
            should_skip = False

            for pattern in author_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    should_skip = True
                    break

            # Skip lines that look like author lists (many capitalized words, no verbs)
            if not should_skip:
                words = stripped.split()
                if len(words) >= 4:
                    capitalized = sum(1 for w in words if w[0].isupper() and len(w) > 1)
                    # If more than 70% of words are capitalized names and line is short
                    if capitalized / len(words) > 0.7 and len(stripped) < 200:
                        # Check if it looks like author names (no common verbs/articles)
                        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                                       'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                                       'could', 'should', 'may', 'might', 'must', 'can', 'for',
                                       'with', 'from', 'that', 'this', 'which', 'where', 'when'}
                        has_common = any(w.lower() in common_words for w in words)
                        if not has_common:
                            should_skip = True

            if not should_skip:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines).strip()

    def _filter_metadata_noise(self, text: str) -> str:
        """Remove author info, affiliations, copyright notices, and other metadata noise."""
        import re

        lines = text.split('\n')
        filtered_lines = []

        # Patterns to skip
        skip_patterns = [
            r'@.*\.(edu|com|org|cn|ac)',  # Email addresses
            r'^[A-Z][a-z]+\s+(University|Institute|Lab|College)',  # Affiliations
            r'^\*.*corresponding author',  # Corresponding author notes
            r'^(Permission|ACM|Copyright|©|\d{4}\s+Copyright)',  # Copyright notices
            r'^(CCS\s+Concepts|ACM\s+Reference|Keywords:)',  # ACM metadata
            r'^https?://(doi\.org|dx\.doi)',  # DOI URLs
            r'^(ISBN|DOI|ISSN)\s*[\d\-]',  # Identifiers
            r'^arXiv:\d+\.\d+',  # arXiv ID lines
            r'^\s*permissions@acm\.org',  # ACM permissions
            r"^(KDD|SIGKDD|SIGIR|WWW|AAAI|ICML|NeurIPS|ICLR|ACL|EMNLP|NAACL|CVPR|ICCV|ECCV|CIKM|RecSys|WSDM)\s*['\"]?\d{2}",  # Conference references
            r"^\d{4}\s+(ACM|IEEE)",  # Year + Publisher
            r"^Proceedings\s+of",  # Proceedings headers
            r"^In\s+Proceedings",  # "In Proceedings of..."
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+.*\d{4}",  # Date patterns
            r"^\d+\s+(pages?|pp\.)",  # Page numbers
            # Conference venue/date lines (English)
            r"(Sydney|Toronto|New York|Seattle|Vancouver|London|Paris|Singapore|Barcelona|San Francisco|Beijing|Shanghai).*\d{4}",
            r"\d{4}년\s+\d{1,2}월",  # Korean date patterns (translated)
            # Author name patterns like "Ye and Guo, et al."
            r"^[A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+,?\s*(et\s+al\.?)?$",
            r",\s*et\s+al\.\s*$",  # Lines ending with "et al."
        ]

        in_author_block = False
        blank_count = 0

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines in author block
            if in_author_block:
                if line_stripped == '':
                    blank_count += 1
                    if blank_count >= 2:
                        in_author_block = False
                    continue
                blank_count = 0

            # Check if line matches skip patterns
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    should_skip = True
                    in_author_block = True
                    blank_count = 0
                    break

            # Skip lines that look like author names followed by affiliation
            if not should_skip and re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s*$', line_stripped):
                # Likely an author name, check next few lines for affiliation patterns
                should_skip = True
                in_author_block = True
                blank_count = 0

            if not should_skip and not in_author_block:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def _filter_tables_and_figures(self, text: str) -> str:
        """Remove tables, figures, and their captions from text before translation."""
        import re

        # First filter metadata noise
        text = self._filter_metadata_noise(text)

        lines = text.split('\n')
        filtered_lines = []
        in_table_or_figure = False
        blank_line_count = 0

        # Pattern for table data: lines with multiple numbers/decimals
        table_data_pattern = re.compile(r'^\s*[\w\-\(\)]+\s+\d+\.?\d*\s+\d+\.?\d*')  # "Model(2019) 0.123 0.456..."
        numeric_heavy_pattern = re.compile(r'(\d+\.?\d*\s+){3,}')  # 3+ consecutive numbers
        header_row_pattern = re.compile(r'^\s*(Model|Dataset|Method|Metric|NG@|HR@|MRR|AUC|Recall|Precision|NDCG|F1)', re.IGNORECASE)
        # Pattern for model names with years like KGCN(2019), KGAT(2019)
        model_year_pattern = re.compile(r'^[A-Z]+[a-z]*[\-]?[A-Z]*\s*\(\d{4}\)\s+\d')

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Detect table/figure captions
            if re.match(r'^(table|표)\s*\d+', line_lower):
                if not in_table_or_figure:
                    filtered_lines.append("\n[표 생략]\n")
                in_table_or_figure = True
                blank_line_count = 0
                continue

            if re.match(r'^(figure|fig\.?|그림)\s*\d+', line_lower):
                if not in_table_or_figure:
                    filtered_lines.append("\n[그림 생략]\n")
                in_table_or_figure = True
                blank_line_count = 0
                continue

            # If we're in a table/figure section
            if in_table_or_figure:
                # Check for blank line
                if line_stripped == '':
                    blank_line_count += 1
                    # Two consecutive blank lines = end of table/figure
                    if blank_line_count >= 2:
                        in_table_or_figure = False
                    continue

                # Reset blank line counter if we see content
                blank_line_count = 0

                # Skip table data rows and headers
                if table_data_pattern.match(line_stripped) or header_row_pattern.match(line_stripped):
                    continue

                # Skip short lines that are likely part of table/figure (captions, labels)
                if len(line_stripped) < 100 and not line_stripped.endswith('.'):
                    continue

                # If we see a long sentence ending with period, probably back to main text
                if len(line_stripped) > 100 and line_stripped.endswith('.'):
                    in_table_or_figure = False
                    filtered_lines.append(line)
                    continue

                # Skip this line (still in table/figure)
                continue

            # Check for table-like data even outside explicit table sections
            if model_year_pattern.match(line_stripped):
                continue
            if numeric_heavy_pattern.search(line_stripped) and len(line_stripped) < 200:
                # Line has many numbers and is short - likely table data
                continue
            if table_data_pattern.match(line_stripped):
                continue

            # Not in table/figure - keep the line
            filtered_lines.append(line)

        # Clean up multiple consecutive [표 생략] or [그림 생략]
        result = '\n'.join(filtered_lines)
        result = re.sub(r'(\[표 생략\]\s*)+', '[표 생략]\n', result)
        result = re.sub(r'(\[그림 생략\]\s*)+', '[그림 생략]\n', result)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

    def _clean_pdf_text(self, text: str) -> str:
        """Clean up PDF extracted text by fixing broken lines and artifacts."""
        import re

        lines = text.split('\n')
        paragraphs = []
        current_para = []

        # Section header patterns
        section_header_patterns = [
            r'^(Abstract|ABSTRACT)\s*$',
            r'^(\d+\.?\s*)?(Introduction|INTRODUCTION)\s*$',
            r'^(\d+\.?\s*)?(Related\s+Work|RELATED\s+WORK)\s*$',
            r'^(\d+\.?\s*)?(Method|METHODS?|Methodology|METHODOLOGY)\s*$',
            r'^(\d+\.?\s*)?(Experiment|EXPERIMENTS?|Evaluation)\s*$',
            r'^(\d+\.?\s*)?(Conclusion|CONCLUSIONS?)\s*$',
            r'^(\d+\.?\s*)?(Reference|REFERENCES?)\s*$',
            r'^(\d+\.?\s*)?(Appendix|APPENDIX)\s*$',
            r'^(\d+\.?\s*)?(Acknowledgment|ACKNOWLEDGMENTS?)\s*$',
            r'^(\d+\.?\s*)?(Discussion|DISCUSSION)\s*$',
            r'^(\d+\.?\s*)?(Results|RESULTS)\s*$',
            r'^(\d+\.?\s*)?(Background|BACKGROUND)\s*$',
            r'^(\d+\.?\s*)?(Preliminar|PRELIMINAR)',
            r'^(\d+\.?\s*)?(Analysis|ANALYSIS)\s*$',
            r'^(\d+\.?\s*)?(Ablation|ABLATION)\s*$',
        ]

        def is_section_header(line: str) -> bool:
            for pattern in section_header_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    return True
            return False

        def should_join(prev_line: str, curr_line: str) -> bool:
            """Determine if two lines should be joined."""
            if not prev_line or not curr_line:
                return False

            prev = prev_line.strip()
            curr = curr_line.strip()

            if not prev or not curr:
                return False

            # Don't join if previous line ends with proper sentence end
            if prev[-1] in '.!?:':
                # But still join if current line starts lowercase (continuation)
                if curr[0].islower():
                    return True
                return False

            # Join if previous line ends with hyphen (word break)
            if prev.endswith('-'):
                return True

            # Join if line is short (likely broken mid-sentence)
            if len(prev) < 80:
                return True

            # Join if current line starts with lowercase
            if curr[0].islower():
                return True

            # Join if current starts with common continuation patterns
            if re.match(r'^(and|or|but|that|which|where|when|while|with|for|to|of|in|on|at|by|from|as|is|are|was|were|has|have|had|can|could|will|would|may|might)\b', curr, re.IGNORECASE):
                return True

            return False

        for line in lines:
            stripped = line.strip()

            # Empty line = paragraph break
            if not stripped:
                if current_para:
                    # Join all lines in current paragraph with space
                    para_text = ' '.join(current_para)
                    # Clean up multiple spaces
                    para_text = re.sub(r'\s+', ' ', para_text)
                    # Fix hyphenated word breaks
                    para_text = re.sub(r'(\w)- (\w)', r'\1\2', para_text)
                    paragraphs.append(para_text)
                    current_para = []
                continue

            # Section header = new paragraph
            if is_section_header(stripped):
                if current_para:
                    para_text = ' '.join(current_para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = re.sub(r'(\w)- (\w)', r'\1\2', para_text)
                    paragraphs.append(para_text)
                    current_para = []
                paragraphs.append("")  # blank before header
                paragraphs.append(stripped)
                paragraphs.append("")  # blank after header
                continue

            # Check if we should join with previous line or start new
            if current_para:
                prev_line = current_para[-1]
                if should_join(prev_line, stripped):
                    # Join with previous, handling hyphen breaks
                    if prev_line.endswith('-'):
                        current_para[-1] = prev_line[:-1] + stripped
                    else:
                        current_para.append(stripped)
                else:
                    # End current paragraph and start new
                    para_text = ' '.join(current_para)
                    para_text = re.sub(r'\s+', ' ', para_text)
                    para_text = re.sub(r'(\w)- (\w)', r'\1\2', para_text)
                    paragraphs.append(para_text)
                    current_para = [stripped]
            else:
                current_para.append(stripped)

        # Don't forget the last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            para_text = re.sub(r'\s+', ' ', para_text)
            para_text = re.sub(r'(\w)- (\w)', r'\1\2', para_text)
            paragraphs.append(para_text)

        # Join paragraphs with double newlines
        result = '\n\n'.join(p for p in paragraphs if p or p == "")

        # Clean up excessive blank lines
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result.strip()

    def _parse_paper_sections(self, text: str) -> list[dict]:
        """Parse paper text into sections"""
        import re

        # First, clean up the PDF text
        text = self._clean_pdf_text(text)

        sections = []

        # Section patterns - more flexible matching
        # Pattern: optional number + section keyword + optional additional text
        section_keywords = {
            'Abstract': ['abstract'],
            'Introduction': ['introduction', 'intro'],
            'Preliminaries': ['preliminary', 'preliminaries', 'problem definition', 'problem statement', 'problem formulation', 'problem setup'],
            'Motivation': ['motivation'],
            'Related Work': ['related work', 'related works', 'background', 'literature review', 'prior work'],
            'Method': ['method', 'methods', 'methodology', 'approach', 'proposed method', 'proposed approach',
                       'our method', 'our approach', 'model', 'framework', 'architecture', 'the .* model',
                       'our framework', 'proposed framework'],
            'Experiments': ['experiment', 'experiments', 'evaluation', 'empirical study', 'empirical evaluation',
                           'experimental setup', 'experimental results', 'results'],
            'Analysis': ['analysis', 'ablation', 'ablation study', 'ablation studies'],
            'Discussion': ['discussion', 'discussions'],
            'Conclusion': ['conclusion', 'conclusions', 'summary', 'future work', 'concluding remarks'],
            'Acknowledgments': ['acknowledgment', 'acknowledgments', 'acknowledgement', 'acknowledgements'],
            'References': ['reference', 'references', 'bibliography'],
            'Appendix': ['appendix', 'supplementary', 'supplementary material'],
        }

        def get_section_name(line: str) -> str | None:
            """Check if line is a section header and return normalized section name."""
            line_lower = line.strip().lower()
            # Remove leading numbers like "1.", "2", "3.", etc.
            line_clean = re.sub(r'^[\d.]+\s*', '', line_lower).strip()

            for section_name, keywords in section_keywords.items():
                for keyword in keywords:
                    # Check if line starts with the keyword
                    if line_clean.startswith(keyword):
                        return section_name
                    # Also check with regex for patterns like "the TIGER model"
                    if keyword.startswith('the ') and re.match(keyword, line_clean):
                        return section_name
            return None

        def is_section_header(line: str) -> bool:
            """Check if a line looks like a section header."""
            stripped = line.strip()
            if not stripped:
                return False

            # Must be relatively short (section titles are usually under 100 chars)
            if len(stripped) > 100:
                return False

            # Check if it matches known section patterns
            if get_section_name(stripped):
                return True

            # Check for numbered sections like "3 TIGER" or "3. Our Method"
            if re.match(r'^\d+\.?\s+[A-Z]', stripped):
                # It's a numbered section, but not a known keyword
                # Still treat as potential section if it's short and title-case
                if len(stripped) < 80:
                    return True

            return False

        lines = text.split('\n')
        current_section = None  # Start with None, not "Abstract"
        current_content = []
        found_first_section = False

        for line in lines:
            stripped = line.strip()

            # Check if this line is a section header
            detected_section = get_section_name(stripped)

            if detected_section or is_section_header(line):
                found_first_section = True

                # Save previous section
                if current_section and current_content:
                    content_text = '\n'.join(current_content).strip()
                    if content_text:
                        # Filter author info from abstract
                        if current_section == "Abstract":
                            content_text = self._filter_abstract_authors(content_text)
                        sections.append({
                            "name": current_section,
                            "content": content_text
                        })

                # Start new section - use detected name or extract from line
                if detected_section:
                    current_section = detected_section
                else:
                    # Extract section name from numbered header like "3 TIGER: ..."
                    cleaned = re.sub(r'^\d+\.?\s*', '', stripped)
                    # Take only the first part before colon if exists
                    if ':' in cleaned:
                        cleaned = cleaned.split(':')[0].strip()
                    current_section = cleaned.title() if cleaned else "Section"
                current_content = []
            elif found_first_section and current_section:
                # Only add content after we've found the first section header
                current_content.append(line)
            # else: Skip content before first section (title, authors, etc.)

        # Don't forget the last section
        if current_content:
            content_text = '\n'.join(current_content).strip()
            if content_text:
                sections.append({
                    "name": current_section,
                    "content": content_text
                })

        # If no sections found, return the whole text as one section
        if not sections:
            sections.append({
                "name": "Full Paper",
                "content": text.strip()
            })

        return sections

    def _split_into_chunks(self, text: str, max_chars: int = 3000) -> list[str]:
        """Split text into chunks, trying to break at paragraph or sentence boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= max_chars:
                chunks.append(remaining)
                break

            # Try to find a good break point within max_chars
            chunk = remaining[:max_chars]

            # Priority 1: Break at paragraph (double newline)
            last_para = chunk.rfind('\n\n')
            if last_para > max_chars * 0.5:  # At least 50% of chunk
                chunks.append(remaining[:last_para].strip())
                remaining = remaining[last_para:].strip()
                continue

            # Priority 2: Break at sentence end (. followed by space or newline)
            last_sentence = -1
            for i in range(len(chunk) - 1, max_chars // 2, -1):
                if chunk[i] == '.' and (i + 1 >= len(chunk) or chunk[i + 1] in ' \n'):
                    last_sentence = i + 1
                    break

            if last_sentence > 0:
                chunks.append(remaining[:last_sentence].strip())
                remaining = remaining[last_sentence:].strip()
                continue

            # Priority 3: Break at any newline
            last_newline = chunk.rfind('\n')
            if last_newline > max_chars * 0.5:
                chunks.append(remaining[:last_newline].strip())
                remaining = remaining[last_newline:].strip()
                continue

            # Fallback: Hard break at max_chars
            chunks.append(remaining[:max_chars].strip())
            remaining = remaining[max_chars:].strip()

        return chunks

    async def _translate_chunk(
        self, client: httpx.AsyncClient, section_name: str, text: str, chunk_num: int = 0, total_chunks: int = 1
    ) -> str:
        """Translate a single chunk of text."""
        # Don't include chunk info in prompt - just translate the text
        prompt = self.SECTION_TRANSLATION_PROMPT.format(text=text)

        response = await client.post(
            self.OLLAMA_API_URL,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 6000,
                    "stop": ["Text to translate:", "Korean:", "---", "\n\n\n"],
                }
            },
        )

        if response.status_code != 200:
            return f"[번역 실패: {response.status_code}]"

        result = response.json()
        translated = result.get("response", "").strip()

        # Post-process: remove any hallucinated section markers
        translated = self._clean_translation(translated)
        return translated

    async def translate_full_paper(self, text: str) -> list[dict]:
        """Translate full paper text to Korean, section by section with chunking for long sections."""
        sections = self._parse_paper_sections(text)
        translated_sections = []

        async with httpx.AsyncClient(timeout=300.0) as client:
            for section in sections:
                # Skip very short sections or references
                if len(section["content"]) < 50:
                    translated_sections.append({
                        "name": section["name"],
                        "original": section["content"],
                        "translated": section["content"]  # Keep as-is
                    })
                    continue

                if section["name"].lower() in ["references", "bibliography", "acknowledgments", "appendix"]:
                    translated_sections.append({
                        "name": section["name"],
                        "original": section["content"],
                        "translated": "[참고문헌 생략]" if "reference" in section["name"].lower() else section["content"]
                    })
                    continue

                content = section["content"]

                try:
                    # Filter out tables and figures before translation
                    filtered_content = self._filter_tables_and_figures(content)

                    # Split long sections into chunks (5000 chars ~ 1500 tokens)
                    chunks = self._split_into_chunks(filtered_content, max_chars=5000)
                    translated_parts = []

                    for i, chunk in enumerate(chunks):
                        translated = await self._translate_chunk(
                            client, section["name"], chunk, i, len(chunks)
                        )
                        translated_parts.append(translated)

                    # Combine all translated parts
                    translated_sections.append({
                        "name": section["name"],
                        "original": content,
                        "translated": "\n\n".join(translated_parts)
                    })

                except httpx.ConnectError:
                    raise OllamaServiceError("Cannot connect to Ollama. Is it running? (ollama serve)")
                except httpx.TimeoutException:
                    translated_sections.append({
                        "name": section["name"],
                        "original": section["content"],
                        "translated": "[번역 시간 초과]"
                    })

        return translated_sections

    FULL_SUMMARY_PROMPT = """다음 논문을 한국어로 요약해주세요.

정확히 아래 형식으로 작성하세요:

**연구 배경**

(이 논문이 해결하려는 문제와 연구 동기를 2-3문장으로 설명)

**핵심 기여**

- (이 논문의 첫 번째 주요 기여)
- (두 번째 주요 기여)
- (세 번째 주요 기여)

**방법론**

(제안된 방법, 모델 구조, 핵심 아이디어를 5-7문장으로 상세히 설명)

규칙: 위 3개 섹션만 작성. 다른 섹션 추가 금지. 각 섹션 제목은 **굵게** 표시.

논문:
{text}

요약:"""

    async def summarize_full_paper(self, text: str) -> str:
        """Summarize full paper text in Korean"""
        # Limit text length to avoid timeout
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... truncated for length ...]"

        prompt = self.FULL_SUMMARY_PROMPT.format(text=text)

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    self.OLLAMA_API_URL,
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 1500,
                            "repeat_penalty": 1.3,
                            "stop": ["---", "Translation:", "English:"],
                        }
                    },
                )

                if response.status_code != 200:
                    raise OllamaServiceError(f"Ollama API error: {response.status_code}")

                result = response.json()
                summary = result.get("response", "").strip()

                # Post-process: clean up formatting
                summary = self._clean_summary(summary)
                return summary

            except httpx.ConnectError:
                raise OllamaServiceError("Cannot connect to Ollama. Is it running? (ollama serve)")
            except httpx.TimeoutException:
                raise OllamaServiceError("Ollama request timed out")

    def _clean_summary(self, text: str) -> str:
        """Clean up summary formatting"""
        import re

        # Keep ** for section titles (연구 배경, 핵심 기여, 방법론) but remove from elsewhere
        # First, protect section titles
        section_titles = ['연구 배경', '핵심 기여', '방법론', '연구배경', '핵심기여']
        for title in section_titles:
            text = text.replace(f'**{title}**', f'__BOLD__{title}__ENDBOLD__')

        # Remove other ** markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        # Restore section title bold markers
        text = text.replace('__BOLD__', '**').replace('__ENDBOLD__', '**')

        # Remove ## headers
        text = re.sub(r'^##\s*', '', text, flags=re.MULTILINE)

        # Replace * bullets with -
        text = re.sub(r'^\s*\*\s+', '- ', text, flags=re.MULTILINE)

        # Ensure blank line after section titles
        for title in section_titles:
            text = re.sub(rf'(\*\*{title}\*\*)\n([^\n])', rf'\1\n\n\2', text)

        # Remove excessive newlines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()


_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service
