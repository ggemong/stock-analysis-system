"""
주식 데이터 수집 모듈
Primary: yfinance -> Fallback1: Alpha Vantage -> Fallback2: FMP
"""

import yfinance as yf
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd
import time

logger = logging.getLogger(__name__)


class StockDataCollector:
    """주식 데이터 수집 클래스 (3단계 Fallback)"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.retry_attempts = settings['data_collection']['retry_attempts']
        self.timeout = settings['data_collection']['timeout']
        self.user_agent = settings['data_collection']['user_agent']
        
        # API Keys (환경변수에서 로드)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.fmp_key = os.getenv('FMP_API_KEY')
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_from_yfinance(self, symbol: str) -> Optional[Dict]:
        """yfinance에서 주식 데이터 가져오기 (Primary)"""
        try:
            logger.info(f"yfinance에서 {symbol} 데이터 수집 시도")
            
            # User-Agent 설정
            yf.set_tz_cache_location("/tmp/yfinance_cache")
            
            ticker = yf.Ticker(symbol)
            
            # 기본 정보
            info = ticker.info
            
            # 과거 데이터 (1년 - MA200 계산을 위해 필요)
            hist = ticker.history(period="1y")
            
            if hist.empty:
                logger.warning(f"❌ yfinance: {symbol} 과거 데이터 없음")
                return None
            
            # 현재 가격
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
            
            # 기본 데이터 구성
            result = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'current_price': float(current_price),
                'previous_close': float(info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)),
                'open': float(info.get('regularMarketOpen', hist['Open'].iloc[-1])),
                'day_high': float(info.get('dayHigh', hist['High'].iloc[-1])),
                'day_low': float(info.get('dayLow', hist['Low'].iloc[-1])),
                'volume': int(info.get('volume', hist['Volume'].iloc[-1])),
                'avg_volume': int(info.get('averageVolume', hist['Volume'].mean())),
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'eps': info.get('trailingEps'),
                'dividend_yield': info.get('dividendYield'),
                '52w_high': info.get('fiftyTwoWeekHigh'),
                '52w_low': info.get('fiftyTwoWeekLow'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'historical_data': hist.tail(200).to_dict('records'),  # 최근 200일
                'source': 'yfinance',
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ yfinance 성공: {symbol} @ ${current_price:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ yfinance 실패 ({symbol}): {str(e)}")
            return None
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=3, max=15)
    )
    def _get_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Alpha Vantage에서 주식 데이터 가져오기 (Fallback 1)"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API Key 없음")
            return None
        
        try:
            logger.info(f"Alpha Vantage에서 {symbol} 데이터 수집 시도")
            
            # Quote Endpoint
            quote_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            
            response = requests.get(quote_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                logger.warning(f"❌ Alpha Vantage: {symbol} 데이터 없음")
                return None
            
            quote = data['Global Quote']
            
            # Time Series Daily (full = 20년치, MA200 계산에 필요)
            time.sleep(12)  # API 제한 (5 calls/min)
            ts_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={self.alpha_vantage_key}"
            
            ts_response = requests.get(ts_url, timeout=self.timeout)
            ts_data = ts_response.json()
            
            historical = []
            if 'Time Series (Daily)' in ts_data:
                for date, values in list(ts_data['Time Series (Daily)'].items())[:200]:
                    historical.append({
                        'Date': date,
                        'Open': float(values['1. open']),
                        'High': float(values['2. high']),
                        'Low': float(values['3. low']),
                        'Close': float(values['4. close']),
                        'Volume': int(values['5. volume'])
                    })
            
            result = {
                'symbol': symbol,
                'current_price': float(quote.get('05. price', 0)),
                'previous_close': float(quote.get('08. previous close', 0)),
                'open': float(quote.get('02. open', 0)),
                'day_high': float(quote.get('03. high', 0)),
                'day_low': float(quote.get('04. low', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').rstrip('%'),
                'historical_data': historical,
                'source': 'Alpha Vantage',
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Alpha Vantage 성공: {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Alpha Vantage 실패 ({symbol}): {str(e)}")
            return None
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=3, max=15)
    )
    def _get_from_fmp(self, symbol: str) -> Optional[Dict]:
        """Financial Modeling Prep에서 주식 데이터 가져오기 (Fallback 2)"""
        if not self.fmp_key:
            logger.warning("FMP API Key 없음")
            return None
        
        try:
            logger.info(f"FMP에서 {symbol} 데이터 수집 시도")
            
            # Quote
            quote_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={self.fmp_key}"
            
            response = requests.get(quote_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"❌ FMP: {symbol} 데이터 없음")
                return None
            
            quote = data[0]
            
            # Historical Data
            hist_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={self.fmp_key}"
            hist_response = requests.get(hist_url, timeout=self.timeout)
            hist_data = hist_response.json()
            
            historical = []
            if 'historical' in hist_data:
                historical = hist_data['historical'][:200]
            
            result = {
                'symbol': symbol,
                'name': quote.get('name', symbol),
                'current_price': float(quote.get('price', 0)),
                'previous_close': float(quote.get('previousClose', 0)),
                'open': float(quote.get('open', 0)),
                'day_high': float(quote.get('dayHigh', 0)),
                'day_low': float(quote.get('dayLow', 0)),
                'volume': int(quote.get('volume', 0)),
                'avg_volume': int(quote.get('avgVolume', 0)),
                'market_cap': quote.get('marketCap'),
                'pe_ratio': quote.get('pe'),
                'eps': quote.get('eps'),
                'change': float(quote.get('change', 0)),
                'change_percent': float(quote.get('changesPercentage', 0)),
                '52w_high': quote.get('yearHigh'),
                '52w_low': quote.get('yearLow'),
                'historical_data': historical,
                'source': 'FMP',
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ FMP 성공: {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"❌ FMP 실패 ({symbol}): {str(e)}")
            return None
    
    def get_stock_data(self, symbol: str) -> Dict:
        """
        주식 데이터 수집 (3단계 Fallback)
        1차: yfinance
        2차: Alpha Vantage
        3차: FMP
        """
        logger.info(f"=== 주식 데이터 수집 시작: {symbol} ===")
        
        # 1차 시도: yfinance
        result = self._get_from_yfinance(symbol)
        if result and result['success']:
            return result
        
        # 2차 시도: Alpha Vantage
        logger.warning(f"⚠️ yfinance 실패, Alpha Vantage로 fallback ({symbol})")
        result = self._get_from_alpha_vantage(symbol)
        if result and result['success']:
            return result
        
        # 3차 시도: FMP
        logger.warning(f"⚠️ Alpha Vantage 실패, FMP로 fallback ({symbol})")
        result = self._get_from_fmp(symbol)
        if result and result['success']:
            return result
        
        # 모든 방법 실패
        logger.error(f"❌ 모든 데이터 소스 실패: {symbol}")
        return {
            'symbol': symbol,
            'success': False,
            'error': 'All data sources failed',
            'timestamp': datetime.now().isoformat()
        }
    
    def collect_multiple(self, symbols: List[str]) -> Dict:
        """여러 주식의 데이터 수집"""
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_stock_data(symbol)
                time.sleep(1)  # Rate limiting 방지
            except Exception as e:
                logger.error(f"수집 중 오류 ({symbol}): {str(e)}")
                results[symbol] = {
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                }
        
        return {
            'stocks': results,
            'collection_time': datetime.now().isoformat(),
            'total_stocks': len(symbols),
            'successful': sum(1 for r in results.values() if r.get('success', False)),
            'failed': sum(1 for r in results.values() if not r.get('success', False))
        }


# 테스트 코드
if __name__ == "__main__":
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    collector = StockDataCollector(settings)
    result = collector.get_stock_data('AAPL')
    
    print("\n=== 주식 데이터 수집 결과 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
