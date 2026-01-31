# 📊 Stock Analysis System

개인 주식 관리 및 분석 자동화 시스템

## 🎯 주요 기능

- **주식 기술적 지표 수집**
  - RSI (Relative Strength Index) + 과열/침체 상태 표시
  - 이동평균 (MA 20/50/200) + 정배열/역배열 감지
  - **장기 이평선 가격 표시** (MA20/50/200 + 현재가 대비 위치)
  - 골든크로스/데드크로스 자동 감지 (최근 5일 내)
  - 볼린저 밴드
  - MACD
  - 이격도(20일) + 상태 분석
  - 변동성, 지지/저항선
  
- **실시간 환율 정보** (USD/KRW)
- **거시경제 지표** (GDP, 금리, 인플레이션 등)
- **Gemini AI 분석용 데이터 생성**
  - **자산 유형별 투자 전략 가이드라인** ⭐ NEW
  - 테크주: 균형 전략 (추세 + 과열 필터)
  - 부동산 ETF: 배당 수익률 스프레드
  - 금 ETF: 추세 + 리스크 오프
  - 암호화폐: 순수 추세추종
- **텔레그램 자동 발송** (매일 오전 7시)
  - 상세 주식 리포트 (섹터, RSI, 이평선, 크로스, 이격도)
  - 이모지 기반 직관적 정보 표시
  - JSON 데이터 첨부
- **GitHub Actions 자동 실행**

## 🏗️ 시스템 아키텍처

```
Primary: yfinance (재시도 로직)
  ↓ 실패시
Fallback 1: Alpha Vantage API
  ↓ 실패시
Fallback 2: Financial Modeling Prep API

환율 전용: ExchangeRate-API
거시경제: FRED API (Federal Reserve Economic Data)
```

## 📁 프로젝트 구조

```
stock-analysis-system/
├── config/
│   ├── stocks.json          # 관리 주식 리스트
│   └── settings.json        # 시스템 설정
├── src/
│   ├── collectors/
│   │   ├── stock_collector.py      # 주식 데이터 수집
│   │   ├── exchange_collector.py   # 환율 데이터 수집
│   │   └── macro_collector.py      # 거시경제 데이터 수집
│   ├── analyzers/
│   │   └── technical_analyzer.py   # 기술적 지표 계산
│   ├── formatters/
│   │   └── gemini_formatter.py     # Gemini AI 포맷 변환
│   └── notifiers/
│       └── telegram_notifier.py    # 텔레그램 발송
├── main.py                  # 메인 실행 파일
├── requirements.txt
├── .github/
│   └── workflows/
│       └── daily-analysis.yml
└── README.md
```

## 🔧 설정 방법

### 1. 환경 변수 설정 (GitHub Secrets)

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key (선택)
FMP_API_KEY=your_fmp_key (선택)
FRED_API_KEY=your_fred_key (선택)
```

### 2. 의존성 설치

**주의:** `pandas-ta` 패키지는 제거되었습니다. 모든 기술적 지표는 pandas와 numpy로 직접 구현되어 있습니다.

```bash
pip install -r requirements.txt
```

**문제 발생 시:**
- Python 3.11 이상 사용 권장
- 가상환경 사용 권장: `python -m venv venv && source venv/bin/activate`

### 3. stocks.json 설정 예시

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
  ]
}
```

**지원하는 종목:**
- 🇺🇸 미국 주식: `AAPL`, `MSFT`, `TSLA` 등
- 🇰🇷 한국 주식: `005930.KS` (삼성전자), `000660.KS` (SK하이닉스) 등
- 📊 한국 ETF: `438650.KS` (TIGER 리츠), `411060.KS` (ACE 금현물) 등
- 💰 암호화폐: `BTC-USD` (비트코인), `ETH-USD` (이더리움) 등

## 🚀 실행 방법

### 로컬 실행
```bash
pip install -r requirements.txt
python main.py
```

### GitHub Actions
- 매일 오전 7시 (KST) 자동 실행
- 수동 실행: Actions 탭에서 "Run workflow"

## 📊 출력 데이터 형식

- JSON 형식으로 구조화된 데이터
- Gemini AI 분석에 최적화된 포맷
- 텔레그램 메시지로 전송

## 🛡️ 에러 핸들링

- 3단계 Fallback 시스템
- 재시도 로직 (exponential backoff)
- 실패 시 알림 발송
- 상세 로깅
