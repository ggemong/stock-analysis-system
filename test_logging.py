#!/usr/bin/env python3
"""
로그 시스템 테스트 스크립트
로그 파일이 정상적으로 생성되는지 확인
"""

import os
import sys
import logging
from pathlib import Path

def test_log_creation():
    """로그 파일 생성 테스트"""
    
    print("=" * 60)
    print("로그 시스템 테스트")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"\n📁 현재 디렉토리: {current_dir}")
    
    # 로그 파일 경로 설정
    log_file = current_dir / 'test_stock_analysis.log'
    print(f"📋 로그 파일 경로: {log_file}")
    
    # 로그 설정
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(str(log_file), encoding='utf-8')
            ],
            force=True  # 기존 설정 덮어쓰기
        )
        print("✅ 로그 시스템 초기화 성공")
    except Exception as e:
        print(f"❌ 로그 시스템 초기화 실패: {e}")
        return False
    
    # 테스트 로그 작성
    logger = logging.getLogger(__name__)
    
    print("\n" + "=" * 60)
    print("테스트 로그 작성 중...")
    print("=" * 60 + "\n")
    
    logger.info("✅ INFO 레벨 테스트")
    logger.warning("⚠️ WARNING 레벨 테스트")
    logger.error("❌ ERROR 레벨 테스트")
    
    # 김치프리미엄 스타일 로그
    logger.info("김치 프리미엄 수집 시작... (환율: 1320.50)")
    logger.info("  🔍 BTC 처리 중...")
    logger.info("  ✅ BTC: +0.35% (균형)")
    logger.info("김치 프리미엄 수집 완료 - 성공: 5/5")
    
    # 로그 파일 확인
    print("\n" + "=" * 60)
    print("로그 파일 확인")
    print("=" * 60)
    
    if log_file.exists():
        file_size = log_file.stat().st_size
        print(f"\n✅ 로그 파일 생성 성공!")
        print(f"   위치: {log_file}")
        print(f"   크기: {file_size} bytes")
        
        # 로그 내용 출력
        print("\n" + "=" * 60)
        print("로그 파일 내용:")
        print("=" * 60)
        with open(log_file, 'r', encoding='utf-8') as f:
            print(f.read())
        
        return True
    else:
        print(f"\n❌ 로그 파일이 생성되지 않았습니다: {log_file}")
        return False

def check_permissions():
    """디렉토리 권한 확인"""
    print("\n" + "=" * 60)
    print("디렉토리 권한 확인")
    print("=" * 60 + "\n")
    
    current_dir = Path.cwd()
    
    # 읽기 권한
    if os.access(current_dir, os.R_OK):
        print("✅ 읽기 권한: OK")
    else:
        print("❌ 읽기 권한: 없음")
    
    # 쓰기 권한
    if os.access(current_dir, os.W_OK):
        print("✅ 쓰기 권한: OK")
    else:
        print("❌ 쓰기 권한: 없음")
        print("   해결: chmod u+w . 실행")
    
    # 실행 권한
    if os.access(current_dir, os.X_OK):
        print("✅ 실행 권한: OK")
    else:
        print("❌ 실행 권한: 없음")

def main():
    """메인 함수"""
    
    # 권한 확인
    check_permissions()
    
    # 로그 생성 테스트
    success = test_log_creation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 완료: 로그 시스템이 정상 작동합니다!")
        print("\n다음 명령어로 실제 시스템을 실행하세요:")
        print("  python main.py --test")
    else:
        print("❌ 테스트 실패: 로그 파일을 생성할 수 없습니다")
        print("\n문제 해결 방법:")
        print("  1. 쓰기 권한 확인: ls -ld .")
        print("  2. 권한 부여: chmod u+w .")
        print("  3. 다른 디렉토리에서 시도")
    print("=" * 60)

if __name__ == "__main__":
    main()
