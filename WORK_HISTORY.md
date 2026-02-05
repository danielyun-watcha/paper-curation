# Paper Curation - Work History

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
