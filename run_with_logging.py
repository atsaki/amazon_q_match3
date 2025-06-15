#!/usr/bin/env python3
"""
ログ機能付きでゲームを実行するスクリプト
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
    print("=== Amazon Q Match3 with DEBUG Logging ===")
    
    # デバッグレベルに設定
    log_level = logging.DEBUG
    
    # ログシステムを初期化
    setup_logging(
        level=log_level,
        log_to_file=True,
        log_to_console=True  # コンソールにも出力
    )
    
    logger = logging.getLogger('GameRunner')
    logger.info("Starting Amazon Q Match3 with DEBUG logging enabled")
    logger.info(f"Log level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {project_root / 'amazon_q_match3.log'}")
    
    try:
        # ゲームをインポートして実行
        from match3_game import Match3Game
        
        game = Match3Game()
        game.run()
        
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Game crashed: {e}", exc_info=True)
        print(f"\nGame crashed! Check the log file for details: {project_root / 'amazon_q_match3.log'}")
    finally:
        logger.info("Game session ended")

if __name__ == "__main__":
    main()
