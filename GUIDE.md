# 주식 분석 시스템 - 상세 사용 가이드

## 📋 목차
1. [초기 설정](#초기-설정)
2. [GitHub 설정](#github-설정)
3. [로컬 테스트](#로컬-테스트)
4. [자동화 설정](#자동화-설정)
5. [문제 해결](#문제-해결)

---

## 초기 설정

### 1. 텔레그램 봇 생성

1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어 입력
3. 봇 이름 및 사용자명 설정
4. **Bot Token** 저장 (예: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Chat ID 확인

1. 봇과 대화 시작 (아무 메시지나 전송)
2. 브라우저에서 접속: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. `"chat":{"id":` 뒤의 숫자가 **Chat ID** (예: `123456789`)

### 3. API Keys 발급 (선택사항)

#### Alpha Vantage (무료)
- https://www.alphavantage.co/support/#api-key
- 일 500회 제한

#### Financial Modeling Prep (무료)
- https://site.financialmodelingprep.com/developer/docs/
- 일 250회 제한

#### FRED (무료, 무제한)
- https://fred.stlouisfed.org/docs/api/api_key.html
- 거시경제 데이터용

---

## GitHub 설정

### 1. 레포지토리 생성

```bash
# GitHub에서 새 레포지토리 생성
# 로컬에서 초기화
git init
git add .
git commit -m "Initial commit: Stock Analysis System"
git branch -M main
git remote add origin https://github.com/your-username/stock-analysis-system.git
git push -u origin main
```

### 2. GitHub Secrets 설정

레포지토리 → Settings → Secrets and variables → Actions → New repository secret

**필수 설정:**
- `TELEGRAM_BOT_TOKEN`: 텔레그램 봇 토큰
- `TELEGRAM_CHAT_ID`: 텔레그램 채팅 ID

**선택 설정:**
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API 키
- `FMP_API_KEY`: FMP API 키
- `FRED_API_KEY`: FRED API 키

### 3. 주식 리스트 설정

`config/stocks.json` 파일 수정:

```json
{
  "stocks": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "market": "US",
      "sector": "Technology",
      "type": "Stock"
    },
    {
      "symbol": "005930.KS",
      "name": "삼성전자",
      "market": "KR",
      "sector": "Technology",
      "type": "Stock"
    },
    {
      "symbol": "438650.KS",
      "name": "TIGER 리츠부동산인프라",
      "market": "KR",
      "sector": "Real Estate",
      "type": "ETF"
    },
    {
      "symbol": "BTC-USD",
      "name": "Bitcoin",
      "market": "Crypto",
      "sector": "Cryptocurrency",
      "type": "Crypto"
    }
  ],
  "portfolio_summary": {
    "total_assets": 4,
    "us_stocks": 1,
    "kr_stocks": 1,
    "kr_etfs": 1,
    "crypto": 1
  },
  "update_date": "2026-01-30"
}
```

**지원하는 종목 형식:**
- **미국 주식**: `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `TSLA` 등
- **한국 주식**: `005930.KS` (삼성전자), `000660.KS` (SK하이닉스), `005380.KS` (현대차) 등
- **한국 ETF**: `438650.KS` (TIGER 리츠), `411060.KS` (ACE 금현물) 등
- **암호화폐**: `BTC-USD` (비트코인), `ETH-USD` (이더리움) 등

---

## 로컬 테스트

### 1. 환경 설정

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

**의존성 설치 시 주의사항:**
- Python 3.11 이상 권장 (GitHub Actions는 3.11 사용)
- `pandas-ta` 패키지는 제거됨 (모든 지표는 pandas/numpy로 직접 구현)
- 설치 오류 발생 시 `pip install --upgrade pip` 먼저 실행

### 2. 환경 변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
# .env 파일 편집하여 실제 값 입력
```

### 3. 컴포넌트 테스트

```bash
# 전체 컴포넌트 테스트
python main.py --test
```

예상 출력:
```
[1/4] 텔레그램 연결 테스트...
✅ 텔레그램 봇 연결 성공: @your_bot_name

[2/4] 환율 수집 테스트...
✅ ExchangeRate-API 성공: 1320.50

[3/4] 주식 데이터 수집 테스트 (AAPL)...
✅ yfinance 성공: AAPL @ $180.00

[4/4] 거시경제 데이터 수집 테스트...
✅ FRED 성공: VIX = 16.5
```

### 4. 전체 실행

```bash
# 실제 분석 실행
python main.py
```

---

## 자동화 설정

### GitHub Actions 스케줄 변경

`.github/workflows/daily-analysis.yml` 수정:

```yaml
on:
  schedule:
    # 매일 오전 7시 (KST) = 22:00 전날 (UTC)
    - cron: '0 22 * * *'
    
    # 다른 시간 예시:
    # 오전 9시 (KST) = 0 0 * * *
    # 오후 6시 (KST) = 0 9 * * *
```

### 수동 실행

1. GitHub 레포지토리 → Actions 탭
2. "Daily Stock Analysis" 선택
3. "Run workflow" 버튼 클릭

---

## 문제 해결

### 0. 의존성 설치 오류

**증상:**
```
ERROR: Could not find a version that satisfies the requirement pandas-ta==0.3.14b0
```

**해결:**
1. requirements.txt가 최신 버전인지 확인
2. `pandas-ta` 패키지는 제거되었습니다 (사용 안함)
3. Python 3.11 이상 사용
4. 가상환경 사용 권장:
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 또는
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 1. yfinance 데이터 수집 실패

**증상:**
```
❌ yfinance 실패: No data found
```

**해결:**
1. API Key 설정 확인 (Alpha Vantage, FMP)
2. 주식 심볼 확인 (대문자 사용)
3. 네트워크 연결 확인

**시스템 자동 처리:**
- yfinance 실패 → Alpha Vantage로 fallback
- Alpha Vantage 실패 → FMP로 fallback

### 2. 텔레그램 전송 실패

**증상:**
```
❌ 텔레그램 전송 오류: Unauthorized
```

**해결:**
1. Bot Token 확인
2. Chat ID 확인
3. 봇과 최소 1회 대화 시작 필요

### 3. GitHub Actions 실패

**증상:**
```
Error: Environment variable not found
```

**해결:**
1. GitHub Secrets 설정 확인
2. Secret 이름 대소문자 확인
3. Workflow 파일 env 섹션 확인

### 4. 환율 데이터 없음

**증상:**
```
❌ 모든 환율 수집 방법 실패
```

**해결:**
- ExchangeRate-API는 무료이고 안정적
- 네트워크 차단 확인
- 로그에서 구체적 에러 확인

### 5. 거시경제 데이터 없음

**증상:**
```
⚠️ FRED API Key 없음
```

**해결:**
- FRED API Key 발급 (무료)
- 없어도 VIX는 yfinance로 수집됨
- 시스템은 정상 동작

---

## 고급 설정

### 기술적 지표 커스터마이징

`config/settings.json` 수정:

```json
{
  "technical_indicators": {
    "rsi_period": 14,        // RSI 기간
    "ma_periods": [20, 50, 200],  // 이동평균 기간
    "bollinger_period": 20,  // 볼린저 밴드 기간
    "bollinger_std": 2       // 표준편차 배수
  }
}
```

### 수집 데이터 확장

거시경제 지표 추가:

```json
{
  "macro_indicators": {
    "fred_series": {
      "GDP": "GDP",
      "UNEMPLOYMENT": "UNRATE",
      "YOUR_INDICATOR": "FRED_SERIES_ID"
    }
  }
}
```

FRED 시리즈 검색: https://fred.stlouisfed.org/

---

## 데이터 흐름

```
1. main.py 실행
   ↓
2. stocks.json에서 주식 리스트 로드
   ↓
3. 데이터 수집
   - 주식: yfinance → Alpha Vantage → FMP
   - 환율: ExchangeRate-API → yfinance
   - 거시경제: FRED API
   ↓
4. 기술적 분석 (RSI, MA, BB, MACD 등)
   ↓
5. Gemini AI 포맷 변환
   ↓
6. 텔레그램 전송
   - 요약 메시지
   - 전체 JSON 파일
   - Gemini 프롬프트
   ↓
7. 로컬에 JSON 저장
```

---

## 지원

문제가 발생하면:
1. `stock_analysis.log` 파일 확인
2. GitHub Actions 로그 확인
3. 컴포넌트 테스트 실행 (`--test`)

---

**버전:** 1.0.0  
**최종 업데이트:** 2025-01-30
