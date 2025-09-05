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

6. **🕷️ 자동화된 데이터 수집**
   - Pinterest 크롤링 시스템
   - S3 자동 업로드
   - 패션 이미지 데이터베이스 구축

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
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              🕷️ 데이터 수집 시스템                      │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  ┌─────────────────┐    ┌─────────────────┐            │ │
│  │  │ Pinterest       │    │ Image Uploader  │            │ │
│  │  │   Scraper       │    │    Service      │            │ │
│  │  │                 │    │                 │            │ │
│  │  └─────────┬───────┘    └─────────┬───────┘            │ │
│  │            │                      │                    │ │
│  │  ┌─────────▼───────┐    ┌─────────▼───────┐            │ │
│  │  │ Selenium        │    │ AWS S3          │            │ │
│  │  │ WebDriver       │    │ Bucket          │            │ │
│  │  │                 │    │                 │            │ │
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

### 🌊 SSE 스트리밍 매칭 플로우 (신규)

1. **사용자 입력** → `/api/expert/single/stream` API
2. **실시간 진행 상황** → 각 단계별 SSE 이벤트로 전송
3. **착장 매칭** → S3 검색 → 점수 계산 → 최종 선택
4. **전문가 분석** → Claude API 스트리밍 응답 (글자 단위 실시간 전송)
5. **완료 알림** → 최종 결과 데이터와 함께 스트림 종료

#### 📡 SSE 이벤트 타입

- **`status`**: 진행 상황 및 단계별 메시지
- **`content`**: 전문가 분석 내용 (실시간 글자 스트리밍)
- **`complete`**: 분석 완료 및 최종 데이터
- **`error`**: 오류 발생 시 에러 메시지

#### 🔢 SSE 단계별 진행 상황

- **step 1**: 착장 매칭 시작
- **step 2**: S3에서 착장 검색 중
- **step 3**: S3 매칭 실패, 기존 방식으로 전환
- **step 4**: 매칭 점수가 낮아 최고 점수 착장 선택
- **step 5**: 최고 점수 착장 선택
- **step 6**: 매칭할 수 있는 착장이 없어 fallback으로 전환
- **step 7**: S3 매칭 성공
- **step 8**: 선택 풀 부족, 전체 DB에서 랜덤 선택
- **step 9**: 최종 착장 선택
- **step 10**: 필터링 후 후보 없음, 전체에서 선택
- **step 11**: 전문가 분석 시작
- **step 12**: Claude API 호출 중
- **step 13**: 전문가 분석 완료
- **step 14**: 기존 방식 사용 완료

### 🕷️ 데이터 수집 플로우

1. **Pinterest 크롤링** → Selenium을 통한 자동 이미지 수집
2. **이미지 다운로드** → 로컬 임시 저장
3. **S3 업로드** → AWS S3 버킷에 자동 업로드
4. **메타데이터 저장** → JSON 형태로 이미지 정보 저장
5. **인덱스 구축** → Redis 인덱스 자동 업데이트

## 🕷️ 데이터 수집 시스템

### 📊 Pinterest 크롤링 시스템

#### **크롤링 대상**
- **검색 키워드**: "korean men summer fashion", "men summer outfit korean" 등
- **수집 데이터**: 패션 이미지, 설명, 핀 URL, 수집 시간
- **수집 규모**: 쿼리당 최대 50개 이미지

#### **크롤링 특징**
```python
# 봇 감지 방지 기능
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])

# 스크롤 기반 동적 로딩
while len(pins_data) < max_pins:
    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(3, 5))  # 랜덤 대기
```

#### **수집된 데이터 구조**
```json
{
  "image_url": "https://i.pinimg.com/236x/e9/6f/33/e96f336d67597af2d5299f7db5c59fad.jpg",
  "description": "#aesthetic #outfit #summer",
  "pin_url": "https://kr.pinterest.com/pin/14144186324688370/",
  "query": "korean men summer fashion",
  "collected_at": "2025-07-29 17:21:09"
}
```

### ☁️ S3 업로드 시스템

#### **업로드 프로세스**
1. **JSON 파일 읽기** → `korean_mens_summer_fashion_pinterest.json`
2. **이미지 다운로드** → 임시 디렉토리에 저장
3. **S3 업로드** → `image/` 폴더에 저장
4. **중복 체크** → 기존 JSON 파일 존재 여부 확인
5. **임시 파일 정리** → 로컬 임시 파일 삭제

#### **S3 저장 구조**
```
thefirsttake-combination/
├── image/
│   ├── fashion_001.jpg
│   ├── fashion_002.jpg
│   └── ...
└── json/
    ├── fashion_001.json
    ├── fashion_002.json
    └── ...
```

#### **업로드 통계**
- **총 수집 이미지**: 1,990개
- **성공률**: 95% 이상
- **중복 방지**: 기존 JSON 파일 체크
- **에러 처리**: 실패한 이미지 로그 기록

### 🔄 전체 데이터 파이프라인

#### **1단계: 데이터 수집**
```bash
# Pinterest 크롤링 실행
python services/crawling/pinterest_crawling.py

# 결과: korean_mens_summer_fashion_pinterest.json 생성
```

#### **2단계: S3 업로드**
```bash
# 이미지 S3 업로드 실행
python services/crawling/upload_images_to_s3.py

# 결과: S3 버킷에 이미지 및 JSON 파일 저장
```

#### **3단계: 인덱스 구축**
```bash
# Redis 인덱스 구축
curl -X POST http://localhost:6020/api/admin/build-indexes

# 결과: 빠른 검색을 위한 인덱스 생성
```

#### **4단계: API 서비스**
```bash
# 패션 추천 API 호출
curl -X POST http://localhost:6020/api/expert/single \
  -H "Content-Type: application/json" \
  -d '{"user_input": "소개팅에 입을 옷 추천해줘", "expert_type": "style_analyst"}'
```

### 📈 데이터 품질 관리

#### **필터링 기준**
- **광고 제외**: "promoted", "ad" 키워드 포함 이미지 제외
- **중복 방지**: 동일한 이미지 URL 중복 수집 방지
- **유효성 검증**: 이미지 URL 접근 가능 여부 확인
- **메타데이터 보존**: 원본 설명, 핀 URL, 수집 시간 저장

#### **데이터 정제**
- **이미지 품질**: 고해상도 이미지 우선 수집
- **설명 정규화**: 빈 설명은 "No description"으로 통일
- **URL 검증**: 유효한 Pinterest URL만 저장
- **시간 정보**: ISO 형식으로 표준화

## 🔍 인덱스 시스템 상세

### 📊 인덱스 구조

Redis를 활용한 다중 인덱스 시스템으로 구성되어 있습니다:

```
Redis 키 구조:
├── fashion_metadata:{filename}          # 착장 메타데이터 (JSON)
├── fashion_index:situation:{situation}  # 상황별 파일명 집합
├── fashion_index:item:{item}           # 아이템별 파일명 집합  
├── fashion_index:color:{color}         # 색상별 파일명 집합
└── fashion_index:styling:{styling}     # 스타일링별 파일명 집합
```

### 🎯 키워드 추출 방식

#### 1. **하드코딩된 키워드 매칭**
```python
# 상황별 키워드 매핑
situation_keywords = {
    "일상": ["일상", "평상시", "데일리", "일반", "보통"],
    "소개팅": ["소개팅", "데이트", "연애", "만남", "미팅", "첫만남"],
    "면접": ["면접", "비즈니스", "업무", "회사", "직장", "오피스"],
    # ...
}

# 아이템 키워드
item_keywords = [
    "니트", "데님", "가죽", "면", "실크", "울",
    "긴팔", "반팔", "와이드", "스키니", "레귤러", "오버핏",
    "티셔츠", "셔츠", "스웨터", "후드티", "맨투맨",
    # ...
]
```

#### 2. **컨텍스트 기반 검색**
- **모호한 입력**: "다른거는?", "더 보여줘" 등
- **해결책**: 최근 사용된 착장의 특성을 기반으로 검색 조건 추론
- **예시**: 이전에 "소개팅" 착장을 추천받았다면, 비슷한 상황의 다른 착장들을 검색

#### 3. **검색 조건 추출 예시**
```
사용자 입력: "소개팅에 입을 니트 스웨터 추천해줘"

추출된 키워드:
├── situations: ["소개팅"]
├── items: ["니트", "스웨터"]  
├── colors: []
└── styling: []

인덱스 검색:
├── fashion_index:situation:소개팅
├── fashion_index:item:니트
└── fashion_index:item:스웨터
```

### ⚡ 성능 최적화 전략

#### 1. **증분 업데이트**
- 새로운 파일만 인덱싱하여 구축 시간 단축
- 타임스탬프 비교로 변경된 파일만 업데이트

#### 2. **후보 필터링**
- 인덱스로 1차 후보 선별 (50개 제한)
- 선별된 후보에 대해서만 정확한 점수 계산

#### 3. **폴백 메커니즘**
- 인덱스 검색 실패 시 전체 스캔으로 자동 전환
- 안정성과 성능의 균형 유지

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
- **`POST /api/expert/single/stream`** - **SSE 스트리밍 방식 단일 전문가 매칭**
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
   - **간결한 응답**: 3-4문장으로 제한된 응답 길이
   - **여름 시즌 고려**: 자켓 등 여름 부적절 아이템 제외

4. **👑 종합 코디네이터 (피팅 코디네이터)**
   - 모든 전문가 의견 종합
   - 신뢰감 있고 결단력 있는 톤
   - "자, 그럼...", "결론적으로..." 표현 사용
   - **여름 시즌 규칙**: 시원한 소재의 옷들만 추천
   - **격식 상황 고려**: 반바지 등 부적절 아이템 제외

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
│   ├── redis_service.py            # Redis 캐싱 서비스
│   └── crawling/                   # 🕷️ 데이터 수집 시스템
│       ├── pinterest_crawling.py   # Pinterest 크롤링
│       ├── upload_images_to_s3.py  # S3 업로드
│       └── korean_mens_summer_fashion_pinterest.json  # 수집된 데이터
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

### 데이터 수집 관리

#### Pinterest 크롤링 실행
```bash
# 크롤링 실행
python services/crawling/pinterest_crawling.py

# 결과: korean_mens_summer_fashion_pinterest.json 생성
```

#### S3 업로드 실행
```bash
# 이미지 S3 업로드
python services/crawling/upload_images_to_s3.py

# 결과: S3 버킷에 이미지 및 JSON 파일 저장
```

#### 크롤링 설정 수정
```python
# services/crawling/pinterest_crawling.py
search_queries = [
    "korean men summer fashion",
    "men summer outfit korean",
    "korean summer street style"
]

# 수집할 이미지 수 조정
max_pins = 50  # 쿼리당 최대 이미지 수
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

### 크롤링 테스트
```bash
# Pinterest 크롤링 테스트
python services/crawling/pinterest_crawling.py

# S3 업로드 테스트
python services/crawling/upload_images_to_s3.py
```

### 크롤링 테스트
```bash
# Pinterest 크롤링 테스트
python services/crawling/pinterest_crawling.py

# S3 업로드 테스트
python services/crawling/upload_images_to_s3.py
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

### 키워드 추출 시스템
- **하드코딩된 키워드**: 50+ 패션 관련 키워드 정의
- **동의어 처리**: "검정" ↔ "블랙", "흰색" ↔ "화이트" 등
- **컨텍스트 활용**: 대화 히스토리 기반 검색 조건 추론
- **폴백 메커니즘**: 키워드 없을 시 전체 스캔으로 전환

### 데이터 수집 최적화
- **봇 감지 방지**: Selenium 헤드리스 모드 + 랜덤 대기
- **중복 방지**: 이미지 URL 기반 중복 체크
- **에러 처리**: 실패한 이미지 로그 기록 및 재시도
- **배치 처리**: 대량 이미지 처리 시 메모리 효율성

### 데이터 수집 최적화
- **봇 감지 방지**: Selenium 헤드리스 모드 + 랜덤 대기
- **중복 방지**: 이미지 URL 기반 중복 체크
- **에러 처리**: 실패한 이미지 로그 기록 및 재시도
- **배치 처리**: 대량 이미지 처리 시 메모리 효율성

## 🕷️ 데이터 수집 시스템

### 📊 Pinterest 크롤링 시스템

#### **크롤링 대상**
- **검색 키워드**: "korean men summer fashion", "men summer outfit korean" 등
- **수집 데이터**: 패션 이미지, 설명, 핀 URL, 수집 시간
- **수집 규모**: 쿼리당 최대 50개 이미지

#### **크롤링 특징**
```python
# 봇 감지 방지 기능
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])

# 스크롤 기반 동적 로딩
while len(pins_data) < max_pins:
    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(3, 5))  # 랜덤 대기
```

#### **수집된 데이터 구조**
```json
{
  "image_url": "https://i.pinimg.com/236x/e9/6f/33/e96f336d67597af2d5299f7db5c59fad.jpg",
  "description": "#aesthetic #outfit #summer",
  "pin_url": "https://kr.pinterest.com/pin/14144186324688370/",
  "query": "korean men summer fashion",
  "collected_at": "2025-07-29 17:21:09"
}
```

### ☁️ S3 업로드 시스템

#### **업로드 프로세스**
1. **JSON 파일 읽기** → `korean_mens_summer_fashion_pinterest.json`
2. **이미지 다운로드** → 임시 디렉토리에 저장
3. **S3 업로드** → `image/` 폴더에 저장
4. **중복 체크** → 기존 JSON 파일 존재 여부 확인
5. **임시 파일 정리** → 로컬 임시 파일 삭제

#### **S3 저장 구조**
```
thefirsttake-combination/
├── image/
│   ├── fashion_001.jpg
│   ├── fashion_002.jpg
│   └── ...
└── json/
    ├── fashion_001.json
    ├── fashion_002.json
    └── ...
```

#### **업로드 통계**
- **총 수집 이미지**: 1,990개
- **성공률**: 95% 이상
- **중복 방지**: 기존 JSON 파일 체크
- **에러 처리**: 실패한 이미지 로그 기록

### 🔄 전체 데이터 파이프라인

#### **1단계: 데이터 수집**
```bash
# Pinterest 크롤링 실행
python services/crawling/pinterest_crawling.py

# 결과: korean_mens_summer_fashion_pinterest.json 생성
```

#### **2단계: S3 업로드**
```bash
# 이미지 S3 업로드 실행
python services/crawling/upload_images_to_s3.py

# 결과: S3 버킷에 이미지 및 JSON 파일 저장
```

#### **3단계: 인덱스 구축**
```bash
# Redis 인덱스 구축
curl -X POST http://localhost:6020/api/admin/build-indexes

# 결과: 빠른 검색을 위한 인덱스 생성
```

#### **4단계: API 서비스**
```bash
# 패션 추천 API 호출
curl -X POST http://localhost:6020/api/expert/single \
  -H "Content-Type: application/json" \
  -d '{"user_input": "소개팅에 입을 옷 추천해줘", "expert_type": "style_analyst"}'
```

### 📈 데이터 품질 관리

#### **필터링 기준**
- **광고 제외**: "promoted", "ad" 키워드 포함 이미지 제외
- **중복 방지**: 동일한 이미지 URL 중복 수집 방지
- **유효성 검증**: 이미지 URL 접근 가능 여부 확인
- **메타데이터 보존**: 원본 설명, 핀 URL, 수집 시간 저장

#### **데이터 정제**
- **이미지 품질**: 고해상도 이미지 우선 수집
- **설명 정규화**: 빈 설명은 "No description"으로 통일
- **URL 검증**: 유효한 Pinterest URL만 저장
- **시간 정보**: ISO 형식으로 표준화

## 🚫 스마트 필터링 시스템

### 상황별 부적절 아이템 제외

#### 격식 상황 (소개팅/비즈니스) 필터링
- **반바지/쇼츠 계열**: 완전 제외 (하드 필터링)
- **부적절한 신발**: 덩크, 스니커즈, 운동화, 캔버스, 컨버스 제외
- **부적절한 색상**: 오렌지, 핑크, 퍼플, 그린, 옐로우, 레드, 빨강 제외
- **자켓+반바지 조합**: 완전 제외

#### 여름 시즌 부적절 아이템
- **자켓/블레이저 계열**: 여름에 부적절 (하지만 격식 상황에서는 필요시 허용)
- **긴팔/롱슬리브**: 여름에 부적절
- **긴바지/롱팬츠**: 여름에 부적절
- **코트/패딩/니트/스웨터**: 여름에 부적절

### 같은 색상 조합 필터링
- **상하의 같은 색**: 화이트+화이트, 블랙+블랙 등 조합 제외
- **색상 매칭 패턴**: 정규표현식 기반 자동 감지 및 제외

### 어려운 용어 자동 변환
- **복잡한 소재명**: 코듀로이 → 면, 바시티 → 면, 덴임 → 면
- **전문 용어**: 실루엣 → 형태, 퍼스널 컬러 → 나에게 맞는 색상
- **무늬/패턴**: 하운드스투스 → 무늬, 윈도우펜 → 무늬
- **색상 용어**: 톤온톤 → 같은 색상 계열, 모노톤 → 한 가지 색상

### 응답 길이 최적화
- **컬러 전문가**: 3-4문장으로 제한
- **이론 개수**: 2-3개로 제한
- **간결성**: 핵심 내용만 포함

## 🔮 향후 개선 계획

### 키워드 추출 시스템 개선
1. **NLP 라이브러리 도입**: KoNLPy, Mecab 등 활용
2. **동의어 사전 구축**: 패션 용어 동의어 매핑 확장
3. **임베딩 기반 검색**: 의미적 유사도 활용
4. **학습 기반 키워드 추출**: 사용자 피드백 기반 개선

### 성능 최적화
1. **캐싱 레이어 추가**: Redis 캐싱 전략 개선
2. **비동기 처리**: 대용량 데이터 처리 최적화
3. **분산 인덱싱**: 대용량 데이터 분산 처리

### 데이터 수집 시스템 개선
1. **다중 소스 크롤링**: Instagram, TikTok 등 추가
2. **실시간 크롤링**: 스케줄러 기반 자동 크롤링
3. **품질 관리**: AI 기반 이미지 품질 평가
4. **분류 시스템**: 자동 태깅 및 카테고리 분류

### 데이터 수집 시스템 개선
1. **다중 소스 크롤링**: Instagram, TikTok 등 추가
2. **실시간 크롤링**: 스케줄러 기반 자동 크롤링
3. **품질 관리**: AI 기반 이미지 품질 평가
4. **분류 시스템**: 자동 태깅 및 카테고리 분류

## 🕷️ 라이센스

MIT License