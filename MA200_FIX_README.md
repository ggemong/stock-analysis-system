# MA200 계산 문제 수정

## 문제 상황
JSON 출력에서 모든 종목의 `MA200` 값이 `null` 또는 `NaN`으로 표시되는 문제가 발생했습니다.

```json
"moving_averages": {
  "MA20": 436.99950103759767,
  "MA50": 443.57740112304685,
  "MA200": null  // ❌ 문제!
}
```

## 원인 분석
MA200(200일 이동평균선)을 계산하려면 **최소 200 거래일**의 데이터가 필요합니다.

기존 설정:
- **yfinance**: `period="6mo"` (약 120-130 거래일) ❌
- **Alpha Vantage**: `outputsize=compact` (최근 100일만) ❌
- **FMP**: 전체 히스토리 제공 ✅

→ 데이터가 부족하여 MA200 계산 불가

## 수정 내용

### 1. yfinance 데이터 수집 기간 변경
**파일**: `src/collectors/stock_collector.py`

```python
# 변경 전 (Line 49-50)
# 과거 데이터 (6개월)
hist = ticker.history(period="6mo")

# 변경 후
# 과거 데이터 (1년 - MA200 계산을 위해 필요)
hist = ticker.history(period="1y")
```

**효과**: 1년 = 약 252 거래일 → MA200 계산 가능 ✅

### 2. Alpha Vantage outputsize 변경
**파일**: `src/collectors/stock_collector.py`

```python
# 변경 전 (Line 117-119)
# Time Series Daily
time.sleep(12)  # API 제한 (5 calls/min)
ts_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={self.alpha_vantage_key}"

# 변경 후
# Time Series Daily (full = 20년치, MA200 계산에 필요)
time.sleep(12)  # API 제한 (5 calls/min)
ts_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={self.alpha_vantage_key}"
```

**효과**: `compact` (100일) → `full` (20년) → MA200 계산 가능 ✅

### 3. FMP
변경 없음 - 이미 전체 히스토리를 제공하고 있음 ✅

## 검증

수정 후 예상 결과:
```json
"moving_averages": {
  "MA20": 436.99950103759767,
  "MA50": 443.57740112304685,
  "MA200": 425.12345678901234  // ✅ 정상 계산됨!
}
```

## 주의사항

### 성능 영향
- **yfinance**: 6개월 → 1년 데이터 수집으로 약간의 시간 증가 (무시할 수준)
- **Alpha Vantage**: `full` 사용 시 응답 크기 증가, API 제한 동일 (5 calls/min)

### API 제한
- Alpha Vantage Free Tier: 5 requests/minute, 500 requests/day
- 종목이 많을 경우 API 제한에 걸릴 수 있으므로 주의

## 테스트 방법

1. 시스템 실행:
```bash
python main.py
```

2. JSON 출력 확인:
```bash
cat stock_analysis_*.json | grep -A 5 "moving_averages"
```

3. MA200 값이 숫자로 표시되는지 확인 (null/NaN이 아닌지)

## 추가 개선 사항

MA200이 여전히 null인 경우:
1. **상장한지 얼마 안 된 종목**: 실제로 200 거래일 데이터가 없을 수 있음
2. **데이터 소스 문제**: API에서 충분한 데이터를 제공하지 않을 수 있음

이 경우 `technical_analyzer.py`의 Line 178에서 데이터 길이를 확인합니다:
```python
ma200_current = ma200.iloc[-1] if len(prices) >= 200 else None
```

## 버전 정보
- **수정 버전**: v1.6.2
- **수정 날짜**: 2026-01-31
- **수정 파일**: `src/collectors/stock_collector.py`
