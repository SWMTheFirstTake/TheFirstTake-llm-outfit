# TheFirstTake LLM Outfit API

LLM 기반 의상 추천 API 서버입니다.

## 🚀 빠른 시작

### 방법 1: Docker 없이 (간단)

1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **서버 실행**
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
- `GET /api/outfit` - 의상 추천
- `GET /docs` - Swagger UI 문서

**서버 주소:** `http://localhost:6020` (로컬) 또는 `http://your-ec2-ip:6020` (프로덕션)

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
   sudo apt-get install -y python3 python3-pip python3-venv git
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

## 📁 프로젝트 구조

```
.
├── main.py                    # FastAPI 메인 애플리케이션
├── requirements.txt           # Python 의존성
├── start_local.py            # 로컬 개발 서버 시작 스크립트
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

`main.py` 파일에 새로운 라우트를 추가하세요:

```python
@app.post("/api/recommend")
async def recommend_outfit(user_preferences: dict):
    # LLM 로직 구현
    return {"recommendation": "추천 의상"}
```

### 환경 변수 설정

`env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요.

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

## 이미지 착장 분석 API (Claude Vision)

- 엔드포인트: `POST /api/vision/analyze-outfit`
- 요청: multipart/form-data로 이미지 파일 업로드 (필드명: `file`)
- 응답 예시:

```
{
  "analysis": "네이비 코튼 셔츠와 베이지 울 팬츠로 구성된 세련된 봄 코디입니다. ..."
}
```

- 환경변수 또는 코드 내 `YOUR_CLAUDE_API_KEY`를 실제 API 키로 교체 필요

## �� 라이센스

MIT License