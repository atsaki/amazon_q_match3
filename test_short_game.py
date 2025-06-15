#!/usr/bin/env python3
"""
短時間テスト用のゲーム実行スクリプト（30秒でゲームオーバー）
"""

import sys
import os
from pathlib import Path

# パスを設定
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src' / 'amazon_q_match3'))

# ログ設定をインポート
from logging_config import setup_logging
import logging

def main():
    print("=== Amazon Q Match3 Short Test (30s) ===")
    
    # ログシステムを初期化
    setup_logging(
        level=logging.DEBUG,
        log_to_file=True,
        log_to_console=True
    )
    
    logger = logging.getLogger('ShortGameTest')
    logger.info("Starting short game test (30 seconds)")
    
    try:
        # ゲームをインポートして実行
        from match3_game import Match3Game
        
        # ゲーム時間を30秒に変更
        game = Match3Game()
        game.time_left = 30  # 30秒に設定
        logger.info(f"Game time set to {game.time_left} seconds")
        
        game.run()
        
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Game crashed: {e}", exc_info=True)
        print(f"\nGame crashed! Check the log file for details: {project_root / 'amazon_q_match3.log'}")
    finally:
        logger.info("Short game test session ended")

if __name__ == "__main__":
    main()
