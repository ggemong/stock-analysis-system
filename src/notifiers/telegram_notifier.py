"""
텔레그램 메시지 및 파일 전송 모듈
"""

import os
import requests
import json
from typing import Dict, Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """텔레그램 알림 전송 클래스"""
    
    def __init__(self, settings: Dict):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.parse_mode = settings['telegram']['parse_mode']
        self.disable_preview = settings['telegram']['disable_web_page_preview']
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID 환경변수 필요")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, text: str) -> bool:
        """텍스트 메시지 전송 (4096자 초과 시 자동 분할)"""
        try:
            MAX_LENGTH = 4096
            
            # 메시지가 짧으면 바로 전송
            if len(text) <= MAX_LENGTH:
                return self._send_single_message(text)
            
            # 긴 메시지는 분할 전송
            logger.info(f"메시지가 길어서({len(text)}자) 분할 전송합니다...")
            
            # 섹션 단위로 분할 (빈 줄 2개 기준)
            sections = text.split('\n\n')
            
            messages = []
            current_msg = ""
            
            for section in sections:
                # 섹션 자체가 너무 크면 강제 분할
                if len(section) > MAX_LENGTH:
                    # 현재 메시지 저장
                    if current_msg:
                        messages.append(current_msg)
                        current_msg = ""
                    
                    # 큰 섹션을 줄 단위로 분할
                    lines = section.split('\n')
                    for line in lines:
                        if len(current_msg) + len(line) + 1 > MAX_LENGTH:
                            messages.append(current_msg)
                            current_msg = line + '\n'
                        else:
                            current_msg += line + '\n'
                    continue
                
                # 섹션 추가 시 길이 체크
                if len(current_msg) + len(section) + 2 > MAX_LENGTH:
                    # 현재 메시지 저장하고 새로 시작
                    messages.append(current_msg)
                    current_msg = section + '\n\n'
                else:
                    current_msg += section + '\n\n'
            
            # 마지막 메시지 추가
            if current_msg.strip():
                messages.append(current_msg)
            
            logger.info(f"총 {len(messages)}개 메시지로 분할")
            
            # 순차 전송
            success_count = 0
            for i, msg in enumerate(messages, 1):
                logger.info(f"메시지 {i}/{len(messages)} 전송 중 ({len(msg)}자)...")
                if self._send_single_message(msg):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ 메시지 {i} 전송 실패")
            
            # 전체 성공 여부
            if success_count == len(messages):
                logger.info(f"✅ 모든 메시지 전송 성공 ({success_count}/{len(messages)})")
                return True
            elif success_count > 0:
                logger.warning(f"⚠️ 일부 메시지 전송 성공 ({success_count}/{len(messages)})")
                return True
            else:
                logger.error("❌ 모든 메시지 전송 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 텔레그램 전송 오류: {str(e)}")
            return False
    
    def _send_single_message(self, text: str) -> bool:
        """단일 메시지 전송 (내부 메서드)"""
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': self.parse_mode,
                'disable_web_page_preview': self.disable_preview
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                return True
            else:
                logger.error(f"❌ 텔레그램 API 오류: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 텔레그램 전송 오류: {str(e)}")
            return False
    
    def send_document(self, file_content: str, filename: str, caption: str = None) -> bool:
        """파일 전송 (JSON 데이터 등)"""
        try:
            logger.info(f"텔레그램 파일 전송 중: {filename}")
            
            url = f"{self.base_url}/sendDocument"
            
            # 파일 객체 생성
            file_obj = BytesIO(file_content.encode('utf-8'))
            file_obj.name = filename
            
            files = {
                'document': (filename, file_obj, 'application/json')
            }
            
            data = {
                'chat_id': self.chat_id
            }
            
            if caption:
                data['caption'] = caption
                data['parse_mode'] = self.parse_mode
            
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                logger.info("✅ 텔레그램 파일 전송 성공")
                return True
            else:
                logger.error(f"❌ 텔레그램 파일 전송 실패: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 텔레그램 파일 전송 오류: {str(e)}")
            return False
    
    def send_analysis_report(
        self,
        summary_message: str,
        gemini_data: Dict,
        gemini_prompt: str
    ) -> bool:
        """분석 리포트 전송 (메시지 + JSON 파일 + Gemini 프롬프트)"""
        try:
            # 1. 요약 메시지 전송
            logger.info("1/3: 요약 메시지 전송")
            msg_success = self.send_message(summary_message)
            
            if not msg_success:
                logger.warning("⚠️ 요약 메시지 전송 실패, 계속 진행")
            
            # 2. 전체 JSON 데이터 전송
            logger.info("2/3: JSON 데이터 전송")
            json_content = json.dumps(gemini_data, indent=2, ensure_ascii=False)
            filename = f"stock_analysis_{gemini_data.get('analysis_date', '').replace(':', '-').replace(' ', '_')}.json"
            
            json_success = self.send_document(
                file_content=json_content,
                filename=filename,
                caption="📊 전체 분석 데이터 (Gemini에 업로드하세요)"
            )
            
            if not json_success:
                logger.warning("⚠️ JSON 파일 전송 실패, 계속 진행")
            
            # 3. Gemini 프롬프트 전송
            logger.info("3/3: Gemini 프롬프트 전송")
            
            # 프롬프트가 너무 길면 파일로 전송
            if len(gemini_prompt) > 4000:
                prompt_success = self.send_document(
                    file_content=gemini_prompt,
                    filename="gemini_prompt.txt",
                    caption="🤖 Gemini AI 분석 프롬프트"
                )
            else:
                prompt_message = f"<b>🤖 Gemini AI 분석 프롬프트</b>\n\n<pre>{gemini_prompt}</pre>"
                prompt_success = self.send_message(prompt_message)
            
            if not prompt_success:
                logger.warning("⚠️ Gemini 프롬프트 전송 실패")
            
            # 최소한 하나라도 성공하면 성공으로 간주
            overall_success = msg_success or json_success or prompt_success
            
            if overall_success:
                logger.info("✅ 분석 리포트 전송 완료 (일부 실패 가능)")
            else:
                logger.error("❌ 모든 전송 실패")
            
            return overall_success
            
        except Exception as e:
            logger.error(f"❌ 분석 리포트 전송 오류: {str(e)}")
            return False
    
    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 전송"""
        try:
            text = f"<b>⚠️ 주식 분석 시스템 오류</b>\n\n<pre>{error_message}</pre>"
            return self.send_message(text)
        except Exception as e:
            logger.error(f"에러 알림 전송 실패: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """텔레그램 연결 테스트"""
        try:
            logger.info("텔레그램 연결 테스트 중...")
            
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"✅ 텔레그램 봇 연결 성공: @{bot_info.get('username')}")
                
                # 테스트 메시지 전송
                test_msg = "🤖 주식 분석 시스템 연결 테스트 성공!"
                return self.send_message(test_msg)
            else:
                logger.error(f"❌ 텔레그램 봇 연결 실패: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 텔레그램 연결 테스트 실패: {str(e)}")
            return False


# 테스트 코드
if __name__ == "__main__":
    import json
    from dotenv import load_dotenv
    
    load_dotenv()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 설정 로드
    with open('../../config/settings.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    try:
        notifier = TelegramNotifier(settings)
        
        # 연결 테스트
        if notifier.test_connection():
            print("✅ 텔레그램 연결 테스트 성공!")
        else:
            print("❌ 텔레그램 연결 테스트 실패!")
            
    except ValueError as e:
        print(f"❌ 설정 오류: {str(e)}")
        print("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID 환경변수를 설정하세요.")
