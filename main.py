"""
주식 분석 시스템 메인 실행 파일
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.collectors.stock_collector import StockDataCollector
from src.collectors.exchange_collector import ExchangeRateCollector
from src.collectors.macro_collector import MacroEconomicCollector
from src.analyzers.technical_analyzer import TechnicalAnalyzer
from src.formatters.gemini_formatter import GeminiFormatter
from src.notifiers.telegram_notifier import TelegramNotifier

# Optional: Kimchi Premium Collector (v1.6.4+)
try:
    from src.collectors.kimchi_premium_collector import KimchiPremiumCollector
    KIMCHI_PREMIUM_AVAILABLE = True
except ImportError:
    KimchiPremiumCollector = None
    KIMCHI_PREMIUM_AVAILABLE = False

# 로깅 설정
log_file_path = project_root / 'stock_analysis.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file_path), encoding='utf-8')
    ]
)

# 로그 파일 위치 출력
print(f"📋 로그 파일 위치: {log_file_path}")

logger = logging.getLogger(__name__)


class StockAnalysisSystem:
    """주식 분석 시스템 메인 클래스"""
    
    def __init__(self):
        # 설정 파일 로드
        self.config_dir = project_root / 'config'
        self.settings = self._load_json(self.config_dir / 'settings.json')
        self.stocks_config = self._load_json(self.config_dir / 'stocks.json')
        
        # 컬렉터 초기화
        self.stock_collector = StockDataCollector(self.settings)
        self.exchange_collector = ExchangeRateCollector(self.settings)
        self.macro_collector = MacroEconomicCollector(self.settings)
        
        # 김치 프리미엄 수집기 (선택적)
        if KIMCHI_PREMIUM_AVAILABLE:
            self.kimchi_collector = KimchiPremiumCollector(self.settings)
            logger.info("김치 프리미엄 수집기 활성화")
        else:
            self.kimchi_collector = None
            logger.warning("김치 프리미엄 수집기 비활성화 (모듈 없음)")
        
        # 분석기 초기화
        self.technical_analyzer = TechnicalAnalyzer(self.settings)
        
        # 포맷터 초기화
        self.gemini_formatter = GeminiFormatter()
        
        # 텔레그램 초기화
        try:
            self.telegram_notifier = TelegramNotifier(self.settings)
        except ValueError as e:
            logger.error(f"텔레그램 초기화 실패: {str(e)}")
            self.telegram_notifier = None
    
    def _load_json(self, filepath: Path) -> dict:
        """JSON 파일 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"JSON 로드 실패 ({filepath}): {str(e)}")
            return {}
    
    def run_analysis(self) -> dict:
        """전체 분석 프로세스 실행"""
        logger.info("=" * 80)
        logger.info("주식 분석 시스템 시작")
        logger.info("=" * 80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'errors': []
        }
        
        try:
            # 1단계: 주식 리스트 추출
            symbols = [stock['symbol'] for stock in self.stocks_config.get('stocks', [])]
            logger.info(f"분석 대상 주식: {', '.join(symbols)}")
            
            if not symbols:
                raise ValueError("분석할 주식이 없습니다. config/stocks.json을 확인하세요.")
            
            # 2단계: 데이터 수집
            logger.info("\n[1/5] 데이터 수집 시작...")
            
            # 2-1. 주식 데이터 수집
            logger.info("주식 데이터 수집 중...")
            stocks_data = self.stock_collector.collect_multiple(symbols)
            logger.info(f"주식 데이터 수집 완료: {stocks_data.get('successful', 0)}/{stocks_data.get('total_stocks', 0)}")
            
            # 2-2. 환율 데이터 수집
            logger.info("환율 데이터 수집 중...")
            exchange_data = self.exchange_collector.collect_all()
            logger.info("환율 데이터 수집 완료")
            
            # 2-3. 거시경제 데이터 수집
            logger.info("거시경제 데이터 수집 중...")
            macro_data = self.macro_collector.collect_all()
            logger.info(f"거시경제 데이터 수집 완료: {macro_data.get('successful', 0)}개 지표")
            
            # 2-4. 김치 프리미엄 수집 (선택적)
            kimchi_data = {'kimchi_premium': {}, 'collection_time': datetime.now().isoformat()}
            
            if self.kimchi_collector:
                logger.info("김치 프리미엄 수집 시작...")
                
                # 환율 가져오기 (여러 소스 시도)
                krw_rate = 0
                
                # 1차: exchange_data에서 가져오기
                if exchange_data.get('exchange_rates', {}).get('KRW', {}).get('success'):
                    krw_rate = exchange_data['exchange_rates']['KRW']['current_rate']
                    logger.info(f"환율 획득 (exchange_data): {krw_rate:.2f}")
                
                # 2차: 환율 수집 실패 시 기본값 사용 (최근 평균 환율)
                if krw_rate <= 0:
                    logger.warning("⚠️ exchange_data에서 환율 없음 - 기본 환율 사용")
                    krw_rate = 1320.0  # 최근 평균 환율 (주기적으로 업데이트 필요)
                    logger.info(f"기본 환율 사용: {krw_rate:.2f}")
                
                try:
                    kimchi_data = self.kimchi_collector.collect_kimchi_premium(krw_rate)
                    successful_kimchi = sum(1 for k, v in kimchi_data.get('kimchi_premium', {}).items() if v.get('success'))
                    total_kimchi = len(kimchi_data.get('kimchi_premium', {}))
                    logger.info(f"김치 프리미엄 수집 완료: {successful_kimchi}/{total_kimchi}개 코인")
                    
                    # 실패 상세 로그
                    if successful_kimchi < total_kimchi:
                        for crypto, data in kimchi_data.get('kimchi_premium', {}).items():
                            if not data.get('success'):
                                logger.warning(f"  ❌ {crypto}: {data.get('error', 'Unknown error')}")
                                
                except Exception as e:
                    logger.error(f"❌ 김치 프리미엄 수집 중 오류: {str(e)}", exc_info=True)
            else:
                logger.info("김치 프리미엄 수집 건너뜀 (모듈 비활성화)")
            
            # 3단계: 기술적 분석
            logger.info("\n[2/5] 기술적 분석 시작...")
            technical_analysis = self.technical_analyzer.analyze_multiple(stocks_data)
            logger.info("기술적 분석 완료")
            
            # 4단계: Gemini 포맷 변환
            logger.info("\n[3/5] Gemini 포맷 변환 시작...")
            gemini_data = self.gemini_formatter.format_for_gemini(
                stocks_data,
                technical_analysis,
                exchange_data,
                macro_data,
                kimchi_data
            )
            logger.info("Gemini 포맷 변환 완료")
            
            # 5단계: 텔레그램 전송
            logger.info("\n[4/5] 텔레그램 전송 시작...")
            
            if self.telegram_notifier:
                # 요약 메시지 생성
                summary_message = self.gemini_formatter.to_telegram_message(gemini_data)
                gemini_prompt = gemini_data.get('gemini_prompt', '')
                
                # 전송
                send_success = self.telegram_notifier.send_analysis_report(
                    summary_message=summary_message,
                    gemini_data=gemini_data,
                    gemini_prompt=gemini_prompt
                )
                
                if send_success:
                    logger.info("✅ 텔레그램 전송 성공")
                else:
                    logger.warning("⚠️ 텔레그램 전송 실패")
                    results['errors'].append("Telegram send failed")
            else:
                logger.warning("⚠️ 텔레그램 미설정 - 전송 건너뜀")
                results['errors'].append("Telegram not configured")
            
            # 6단계: 결과 저장 (선택사항)
            logger.info("\n[5/5] 결과 저장 중...")
            output_file = f"analysis_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(gemini_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"결과 저장 완료: {output_file}")
            
            # 최종 결과
            results['success'] = True
            results['output_file'] = output_file
            results['stocks_analyzed'] = stocks_data.get('successful', 0)
            results['stocks_failed'] = stocks_data.get('failed', 0)
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ 주식 분석 시스템 완료")
            logger.info("=" * 80)
            
            return results
            
        except Exception as e:
            logger.error(f"\n❌ 시스템 오류: {str(e)}", exc_info=True)
            results['errors'].append(str(e))
            
            # 에러 알림 전송
            if self.telegram_notifier:
                error_msg = f"시스템 오류 발생:\n{str(e)}"
                self.telegram_notifier.send_error_notification(error_msg)
            
            return results
    
    def test_components(self):
        """각 컴포넌트 테스트"""
        logger.info("=" * 80)
        logger.info("컴포넌트 테스트 시작")
        logger.info("=" * 80)
        
        # 1. 텔레그램 테스트
        if self.telegram_notifier:
            logger.info("\n[1/4] 텔레그램 연결 테스트...")
            self.telegram_notifier.test_connection()
        
        # 2. 환율 테스트
        logger.info("\n[2/4] 환율 수집 테스트...")
        exchange_result = self.exchange_collector.get_exchange_rate('KRW')
        logger.info(f"결과: {json.dumps(exchange_result, indent=2, ensure_ascii=False)}")
        
        # 3. 주식 데이터 테스트
        logger.info("\n[3/4] 주식 데이터 수집 테스트 (AAPL)...")
        stock_result = self.stock_collector.get_stock_data('AAPL')
        logger.info(f"성공: {stock_result.get('success', False)}")
        
        # 4. 거시경제 테스트
        logger.info("\n[4/4] 거시경제 데이터 수집 테스트...")
        macro_result = self.macro_collector.collect_all()
        logger.info(f"수집 성공: {macro_result.get('successful', 0)}개")
        
        logger.info("\n" + "=" * 80)
        logger.info("컴포넌트 테스트 완료")
        logger.info("=" * 80)


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='주식 분석 시스템')
    parser.add_argument(
        '--test',
        action='store_true',
        help='컴포넌트 테스트 모드'
    )
    
    args = parser.parse_args()
    
    try:
        system = StockAnalysisSystem()
        
        if args.test:
            # 테스트 모드
            system.test_components()
        else:
            # 일반 실행
            results = system.run_analysis()
            
            # 결과 출력
            print("\n" + "=" * 80)
            print("실행 결과:")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            print("=" * 80)
            
            # 종료 코드 설정
            sys.exit(0 if results['success'] else 1)
            
    except Exception as e:
        logger.error(f"치명적 오류: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
