"""
김치 프리미엄 수집 모듈
국내(업비트) vs 해외(바이낸스) 가격 비교
"""

import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class KimchiPremiumCollector:
    """김치 프리미엄 계산 클래스"""
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.timeout = settings['data_collection']['timeout']
        
        # API 엔드포인트
        self.upbit_url = "https://api.upbit.com/v1/ticker"
        # 바이낸스 대신 CoinGecko 사용 (글로벌 접근 가능)
        self.coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
        
        # 주요 암호화폐 목록
        self.crypto_pairs = {
            'BTC': {'upbit': 'KRW-BTC', 'coingecko_id': 'bitcoin'},
            'ETH': {'upbit': 'KRW-ETH', 'coingecko_id': 'ethereum'},
            'XRP': {'upbit': 'KRW-XRP', 'coingecko_id': 'ripple'},
            'SOL': {'upbit': 'KRW-SOL', 'coingecko_id': 'solana'},
            'ADA': {'upbit': 'KRW-ADA', 'coingecko_id': 'cardano'}
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_upbit_price(self, market: str) -> Optional[float]:
        """업비트 가격 조회"""
        try:
            params = {'markets': market}
            response = requests.get(
                self.upbit_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                price = data[0].get('trade_price')
                return float(price) if price else None
            
            return None
            
        except Exception as e:
            logger.error(f"업비트 가격 조회 실패 ({market}): {str(e)}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_global_price(self, coingecko_id: str) -> Optional[float]:
        """CoinGecko에서 글로벌 가격 조회 (USD)"""
        try:
            params = {
                'ids': coingecko_id,
                'vs_currencies': 'usd'
            }
            response = requests.get(
                self.coingecko_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if coingecko_id in data and 'usd' in data[coingecko_id]:
                price = data[coingecko_id]['usd']
                return float(price) if price else None
            
            return None
            
        except Exception as e:
            logger.error(f"CoinGecko 가격 조회 실패 ({coingecko_id}): {str(e)}")
            return None
    
    def calculate_kimchi_premium(
        self,
        upbit_price_krw: float,
        global_price_usd: float,  # 파라미터명 변경 (binance → global)
        exchange_rate: float
    ) -> Dict:
        """김치 프리미엄 계산"""
        try:
            # 글로벌 가격을 원화로 환산
            global_price_krw = global_price_usd * exchange_rate
            
            # 김치 프리미엄 계산 (%)
            premium = ((upbit_price_krw - global_price_krw) / global_price_krw) * 100
            
            # 상태 판단
            if premium > 5:
                status = "높은 프리미엄"
                signal = "국내 매도 우위"
            elif premium > 2:
                status = "프리미엄"
                signal = "국내 약간 비쌈"
            elif premium > -2:
                status = "균형"
                signal = "정상 범위"
            elif premium > -5:
                status = "디스카운트"
                signal = "국내 약간 저렴"
            else:
                status = "높은 디스카운트"
                signal = "국내 매수 우위"
            
            return {
                'upbit_price_krw': round(upbit_price_krw, 2),
                # 하위 호환성을 위해 binance 필드도 유지
                'binance_price_usd': round(global_price_usd, 2),
                'binance_price_krw': round(global_price_krw, 2),
                'global_price_usd': round(global_price_usd, 2),
                'global_price_krw': round(global_price_krw, 2),
                'premium_percent': round(premium, 2),
                'status': status,
                'signal': signal,
                'exchange_rate_used': exchange_rate
            }
            
        except Exception as e:
            logger.error(f"김치 프리미엄 계산 오류: {str(e)}")
            return {}
    
    def collect_kimchi_premium(self, exchange_rate: float) -> Dict:
        """전체 암호화폐의 김치 프리미엄 수집"""
        logger.info(f"김치 프리미엄 수집 시작... (환율: {exchange_rate:.2f})")
        
        results = {}
        
        for crypto, pairs in self.crypto_pairs.items():
            try:
                logger.info(f"  🔍 {crypto} 처리 중...")
                
                # 업비트 가격 (KRW)
                logger.debug(f"    업비트 API 호출: {pairs['upbit']}")
                upbit_price = self._get_upbit_price(pairs['upbit'])
                logger.debug(f"    업비트 가격: {upbit_price}")
                
                # 글로벌 가격 (USD) - CoinGecko
                logger.debug(f"    CoinGecko API 호출: {pairs['coingecko_id']}")
                global_price = self._get_global_price(pairs['coingecko_id'])
                logger.debug(f"    CoinGecko 가격: {global_price}")
                
                if upbit_price and global_price and exchange_rate:
                    # 김치 프리미엄 계산
                    premium_data = self.calculate_kimchi_premium(
                        upbit_price,
                        global_price,
                        exchange_rate
                    )
                    
                    results[crypto] = {
                        **premium_data,
                        'upbit_market': pairs['upbit'],
                        'global_source': 'CoinGecko',
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(
                        f"  ✅ {crypto}: {premium_data.get('premium_percent', 0):+.2f}% "
                        f"({premium_data.get('status', 'N/A')})"
                    )
                else:
                    # 상세 실패 원인
                    reasons = []
                    if not upbit_price:
                        reasons.append("업비트 가격 없음")
                    if not global_price:
                        reasons.append("글로벌 가격 없음")
                    if not exchange_rate:
                        reasons.append("환율 없음")
                    
                    error_msg = ', '.join(reasons)
                    
                    results[crypto] = {
                        'success': False,
                        'error': error_msg,
                        'upbit_market': pairs['upbit'],
                        'global_source': 'CoinGecko',
                        'upbit_price': upbit_price,
                        'global_price': global_price
                    }
                    logger.warning(f"  ⚠️ {crypto} 실패: {error_msg}")
                    
            except Exception as e:
                logger.error(f"  ❌ {crypto} 처리 중 오류: {str(e)}", exc_info=True)
                results[crypto] = {
                    'success': False,
                    'error': str(e),
                    'upbit_market': pairs.get('upbit'),
                    'global_source': 'CoinGecko'
                }
        
        logger.info(f"김치 프리미엄 수집 완료 - 성공: {sum(1 for v in results.values() if v.get('success'))}/{len(results)}")
        
        return {
            'kimchi_premium': results,
            'collection_time': datetime.now().isoformat(),
            'exchange_rate': exchange_rate
        }
    
    def get_trading_signal(self, premium_percent: float) -> Dict:
        """김치 프리미엄 기반 매매 신호"""
        
        if premium_percent > 5:
            return {
                'action': '국내 매도 고려',
                'reason': f'김치 프리미엄 {premium_percent:.1f}% - 국내가 해외보다 {premium_percent:.1f}% 비쌈',
                'strategy': '업비트에서 매도 후 바이낸스에서 매수하는 차익거래 가능',
                'risk': '환전 및 송금 수수료, 시간 고려 필요'
            }
        elif premium_percent > 2:
            return {
                'action': '국내 매수 자제',
                'reason': f'김치 프리미엄 {premium_percent:.1f}% - 국내가 약간 비쌈',
                'strategy': '급하지 않다면 프리미엄 하락 대기',
                'risk': '프리미엄이 더 상승할 수 있음'
            }
        elif premium_percent > -2:
            return {
                'action': '정상 거래',
                'reason': f'김치 프리미엄 {premium_percent:.1f}% - 정상 범위',
                'strategy': '기술적 분석 및 추세에 따라 매매',
                'risk': '일반적인 암호화폐 변동성'
            }
        elif premium_percent > -5:
            return {
                'action': '국내 매수 기회',
                'reason': f'김치 디스카운트 {abs(premium_percent):.1f}% - 국내가 약간 저렴',
                'strategy': '업비트에서 매수 유리',
                'risk': '디스카운트가 더 심해질 수 있음'
            }
        else:
            return {
                'action': '국내 적극 매수',
                'reason': f'김치 디스카운트 {abs(premium_percent):.1f}% - 국내가 해외보다 {abs(premium_percent):.1f}% 저렴',
                'strategy': '업비트 매수 후 바이낸스로 전송 시 차익 가능',
                'risk': '출금 수수료 및 시간, 네트워크 상황 고려'
            }


# 테스트 코드
if __name__ == "__main__":
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 설정 로드
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    # 테스트용 환율 (실제로는 exchange_collector에서 가져옴)
    test_exchange_rate = 1432.5
    
    collector = KimchiPremiumCollector(settings)
    
    print(f"\n{'='*60}")
    print(f"김치 프리미엄 수집 테스트")
    print(f"환율: {test_exchange_rate:.2f}원")
    print(f"{'='*60}\n")
    
    # 김치 프리미엄 수집
    result = collector.collect_kimchi_premium(test_exchange_rate)
    
    print("\n=== 수집 결과 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 매매 신호 예시
    print("\n=== 매매 신호 예시 ===")
    for crypto, data in result['kimchi_premium'].items():
        if data.get('success'):
            premium = data['premium_percent']
            signal = collector.get_trading_signal(premium)
            print(f"\n{crypto}:")
            print(f"  프리미엄: {premium:.2f}%")
            print(f"  액션: {signal['action']}")
            print(f"  이유: {signal['reason']}")
