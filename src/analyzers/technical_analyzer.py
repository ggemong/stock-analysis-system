"""
기술적 지표 계산 모듈
RSI, MA, Bollinger Bands, MACD 등
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """기술적 지표 계산 클래스"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.rsi_period = settings['technical_indicators']['rsi_period']
        self.ma_periods = settings['technical_indicators']['ma_periods']
        self.bb_period = settings['technical_indicators']['bollinger_period']
        self.bb_std = settings['technical_indicators']['bollinger_std']
        self.macd_fast = settings['technical_indicators']['macd_fast']
        self.macd_slow = settings['technical_indicators']['macd_slow']
        self.macd_signal = settings['technical_indicators']['macd_signal']
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI (Relative Strength Index) 계산"""
        try:
            if len(prices) < period + 1:
                return None
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # ZeroDivision 방지
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            
            # NaN 체크
            final_rsi = rsi.iloc[-1]
            if pd.isna(final_rsi) or np.isinf(final_rsi):
                return None
            
            return float(final_rsi)
        except Exception as e:
            logger.error(f"RSI 계산 오류: {str(e)}")
            return None
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict:
        """이동평균선 계산"""
        try:
            mas = {}
            for period in self.ma_periods:
                ma = prices.rolling(window=period).mean()
                mas[f'MA{period}'] = float(ma.iloc[-1]) if not ma.empty else None
            
            return mas
        except Exception as e:
            logger.error(f"MA 계산 오류: {str(e)}")
            return {}
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Dict:
        """볼린저 밴드 계산"""
        try:
            ma = prices.rolling(window=self.bb_period).mean()
            std = prices.rolling(window=self.bb_period).std()
            
            upper = ma + (std * self.bb_std)
            lower = ma - (std * self.bb_std)
            
            current_price = prices.iloc[-1]
            bb_position = (current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]) * 100
            
            return {
                'upper': float(upper.iloc[-1]),
                'middle': float(ma.iloc[-1]),
                'lower': float(lower.iloc[-1]),
                'position': float(bb_position),  # 0-100%
                'width': float((upper.iloc[-1] - lower.iloc[-1]) / ma.iloc[-1] * 100)
            }
        except Exception as e:
            logger.error(f"Bollinger Bands 계산 오류: {str(e)}")
            return {}
    
    def calculate_macd(self, prices: pd.Series) -> Dict:
        """MACD 계산"""
        try:
            ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
            ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
            
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line.iloc[-1]),
                'signal': float(signal_line.iloc[-1]),
                'histogram': float(histogram.iloc[-1]),
                'trend': 'bullish' if histogram.iloc[-1] > 0 else 'bearish'
            }
        except Exception as e:
            logger.error(f"MACD 계산 오류: {str(e)}")
            return {}
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """변동성 (표준편차) 계산"""
        try:
            returns = prices.pct_change()
            volatility = returns.rolling(window=period).std() * np.sqrt(252) * 100  # 연율화
            return float(volatility.iloc[-1])
        except Exception as e:
            logger.error(f"변동성 계산 오류: {str(e)}")
            return None
    
    def calculate_support_resistance(self, prices: pd.Series, window: int = 20) -> Dict:
        """지지선/저항선 계산 (간단한 방식)"""
        try:
            recent_prices = prices.tail(window)
            
            resistance = float(recent_prices.max())
            support = float(recent_prices.min())
            
            return {
                'resistance': resistance,
                'support': support,
                'distance_to_resistance': (resistance - prices.iloc[-1]) / prices.iloc[-1] * 100,
                'distance_to_support': (prices.iloc[-1] - support) / prices.iloc[-1] * 100
            }
        except Exception as e:
            logger.error(f"지지/저항 계산 오류: {str(e)}")
            return {}
    
    def calculate_disparity(self, prices: pd.Series, period: int = 20) -> Dict:
        """이격도 계산 (현재가 / 이동평균 * 100)"""
        try:
            ma = prices.rolling(window=period).mean()
            current_price = prices.iloc[-1]
            ma_value = ma.iloc[-1]
            
            if pd.isna(ma_value) or ma_value == 0:
                return {}
            
            disparity = (current_price / ma_value) * 100
            
            # 이격도 해석
            if disparity > 105:
                status = "과열"
            elif disparity > 102:
                status = "강세"
            elif disparity < 95:
                status = "침체"
            elif disparity < 98:
                status = "약세"
            else:
                status = "중립"
            
            return {
                'disparity_20': float(disparity),
                'status': status,
                'ma_20': float(ma_value)
            }
        except Exception as e:
            logger.error(f"이격도 계산 오류: {str(e)}")
            return {}
    
    def detect_ma_alignment(self, prices: pd.Series) -> Dict:
        """이동평균 정배열/역배열 및 골든/데드크로스 감지"""
        try:
            ma20 = prices.rolling(window=20).mean()
            ma50 = prices.rolling(window=50).mean()
            ma200 = prices.rolling(window=200).mean()
            
            current_price = prices.iloc[-1]
            ma20_current = ma20.iloc[-1]
            ma50_current = ma50.iloc[-1]
            ma200_current = ma200.iloc[-1] if len(prices) >= 200 else None
            
            # 정배열/역배열 판단
            if ma200_current:
                if current_price > ma20_current > ma50_current > ma200_current:
                    alignment = "정배열"
                elif current_price < ma20_current < ma50_current < ma200_current:
                    alignment = "역배열"
                else:
                    alignment = "혼조"
            else:
                if current_price > ma20_current > ma50_current:
                    alignment = "정배열"
                elif current_price < ma20_current < ma50_current:
                    alignment = "역배열"
                else:
                    alignment = "혼조"
            
            # 골든크로스/데드크로스 감지 (최근 5일 내)
            cross_signal = None
            if len(ma20) >= 5 and len(ma50) >= 5:
                # 최근 5일간 크로스 발생 여부 확인
                for i in range(-5, 0):
                    if i == -len(ma20):
                        break
                    
                    prev_ma20 = ma20.iloc[i-1]
                    prev_ma50 = ma50.iloc[i-1]
                    curr_ma20 = ma20.iloc[i]
                    curr_ma50 = ma50.iloc[i]
                    
                    # 골든크로스: MA20이 MA50을 상향 돌파
                    if prev_ma20 < prev_ma50 and curr_ma20 > curr_ma50:
                        days_ago = abs(i)
                        cross_signal = f"골든크로스 ({days_ago}일 전)"
                        break
                    # 데드크로스: MA20이 MA50을 하향 돌파
                    elif prev_ma20 > prev_ma50 and curr_ma20 < curr_ma50:
                        days_ago = abs(i)
                        cross_signal = f"데드크로스 ({days_ago}일 전)"
                        break
            
            if not cross_signal:
                # 현재 위치 기반 예상
                if ma20_current > ma50_current:
                    gap = ((ma20_current - ma50_current) / ma50_current) * 100
                    if gap < 1:
                        cross_signal = "골든크로스 임박"
                    else:
                        cross_signal = "상승 유지"
                else:
                    gap = ((ma50_current - ma20_current) / ma50_current) * 100
                    if gap < 1:
                        cross_signal = "데드크로스 임박"
                    else:
                        cross_signal = "하락 유지"
            
            return {
                'alignment': alignment,
                'cross_signal': cross_signal,
                'ma20': float(ma20_current),
                'ma50': float(ma50_current),
                'ma200': float(ma200_current) if ma200_current else None
            }
            
        except Exception as e:
            logger.error(f"이동평균 배열 감지 오류: {str(e)}")
            return {}
    
    def analyze_stock(self, stock_data: Dict) -> Dict:
        """주식 데이터에 대한 전체 기술적 분석"""
        try:
            if not stock_data.get('success') or not stock_data.get('historical_data'):
                logger.warning(f"분석 불가: {stock_data.get('symbol', 'Unknown')}")
                return {
                    'symbol': stock_data.get('symbol'),
                    'success': False,
                    'error': 'No historical data'
                }
            
            # 데이터프레임 생성
            hist_data = stock_data['historical_data']
            
            # yfinance 형식
            if isinstance(hist_data, list) and hist_data and 'Close' in hist_data[0]:
                df = pd.DataFrame(hist_data)
            # Alpha Vantage/FMP 형식
            elif isinstance(hist_data, list) and hist_data and 'close' in hist_data[0]:
                df = pd.DataFrame(hist_data)
                df.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
            else:
                logger.error(f"알 수 없는 데이터 형식: {stock_data.get('symbol')}")
                return {'success': False, 'error': 'Unknown data format'}
            
            if df.empty or 'Close' not in df.columns:
                return {'success': False, 'error': 'Invalid data format'}
            
            prices = pd.Series(df['Close'].values)
            
            # 기술적 지표 계산
            analysis = {
                'symbol': stock_data['symbol'],
                'current_price': stock_data.get('current_price'),
                'rsi': self.calculate_rsi(prices, self.rsi_period),
                'moving_averages': self.calculate_moving_averages(prices),
                'bollinger_bands': self.calculate_bollinger_bands(prices),
                'macd': self.calculate_macd(prices),
                'volatility': self.calculate_volatility(prices),
                'support_resistance': self.calculate_support_resistance(prices),
                'disparity': self.calculate_disparity(prices, 20),
                'ma_alignment': self.detect_ma_alignment(prices),
                'success': True
            }
            
            # 신호 생성
            analysis['signals'] = self._generate_signals(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"기술적 분석 오류 ({stock_data.get('symbol')}): {str(e)}")
            return {
                'symbol': stock_data.get('symbol'),
                'success': False,
                'error': str(e)
            }
    
    def _generate_signals(self, analysis: Dict) -> Dict:
        """기술적 지표 기반 매매 신호 생성"""
        signals = {
            'overall': 'NEUTRAL',
            'strength': 0,  # -100 to 100
            'details': []
        }
        
        strength = 0
        
        # RSI 신호
        rsi = analysis.get('rsi')
        if rsi:
            if rsi < 30:
                signals['details'].append('RSI 과매도 (매수 신호)')
                strength += 20
            elif rsi > 70:
                signals['details'].append('RSI 과매수 (매도 신호)')
                strength -= 20
            elif rsi < 40:
                signals['details'].append('RSI 저평가 구간')
                strength += 10
            elif rsi > 60:
                signals['details'].append('RSI 고평가 구간')
                strength -= 10
        
        # 이동평균 신호
        mas = analysis.get('moving_averages', {})
        current_price = analysis.get('current_price')
        
        if current_price and mas:
            ma20 = mas.get('MA20')
            ma50 = mas.get('MA50')
            ma200 = mas.get('MA200')
            
            # 골든크로스/데드크로스
            if ma20 and ma50:
                if ma20 > ma50:
                    signals['details'].append('단기 상승 추세 (MA20 > MA50)')
                    strength += 15
                else:
                    signals['details'].append('단기 하락 추세 (MA20 < MA50)')
                    strength -= 15
            
            # 200일 이평선 위치
            if ma200:
                if current_price > ma200:
                    signals['details'].append('장기 상승 추세 (가격 > MA200)')
                    strength += 10
                else:
                    signals['details'].append('장기 하락 추세 (가격 < MA200)')
                    strength -= 10
        
        # 볼린저 밴드 신호
        bb = analysis.get('bollinger_bands', {})
        if bb:
            position = bb.get('position', 50)
            if position < 20:
                signals['details'].append('볼린저 밴드 하단 근접 (반등 가능성)')
                strength += 15
            elif position > 80:
                signals['details'].append('볼린저 밴드 상단 근접 (조정 가능성)')
                strength -= 15
        
        # MACD 신호
        macd = analysis.get('macd', {})
        if macd:
            if macd.get('trend') == 'bullish':
                signals['details'].append('MACD 상승 추세')
                strength += 10
            else:
                signals['details'].append('MACD 하락 추세')
                strength -= 10
        
        # 전체 신호 결정
        signals['strength'] = max(-100, min(100, strength))
        
        if strength > 30:
            signals['overall'] = 'STRONG_BUY'
        elif strength > 10:
            signals['overall'] = 'BUY'
        elif strength < -30:
            signals['overall'] = 'STRONG_SELL'
        elif strength < -10:
            signals['overall'] = 'SELL'
        else:
            signals['overall'] = 'NEUTRAL'
        
        return signals
    
    def analyze_multiple(self, stocks_data: Dict) -> Dict:
        """여러 주식에 대한 기술적 분석"""
        results = {}
        
        if 'stocks' not in stocks_data:
            return {'error': 'No stocks data provided'}
        
        for symbol, stock_data in stocks_data['stocks'].items():
            results[symbol] = self.analyze_stock(stock_data)
        
        return {
            'technical_analysis': results,
            'analysis_time': pd.Timestamp.now().isoformat()
        }


# 테스트 코드
if __name__ == "__main__":
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 샘플 데이터로 테스트
    sample_data = {
        'symbol': 'AAPL',
        'current_price': 150.0,
        'success': True,
        'historical_data': [
            {'Close': 145 + i, 'Open': 144 + i, 'High': 146 + i, 'Low': 144 + i, 'Volume': 1000000}
            for i in range(200)
        ]
    }
    
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    analyzer = TechnicalAnalyzer(settings)
    result = analyzer.analyze_stock(sample_data)
    
    print("\n=== 기술적 분석 결과 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
