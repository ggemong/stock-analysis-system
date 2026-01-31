# 김치 프리미엄 수집 트러블슈팅 가이드

## 문제: 텔레그램에 김치프리미엄 타이틀만 나오고 내용이 없음

### 원인 분석

김치프리미엄 데이터가 표시되지 않는 주요 원인:

1. **환율 데이터 수집 실패** (가장 흔함)
   - ExchangeRate-API 또는 yfinance에서 KRW 환율을 가져오지 못함
   - 환율이 없으면 김치프리미엄 계산 불가

2. **API 호출 제한/차단**
   - GitHub Actions 환경에서 upbit.com 또는 binance.com 접근 제한
   - 네트워크 방화벽이나 rate limit

3. **네트워크 타임아웃**
   - 설정된 timeout(30초) 내에 응답 없음

4. **API 응답 형식 변경**
   - 업비트/바이낸스 API 스펙 변경

---

## 해결 방법

### v1.6.5 업데이트 내용

#### 1. 환율 Fallback 로직 추가
```python
# 환율 수집 실패 시 기본 환율 사용 (1320 KRW/USD)
if krw_rate <= 0:
    krw_rate = 1320.0  # 주기적으로 업데이트 필요
```

**참고**: 기본 환율은 최근 평균값으로 설정되어 있습니다. 정확성을 위해 주기적으로 `main.py` 138번 줄의 값을 업데이트하세요.

#### 2. 상세 로그 추가
```python
# 각 코인별 처리 과정 로그
logger.info(f"  🔍 {crypto} 처리 중...")
logger.debug(f"    업비트 가격: {upbit_price}")
logger.debug(f"    바이낸스 가격: {binance_price}")
```

#### 3. 실패 원인 명시
```python
# 어떤 데이터가 없는지 정확히 표시
reasons = []
if not upbit_price:
    reasons.append("업비트 가격 없음")
if not binance_price:
    reasons.append("바이낸스 가격 없음")
```

---

## 로그 확인 방법

### 정상 수집 시 로그
```
김치 프리미엄 수집 시작... (환율: 1320.50)
  🔍 BTC 처리 중...
    업비트 API 호출: KRW-BTC
    업비트 가격: 157800000.0
    바이낸스 API 호출: BTCUSDT
    바이낸스 가격: 119500.25
  ✅ BTC: +0.35% (균형)
김치 프리미엄 수집 완료 - 성공: 5/5
```

### 실패 시 로그 예시
```
김치 프리미엄 수집 시작... (환율: 1320.00)
  🔍 BTC 처리 중...
  ⚠️ BTC 실패: 업비트 가격 없음
  🔍 ETH 처리 중...
  ❌ ETH 처리 중 오류: HTTPSConnectionPool timeout
김치 프리미엄 수집 완료 - 성공: 0/5
```

---

## 수동 테스트 방법

### 1. 김치프리미엄 수집기 단독 테스트
```bash
cd /path/to/stock-analysis-system
python -m src.collectors.kimchi_premium_collector
```

### 2. 환율 수집 테스트
```bash
python -m src.collectors.exchange_collector
```

### 3. 전체 시스템 테스트 모드
```bash
python main.py --test
```

---

## GitHub Actions 환경 대응

### Network Access 설정 확인

GitHub Actions에서 외부 API 호출이 차단될 수 있습니다. `.github/workflows` 파일에 다음 확인:

```yaml
# 필요시 특정 도메인 허용 설정
env:
  PYTHONHTTPSVERIFY: 0  # SSL 검증 우회 (보안 주의)
```

### API 도메인 상태 확인

- Upbit API: `https://api.upbit.com` - 한국 IP에서만 접근 가능할 수 있음
- Binance API: `https://api.binance.com` - 일부 국가/리전에서 차단

**대안**: 프록시 서버 사용 또는 VPN 설정

---

## 기본 환율 업데이트 방법

`main.py` 138번 줄의 기본 환율을 주기적으로 업데이트하세요:

```python
# 최근 USD/KRW 환율을 확인하여 업데이트
krw_rate = 1320.0  # 예: 2025년 1월 기준 평균
```

**환율 확인 사이트**:
- https://www.xe.com/currencyconverter/
- https://www.google.com/finance/quote/USD-KRW

---

## 긴급 비활성화 방법

김치프리미엄 기능을 임시로 끄려면:

### 방법 1: 모듈 제거
```bash
# kimchi_premium_collector.py 파일 이름 변경
mv src/collectors/kimchi_premium_collector.py \
   src/collectors/kimchi_premium_collector.py.disabled
```

### 방법 2: main.py 수정
```python
# main.py 59-64번 줄 주석 처리
# if KIMCHI_PREMIUM_AVAILABLE:
#     self.kimchi_collector = KimchiPremiumCollector(self.settings)
# else:
#     self.kimchi_collector = None
self.kimchi_collector = None  # 강제 비활성화
```

---

## API Rate Limit 대응

업비트/바이낸스 API는 rate limit이 있습니다:

- **업비트**: 초당 10회, 분당 600회
- **바이낸스**: 가중치 기반 제한

현재 설정으로는 문제없지만, 코인 개수를 늘릴 경우 retry 로직 조정 필요:

```python
# kimchi_premium_collector.py 35-38번 줄
@retry(
    stop=stop_after_attempt(5),  # 3 → 5로 증가
    wait=wait_exponential(multiplier=2, min=4, max=20)  # 대기 시간 증가
)
```

---

## 추가 지원

문제가 지속되면 `stock_analysis.log` 파일 전체를 확인하여:
1. 정확한 에러 메시지 파악
2. 네트워크 연결 상태 확인
3. API 키/인증 문제 여부 확인

**버전**: v1.6.5
**업데이트**: 2025-01-31
