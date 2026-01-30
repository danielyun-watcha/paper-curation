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

    SECTION_TRANSLATION_PROMPT = """You are a professional translator. Translate the following research paper section to Korean.

IMPORTANT:
- Translate naturally and accurately
- Keep technical terms in English with Korean explanation in parentheses if needed
- Preserve mathematical equations and formulas as-is (do not translate LaTeX/math notation)
- SKIP the following content (do not translate):
  * Table descriptions and table contents
  * Figure descriptions and captions
  * Author names, affiliations, emails
  * Acknowledgments
  * References/Bibliography
- Output ONLY the Korean translation of the main text and equations

Section: {section_name}

Content:
{text}

Korean Translation:"""

    def _parse_paper_sections(self, text: str) -> list[dict]:
        """Parse paper text into sections"""
        import re

        sections = []

        # Common section patterns in research papers
        section_patterns = [
            r'^(Abstract|ABSTRACT)\s*$',
            r'^(\d+\.?\s*)?(Introduction|INTRODUCTION)\s*$',
            r'^(\d+\.?\s*)?(Related\s+Work|RELATED\s+WORK|Background|BACKGROUND|Literature\s+Review)\s*$',
            r'^(\d+\.?\s*)?(Method|METHODS?|Methodology|METHODOLOGY|Approach|APPROACH|Proposed\s+Method)\s*$',
            r'^(\d+\.?\s*)?(Experiment|EXPERIMENTS?|Evaluation|EVALUATION|Results|RESULTS)\s*$',
            r'^(\d+\.?\s*)?(Discussion|DISCUSSION)\s*$',
            r'^(\d+\.?\s*)?(Conclusion|CONCLUSIONS?|Summary|SUMMARY)\s*$',
            r'^(\d+\.?\s*)?(Acknowledgment|ACKNOWLEDGMENTS?)\s*$',
            r'^(\d+\.?\s*)?(Reference|REFERENCES?|Bibliography)\s*$',
        ]

        combined_pattern = '|'.join(f'({p})' for p in section_patterns)

        lines = text.split('\n')
        current_section = "Abstract"
        current_content = []

        for line in lines:
            # Check if this line is a section header
            is_header = False
            for pattern in section_patterns:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    # Save previous section
                    if current_content:
                        content_text = '\n'.join(current_content).strip()
                        if content_text:
                            sections.append({
                                "name": current_section,
                                "content": content_text
                            })
                    # Start new section
                    current_section = re.sub(r'^\d+\.?\s*', '', line.strip()).title()
                    current_content = []
                    is_header = True
                    break

            if not is_header:
                current_content.append(line)

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

    async def translate_full_paper(self, text: str) -> list[dict]:
        """Translate full paper text to Korean, section by section"""
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

                if section["name"].lower() in ["references", "bibliography", "acknowledgments"]:
                    translated_sections.append({
                        "name": section["name"],
                        "original": section["content"],
                        "translated": "[참고문헌 생략]" if "reference" in section["name"].lower() else section["content"]
                    })
                    continue

                # Limit section length
                content = section["content"]
                if len(content) > 5000:
                    content = content[:5000] + "\n\n[... 길이 제한으로 생략 ...]"

                prompt = self.SECTION_TRANSLATION_PROMPT.format(
                    section_name=section["name"],
                    text=content
                )

                try:
                    response = await client.post(
                        self.OLLAMA_API_URL,
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.3,
                                "num_predict": 4096,
                            }
                        },
                    )

                    if response.status_code != 200:
                        translated_sections.append({
                            "name": section["name"],
                            "original": section["content"],
                            "translated": f"[번역 실패: {response.status_code}]"
                        })
                        continue

                    result = response.json()
                    translated_text = result.get("response", "").strip()

                    translated_sections.append({
                        "name": section["name"],
                        "original": section["content"],
                        "translated": translated_text
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
