# Paper Curation

ML/AI 연구자를 위한 논문 큐레이션 웹사이트. arXiv, ACM, IEEE 논문을 수집하고 카테고리/태그로 관리합니다.

## 기술 스택

- **Frontend**: React + Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.9+)
- **Storage**: JSON 파일 (간단한 저장)
- **기타**: Pydantic v2, httpx (async HTTP client)

## 주요 기능

### 논문 Import
- **arXiv**: URL 입력시 메타데이터 자동 추출 (제목, 저자, 초록, 년도)
- **ACM/DOI**: Semantic Scholar API로 메타데이터 가져오기 (제목, 저자, 초록, 년도)

### 자동 태그 예측
논문 추가시 태그를 선택하지 않으면 제목/초록을 분석하여 자동으로 태그 추천 (최대 3개):
- `LLM`, `VAE`, `GCN`, `CTR`, `KD`, `MoE`, `RL`
- `Transformer`, `Sequential`, `Diffusion`
- `Industrial` - A/B 테스트 언급시 자동 추가

### 분류 및 검색
- 카테고리: RecSys, ML, NLP, CV, RL, Other
- 태그 기반 필터링
- 제목/초록 검색
- 연도별 필터링

## 프로젝트 구조

```
paper-curation/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 앱
│   │   ├── config.py        # 설정
│   │   ├── database.py      # JSON 파일 관리
│   │   ├── models/          # 데이터 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── routers/         # API 엔드포인트
│   │   └── services/        # arXiv/DOI 서비스
│   ├── data/
│   │   └── papers.json      # 논문 데이터 저장
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React 컴포넌트
│   │   ├── lib/             # API 클라이언트
│   │   └── types/           # TypeScript 타입
│   └── package.json
└── README.md
```

## 로컬 개발

### 요구사항

- Python 3.9+
- Node.js 18+

### Backend 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev -- -H 0.0.0.0
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/docs

### 같은 네트워크에서 접속

같은 WiFi 네트워크의 다른 기기에서 접속하려면:

```bash
# IP 주소 확인
ipconfig getifaddr en0

# frontend/.env.local 수정
NEXT_PUBLIC_API_URL=http://YOUR_IP:8000
```

## API 엔드포인트

### Papers

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/papers/arxiv` | arXiv URL로 논문 import |
| POST | `/api/papers/doi` | ACM/IEEE/DOI URL로 논문 import |
| POST | `/api/papers` | 수동 논문 추가 |
| GET | `/api/papers` | 논문 목록 (검색/필터 지원) |
| GET | `/api/papers/{id}` | 논문 상세 |
| PUT | `/api/papers/{id}` | 논문 수정 |
| DELETE | `/api/papers/{id}` | 논문 삭제 |

### Tags

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/tags` | 태그 목록 (사용 빈도순) |
| POST | `/api/tags` | 태그 생성 |
| DELETE | `/api/tags/{id}` | 태그 삭제 |

## 환경 변수

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 지원 논문 소스

| 소스 | URL 예시 | 메타데이터 |
|------|----------|-----------|
| arXiv | `https://arxiv.org/abs/2402.17152` | 제목, 저자, 초록, 년도 |
| ACM | `https://dl.acm.org/doi/10.1145/xxxxx` | 제목, 저자, 초록*, 년도 |
| IEEE | `https://ieeexplore.ieee.org/document/xxxxx` | 제목, 저자, 년도 |
| DOI | `https://doi.org/10.xxxx/xxxxx` | 제목, 저자, 년도 |

*초록은 Semantic Scholar API에서 가져옴 (없을 수 있음)
