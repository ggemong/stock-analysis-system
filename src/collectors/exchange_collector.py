"""
환율 데이터 수집 모듈
Primary: ExchangeRate-API -> Fallback: yfinance
"""

import requests
import yfinance as yf
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import json

logger = logging.getLogger(__name__)


class ExchangeRateCollector:
    """환율 정보 수집 클래스 (하이브리드 방식)"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.base_currency = settings['exchange_rates']['base_currency']
        self.target_currencies = settings['exchange_rates']['target_currencies']
        self.timeout = settings['data_collection']['timeout']
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_from_exchangerate_api(self, target_currency: str) -> Optional[Dict]:
        """ExchangeRate-API에서 환율 정보 가져오기 (Primary)"""
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}"
            
            logger.info(f"ExchangeRate-API에서 {self.base_currency}/{target_currency} 데이터 수집 시도")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if target_currency in data['rates']:
                current_rate = data['rates'][target_currency]
                
                result = {
                    'pair': f"{self.base_currency}/{target_currency}",
                    'current_rate': current_rate,
                    'timestamp': data['time_last_updated'],
                    'source': 'ExchangeRate-API',
                    'success': True
                }
                
                logger.info(f"✅ ExchangeRate-API 성공: {current_rate:.2f}")
                return result
            else:
                logger.warning(f"❌ {target_currency} not found in response")
                return None
                
        except Exception as e:
            logger.error(f"❌ ExchangeRate-API 실패: {str(e)}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_from_yfinance(self, target_currency: str) -> Optional[Dict]:
        """yfinance에서 환율 정보 가져오기 (Fallback)"""
        try:
            symbol = f"{self.base_currency}{target_currency}=X"
            
            logger.info(f"yfinance에서 {symbol} 데이터 수집 시도")
            
            ticker = yf.Ticker(symbol)
            
            # 현재 환율
            info = ticker.info
            current_rate = info.get('regularMarketPrice') or info.get('previousClose')
            
            if not current_rate:
                logger.warning(f"❌ yfinance: 현재 환율 정보 없음")
                return None
            
            # 과거 데이터 (1개월)
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                logger.warning(f"❌ yfinance: 과거 데이터 없음")
                previous_rate = current_rate
            else:
                previous_rate = hist['Close'].iloc[0]
            
            change = current_rate - previous_rate
            change_percent = (change / previous_rate) * 100 if previous_rate else 0
            
            result = {
                'pair': f"{self.base_currency}/{target_currency}",
                'current_rate': float(current_rate),
                'previous_rate': float(previous_rate),
                'change': float(change),
                'change_percent': float(change_percent),
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance',
                'success': True
            }
            
            logger.info(f"✅ yfinance 성공: {current_rate:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ yfinance 실패: {str(e)}")
            return None
    
    def get_exchange_rate(self, target_currency: str = 'KRW') -> Dict:
        """
        환율 정보 수집 (하이브리드 방식)
        1차: ExchangeRate-API
        2차: yfinance (fallback)
        """
        logger.info(f"=== 환율 수집 시작: {self.base_currency}/{target_currency} ===")
        
        # 1차 시도: ExchangeRate-API
        result = self._get_from_exchangerate_api(target_currency)
        
        if result and result['success']:
            # 1개월 전 데이터 추가 (ExchangeRate-API는 historical 무료 제공 안함)
            # yfinance로 보완
            hist_data = self._get_historical_comparison(target_currency)
            if hist_data:
                result.update(hist_data)
            
            return result
        
        # 2차 시도: yfinance (fallback)
        logger.warning("⚠️ ExchangeRate-API 실패, yfinance로 fallback")
        result = self._get_from_yfinance(target_currency)
        
        if result and result['success']:
            return result
        
        # 모든 방법 실패
        logger.error("❌ 모든 환율 수집 방법 실패")
        return {
            'pair': f"{self.base_currency}/{target_currency}",
            'success': False,
            'error': 'All data sources failed',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_historical_comparison(self, target_currency: str) -> Optional[Dict]:
        """1개월 전 데이터와 비교 (yfinance 활용)"""
        try:
            symbol = f"{self.base_currency}{target_currency}=X"
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                return None
            
            previous_rate = hist['Close'].iloc[0]
            current_rate = hist['Close'].iloc[-1]
            change = current_rate - previous_rate
            change_percent = (change / previous_rate) * 100
            
            return {
                'previous_rate': float(previous_rate),
                'change': float(change),
                'change_percent': float(change_percent),
                '1m_high': float(hist['High'].max()),
                '1m_low': float(hist['Low'].min()),
                '1m_avg': float(hist['Close'].mean())
            }
            
        except Exception as e:
            logger.warning(f"과거 데이터 수집 실패: {str(e)}")
            return None
    
    def collect_all(self) -> Dict:
        """모든 타겟 통화에 대한 환율 수집"""
        results = {}
        
        for currency in self.target_currencies:
            results[currency] = self.get_exchange_rate(currency)
        
        return {
            'exchange_rates': results,
            'collection_time': datetime.now().isoformat()
        }


# 테스트 코드
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 설정 로드
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    collector = ExchangeRateCollector(settings)
    result = collector.collect_all()
    
    print("\n=== 환율 수집 결과 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
