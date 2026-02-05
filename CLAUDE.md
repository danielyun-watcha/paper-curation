# Paper Curation - Claude Development Guide

> 이 문서는 Claude가 이 프로젝트에서 작업할 때 참고할 종합 가이드입니다.
> 세션별 작업 기록은 `WORK_HISTORY.md`를 참고하세요.

## 프로젝트 개요

학술 논문 큐레이션 및 관리 시스템. 사용자가 관심있는 논문을 수집하고, 관련 논문을 찾고, 읽기 상태를 추적하는 웹 애플리케이션.

### 핵심 기능
- 📚 **논문 관리**: JSON 파일 기반 로컬 컬렉션
- 🔍 **Google Scholar 검색**: scholarly 라이브러리를 통한 논문 검색
- 🔗 **Connected Papers**: Semantic Scholar API로 관련 논문 찾기
- 📊 **그래프 시각화**: 논문 간 연관성을 인터랙티브 그래프로 표시
- 📖 **읽기 추적**: 논문별 읽기 상태 및 메모 관리
- 📄 **PDF 업로드**: 로컬 PDF 파일 업로드 및 관리

### 기술 스택
- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Database**: JSON 파일 (`backend/data/papers.json`)
- **External APIs**: Semantic Scholar, Google Scholar, arXiv, Crossref

## 프로젝트 구조

```
paper-curation/
├── backend/                      # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 설정 (환경변수)
│   │   ├── routers/
│   │   │   └── papers.py        # 논문 API 엔드포인트
│   │   ├── services/
│   │   │   ├── paper_service.py           # 논문 CRUD
│   │   │   ├── scholar_service.py         # Google Scholar 검색
│   │   │   ├── semantic_scholar_service.py # Semantic Scholar API
│   │   │   ├── arxiv_service.py           # arXiv API
│   │   │   └── crossref_service.py        # Crossref DOI 검색
│   │   ├── schemas/
│   │   │   └── paper.py         # Pydantic 모델 (API 스키마)
│   │   └── utils/
│   │       └── pdf_utils.py     # PDF 처리 유틸
│   ├── data/
│   │   ├── papers.json          # 논문 데이터 (JSON DB)
│   │   └── uploads/             # 업로드된 PDF 파일
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

## 작업 기록

세션별 상세 작업 기록은 `WORK_HISTORY.md`를 참고하세요.

- 2026-02-05 (Session 1): Connected Papers 기본 기능 구현
- 2026-02-05 (Session 2): 그래프 시각화 및 레이아웃 최적화
