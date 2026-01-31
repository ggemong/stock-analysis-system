"""
거시경제 지표 수집 모듈
Primary: FRED API (Federal Reserve Economic Data)
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class MacroEconomicCollector:
    """거시경제 지표 수집 클래스"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.series = settings['macro_indicators']['fred_series']
        self.timeout = settings['data_collection']['timeout']
        
        # FRED API가 없으면 경고만 하고 진행
        if not self.fred_api_key:
            logger.warning("⚠️ FRED API Key 없음 - 거시경제 지표 수집 건너뜀")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_fred_series(self, series_id: str, series_name: str) -> Optional[Dict]:
        """FRED에서 특정 경제 지표 가져오기"""
        if not self.fred_api_key:
            return None
        
        try:
            logger.info(f"FRED에서 {series_name} ({series_id}) 데이터 수집 시도")
            
            # 최근 데이터 조회
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 12  # 최근 12개 데이터 포인트
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'observations' not in data or not data['observations']:
                logger.warning(f"❌ FRED: {series_name} 데이터 없음")
                return None
            
            observations = data['observations']
            
            # 최신 값 (가장 최근 유효한 데이터)
            latest = None
            for obs in observations:
                if obs['value'] != '.':
                    latest = obs
                    break
            
            if not latest:
                logger.warning(f"❌ FRED: {series_name} 유효한 데이터 없음")
                return None
            
            current_value = float(latest['value'])
            current_date = latest['date']
            
            # 이전 값 (변화율 계산용)
            previous_value = None
            for obs in observations[1:]:
                if obs['value'] != '.':
                    previous_value = float(obs['value'])
                    break
            
            # 변화 계산
            change = None
            change_percent = None
            if previous_value:
                change = current_value - previous_value
                change_percent = (change / previous_value) * 100 if previous_value != 0 else 0
            
            # 과거 12개월 데이터
            historical = []
            for obs in observations:
                if obs['value'] != '.':
                    historical.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
            
            result = {
                'indicator': series_name,
                'series_id': series_id,
                'current_value': current_value,
                'current_date': current_date,
                'previous_value': previous_value,
                'change': change,
                'change_percent': change_percent,
                'historical': historical,
                'source': 'FRED',
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ FRED 성공: {series_name} = {current_value}")
            return result
            
        except Exception as e:
            logger.error(f"❌ FRED 실패 ({series_name}): {str(e)}")
            return None
    
    def _get_vix_alternative(self) -> Optional[Dict]:
        """VIX 대체 데이터 (yfinance 사용)"""
        try:
            import yfinance as yf
            
            logger.info("yfinance에서 VIX 데이터 수집")
            
            ticker = yf.Ticker("^VIX")
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                return None
            
            current_value = hist['Close'].iloc[-1]
            previous_value = hist['Close'].iloc[0]
            change = current_value - previous_value
            change_percent = (change / previous_value) * 100
            
            return {
                'indicator': 'VIX',
                'current_value': float(current_value),
                'previous_value': float(previous_value),
                'change': float(change),
                'change_percent': float(change_percent),
                'source': 'yfinance',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"VIX 대체 수집 실패: {str(e)}")
            return None
    
    def collect_all(self) -> Dict:
        """모든 거시경제 지표 수집"""
        results = {}
        
        if not self.fred_api_key:
            logger.warning("⚠️ FRED API Key 없음 - 최소 데이터만 수집")
            
            # VIX만 yfinance로 수집
            vix_data = self._get_vix_alternative()
            if vix_data:
                results['VIX'] = vix_data
            
            return {
                'macro_indicators': results,
                'collection_time': datetime.now().isoformat(),
                'note': 'FRED API Key not configured - limited data'
            }
        
        # FRED 데이터 수집
        for name, series_id in self.series.items():
            try:
                if name == 'VIX':
                    # VIX는 FRED와 yfinance 둘 다 시도
                    result = self._get_fred_series(series_id, name)
                    if not result or not result.get('success'):
                        result = self._get_vix_alternative()
                else:
                    result = self._get_fred_series(series_id, name)
                
                if result and result.get('success'):
                    results[name] = result
                    
            except Exception as e:
                logger.error(f"지표 수집 오류 ({name}): {str(e)}")
        
        return {
            'macro_indicators': results,
            'collection_time': datetime.now().isoformat(),
            'total_indicators': len(self.series),
            'successful': len(results),
            'failed': len(self.series) - len(results)
        }
    
    def get_market_sentiment_summary(self, data: Dict) -> str:
        """거시경제 지표 기반 시장 심리 요약"""
        if not data.get('macro_indicators'):
            return "거시경제 데이터 부족"
        
        indicators = data['macro_indicators']
        summary_parts = []
        
        # VIX 분석
        if 'VIX' in indicators:
            vix = indicators['VIX']['current_value']
            if vix < 15:
                summary_parts.append("VIX 낮음 (시장 안정)")
            elif vix > 25:
                summary_parts.append("VIX 높음 (시장 불안)")
            else:
                summary_parts.append("VIX 보통")
        
        # 금리 분석
        if 'FED_RATE' in indicators:
            fed_rate = indicators['FED_RATE']['current_value']
            change = indicators['FED_RATE'].get('change', 0)
            if change > 0:
                summary_parts.append(f"Fed 금리 상승 ({fed_rate:.2f}%)")
            elif change < 0:
                summary_parts.append(f"Fed 금리 하락 ({fed_rate:.2f}%)")
            else:
                summary_parts.append(f"Fed 금리 유지 ({fed_rate:.2f}%)")
        
        # 실업률 분석
        if 'UNEMPLOYMENT' in indicators:
            unemployment = indicators['UNEMPLOYMENT']['current_value']
            if unemployment < 4:
                summary_parts.append("실업률 낮음 (경제 강세)")
            elif unemployment > 6:
                summary_parts.append("실업률 높음 (경제 약세)")
        
        return " | ".join(summary_parts) if summary_parts else "분석 불가"


# 테스트 코드
if __name__ == "__main__":
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    collector = MacroEconomicCollector(settings)
    result = collector.collect_all()
    
    print("\n=== 거시경제 지표 수집 결과 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('macro_indicators'):
        sentiment = collector.get_market_sentiment_summary(result)
        print(f"\n시장 심리: {sentiment}")
