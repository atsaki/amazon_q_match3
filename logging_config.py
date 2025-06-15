"""
Amazon Q Match3 ログ設定
"""

import logging
import sys
from pathlib import Path

def setup_logging(level=logging.INFO, log_to_file=True, log_to_console=True):
    """
    ログシステムを設定
    
    Args:
        level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: ファイルにログを出力するか
        log_to_console: コンソールにログを出力するか
    """
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    handlers = []
    
    # ファイルハンドラー
    if log_to_file:
        log_file = Path(__file__).parent / 'amazon_q_match3.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)
    
    # コンソールハンドラー
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        handlers.append(console_handler)
    
    # ハンドラーを追加
    for handler in handlers:
        root_logger.addHandler(handler)
    
    return root_logger

def get_game_logger(name='Match3Game'):
    """ゲーム用ロガーを取得"""
    return logging.getLogger(name)

# デフォルト設定
if __name__ == "__main__":
    # テスト用
    setup_logging(level=logging.DEBUG)
    logger = get_game_logger()
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
