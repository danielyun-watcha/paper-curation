# Paper Curation - Claude Development Guide

> 이 문서는 Claude가 이 프로젝트에서 작업할 때 참고할 종합 가이드입니다.
> 세션별 작업 기록은 `WORK_HISTORY.md`를 참고하세요.

## 프로젝트 개요

학술 논문 큐레이션 및 관리 시스템. 사용자가 관심있는 논문을 수집하고, 관련 논문을 찾고, 읽기 상태를 추적하는 웹 애플리케이션.

### 핵심 기능
- 📚 **논문 관리**: SQLite 기반 로컬 데이터베이스
- 🔍 **Google Scholar 검색**: scholarly 라이브러리를 통한 논문 검색
- 🔗 **Connected Papers**: Semantic Scholar API로 관련 논문 찾기
- 📊 **그래프 시각화**: 논문 간 연관성을 인터랙티브 그래프로 표시
- 📖 **읽기 추적**: 논문별 읽기 상태 및 메모 관리
- 📄 **PDF 업로드**: 로컬 PDF 파일 업로드 및 자동 메타데이터 추출

### 기술 스택
- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Database**: SQLite (`backend/data/papers.db`)
- **External APIs**: Semantic Scholar, Google Scholar, arXiv, Crossref, DeepL (번역)

## 프로젝트 구조

```
paper-curation/
├── backend/                      # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 설정 (환경변수)
│   │   ├── db/                  # SQLite 데이터베이스
│   │   │   ├── __init__.py
│   │   │   ├── connection.py    # DB 연결 관리
│   │   │   └── schema.py        # 테이블 스키마
│   │   ├── repositories/
│   │   │   └── paper_repository.py # 논문 CRUD (SQLite)
│   │   ├── routers/
│   │   │   └── papers.py        # 논문 API 엔드포인트
│   │   ├── services/
│   │   │   ├── scholar_service.py         # Google Scholar 검색
│   │   │   ├── semantic_scholar_service.py # Semantic Scholar API
│   │   │   ├── arxiv_service.py           # arXiv API
│   │   │   ├── crossref_service.py        # Crossref DOI 검색
│   │   │   ├── deepl_service.py           # DeepL 번역 API
│   │   │   └── cache_service.py           # 인메모리 캐시 (API 응답)
│   │   ├── schemas/
│   │   │   └── paper.py         # Pydantic 모델 (API 스키마)
│   │   └── utils/
│   │       └── pdf_utils.py     # PDF 처리 유틸
│   ├── data/
│   │   ├── papers.db            # SQLite 데이터베이스
│   │   └── uploads/             # 업로드된 PDF 파일
│   ├── scripts/
│   │   └── migrate_to_sqlite.py # JSON→SQLite 마이그레이션
│   ├── venv/                    # Python 가상환경
│   ├── requirements.txt         # Python 의존성
│   └── .env                     # 환경변수 (API keys)
│
├── frontend/                    # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # 홈 (논문 목록)
│   │   │   ├── search/
│   │   │   │   └── page.tsx     # Scholar 검색 + Connected Papers
│   │   │   ├── papers/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx # 논문 상세 + Study 모드
│   │   │   └── layout.tsx       # 레이아웃 (네비게이션)
│   │   ├── components/
│   │   │   ├── papers/
│   │   │   │   ├── PaperCard.tsx      # 논문 카드 컴포넌트
│   │   │   │   ├── PaperDetail.tsx    # 논문 상세 정보
│   │   │   │   ├── PaperList.tsx      # 논문 목록
│   │   │   │   └── PaperFilters.tsx   # 필터 UI
│   │   │   └── ConnectedPapersGraph.tsx # 그래프 시각화
│   │   ├── lib/
│   │   │   └── api.ts           # API 클라이언트
│   │   └── types/
│   │       └── index.ts         # TypeScript 타입 정의
│   ├── public/                  # 정적 파일
│   ├── package.json             # npm 의존성
│   └── .env.local               # 환경변수 (API URL)
│
├── WORK_HISTORY.md              # 세션별 작업 기록
├── CLAUDE.md                    # 이 파일 (프로젝트 가이드)
└── README.md                    # 프로젝트 README
```

## 개발 환경 설정

### 1. Backend 실행
```bash
cd /Users/daniel/paper-curation/backend

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치 (최초 1회)
pip install -r requirements.txt

# 서버 실행 (port 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 백그라운드 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
```

### 2. Frontend 실행
```bash
cd /Users/daniel/paper-curation/frontend

# 의존성 설치 (최초 1회)
npm install

# 개발 서버 실행 (port 3000)
npm run dev

# 또는 백그라운드 실행
npm run dev &
```

### 3. 환경변수

**Backend** (`.env`):
```env
SEMANTIC_SCHOLAR_API_KEY=ROGwfVuNS57GejcWFcH7C4yi6XrsVaQs9dkeSThD
```

**Frontend** (`.env.local`):
```env
NEXT_PUBLIC_API_URL=http://172.16.20.12:8000
```

### 4. 접속 URL
- Frontend: http://localhost:3000
- Backend API: http://172.16.20.12:8000
- API Docs: http://172.16.20.12:8000/docs

## API 엔드포인트

### 논문 관리
- `GET /api/papers` - 논문 목록 조회 (필터링, 페이지네이션)
- `GET /api/papers/{id}` - 논문 상세 조회
- `POST /api/papers` - 논문 추가
- `PUT /api/papers/{id}` - 논문 수정
- `DELETE /api/papers/{id}` - 논문 삭제
- `POST /api/papers/import-arxiv` - arXiv에서 논문 가져오기
- `POST /api/papers/import-doi` - DOI로 논문 가져오기
- `POST /api/papers/extract-pdf-metadata` - PDF에서 메타데이터 자동 추출
- `POST /api/papers/upload-pdf` - PDF 업로드

### 검색 & 추천
- `GET /api/papers/search-scholar?query={query}&limit={limit}` - Google Scholar 검색
- `GET /api/papers/related/{paper_id}` - 컬렉션 논문의 관련 논문 찾기
- `GET /api/papers/related-external?arxiv_id=...&doi=...&title=...` - 외부 논문의 관련 논문 찾기

### 메타데이터
- `GET /api/tags` - 모든 태그 목록
- `GET /api/papers/years` - 모든 연도 목록

### 읽기 추적
- `PUT /api/papers/{id}/reading-status` - 읽기 상태 업데이트
  - Body: `{"reading_status": "unread" | "in_progress" | "completed"}`

## 핵심 개념 및 워크플로우

### 1. 논문 추가 방법

#### A. Google Scholar 검색
1. `/search` 페이지에서 키워드 검색
2. 검색 결과에서 "Add" 버튼 클릭
3. 자동으로 메타데이터 추출 및 저장

#### B. arXiv ID로 가져오기
1. 홈 페이지에서 "Import from arXiv" 버튼
2. arXiv ID 입력 (예: `2506.10347`)
3. arXiv API에서 메타데이터 자동 추출

#### C. DOI로 가져오기
1. 홈 페이지에서 "Import from DOI" 버튼
2. DOI 입력 (예: `10.1145/3711896.3737026`)
3. Crossref API에서 메타데이터 자동 추출

#### D. PDF 업로드
1. 홈 페이지에서 "Upload PDF" 버튼
2. PDF 파일 선택
3. 제목/저자 수동 입력 또는 PDF에서 추출

### 2. Connected Papers 워크플로우

#### 동작 원리
1. 사용자가 논문에서 "Connect" 버튼 클릭
2. 논문의 arXiv ID, DOI, 또는 제목으로 Semantic Scholar에서 검색
3. Semantic Scholar Recommendations API 호출
4. 10개의 관련 논문 추천받기
5. 그래프 시각화:
   - 중심에 원본 논문
   - 주변에 10개 관련 논문 원형 배치
   - 색상: 연도별 그라데이션 (최신=보라, 오래됨=청록)
   - 크기: 인용수에 비례
   - 엣지 굵기: 연결 강도 (추천 순위 + 유사도)

#### Paper ID 생성 우선순위
```python
if arxiv_id:
    paper_id = f"ArXiv:{arxiv_id}"
elif doi:
    paper_id = f"DOI:{doi}"
else:
    # Title로 검색 후 Semantic Scholar ID 사용
    result = await search_by_title(title)
    paper_id = result.ss_id
```

#### 그래프 알고리즘
- **중심-논문 연결**: 추천 순위 기반 강도 (1위=1.0, 10위=0.1)
- **논문-논문 크로스링크**:
  - 인용수 차이 150 이내 OR 연도 차이 2년 이내
  - 유사도 = (인용 유사도 + 연도 유사도) / 2
  - 엣지 굵기 = 0.8 + (유사도 × 1.2)

### 3. 데이터 모델

#### Paper Schema (백엔드)
```python
class Paper(BaseModel):
    id: str                           # UUID
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    conference: Optional[str] = None  # 학회/저널명
    url: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    pdf_path: Optional[str] = None
    tags: List[str] = []
    category: str                     # "unread" | "in_progress" | "completed"
    is_favorite: bool = False
    reading_status: str = "unread"    # "unread" | "in_progress" | "completed"
    notes: Optional[str] = None
    created_at: str                   # ISO timestamp
    published_at: Optional[str] = None # 실제 출판일
```

#### Connected Papers Response
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

### 4. 주요 컴포넌트

#### ConnectedPapersGraph
- **라이브러리**: `react-force-graph-2d`
- **레이아웃**: 고정 원형 (force simulation 비활성화)
- **Props**:
  - `sourceTitle`: 중심 논문 제목
  - `sourceYear`: 중심 논문 연도
  - `sourceCitations`: 중심 논문 인용수
  - `connectedPapers`: 관련 논문 배열 (10개)

#### Search Page 레이아웃
```
┌─────────────────────────────────────┐
│       Search Box (full width)       │
└─────────────────────────────────────┘
┌────┬──────────────┬─────────────────┐
│    │              │                 │
│ S  │   Connected  │  Paper Details  │
│ c  │    Papers    │                 │
│ h  │    Graph     │   (10 papers)   │
│ o  │              │                 │
│ l  │              │                 │
│ a  │              │   [scrollable]  │
│ r  │              │                 │
│    │              │                 │
│ R  │              │                 │
│ e  │              │                 │
│ s  │              │                 │
│ u  │              │                 │
│ l  │              │                 │
│ t  │              │                 │
│ s  │              │                 │
└────┴──────────────┴─────────────────┘
 2/12      5/12           5/12
```

## 자주 사용하는 작업

### 코드 수정 후 재시작
```bash
# Frontend는 자동 hot reload
# Backend도 --reload 옵션으로 자동 reload

# 캐시 문제 발생 시
cd frontend
rm -rf .next
npm run dev
```

### 포트 충돌 해결
```bash
# Backend (8000)
lsof -ti:8000 | xargs kill -9

# Frontend (3000)
lsof -ti:3000 | xargs kill -9
```

### 데이터 백업
```bash
cp backend/data/papers.json backend/data/papers.json.backup
```

### 로그 확인
```bash
# Backend 로그 (uvicorn 실행 중인 터미널 확인)
# Frontend 로그 (npm run dev 실행 중인 터미널 확인)

# 백그라운드 실행 시
tail -f /private/tmp/claude-501/tasks/*.output
```

## 문제 해결

### Google Scholar 검색 실패
- **원인**: Google Scholar가 자동화된 요청 차단
- **증상**: 검색이 30초 후 타임아웃
- **해결**:
  - VPN 사용 (단, 로컬 네트워크 접속 불가)
  - Semantic Scholar API로 대체 검색 고려

### Rate Limiting
- **Semantic Scholar**: API key 사용으로 완화
- **arXiv**: Rate limit 있지만 일반적으로 문제없음
- **Crossref**: 공개 API, rate limit 관대

### PDF 업로드 실패
- **파일 크기 제한**: FastAPI 기본값 확인
- **경로 권한**: `backend/data/uploads/` 쓰기 권한 확인

### 그래프 렌더링 안 됨
- **원인**: 컨테이너 크기 계산 실패
- **해결**: 페이지 새로고침, 브라우저 개발자 도구 콘솔 확인

## 코딩 가이드라인

### 사용자 선호사항
- 한국어-영어 혼용 UI (주로 영어 UI + 한국어 레이블)
- 다크모드 지원
- 간결하고 직관적인 UX
- 과도한 엔지니어링 지양 (YAGNI 원칙)

### 코드 스타일
- **Backend**: PEP 8, 타입 힌트 사용
- **Frontend**: 함수형 컴포넌트, TypeScript strict mode
- **Naming**: 변수명 명확하게, 약어 최소화

### 에러 처리
- API 에러는 사용자에게 명확한 메시지로 표시
- 백엔드 에러는 적절한 HTTP 상태 코드 반환
- 로딩 상태 명확히 표시

### 테스트
- 수동 테스트 위주 (자동화 테스트 없음)
- 주요 워크플로우 체크리스트:
  1. [ ] 논문 추가 (Scholar, arXiv, DOI, PDF)
  2. [ ] 논문 검색 및 필터링
  3. [ ] Connected Papers 그래프
  4. [ ] 읽기 상태 변경
  5. [ ] Study 모드

## 참고 링크

- **Semantic Scholar API**: https://api.semanticscholar.org/api-docs/
- **arXiv API**: https://info.arxiv.org/help/api/index.html
- **Crossref API**: https://api.crossref.org/swagger-ui/index.html
- **react-force-graph-2d**: https://github.com/vasturiano/react-force-graph

---

# 개발 히스토리

## 2026-02-05 (Session 2): Connected Papers Graph Visualization

### 개요
Connected Papers 기능을 단순 리스트에서 인터랙티브 그래프 시각화로 업그레이드. connectedpapers.com 스타일의 원형 그래프 레이아웃을 구현하여 논문 간 연관성을 시각적으로 표현.

### 주요 구현 사항

#### 1. ConnectedPapersGraph 컴포넌트 (`frontend/src/components/ConnectedPapersGraph.tsx`)
- **그래프 라이브러리**: `react-force-graph-2d` 사용
- **레이아웃**: 안정적인 원형(circular) 배치
  - 중심 노드(origin paper) + 주변에 10개 논문 원형 배치
  - 모든 노드 위치 고정 (force simulation 비활성화)
  - 완벽한 원형: 모든 주변 노드가 중심으로부터 동일한 거리

- **시각적 특징**:
  - **색상**: 연도별 그라데이션
    - 최신 논문 (2025-2026): 진한 보라색 `hsl(270, 95%, 15%)`
    - 오래된 논문 (2019-2020): 연한 청록색 `hsl(180, 45%, 85%)`
    - HSL 색공간 활용: hue 180°→270°, lightness 85%→15%
  - **크기**: 인용 수에 비례 (로그 스케일, 6-12px)
  - **엣지 굵기**: 연결 강도에 비례
    - 중심-논문: 추천 순위 기반 강도
    - 논문-논문: 인용수/연도 유사도 기반 강도
  - **레이블**: 각 노드 외부에 #1, #2, ... 번호 표시 (방사형 배치)

- **상호작용**:
  - 노드 클릭 → 논문 URL 새 창으로 열기
  - 호버 → 제목, 연도, 인용수 툴팁 표시
  - 줌/팬 지원

- **범례**:
  - Origin Paper (보라색 + 노란색 테두리)
  - Newer/Older (색상 샘플)
  - Size ∝ Citations (크기 비교)
  - 굵을수록 연결 강함 (한국어, 엣지 굵기 샘플)
  - Hover or click nodes for details

#### 2. 그래프 알고리즘
- **중심-논문 연결**: 추천 순위 기반
  ```typescript
  const rankStrength = 1 - (index / connectedPapers.length); // 1위: 1.0, 10위: 0.1
  ```
- **논문-논문 크로스링크**: 유사도 기반 자동 연결
  ```typescript
  // 인용수 차이 150개 이내 또는 연도 차이 2년 이내
  if (citationDiff < 150 || yearDiff <= 2) {
    const citationSimilarity = 1 - Math.min(citationDiff / 150, 1);
    const yearSimilarity = 1 - Math.min(yearDiff / 5, 1);
    const strength = (citationSimilarity + yearSimilarity) / 2;
  }
  ```

#### 3. 레이아웃 개선 (`frontend/src/app/search/page.tsx`)
- **Before**: 좌우 2열 (Scholar 검색 + Connected Papers)
- **After**: 3열 레이아웃
  - 왼쪽 (2/12): Scholar Results (컴팩트 사이드바)
  - 중앙 (5/12): Connected Papers Graph
  - 오른쪽 (5/12): Paper Details (10개 논문 리스트)
- **특징**:
  - 모든 열 동일 높이 (600px)
  - 각 열 독립적 스크롤 (`overflow-y-auto`)
  - Search Box는 상단 전체 너비
  - Graph가 Search Box 바로 아래 위치

#### 4. Backend 개선
- **추천 논문 수 증가**: 5개 → 10개
  ```python
  # backend/app/routers/papers.py
  recommendations = await ss_service.get_recommendations(ss_paper_id, limit=10)
  ```
- **Semantic Scholar API Key 지원**
  ```python
  # backend/app/config.py
  semantic_scholar_api_key: Optional[str] = None

  # backend/app/services/semantic_scholar_service.py
  def _get_headers(self) -> dict:
      api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
      if api_key:
          return {"x-api-key": api_key}
      return {}
  ```
  - API Key: `ROGwfVuNS57GejcWFcH7C4yi6XrsVaQs9dkeSThD`
  - Rate limit 완화 목적

- **Google Scholar 타임아웃 추가**
  ```python
  # backend/app/services/scholar_service.py
  return await asyncio.wait_for(
      loop.run_in_executor(self._executor, self._search_sync, query, limit),
      timeout=30.0
  )
  ```

#### 5. 버그 수정
1. **새 검색 시 그래프 초기화**
   - 문제: 새로운 검색을 해도 이전 그래프가 남아있음
   - 해결: `handleSearch()`에서 `setHasConnected(false)` 추가

2. **그래프 렌더링 실패**
   - 문제: 그래프 영역이 빈 공간으로 표시됨
   - 원인: Flex layout에서 초기 컨테이너 크기 계산 실패
   - 해결:
     - 100ms 지연 후 크기 계산
     - `connectedPapers` 변경 시 재계산

3. **범례 잘림**
   - 문제: `overflow-hidden`으로 인해 하단 범례가 보이지 않음
   - 해결: `overflow-y-auto`로 변경

### 사용자 피드백 & 반복 개선

#### 색상 대비 강화
- **초기**: 미묘한 색상 차이
- **사용자**: "차이를 훨씬더 심하게 해줘 색이 안보여"
- **최종**: Lightness 85%→15% (70% 차이), Hue 180°→270° (90° 회전)

#### 노드 레이블 위치
- **시도 1**: 노드 내부 → "숫자가 다른 요소에 가려져"
- **시도 2**: 보라색 배경 원 → "왜 보라색 원이 나와"
- **시도 3**: 노드 옆 고정 위치 → "서로 겹쳐"
- **최종**: 방사형 배치 (중심으로부터 각도 계산)

#### 유사도 표현
- **초기 제안**: 노드 간 거리로 표현 (유사할수록 가깝게)
- **사용자 제안**: "거리로 하지말고 엣지를 좀 더 진하게 하면 어때?"
- **최종**: 엣지 굵기 + 투명도로 연결 강도 표현

#### 레이아웃 조정
- **초기**: Graph 아래에 Paper Details
- **사용자**: "그림 크기를 조금 줄이고 paper details도 오른쪽에"
- **최종**: 3열 나란히, 모두 600px 높이

### 기술적 세부사항

#### Force Simulation 비활성화
```typescript
d3AlphaDecay={1}        // 즉시 종료
d3VelocityDecay={1}     // 움직임 없음
cooldownTicks={0}       // 시뮬레이션 없음
```

#### 노드 커스텀 렌더링
```typescript
nodeCanvasObject={(node, ctx, globalScale) => {
  // 그림자
  ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';

  // 중심 노드 외곽 글로우
  if (n.isCenter) {
    ctx.fillStyle = 'rgba(168, 85, 247, 0.3)';
  }

  // 방사형 레이블
  const angle = Math.atan2(node.y - centerY, node.x - centerX);
  const labelX = node.x + Math.cos(angle) * labelDistance;
  const labelY = node.y + Math.sin(angle) * labelDistance;
}}
```

#### 반응형 크기 계산
```typescript
useEffect(() => {
  const updateDimensions = () => {
    const width = containerRef.current.offsetWidth;
    const height = Math.min(500, Math.max(400, width * 0.7));
    setDimensions({ width, height });
  };

  const timer = setTimeout(updateDimensions, 100); // Layout settle delay
  // ...
}, [connectedPapers]);
```

### 파일 변경 내역
```
frontend/src/components/ConnectedPapersGraph.tsx (NEW - 343 lines)
frontend/src/app/search/page.tsx (MAJOR REWRITE)
frontend/package.json (ADD react-force-graph-2d)
backend/app/routers/papers.py (limit: 5 → 10)
backend/app/services/semantic_scholar_service.py (API key support)
backend/app/services/scholar_service.py (30s timeout)
backend/app/config.py (semantic_scholar_api_key field)
backend/.env (SEMANTIC_SCHOLAR_API_KEY)
```

### 의존성 추가
```json
{
  "react-force-graph-2d": "^1.25.4"
}
```

### Git Commit
- **Commit**: 08ddb6c
- **Branch**: main
- **Date**: 2026-02-05
- **Message**: "Add Connected Papers graph visualization with optimized layout"

### 알려진 이슈
1. **그래프 초기 로딩 지연**: 100ms 지연으로 인한 약간의 깜빡임
2. **모바일 반응형**: 3열 레이아웃이 작은 화면에서 최적화 필요
3. **크로스링크 과다**: 논문이 많을 경우 엣지가 너무 많아질 수 있음

### 향후 개선 가능성
1. 그래프 레이아웃 옵션 (원형 외 다른 레이아웃)
2. 필터링 (특정 연도대, 인용수 범위)
3. 애니메이션 효과 (노드 클릭 시 확장)
4. 엣지 호버 시 유사도 점수 표시
5. 그래프 내보내기 (이미지, PDF)

---

## 2026-02-05 (Session 1): Connected Papers Feature

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
1. Semantic Scholar API key 추가 (rate limit 완화) → Session 2에서 구현됨
2. Connect 실패 시 retry 로직
3. Connected Papers 패널에 "Close" 버튼 추가
4. 이미 추가된 논문 표시 (중복 방지)
5. Citation count 기반 정렬 옵션

---

## 2026-02-05 (Session 3): PDF Auto-Metadata + Cache Service + Graph Improvements

### 개요
PDF 업로드 시 자동 메타데이터 추출 기능 추가. PDF에서 제목을 추출한 뒤 Semantic Scholar에서 전체 메타데이터를 검색하여 폼을 자동 채움. 추가로 Semantic Scholar API 응답 캐시와 그래프 렌더링 개선도 포함.

### 주요 구현 사항

#### 1. PDF Auto-Metadata Extraction

##### Backend: 새 엔드포인트 (`backend/app/routers/papers.py`)
- `POST /api/papers/extract-pdf-metadata`
  - PDF 파일 업로드 받음
  - `pdf_service.extract_title_from_pdf()`로 제목 추출
  - 추출된 제목으로 `semantic_scholar_service.search_by_title()` 호출
  - 성공 시: title, authors, abstract, year, url, doi, arxiv_id, citation_count 반환 (source: "semantic_scholar")
  - 실패 시: PDF에서 추출한 제목만 반환 (source: "pdf")

##### Backend: 새 스키마 (`backend/app/schemas/paper.py`)
```python
class PdfMetadataResponse(BaseModel):
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: int = 0
    source: str = "pdf"  # "pdf" or "semantic_scholar"
```

##### Frontend: PdfUploader 개선 (`frontend/src/components/papers/PdfUploader.tsx`)
- PDF 파일 선택 시 즉시 `/api/papers/extract-pdf-metadata` 호출
- 로딩 상태: "Extracting metadata from PDF..." (animate-pulse)
- 성공 시 폼 필드 자동 채우기 (title, authors, abstract, year)
- 피드백 메시지:
  - Semantic Scholar 매칭: "Metadata auto-filled from Semantic Scholar" (녹색)
  - PDF만 추출: "Title extracted from PDF (metadata not found on Semantic Scholar)" (노란색)
- 추출 실패 시 사용자 수동 입력으로 fallback (에러 무시)
- Submit 버튼: extracting 중 비활성화

##### Frontend: API 클라이언트 (`frontend/src/lib/api.ts`)
```typescript
extractPdfMetadata: async (pdf: File): Promise<PdfMetadataResponse>
```

##### Frontend: 타입 정의 (`frontend/src/types/index.ts`)
```typescript
export interface PdfMetadataResponse {
  title: string;
  authors: string[];
  abstract: string | null;
  year: number | null;
  url: string | null;
  doi: string | null;
  arxiv_id: string | null;
  citation_count: number;
  source: 'pdf' | 'semantic_scholar';
}
```

#### 2. Recommendation Cache Service (`backend/app/services/cache_service.py`)
- 인메모리 캐시 (`dict` 기반)
- TTL 기반 만료 (기본 1시간)
- `get(key)`, `set(key, value, ttl)` 메서드
- 주기적 클린업 스케줄러 (`start_cache_cleanup_scheduler()`)
- `semantic_scholar_service.get_recommendations()`에서 활용
- `main.py`에서 startup event로 클린업 태스크 시작

#### 3. Graph Rendering 개선 (`frontend/src/components/ConnectedPapersGraph.tsx`)
- 좌표 시스템: 절대 좌표 → (0,0) 중심 상대 좌표로 변경
- 노드 크기 축소: center 14→10, min 6→4, max 12→9
- 줌/팬 비활성화: `enableZoomInteraction={false}`, `enablePanInteraction={false}`
- 빈 데이터 처리: 조건부 렌더링 추가
- 투명 배경: `backgroundColor="rgba(255,255,255,0)"`
- 차원 계산 개선: `getBoundingClientRect()` 사용, 다중 retry (0ms, 100ms, 300ms)

### 파일 변경 내역
```
backend/app/services/cache_service.py (NEW)
backend/app/main.py (startup event 추가)
backend/app/services/semantic_scholar_service.py (캐시 연동)
backend/app/routers/papers.py (extract-pdf-metadata 엔드포인트)
backend/app/schemas/paper.py (PdfMetadataResponse)
backend/app/schemas/__init__.py (export 추가)
frontend/src/components/ConnectedPapersGraph.tsx (렌더링 개선)
frontend/src/app/search/page.tsx (레이아웃 미세 조정)
frontend/src/components/papers/PdfUploader.tsx (auto-metadata)
frontend/src/lib/api.ts (extractPdfMetadata 메서드)
frontend/src/types/index.ts (PdfMetadataResponse 타입)
```

### Git Commits
1. **ef4cc5a** - "Add recommendation cache service and improve graph rendering"
2. **eaad3c4** - "Add PDF upload auto-metadata extraction via Semantic Scholar"

### 알려진 이슈
1. **PDF 제목 추출 정확도**: PDF metadata가 없거나 첫 페이지 레이아웃이 복잡한 경우 잘못된 제목 추출 가능
2. **Semantic Scholar 매칭 실패**: 추출된 제목이 부정확하면 Semantic Scholar에서 매칭 실패 → PDF-only 결과 반환

---

## 2026-02-06 (Session 4): Auto Category Prediction Fix

### 개요
단일 arXiv/DOI import 시 category가 항상 "other"로 설정되던 버그 수정. `predict_category()` 함수를 호출하도록 변경하여 논문 제목/abstract 기반 자동 분류 기능 활성화.

### 문제 분석

#### 증상
- arXiv URL로 논문 import 시 category가 항상 "other"로 설정됨
- 예: "Tail-Aware Data Augmentation for Long-Tail Sequential Recommendation" → "other" (예상: "recsys")

#### 원인
`/api/papers/arxiv` 및 `/api/papers/doi` 엔드포인트에서 `predict_category()` 함수를 호출하지 않음:

```python
# 변경 전 (papers.py:693)
"category": request.category,  # request.category 기본값이 "other"
```

반면 bulk import나 Scholar 검색에서는 `predict_category()`를 호출하고 있었음:
```python
# bulk import (papers.py:501)
category = request.category or predict_category(paper_data.title, paper_data.abstract)
```

#### 스키마 기본값
```python
# schemas/paper.py:39
class ArxivImportRequest(BaseModel):
    arxiv_url: str
    category: Category = Category.OTHER  # ← 기본값 "other"
```

### 수정 내용

#### 1. arXiv Import (`/api/papers/arxiv`)
```python
# 변경 후 (papers.py:676-679)
# Auto-predict category if not specified (default is "other")
category = request.category
if category == Category.OTHER:
    category = predict_category(paper_data.title, paper_data.abstract)
```

#### 2. DOI Import (`/api/papers/doi`)
```python
# 변경 후 (papers.py:746-749)
# Auto-predict category if not specified (default is "other")
category = request.category
if category == Category.OTHER and abstract:
    category = predict_category(title, abstract)
```

### 테스트 결과
```bash
# 수정 전
curl -X POST ".../arxiv" -d '{"arxiv_url": "https://arxiv.org/abs/2601.10933"}'
# → category: "other"

# 수정 후
curl -X POST ".../arxiv" -d '{"arxiv_url": "https://arxiv.org/abs/2601.10933"}'
# → category: "recsys", tags: ["Sequential"]
```

### 파일 변경 내역
```
backend/app/routers/papers.py (MODIFIED)
  - import_from_arxiv(): predict_category() 호출 추가
  - import_from_doi(): predict_category() 호출 추가
```

### Category 자동 분류 키워드 (참고)
```python
CATEGORY_KEYWORDS = {
    "recsys": ["recommendation", "recommender", "collaborative filtering", ...],
    "nlp": ["language model", "llm", "gpt", "bert", "transformer", ...],
    "cv": ["image", "vision", "object detection", "segmentation", ...],
    "rl": ["reinforcement learning", "policy gradient", "q-learning", ...],
    "ml": ["classification", "regression", "neural network", ...],
}
```

---

## 2026-02-09 (Session 5): DeepL Translation + LaTeX Rendering + Layout Improvements

### 개요
논문 전체 번역 기능을 Ollama에서 DeepL API로 전환하여 번역 품질 대폭 향상. PDF 텍스트 전처리 개선, 학회 정보 필터링, LaTeX 수식 렌더링, 페이지별 레이아웃 최적화 구현.

### 주요 구현 사항

#### 1. DeepL API 번역 서비스 (`backend/app/services/deepl_service.py`)
- **인증 방식**: Header 기반 (`Authorization: DeepL-Auth-Key {key}`)
- **API Endpoint**: `https://api-free.deepl.com/v2/translate` (Free tier)
- **월간 한도**: 500,000 characters
- **후처리 기능**: `_clean_translated_text()` - 번역 결과에서 학회 정보/저자명 필터링

```python
class DeepLService:
    async def translate(self, text: str, target_lang: str = "KO") -> str:
        response = await client.post(
            self.API_URL,
            headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"},
            json={"text": [text], "target_lang": target_lang}
        )
        translated = translations[0].get("text", "")
        return self._clean_translated_text(translated)
```

#### 2. PDF 텍스트 전처리 개선 (`backend/app/services/ollama_service.py`)
- **`_clean_pdf_text()`**: PDF 추출 시 깨진 줄바꿈 복원
  - 짧은 줄 자동 결합 (80자 미만)
  - 하이픈 단어 분리 복원 (`recommen-\ndation` → `recommendation`)
  - 소문자로 시작하는 줄 이전 문장과 결합
  - 섹션 헤더 인식 및 보존

- **`_filter_metadata_noise()`**: 학회/저자 정보 필터링 강화
  ```python
  skip_patterns = [
      r"(WWW|KDD|SIGIR|AAAI|ICML|NeurIPS|...) *['\"]?\d{2}",
      r"(January|February|...|December)\s+\d+.*\d{4}",
      r"(Sydney|Toronto|New York|...).*\d{4}",
      r"^[A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+,?\s*(et\s+al\.?)?$",
  ]
  ```

#### 3. 번역 후 필터링 (`backend/app/services/deepl_service.py`)
- **`_clean_translated_text()`**: 한국어 번역 결과 정리
  ```python
  skip_patterns = [
      r"\d{4}년\s+\d{1,2}월\s+\d{1,2}일",  # 한국어 날짜
      r"(호주|미국|영국|...) (시드니|토론토|...)",  # 한국어 도시명
      r"^[가-힣]+\s*(and|와|과)\s*[가-힣]+.*et\s+al",  # 저자명
  ]
  ```

#### 4. LaTeX 수식 렌더링 (`frontend/src/components/LatexText.tsx`)
- **KaTeX 라이브러리** 사용
- **지원 문법**:
  - Inline: `$...$`, `\(...\)`
  - Display: `$$...$$`, `\[...\]`
- **Study 페이지** 번역/요약에 적용

```tsx
export function LatexText({ text }: { text: string }) {
  // Regex로 LaTeX 패턴 감지
  const latexRegex = /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)/g;

  // KaTeX로 렌더링
  const html = katex.renderToString(latex, {
    throwOnError: false,
    displayMode: isDisplay,
  });

  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}
```

#### 5. 페이지별 레이아웃 최적화
- **layout.tsx**: `max-width` 제거 (페이지별 개별 설정)
- **Home (page.tsx)**: `max-w-7xl` (기존 사이즈)
- **Study (study/layout.tsx)**: `max-w-[1444px]` (PDF 2단 컬럼 100% 표시)
- **Search**: 기존 동적 너비 유지 (`max-w-4xl` / `max-w-7xl`)

#### 6. PDF.js 에러 처리 (`frontend/src/components/pdf/PdfHighlighter.tsx`)
- **문제**: `this[#editorTypes] is not iterable` 에러 (pdfjs-dist 버그)
- **해결**:
  - `console.error` 필터링
  - `window.error` 이벤트 억제
  - `PdfErrorBoundary` 컴포넌트로 에러 격리

```typescript
// Suppress PDF.js annotation editor errors
window.addEventListener('error', (event) => {
  if (event.message?.includes('#editorTypes')) {
    event.preventDefault();
    return false;
  }
});
```

### 환경 변수
```env
# backend/.env
DEEPL_API_KEY=c764687c-0d6a-4fc5-b217-0a9ee30eedc7:fx
```

### 파일 변경 내역
```
backend/app/services/deepl_service.py (NEW)
  - DeepL API 번역 서비스
  - Header 기반 인증
  - 번역 후 필터링

backend/app/services/ollama_service.py (MODIFIED)
  - _clean_pdf_text(): PDF 텍스트 전처리
  - _filter_metadata_noise(): 학회 정보 필터링 강화

backend/app/config.py (MODIFIED)
  - deepl_api_key 필드 추가

backend/app/routers/papers.py (MODIFIED)
  - translate-full 엔드포인트 DeepL 사용

frontend/src/components/LatexText.tsx (NEW)
  - KaTeX 기반 LaTeX 렌더링 컴포넌트

frontend/src/components/pdf/PdfHighlighter.tsx (MODIFIED)
  - PDF.js 에러 억제
  - PdfErrorBoundary 추가

frontend/src/app/layout.tsx (MODIFIED)
  - max-width 제거 (페이지별 설정)

frontend/src/app/page.tsx (MODIFIED)
  - max-w-7xl 추가

frontend/src/app/study/layout.tsx (NEW)
  - max-w-[1444px] Study 전용 레이아웃

frontend/package.json (MODIFIED)
  - katex, react-katex 의존성 추가
```

### 의존성 추가
```json
{
  "katex": "^0.16.x",
  "react-katex": "^3.x"
}
```

### 알려진 이슈
1. **DeepL 월간 한도**: Free tier 500,000자 제한
2. **PDF 텍스트 추출**: 복잡한 레이아웃(다단, 표 포함)에서 일부 누락 가능
3. **LaTeX 호환성**: 일부 복잡한 수식 패키지 미지원

### 사용 방법
1. Study 페이지에서 논문 선택
2. PDF에서 텍스트 드래그 선택 → "번역하기" 버튼 클릭
3. Summary 기능으로 논문 요약 (Ollama)

---

## 2026-02-10 (Session 6): Drag-to-Translate + PDF UX Improvements

### 개요
전체 논문 번역 기능을 제거하고, PDF에서 텍스트를 드래그 선택하여 번역하는 방식으로 변경. PDF 뷰어 UX 개선 (100% 줌, 맨 위부터 시작).

### 주요 변경 사항

#### 1. 전체 번역 기능 제거
- Study 페이지에서 "Translate" 버튼 및 관련 UI 제거
- `fullTranslation`, `fullTranslating` 등 상태 제거
- papers.json에서 기존 `full_translation` 데이터 제거

#### 2. 드래그 선택 번역 구현 (`PdfHighlighter.tsx`)
- PDF에서 텍스트 선택 시 팝업에 "번역하기" 버튼 표시
- DeepL API (`/api/papers/translate-text`) 호출
- 번역 결과를 녹색 박스로 표시
- 이벤트 버블링 방지 (`e.stopPropagation()`)

```typescript
const handleTranslate = async (e: React.MouseEvent) => {
  e.preventDefault();
  e.stopPropagation();
  // DeepL API 호출
  const response = await fetch('/api/papers/translate-text', {
    method: 'POST',
    body: JSON.stringify({ text: selectedText }),
  });
  const data = await response.json();
  setTranslation(data.translated);
};
```

#### 3. PDF 뷰어 UX 개선
- **줌 레벨**: 120% → 100%로 변경
- **초기 스크롤**: PDF 로드 시 맨 위(1페이지)부터 시작
- **CSS 정리**: 과도한 flex 레이아웃 제거 (PDF 표시 버그 수정)

```typescript
// PDF 로드 시 맨 위로 스크롤
scrollRef={(scrollTo) => {
  if (!hasScrolledRef.current) {
    hasScrolledRef.current = true;
    setTimeout(() => scrollTo({ pageNumber: 1, top: 0 }), 150);
  }
}}
```

#### 4. DeepL 서비스 정리 (`deepl_service.py`)
- `_clean_translated_text()` 메서드 제거 (과도한 필터링으로 번역 결과 삭제 버그)
- `translate_sections()` 메서드 제거 (전체 번역용, 미사용)
- `import re` 제거
- 간결한 단일 `translate()` 메서드만 유지

**문제 해결**: "Huawei", "Google" 등 키워드가 포함된 문장이 번역되지 않던 버그
- 원인: `_clean_translated_text()`가 회사명이 포함된 모든 라인 삭제
- 해결: 필터링 로직 완전 제거

### 파일 변경 내역
```
backend/app/services/deepl_service.py (SIMPLIFIED)
  - _clean_translated_text() 제거
  - translate_sections() 제거
  - 86줄 → 110줄로 감소

backend/app/routers/papers.py (MODIFIED)
  - translate-text 엔드포인트 유지

frontend/src/app/study/page.tsx (SIMPLIFIED)
  - 전체 번역 UI 제거
  - Summary 기능만 유지

frontend/src/components/pdf/PdfHighlighter.tsx (MODIFIED)
  - 드래그 선택 번역 기능
  - PDF 초기 스크롤 위치 수정
  - 줌 레벨 100%

frontend/src/app/globals.css (MODIFIED)
  - PDF 센터링 CSS 간소화

backend/data/papers.json (MODIFIED)
  - full_translation 필드 제거
```

### API 엔드포인트
```
POST /api/papers/translate-text
  Request:  { "text": "영어 텍스트", "target_lang": "KO" }
  Response: { "original": "영어 텍스트", "translated": "한국어 번역" }
```

### 사용 방법
1. Study 페이지에서 논문 PDF 열기
2. 번역하고 싶은 텍스트 드래그 선택
3. 팝업에서 "번역하기" 버튼 클릭
4. 녹색 박스에 한국어 번역 표시
5. (선택) 하이라이트 색상 선택 후 "Highlight" 버튼으로 저장

---

## 2026-02-10 (Session 7): Study UI 개선 + 브라우저별 데이터 분리

### 개요
Study 페이지의 UI를 개선하고, Summary/Highlights/Session 데이터를 브라우저별로 분리 저장하도록 변경. 기존에 모든 사용자가 공유하던 Summary를 localStorage로 이동하여 각 PC/브라우저마다 독립적인 Study 환경 제공.

### 주요 변경 사항

#### 1. Study 페이지 UI 통합 (`frontend/src/app/study/page.tsx`)
- **버튼 정리**: 3개 버튼 → 2개로 통합
  - Before: `[Summary(보라)] [Highlights(노랑)] [Summary(파랑)] [Save]`
  - After: `[Summary(보라)] [Notes(에메랄드)] [Save]`
- **Notes 패널**: Summary와 Highlights를 하나의 패널로 통합
  - Summary 섹션 (접기/펼치기 가능, 보라색 테마)
  - Highlights & Comments 섹션 (접기/펼치기 가능, 노랑색 테마)
- **패널 너비**: `w-96` (384px)

#### 2. 브라우저별 데이터 분리 (localStorage 전환)
- **변경 전**: Summary는 백엔드 `papers.json`에 저장 → 모든 사용자 공유
- **변경 후**: Summary도 localStorage에 저장 → 브라우저별 분리

```
저장소 구조:
┌─────────────────┐
│  Backend Server │  ← Summary 생성만 담당 (저장 X)
└────────┬────────┘
         │
   ┌─────┴─────┐
   │           │
Chrome      Safari
localStorage localStorage
- Summary    - Summary
- Highlights - Highlights
- Session    - Session
```

**localStorage 키**:
| 데이터 | Key |
|--------|-----|
| Summary | `pdf-summary-{paperId}` |
| Highlights | `pdf-highlights-{paperId}` |
| Session | `study-session` |

#### 3. 백엔드 변경 (`backend/app/routers/papers.py`)
- `/api/papers/{id}/summarize-full` 엔드포인트
- Summary 생성 후 `papers.json` 저장 로직 제거
- Ollama로 생성만 하고 프론트엔드에 반환

```python
# 변경 전
repo.update(paper_id, {"full_summary": summary})

# 변경 후 (저장 로직 제거)
# Note: Summary is NOT saved to backend anymore
# Frontend saves it to localStorage for per-browser storage
```

### State 변수 변경

```typescript
// 제거된 state
const [showHighlights, setShowHighlights] = useState(false);
const [showResults, setShowResults] = useState(false);

// 새로운 state
const [showRightPanel, setShowRightPanel] = useState(false);
const [showHighlightsContent, setShowHighlightsContent] = useState(true);
```

### 파일 변경 내역
```
frontend/src/app/study/page.tsx (MAJOR UPDATE)
  - UI 버튼 통합 (3개 → 2개)
  - Notes 패널에 Summary + Highlights 통합
  - Summary localStorage 저장으로 전환
  - Notes 버튼 색상: emerald

backend/app/routers/papers.py (MODIFIED)
  - summarize-full 엔드포인트에서 papers.json 저장 제거
```

### 사용자 경험 변화
1. **UI 간소화**: 버튼이 줄어들어 더 직관적
2. **통합 패널**: Summary와 Highlights를 한 곳에서 관리
3. **프라이버시**: 다른 PC/브라우저에서 접속 시 독립적인 데이터
4. **오프라인 저장**: 브라우저 데이터 삭제 전까지 유지

### 알려진 제한사항
1. **브라우저 데이터 삭제 시 손실**: localStorage 기반이므로 브라우저 캐시/데이터 삭제 시 Highlights 사라짐
2. **용량 제한**: localStorage는 보통 5-10MB 제한 (대부분 충분)

---

## 2026-02-10 (Session 8): SQLite 마이그레이션

### 개요
JSON 파일 기반 저장소(`papers.json`)를 SQLite 데이터베이스로 마이그레이션. Summary를 서버 DB에 저장하여 모든 기기에서 공유 가능하도록 변경.

### 주요 변경 사항

#### 1. SQLite 데이터베이스 인프라
- `backend/app/db/__init__.py` - 패키지 초기화
- `backend/app/db/connection.py` - SQLite 연결 관리, `get_db()` context manager
- `backend/app/db/schema.py` - 테이블 스키마 정의

#### 2. 데이터베이스 스키마
```sql
-- Papers 테이블
CREATE TABLE papers (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,          -- JSON array
    abstract TEXT,
    year INTEGER,
    arxiv_id TEXT UNIQUE,
    arxiv_url TEXT,
    doi TEXT UNIQUE,
    paper_url TEXT,
    conference TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    published_at TEXT,
    pdf_path TEXT,
    summary_one_line TEXT,
    summary_contribution TEXT,
    summary_methodology TEXT,
    summary_results TEXT,
    full_summary TEXT,
    translation TEXT,
    full_translation TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Tags 테이블
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE
);

-- Paper-Tag 관계 (다대다)
CREATE TABLE paper_tags (
    paper_id TEXT REFERENCES papers(id) ON DELETE CASCADE,
    tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, tag_id)
);
```

#### 3. Repository 재작성 (`backend/app/repositories/paper_repository.py`)
- JSON 파일 대신 SQLite 쿼리 사용
- 동일한 public interface 유지 (routers 변경 최소화)
- JSON 필드 직렬화/역직렬화 처리 (authors, translation)
- 태그 관계 처리 (paper_tags 테이블)

#### 4. 마이그레이션 스크립트 (`backend/scripts/migrate_to_sqlite.py`)
```bash
cd backend
python scripts/migrate_to_sqlite.py
```
- papers.json → papers.db 데이터 이전
- 기존 JSON 파일 백업 (`papers.json.backup`)

#### 5. Summary 저장 위치 변경
- **변경 전**: localStorage (브라우저별 분리)
- **변경 후**: 서버 DB (모든 기기에서 공유)
- Highlights는 여전히 localStorage에 저장

### 데이터 저장 구조

| 데이터 | 저장 위치 | 공유 범위 |
|--------|----------|----------|
| Papers | SQLite DB | 서버 전체 |
| Summary | SQLite DB | 서버 전체 |
| Highlights | localStorage | 브라우저별 |
| Session | localStorage | 브라우저별 |

### 파일 변경 내역
```
backend/app/db/__init__.py (NEW)
backend/app/db/connection.py (NEW)
backend/app/db/schema.py (NEW)
backend/app/database.py (SIMPLIFIED - 유틸만 유지)
backend/app/main.py (ADD startup init_db)
backend/app/repositories/paper_repository.py (REWRITE)
backend/app/routers/papers.py (MODIFY - Summary 저장)
backend/app/routers/tags.py (REWRITE - SQLite 사용)
backend/scripts/migrate_to_sqlite.py (NEW)
frontend/src/app/study/page.tsx (MODIFY - Summary 서버에서 로드)
.gitignore (ADD *.db, *.backup, *_cache.json)
```

### Git Commit
- **Commit**: a066ac2
- **Branch**: main
- **Date**: 2026-02-10
- **Message**: "Migrate storage from JSON to SQLite"

### SQLite 장점
1. **계정 불필요**: 파일 기반 DB, 별도 설치/설정 없음
2. **Python 내장**: sqlite3 모듈 기본 포함
3. **ACID 보장**: 트랜잭션 지원
4. **인덱스**: 빠른 검색 (arxiv_id, doi, year, category)
5. **관계형**: 태그-논문 다대다 관계 정규화

### 마이그레이션 방법
기존 사용자가 업데이트 시:
```bash
cd backend
source venv/bin/activate
python scripts/migrate_to_sqlite.py
```
