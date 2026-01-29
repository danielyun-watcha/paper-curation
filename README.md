# Paper Curation

ML/AI 연구자를 위한 논문 큐레이션 웹사이트. arXiv 논문을 수집하고 카테고리/태그로 관리합니다.

## 기술 스택

- **Frontend**: React + Next.js 14 (App Router) + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + SQLAlchemy (async)
- **기타**: Pydantic v2, httpx (async HTTP client)

## 기능

- arXiv URL로 논문 자동 import (메타데이터 자동 추출)
- 수동 논문 추가
- 카테고리별 분류 (RecSys, ML, NLP, CV, RL, Other)
- 태그 기반 관리
- 제목/초록 검색
- 복합 필터링 (카테고리 + 태그 + 연도)

## 프로젝트 구조

```
paper-curation/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 앱
│   │   ├── config.py        # 설정
│   │   ├── database.py      # DB 연결
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   ├── routers/         # API 엔드포인트
│   │   └── services/        # 비즈니스 로직
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React 컴포넌트
│   │   ├── lib/             # API 클라이언트
│   │   └── types/           # TypeScript 타입
│   └── Dockerfile
└── docker-compose.yml
```

## 로컬 개발

### 요구사항

- Python 3.9+
- Node.js 18+
- PostgreSQL 15 (또는 Docker)

### Backend 실행

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (SQLite 사용)
uvicorn app.main:app --reload --port 8000
```

### Frontend 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API 문서 (Swagger): http://localhost:8000/docs

## Docker로 실행

```bash
# 전체 스택 실행
docker compose up -d

# 로그 확인
docker compose logs -f
```

## API 엔드포인트

### Papers

- `POST /api/papers/arxiv` - arXiv URL로 논문 import
- `POST /api/papers` - 수동 논문 추가
- `GET /api/papers` - 논문 목록 (검색/필터 지원)
- `GET /api/papers/{id}` - 논문 상세
- `PUT /api/papers/{id}` - 논문 수정
- `DELETE /api/papers/{id}` - 논문 삭제

### Tags

- `GET /api/tags` - 태그 목록 (사용 빈도순)
- `POST /api/tags` - 태그 생성
- `DELETE /api/tags/{id}` - 태그 삭제

## 환경 변수

### Backend (.env)

```
DATABASE_URL=sqlite+aiosqlite:///./paper_curation.db
# PostgreSQL: postgresql+asyncpg://user:password@localhost:5432/paper_curation
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
