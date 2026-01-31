# Stock Analysis System v1.6.5 - 릴리스 노트

## 🎯 주요 수정사항

### 김치프리미엄 데이터 수집 안정성 개선

**문제**: 텔레그램에서 "🌶️ 김치 프리미엄" 타이틀만 표시되고 내용이 없음

**원인**:
1. 환율 데이터 수집 실패 시 김치프리미엄 수집 건너뜀
2. 빈 데이터(`{}`)가 전달되어도 타이틀은 표시되지만 내용 없음
3. 실패 원인이 명확하지 않아 디버깅 어려움

---

## ✨ 새로운 기능

### 1. 환율 Fallback 로직 (main.py)
```python
# 환율 수집 실패 시 기본 환율 사용
if krw_rate <= 0:
    logger.warning("⚠️ exchange_data에서 환율 없음 - 기본 환율 사용")
    krw_rate = 1320.0  # 최근 평균 환율
    logger.info(f"기본 환율 사용: {krw_rate:.2f}")
```

**효과**: 환율 API가 실패해도 김치프리미엄 계산 가능

### 2. 상세 로그 시스템
```python
logger.info(f"  🔍 {crypto} 처리 중...")
logger.debug(f"    업비트 가격: {upbit_price}")
logger.debug(f"    바이낸스 가격: {binance_price}")
```

**효과**: 어떤 단계에서 실패했는지 정확히 파악 가능

### 3. 실패 원인 명시
```python
reasons = []
if not upbit_price:
    reasons.append("업비트 가격 없음")
if not binance_price:
    reasons.append("바이낸스 가격 없음")

error_msg = ', '.join(reasons)
logger.warning(f"  ⚠️ {crypto} 실패: {error_msg}")
```

**효과**: 각 코인별 실패 원인을 명확히 알 수 있음

### 4. 텔레그램 포맷터 개선
```python
# 실제 성공 데이터가 있을 때만 타이틀 표시
if data.get('kimchi_premium') and len(data['kimchi_premium']) > 0:
    has_content = False
    # ... 데이터 처리 ...
    
    # 데이터가 없으면 타이틀도 제거
    if not has_content:
        msg = msg.replace(f"\n<b>🌶️ 김치 프리미엄</b>\n", "")
```

**효과**: 빈 섹션이 표시되지 않음

---

## 📋 로그 예시

### ✅ 정상 수집
```
김치 프리미엄 수집 시작... (환율: 1320.50)
  🔍 BTC 처리 중...
    업비트 API 호출: KRW-BTC
    업비트 가격: 157800000.0
    바이낸스 API 호출: BTCUSDT
    바이낸스 가격: 119500.25
  ✅ BTC: +0.35% (균형)
  🔍 ETH 처리 중...
  ✅ ETH: +1.25% (프리미엄)
김치 프리미엄 수집 완료 - 성공: 5/5
```

### ⚠️ 부분 실패
```
김치 프리미엄 수집 시작... (환율: 1320.00)
  🔍 BTC 처리 중...
  ✅ BTC: +0.35% (균형)
  🔍 ETH 처리 중...
  ⚠️ ETH 실패: 업비트 가격 없음
  🔍 XRP 처리 중...
  ✅ XRP: -0.15% (균형)
김치 프리미엄 수집 완료 - 성공: 2/5

실패 상세:
  ❌ ETH: 업비트 가격 없음
  ❌ SOL: 바이낸스 가격 없음
```

### ❌ 전체 실패
```
⚠️ exchange_data에서 환율 없음 - 기본 환율 사용
기본 환율 사용: 1320.00
김치 프리미엄 수집 시작... (환율: 1320.00)
  🔍 BTC 처리 중...
  ❌ BTC 처리 중 오류: HTTPSConnectionPool timeout
김치 프리미엄 수집 완료 - 성공: 0/5
```

---

## 📚 추가 문서

### KIMCHI_PREMIUM_TROUBLESHOOTING.md
김치프리미엄 수집 문제 해결 가이드:
- 원인 분석 체크리스트
- 수동 테스트 방법
- GitHub Actions 환경 대응
- 기본 환율 업데이트 방법
- 긴급 비활성화 방법

---

## 🔧 업그레이드 방법

### 1. 기존 시스템 백업
```bash
mv stock-analysis-system stock-analysis-system-backup
```

### 2. 새 버전 압축 해제
```bash
tar -xzf stock-analysis-system-v1_6_5-complete.tar.gz
```

### 3. 설정 파일 복사
```bash
# 기존 환경변수/설정 유지
cp stock-analysis-system-backup/.env stock-analysis-system/
cp stock-analysis-system-backup/config/stocks.json stock-analysis-system/config/
```

### 4. 의존성 재설치
```bash
cd stock-analysis-system
pip install -r requirements.txt --break-system-packages
```

### 5. 테스트 실행
```bash
python main.py --test
```

---

## 🎮 테스트 방법

### 김치프리미엄 단독 테스트
```bash
python -m src.collectors.kimchi_premium_collector
```

### 환율 수집 테스트
```bash
python -m src.collectors.exchange_collector
```

### 전체 시스템 테스트
```bash
python main.py --test
```

---

## ⚙️ 설정 조정

### 기본 환율 변경 (필요시)
`main.py` 138번 줄 수정:
```python
krw_rate = 1350.0  # 현재 환율에 맞게 조정
```

### 디버그 모드 활성화
`main.py` 32번 줄:
```python
logging.basicConfig(
    level=logging.DEBUG,  # INFO → DEBUG 변경
    ...
)
```

---

## 🐛 알려진 제한사항

1. **GitHub Actions 환경**
   - 업비트/바이낸스 API가 특정 리전에서 차단될 수 있음
   - 필요시 프록시 설정 또는 VPN 사용

2. **API Rate Limit**
   - 업비트: 초당 10회, 분당 600회
   - 바이낸스: 가중치 기반 제한
   - 현재 5개 코인으로는 문제없음

3. **기본 환율 정확도**
   - 환율 API 실패 시 사용되는 기본값(1320)은 근사치
   - 정확한 계산이 필요하면 주기적으로 업데이트 필요

---

## 📞 지원

문제 발생 시:
1. `stock_analysis.log` 파일 확인
2. `KIMCHI_PREMIUM_TROUBLESHOOTING.md` 참고
3. 로그를 첨부하여 이슈 리포트

---

**버전**: v1.6.5  
**릴리스 날짜**: 2025-01-31  
**이전 버전**: v1.6.4  
**호환성**: Python 3.8+
