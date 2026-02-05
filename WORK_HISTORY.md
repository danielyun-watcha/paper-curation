# Paper Curation - Work History

## 2026-02-05: Connected Papers Feature

### 개요
Semantic Scholar Recommendations API를 활용한 Connected Papers 기능 구현. connectedpapers.com처럼 논문 간 연관성을 찾아주는 기능이지만, 그래프 시각화 대신 5개의 가장 관련있는 논문을 리스트로 표시.

### 사용자 요구사항 변화
1. **초기 요구**: "Related Papers 탭에서 내 컬렉션 논문 선택 → 관련 논문 5개 찾기"
2. **중간 수정**: "Google Scholar 검색 결과에도 Connect 버튼 추가"
3. **레이아웃 변경**: "Connected Papers를 아래가 아니라 오른쪽에 표시"
4. **Paper Detail 연동**: "논문 상세에서 Connect 클릭 시 자동으로 Connected Papers 표시"
5. **최종 단순화**: "Related Papers 탭 제거, Scholar 검색 + Connect만 사용"

### 구현된 기능

#### Backend (FastAPI)
1. **SemanticScholarService** (`backend/app/services/semantic_scholar_service.py`)
   - `get_recommendations(paper_id, limit=5)` 메서드 추가
   - Semantic Scholar Recommendations API 사용: `GET /recommendations/v1/papers/forpaper/{paper_id}`
   - `citation_count: int` 필드 추가 (인용 수)
   - `ss_id: Optional[str]` 필드 추가 (Semantic Scholar paper ID, SHA hash)
   - arxiv_id/doi가 없을 때 title 검색 후 ss_id를 fallback으로 사용

2. **새로운 Schema** (`backend/app/schemas/paper.py`)
   ```python
   class RelatedPaperResult(BaseModel):
       title: str
       authors: List[str]
       abstract: Optional[str] = None
       year: Optional[int] = None
       url: Optional[str] = None
       cited_by: int = 0
       arxiv_id: Optional[str] = None
       doi: Optional[str] = None

   class RelatedPapersResponse(BaseModel):
       paper_id: str
       paper_title: str
       results: List[RelatedPaperResult]
   ```

3. **새로운 API 엔드포인트** (`backend/app/routers/papers.py`)
   - `GET /api/papers/related/{paper_id}` - 컬렉션 내 논문의 관련 논문 찾기
   - `GET /api/papers/related-external?arxiv_id=...&doi=...&title=...` - 외부 논문의 관련 논문 찾기
   - Paper ID 생성 우선순위: `ArXiv:{arxiv_id}` > `DOI:{doi}` > `title search + ss_id`

#### Frontend (Next.js 14 + React)
1. **Search Page 재구성** (`frontend/src/app/search/page.tsx`)
   - **Before**: Google Scholar Search / Related Papers 2개 탭
   - **After**: 단일 페이지, side-by-side 레이아웃
     - 왼쪽: Scholar 검색창 + 검색 결과
     - 오른쪽: Connected Papers 패널 (Connect 버튼 클릭 시 나타남)
   - 레이아웃:
     - `hasConnected` false: `max-w-4xl` (중앙 정렬)
     - `hasConnected` true: `max-w-7xl` + `grid-cols-2` (좌우 분할)
   - 우측 패널: `lg:sticky lg:top-4` (스크롤 시 상단 고정)

2. **Connect 기능**
   - Scholar 검색 결과 각 논문에 "Connect" 버튼
   - Connected Papers 패널 내 논문에도 "Connect" 버튼 (체이닝)
   - URL에서 arxiv_id/doi 추출 후 API 호출
   - 추출 실패 시 title로 검색
   - Connect → Connect → Connect... 무한 체이닝 가능

3. **Paper Detail 연동** (`frontend/src/components/papers/PaperDetail.tsx`)
   - "Connect" 버튼 추가 (Study와 Delete 버튼 사이)
   - 클릭 시 `/search?connect={paper.id}` 로 이동
   - Search 페이지에서 `?connect=` 파라미터 감지 → 자동으로 Connected Papers 표시

4. **API Client** (`frontend/src/lib/api.ts`)
   ```typescript
   getRelatedPapers: async (paperId: string): Promise<RelatedPapersResponse>
   getRelatedPapersExternal: async (params: {
     arxiv_id?: string;
     doi?: string;
     title?: string
   }): Promise<RelatedPapersResponse>
   ```

### 기술적 세부사항

#### Semantic Scholar API
- **Endpoint**: `https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paper_id}`
- **Parameters**:
  - `limit`: 5 (고정)
  - `fields`: title,authors,abstract,year,url,externalIds,citationCount
  - `from`: all-cs (컴퓨터 과학 분야)
- **Paper ID 형식**:
  - ArXiv: `ArXiv:2506.10347`
  - DOI: `DOI:10.1145/3711896.3737026`
  - SS ID: `abc123def456...` (SHA hash)

#### 에러 처리
- 404: "Paper not found in Semantic Scholar"
- 429: "Rate limited by Semantic Scholar API"
- Google Scholar 검색 결과는 url/pub_url에서 arxiv_id/doi 추출 시도
- 추출 실패 시 title로 Semantic Scholar 검색 → ss_id 획득 → Recommendations API 호출

#### URL 파라미터
- `/search?connect={paper_id}` - 컬렉션 내 논문의 Connected Papers 자동 표시

### 제거된 기능
- Related Papers 탭 완전 제거
- `papers`, `papersLoading`, `papersLoadError`, `selectedPaperId`, `paperFilter` 등 state 제거
- `handleFindRelated`, `handleConnectRelated` 등 handler 제거
- `filteredPapers` 등 컬렉션 관련 로직 제거

### 파일 변경 내역
```
backend/app/services/semantic_scholar_service.py (NEW)
backend/app/schemas/paper.py (MODIFIED)
backend/app/schemas/__init__.py (MODIFIED)
backend/app/routers/papers.py (MODIFIED)
frontend/src/types/index.ts (MODIFIED)
frontend/src/lib/api.ts (MODIFIED)
frontend/src/app/search/page.tsx (REWRITTEN)
frontend/src/components/papers/PaperDetail.tsx (MODIFIED)
```

### Git Commit
- **Commit**: abc6328
- **Branch**: main
- **Date**: 2026-02-05
- **Message**: "Add Connected Papers feature with side-by-side layout"

### 알려진 이슈
1. **Google Scholar 결과에서 Connect 실패 가능성**
   - Scholar 검색 결과의 URL에서 arxiv_id/doi 추출 실패 시
   - Title로 Semantic Scholar 검색했는데 매칭 안 될 경우
   - 에러: "Cannot find this paper in Semantic Scholar"

2. **Rate Limiting**
   - Semantic Scholar API는 rate limit 있음 (429 에러)
   - 현재 별도 처리 없음 (에러 메시지만 표시)

### 향후 개선 가능성
1. Semantic Scholar API key 추가 (rate limit 완화)
2. Connect 실패 시 retry 로직
3. Connected Papers 패널에 "Close" 버튼 추가
4. 이미 추가된 논문 표시 (중복 방지)
5. Citation count 기반 정렬 옵션

---

## Context for Future Sessions

### 프로젝트 구조
- **Backend**: FastAPI (Python) - `/Users/daniel/paper-curation/backend`
- **Frontend**: Next.js 14 (React, TypeScript, Tailwind) - `/Users/daniel/paper-curation/frontend`
- **Database**: JSON 파일 기반 (`backend/data/papers.json`)
- **API Base URL**: `http://172.16.20.12:8000` (VPN 내부 IP)

### 실행 방법
```bash
# Backend (port 8000)
cd /Users/daniel/paper-curation/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (port 3000)
cd /Users/daniel/paper-curation/frontend
npm run dev
```

### 주요 의존성
- **Backend**: fastapi, httpx, python-dotenv
- **Frontend**: next@14, react, tailwind
- **External APIs**:
  - Semantic Scholar (recommendations)
  - Google Scholar (via scholarly library)
  - arXiv API
  - DOI (via Crossref)

### 환경 변수
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://172.16.20.12:8000`

### 참고사항
- `.next` 캐시 이슈가 자주 발생 → `rm -rf .next` 후 재시작
- Backend는 hot reload 지원
- 한국어-영어 혼용 UI (사용자가 한국인)
