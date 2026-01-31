# 하위 호환성 수정 (v1.6.4 - Backward Compatibility)

## 문제
GitHub에 `kimchi_premium_collector.py` 파일이 없을 때 시스템이 실행되지 않음.

```
ModuleNotFoundError: No module named 'src.collectors.kimchi_premium_collector'
```

## 해결책
김치 프리미엄 기능을 **선택적(Optional)**으로 변경하여, 파일이 없어도 시스템이 정상 동작하도록 수정.

## 수정 내용

### 1. src/collectors/__init__.py
```python
# 조건부 import - 파일이 없어도 에러 없음
try:
    from .kimchi_premium_collector import KimchiPremiumCollector
    __all__ = [
        'StockDataCollector',
        'ExchangeRateCollector',
        'MacroEconomicCollector',
        'KimchiPremiumCollector'  # 있을 때만 export
    ]
except ImportError:
    __all__ = [
        'StockDataCollector',
        'ExchangeRateCollector',
        'MacroEconomicCollector'
    ]
    KimchiPremiumCollector = None  # 없으면 None
```

### 2. main.py
```python
# Optional import
try:
    from src.collectors.kimchi_premium_collector import KimchiPremiumCollector
    KIMCHI_PREMIUM_AVAILABLE = True
except ImportError:
    KimchiPremiumCollector = None
    KIMCHI_PREMIUM_AVAILABLE = False

# 조건부 초기화
if KIMCHI_PREMIUM_AVAILABLE:
    self.kimchi_collector = KimchiPremiumCollector(self.settings)
    logger.info("김치 프리미엄 수집기 활성화")
else:
    self.kimchi_collector = None
    logger.warning("김치 프리미엄 수집기 비활성화 (모듈 없음)")

# 조건부 실행
if self.kimchi_collector:
    kimchi_data = self.kimchi_collector.collect_kimchi_premium(krw_rate)
else:
    kimchi_data = {'kimchi_premium': {}, 'collection_time': datetime.now().isoformat()}
```

## 동작 방식

### Case 1: kimchi_premium_collector.py 있음 ✅
```
✅ 김치 프리미엄 수집기 활성화
✅ 업비트/바이낸스 가격 비교
✅ 김치 프리미엄 데이터 JSON에 포함
```

### Case 2: kimchi_premium_collector.py 없음 ✅
```
⚠️ 김치 프리미엄 수집기 비활성화 (모듈 없음)
✅ 나머지 기능은 정상 동작
✅ 빈 김치 프리미엄 데이터 전달 (에러 없음)
```

## GitHub에 파일 추가하는 방법

### 방법 1: Git 명령어
```bash
cd stock-analysis-system
git add src/collectors/kimchi_premium_collector.py
git commit -m "Add kimchi premium collector"
git push
```

### 방법 2: GitHub 웹 인터페이스
1. GitHub 저장소 이동
2. `src/collectors/` 폴더로 이동
3. "Add file" → "Upload files" 클릭
4. `kimchi_premium_collector.py` 업로드
5. Commit changes

### 방법 3: 전체 다시 업로드
압축 파일을 풀고 전체 파일을 GitHub에 푸시:
```bash
tar -xzf stock-analysis-system-v1.6.4-final.tar.gz
cd stock-analysis-system
git add .
git commit -m "Update to v1.6.4 with kimchi premium"
git push
```

## 확인 방법

### 로컬 테스트
```bash
python main.py
```

로그 확인:
- **파일 있음**: "김치 프리미엄 수집기 활성화"
- **파일 없음**: "김치 프리미엄 수집기 비활성화 (모듈 없음)"

### GitHub Actions 로그 확인
```
[2/5] 데이터 수집 시작...
주식 데이터 수집 중...
환율 데이터 수집 중...
거시경제 데이터 수집 중...
김치 프리미엄 수집 건너뜀 (모듈 비활성화)  ← 이 메시지가 보임
```

## 장점

1. **하위 호환성**: 이전 버전 코드도 정상 동작
2. **점진적 업그레이드**: 파일 하나씩 추가 가능
3. **에러 없음**: 누락된 파일로 인한 실행 중단 없음
4. **명확한 로그**: 어떤 기능이 활성화/비활성화되었는지 명확

## 주의사항

⚠️ **김치 프리미엄 기능을 사용하려면**:
- `kimchi_premium_collector.py` 파일을 반드시 GitHub에 업로드해야 함
- 파일 경로: `src/collectors/kimchi_premium_collector.py`

✅ **파일 없어도**:
- 시스템은 정상 실행됨
- 나머지 모든 기능(MA200, 잼스 페르소나, 기술적 분석 등) 정상 동작

## 버전 정보
- v1.6.4 (backward compatibility)
- 수정 날짜: 2026-01-31
- 변경: 김치 프리미엄 기능 선택적으로 변경
