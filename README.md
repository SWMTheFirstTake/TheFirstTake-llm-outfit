# TheFirstTake LLM Outfit API

🤖 **LLM 기반 패션 큐레이션 및 스타일 분석 API 서버**

Claude Vision API를 활용한 이미지 기반 패션 분석과 다중 전문가 시스템을 통한 개인화된 의상 추천을 제공합니다.

## 🎯 시스템 개요

이 프로젝트는 **LLM Server**로 구성되어 있으며, 다음과 같은 핵심 기능을 제공합니다:

### ✨ 주요 기능

1. **🎨 LLM 기반 패션 큐레이션**
   - Claude API를 활용한 스마트한 스타일 분석
   - 개인화된 패션 추천 시스템
   - **🚀 Redis 인덱싱 기반 고성능 매칭**

2. **👁️ 비전 분석 (Vision Analysis)**
   - 착용 사진 스타일 평가
   - 옷 사진 코디 추천
   - 이미지 기반 패션 아이템 인식

3. **💬 프롬프트 관리**
   - 대화 히스토리 기반 개인화
   - 사용자 선호도 학습
   - **🔄 컨텍스트 인식 검색**

4. **🎭 다중 전문가 시스템**
   - 스타일 분석 전문가
   - 트렌드 전문가  
   - 컬러 전문가
   - 종합 코디네이터

5. **⚡ 고성능 S3 기반 매칭**
   - Redis 인덱싱으로 초고속 검색
   - 대화 컨텍스트 활용 스마트 매칭
   - S3 JSON 데이터 기반 정확한 매칭

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Server (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  Vision Analysis│    │   Style Analyzer│                │
│  │      API        │    │                 │                │
│  └─────────┬───────┘    └─────────┬───────┘                │
│            │                      │                        │
│  ┌─────────▼───────┐    ┌─────────▼───────┐                │
│  │ Claude Vision   │    │ • Outfit Photo  │                │
│  │    Service      │    │   Coordination  │                │
│  │                 │    │   Recommendation│                │
│  └─────────┬───────┘    │ • Worn Photo    │                │
│            │            │   Style Eval.   │                │
│  ┌─────────▼───────┐    └─────────┬───────┘                │
│  │ Claude Vision   │              │                        │
│  │      API        │              │                        │
│  └─────────────────┘              │                        │
│                                   │                        │
│  ┌────────────────────────────────▼─────────────────────┐  │
│  │              Curation API                            │  │
│  └─────────────────┬─────────────────────────────────────┘  │
│                    │                                      │
│  ┌─────────────────▼─────────────────────────────────────┐  │
│  │  ┌─────────────────┐    ┌─────────────────┐          │  │
│  │  │ LLM Service     │    │   Prompt        │          │  │
│  │  │    Claude       │    │   Manager       │          │  │
│  │  │                 │    │                 │          │  │
│  │  └─────────┬───────┘    └─────────┬───────┘          │  │
│  │            │                      │                  │  │
│  │  ┌─────────▼───────┐    ┌─────────▼───────┐          │  │
│  │  │ LLM API Claude  │    │ • Prompt        │          │  │
│  │  │                 │    │   Inquiry       │          │  │
│  │  │                 │    │ • New Response  │          │  │
│  │  │                 │    │   Storage       │          │  │
│  │  └─────────────────┘    └─────────────────┘          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              🚀 고성능 매칭 시스템                      │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  ┌─────────────────┐    ┌─────────────────┐            │ │
│  │  │ Outfit Matcher  │    │ Fashion Index   │            │ │
│  │  │    Service      │    │    Service      │            │ │
│  │  │                 │    │                 │            │ │
│  │  └─────────┬───────┘    └─────────┬───────┘            │ │
│  │            │                      │                    │ │
│  │  ┌─────────▼───────┐    ┌─────────▼───────┐            │ │
│  │  │ Score Calculator│    │ Redis Indexes   │            │ │
│  │  │                 │    │ • Situation     │            │ │
│  │  │                 │    │ • Item          │            │ │
│  │  │                 │    │ • Color         │            │ │
│  │  │                 │    │ • Styling       │            │ │
│  │  └─────────────────┘    └─────────────────┘            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 데이터 플로우

1. **이미지 업로드** → Vision Analysis API
2. **Claude Vision 분석** → 스타일 정보 추출
3. **다중 전문가 평가** → 개별 전문가 의견 수집
4. **종합 코디네이션** → 최종 추천 생성
5. **개인화 적용** → 사용자 히스토리 기반 맞춤 조정

### 🚀 고성능 매칭 플로우

1. **사용자 입력** → `/api/expert/single` API
2. **검색 조건 추출** → 키워드 + 대화 컨텍스트 분석
3. **Redis 인덱스 검색** → 상황/아이템/색상/스타일링 기반 후보 선별
4. **스코어 계산** → 선별된 후보들에 대해서만 정확도 계산
5. **결과 반환** → 최적화된 매칭 결과 제공

## 🚀 빠른 시작

### 방법 1: Docker 없이 (간단)

1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**
   ```bash
   cp env.example .env
   # .env 파일에서 CLAUDE_API_KEY 설정
   ```

3. **서버 실행**
   ```bash
   python main.py
   ```
   또는
   ```bash
   python start_local.py
   ```

### 방법 2: Docker 사용 (권장)

1. **Docker로 실행**
   ```bash
   docker-compose up --build
   ```

### API 엔드포인트

- `GET /` - API 환영 메시지
- `GET /health` - 헬스 체크
- `POST /api/vision/analyze-outfit` - 이미지 기반 패션 분석
- `POST /api/fashion/experts` - 다중 전문가 패션 추천
- **`POST /api/expert/single`** - **고성능 S3 기반 단일 전문가 매칭**
- `GET /docs` - Swagger UI 문서

**서버 주소:** `http://localhost:6020` (로컬) 또는 `http://your-ec2-ip:6020` (프로덕션)

## ⚡ 고성능 매칭 시스템

### 🎯 `/api/expert/single` API

**초고속 S3 기반 착장 매칭**을 제공하는 API입니다.

#### 특징
- **Redis 인덱싱**: 전체 S3 스캔 대신 인덱스 기반 빠른 검색
- **컨텍스트 인식**: 대화 히스토리를 활용한 스마트 검색
- **정확한 매칭**: 7가지 기준으로 정확도 계산
- **다양성 보장**: 중복 방지 및 다양한 스타일 제공

#### 요청 예시
```json
{
  "user_input": "소개팅을 가야 하는 상황이야",
  "room_id": 59,
  "expert_type": "color_expert"
}
```

#### 응답 예시
```json
{
  "data": {
    "search_method": "index",
    "matches": [
      {
        "filename": "outfit_001.json",
        "score": 0.85,
        "situations": ["소개팅", "첫만남"],
        "extracted_items": {
          "top": {"item": "블랙 니트 스웨터", "color": "블랙"},
          "bottom": {"item": "와이드 카고 팬츠", "color": "그레이"},
          "shoes": {"item": "브라운 로퍼", "color": "브라운"}
        }
      }
    ]
  }
}
```

### 🔧 인덱스 관리 API (관리자용)

- `POST /api/admin/build-indexes` - 인덱스 구축
- `POST /api/admin/rebuild-indexes` - 인덱스 재구축
- `GET /api/admin/index-stats` - 인덱스 통계
- `POST /api/admin/search-by-situation` - 상황별 검색 테스트
- `POST /api/admin/search-by-item` - 아이템별 검색 테스트

### 📊 성능 개선 효과

| 항목 | 기존 방식 | 인덱스 방식 | 개선율 |
|------|-----------|-------------|--------|
| 응답 시간 | 3-5초 | 0.5-1초 | **80% 향상** |
| S3 요청 수 | 전체 파일 스캔 | 후보만 조회 | **90% 감소** |
| 메모리 사용량 | 전체 데이터 로드 | 인덱스만 사용 | **70% 감소** |

## 🎭 다중 전문가 시스템

### 전문가 구성

1. **🎯 스타일 분석 전문가**
   - 체형과 핏감 관점에서 분석
   - 까다롭고 분석적인 톤
   - "음...", "흠...", "체형을 보니..." 표현 사용

2. **🔥 트렌드 전문가**
   - 최신 패션 트렌드 반영
   - 젊고 트렌디한 느낌
   - "와!", "오!", "이번 시즌에..." 표현 사용

3. **🎨 컬러 전문가**
   - 퍼스널 컬러와 색상 조합 분석
   - 따뜻하고 열정적인 톤
   - "색상으로 보면...", "컬러 관점에서..." 표현 사용

4. **👑 종합 코디네이터**
   - 모든 전문가 의견 종합
   - 신뢰감 있고 결단력 있는 톤
   - "자, 그럼...", "결론적으로..." 표현 사용

### 전문가 상호작용

- **독립적 판단**: 각 전문가는 자신의 분야에서 독립적으로 평가
- **동의/반대**: 좋은 제안에는 동의, 문제가 있는 제안에는 반대
- **개성 있는 공격**: 필요시 다른 전문가 의견에 대해 개성 있게 비판
- **완전한 차별화**: 반대할 때는 색상, 소재, 핏을 완전히 다르게 제시

## 📁 프로젝트 구조

```
.
├── main.py                    # FastAPI 메인 애플리케이션
├── config.py                  # 설정 관리
├── requirements.txt           # Python 의존성
├── start_local.py            # 로컬 개발 서버 시작 스크립트
├── api/                      # API 라우터
│   ├── __init__.py
│   └── fashion_routes.py     # 패션 관련 API 엔드포인트
├── services/                 # 비즈니스 로직 서비스
│   ├── __init__.py
│   ├── claude_vision_service.py    # Claude Vision API 서비스
│   ├── fashion_expert_service.py   # 다중 전문가 시스템
│   ├── outfit_matcher_service.py   # 🚀 고성능 매칭 서비스
│   ├── fashion_index_service.py    # 🚀 Redis 인덱싱 서비스
│   ├── score_calculator_service.py # 🚀 스코어 계산 서비스
│   ├── s3_service.py               # S3 데이터 관리 서비스
│   └── redis_service.py            # Redis 캐싱 서비스
├── models/                   # 데이터 모델
│   ├── __init__.py
│   └── fashion_models.py     # 패션 관련 데이터 모델
├── .github/workflows/        # GitHub Actions CI/CD
│   ├── deploy.yml           # Docker 배포 (고급)
│   └── deploy-simple.yml    # 직접 배포 (간단)
├── scripts/                 # 배포 스크립트
│   ├── deploy_ec2.sh       # Docker 배포 스크립트
│   └── deploy_simple.sh    # 직접 배포 스크립트
├── Dockerfile              # Docker 이미지 설정 (선택사항)
├── docker-compose.yml      # 로컬 개발용 Docker Compose (선택사항)
├── env.example             # 환경 변수 예시
└── README.md              # 프로젝트 문서
```

## 🔧 개발 가이드

### 새로운 API 엔드포인트 추가

`api/fashion_routes.py` 파일에 새로운 라우트를 추가하세요:

```python
@router.post("/api/recommend")
async def recommend_outfit(user_preferences: dict):
    # LLM 로직 구현
    return {"recommendation": "추천 의상"}
```

### 새로운 전문가 추가

`services/fashion_expert_service.py`에서 새로운 전문가 타입을 추가하세요:

```python
class FashionExpertType(Enum):
    STYLE_ANALYST = "style_analyst"
    TREND_EXPERT = "trend_expert"
    COLOR_EXPERT = "color_expert"
    FITTING_COORDINATOR = "fitting_coordinator"
    YOUR_NEW_EXPERT = "your_new_expert"  # 새로운 전문가
```

### 인덱스 관리

#### 인덱스 구축
```bash
# 전체 인덱스 구축
curl -X POST http://localhost:6020/api/admin/build-indexes

# 인덱스 재구축 (기존 데이터 삭제 후 재생성)
curl -X POST http://localhost:6020/api/admin/rebuild-indexes

# 인덱스 통계 확인
curl -X GET http://localhost:6020/api/admin/index-stats
```

#### 인덱스 구조
```
Redis 키 구조:
- fashion_metadata:{filename} - 착장 메타데이터
- fashion_index:situation:{situation} - 상황별 파일명 집합
- fashion_index:item:{item} - 아이템별 파일명 집합
- fashion_index:color:{color} - 색상별 파일명 집합
- fashion_index:styling:{styling} - 스타일링별 파일명 집합
```

### 환경 변수 설정

`env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요:

```bash
CLAUDE_API_KEY=your_claude_api_key_here
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=your_s3_bucket_name
```

## 🚀 배포

### Docker 없이 배포 (추천)

main 브랜치에 푸시하면 자동으로 배포됩니다:

```bash
git add .
git commit -m "새로운 기능 추가"
git push origin main
```

### Docker로 배포

Docker 관련 파일들을 사용하려면 `.github/workflows/deploy.yml`을 사용하세요.

## 🏗️ CI/CD 파이프라인

### 옵션 1: Docker 없이 배포 (간단)

GitHub Actions를 통해 EC2에 직접 배포합니다.

#### 필요한 GitHub Secrets

- `LLM_OUTFIT_EC2_HOST` - EC2 인스턴스의 퍼블릭 IP
- `LLM_OUTFIT_EC2_USERNAME` - EC2 인스턴스의 SSH 사용자명 (보통 ubuntu)
- `LLM_OUTFIT_EC2_SSH_KEY` - EC2 인스턴스 접속용 SSH 프라이빗 키

#### EC2 설정

1. **Python 및 Git 설치**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv git redis-server
   ```

2. **프로젝트 클론**
   ```bash
   cd /home/ubuntu
   git clone https://github.com/your-username/TheFirstTake-llm-outfit.git llm-outfit-api
   ```

3. **수동 배포 (선택사항)**
   ```bash
   chmod +x scripts/deploy_simple.sh
   ./scripts/deploy_simple.sh
   ```

### 옵션 2: Docker로 배포 (고급)

AWS ECR과 Docker를 사용한 배포입니다.

#### 필요한 GitHub Secrets

- `LLM_OUTFIT_AWS_ACCESS_KEY_ID`
- `LLM_OUTFIT_AWS_SECRET_ACCESS_KEY`
- `LLM_OUTFIT_AWS_REGION`
- `LLM_OUTFIT_EC2_HOST`
- `LLM_OUTFIT_EC2_USERNAME`
- `LLM_OUTFIT_EC2_SSH_KEY`

## 📊 API 사용 예시

### 🚀 고성능 단일 전문가 매칭 API

- **엔드포인트**: `POST /api/expert/single`
- **요청**:
```json
{
  "user_input": "소개팅을 가야 하는 상황이야",
  "room_id": 59,
  "expert_type": "color_expert"
}
```

- **응답 예시**:
```json
{
  "data": {
    "search_method": "index",
    "matches": [
      {
        "filename": "outfit_001.json",
        "score": 0.85,
        "situations": ["소개팅", "첫만남"],
        "extracted_items": {
          "top": {"item": "블랙 니트 스웨터", "color": "블랙"},
          "bottom": {"item": "와이드 카고 팬츠", "color": "그레이"},
          "shoes": {"item": "브라운 로퍼", "color": "브라운"}
        }
      }
    ]
  }
}
```

### 이미지 착장 분석 API (Claude Vision)

- **엔드포인트**: `POST /api/vision/analyze-outfit`
- **요청**: multipart/form-data로 이미지 파일 업로드 (필드명: `file`)
- **응답 예시**:

```json
{
  "analysis": "네이비 코튼 셔츠와 베이지 울 팬츠로 구성된 세련된 봄 코디입니다. 차콜 컬러의 슬림핏 셔츠가 깔끔한 실루엣을 만들어내고, 베이지 톤의 울 팬츠와 조화를 이루어 세련된 느낌을 줍니다. 전체적으로 비즈니스 캐주얼에 적합한 조합입니다."
}
```

### 다중 전문가 패션 추천 API

- **엔드포인트**: `POST /api/fashion/experts`
- **요청**:

```json
{
  "occasion": "소개팅",
  "style_preference": "트렌디하고 깔끔한",
  "user_info": {
    "age": 25,
    "gender": "male"
  }
}
```

- **응답 예시**:

```json
{
  "recommendations": {
    "style_analyst": "음... 체형을 보니 네이비 슬림핏 코튼 셔츠가 잘 어울릴 거야. 깔끔한 실루엣이 멋있어 보일 거야.",
    "trend_expert": "와! 이번 시즌에 라벤더 오버핏 린넨 셔츠가 대세야! 트렌디해!",
    "color_expert": "색상으로 보면 세이지 그린이 퍼스널 컬러랑 완벽해! 컬러 조합이 좋아!",
    "fitting_coordinator": "자, 그럼 라벤더 오버핏 린넨 셔츠에 세이지 그린 레귤러핏 데님 팬츠를 추천할게. 완전 트렌디해!"
  }
}
```

## 🔑 환경변수

- `CLAUDE_API_KEY` - Claude API 키 (필수)
- `REDIS_URL` - Redis 연결 URL (선택사항, 캐싱용)
- `AWS_ACCESS_KEY_ID` - AWS 액세스 키 (S3 사용시)
- `AWS_SECRET_ACCESS_KEY` - AWS 시크릿 키 (S3 사용시)
- `AWS_REGION` - AWS 리전 (S3 사용시)
- `S3_BUCKET_NAME` - S3 버킷 이름 (S3 사용시)
- `LOG_LEVEL` - 로그 레벨 (기본값: INFO)

## 🧪 테스트

### 성능 테스트
```bash
python test_index_performance.py
```

### 컨텍스트 검색 테스트
```bash
python test_context_search.py
```

### Pinterest API 테스트
```bash
python test_pinterest_api.py
```

## 📈 성능 최적화

### 인덱스 기반 검색
- **기존**: 전체 S3 파일 스캔 (3-5초)
- **개선**: Redis 인덱스 기반 검색 (0.5-1초)
- **개선율**: 80% 응답 시간 단축

### 컨텍스트 인식 검색
- **모호한 입력**: "다른거는?", "더 보여줘"
- **해결책**: 대화 히스토리 기반 검색 조건 추론
- **효과**: 사용자 경험 향상

## �� 라이센스

MIT License