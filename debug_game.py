#!/usr/bin/env python3
"""
デバッグ用のゲーム実行スクリプト
クラッシュの原因を特定するためのエラーハンドリングを追加
"""

import sys
import traceback
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'amazon_q_match3'))

try:
    from match3_game import Match3Game
    
    print("=== Amazon Q Match3 Debug Mode ===")
    print("ゲームを開始します...")
    
    game = Match3Game()
    game.run()
    
except Exception as e:
    print(f"\n=== CRASH DETECTED ===")
    print(f"エラータイプ: {type(e).__name__}")
    print(f"エラーメッセージ: {str(e)}")
    print(f"\n=== FULL TRACEBACK ===")
    traceback.print_exc()
    print(f"\n=== DEBUG INFO ===")
    print(f"Python version: {sys.version}")
    
    # Pygameの状態確認
    try:
        import pygame
        print(f"Pygame version: {pygame.version.ver}")
        print(f"Pygame initialized: {pygame.get_init()}")
    except:
        print("Pygame import failed")
    
    input("\nPress Enter to exit...")
