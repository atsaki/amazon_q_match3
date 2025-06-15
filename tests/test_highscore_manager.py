"""
ハイスコア管理システムのテスト
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# パスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'amazon_q_match3'))

from highscore_manager import HighScoreManager

class TestHighScoreManager(unittest.TestCase):
    """ハイスコア管理のテスト"""
    
    def setUp(self):
        """各テストの前に実行される初期化"""
        # 一時ファイルを使用
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.manager = HighScoreManager(self.temp_file.name)
    
    def tearDown(self):
        """各テストの後に実行されるクリーンアップ"""
        # 一時ファイルを削除
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_initialization(self):
        """初期化テスト"""
        self.assertIsInstance(self.manager.highscores, dict)
        self.assertIn("30", self.manager.highscores)
        self.assertIn("60", self.manager.highscores)
        self.assertIn("180", self.manager.highscores)
    
    def test_add_score(self):
        """スコア追加テスト"""
        # 最初のスコアを追加
        is_highscore = self.manager.add_score(180, 1000, "Player1")
        self.assertTrue(is_highscore)  # 最初のスコアは必ずハイスコア
        
        # スコアが正しく保存されているかチェック
        scores = self.manager.get_highscores(180)
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["score"], 1000)
        self.assertEqual(scores[0]["player"], "Player1")
    
    def test_score_sorting(self):
        """スコアソートテスト"""
        # 複数のスコアを追加
        self.manager.add_score(180, 500, "Player1")
        self.manager.add_score(180, 1000, "Player2")
        self.manager.add_score(180, 750, "Player3")
        
        scores = self.manager.get_highscores(180)
        
        # スコアが降順でソートされているかチェック
        self.assertEqual(scores[0]["score"], 1000)
        self.assertEqual(scores[1]["score"], 750)
        self.assertEqual(scores[2]["score"], 500)
    
    def test_max_scores_limit(self):
        """最大スコア数制限テスト"""
        # 11個のスコアを追加（制限は10個）
        for i in range(11):
            self.manager.add_score(180, i * 100, f"Player{i}")
        
        scores = self.manager.get_highscores(180)
        
        # 上位10個のみ保持されているかチェック
        self.assertEqual(len(scores), 10)
        self.assertEqual(scores[0]["score"], 1000)  # 最高スコア
        self.assertEqual(scores[-1]["score"], 100)  # 10位のスコア
    
    def test_get_best_score(self):
        """最高スコア取得テスト"""
        # スコアなしの場合
        self.assertEqual(self.manager.get_best_score(180), 0)
        
        # スコア追加後
        self.manager.add_score(180, 1500, "Player1")
        self.manager.add_score(180, 1000, "Player2")
        
        self.assertEqual(self.manager.get_best_score(180), 1500)
    
    def test_is_highscore(self):
        """ハイスコア判定テスト"""
        # 10個のスコアを追加
        for i in range(10):
            self.manager.add_score(180, (i + 1) * 100, f"Player{i}")
        
        # 11位相当のスコアはハイスコアではない
        self.assertFalse(self.manager.is_highscore(180, 50))
        
        # 10位以上のスコアはハイスコア
        self.assertTrue(self.manager.is_highscore(180, 150))
        self.assertTrue(self.manager.is_highscore(180, 1500))
    
    def test_get_rank(self):
        """順位取得テスト"""
        # スコアを追加
        self.manager.add_score(180, 1000, "Player1")
        self.manager.add_score(180, 800, "Player2")
        self.manager.add_score(180, 600, "Player3")
        
        # 順位チェック
        self.assertEqual(self.manager.get_rank(180, 1200), 1)  # 1位
        self.assertEqual(self.manager.get_rank(180, 900), 2)   # 2位
        self.assertEqual(self.manager.get_rank(180, 700), 3)   # 3位
        self.assertEqual(self.manager.get_rank(180, 500), 4)   # 4位
    
    def test_different_time_modes(self):
        """異なる時間モードのテスト"""
        # 各モードにスコアを追加
        self.manager.add_score(30, 300, "Player1")
        self.manager.add_score(60, 600, "Player2")
        self.manager.add_score(180, 1800, "Player3")
        
        # 各モードのスコアが独立して管理されているかチェック
        self.assertEqual(self.manager.get_best_score(30), 300)
        self.assertEqual(self.manager.get_best_score(60), 600)
        self.assertEqual(self.manager.get_best_score(180), 1800)
    
    def test_get_all_time_best(self):
        """全体最高スコア取得テスト"""
        # 各モードにスコアを追加
        self.manager.add_score(30, 500, "Player1")
        self.manager.add_score(60, 1200, "Player2")
        self.manager.add_score(180, 800, "Player3")
        
        best_score, best_mode = self.manager.get_all_time_best()
        self.assertEqual(best_score, 1200)
        self.assertEqual(best_mode, "60秒")
    
    def test_clear_highscores(self):
        """ハイスコアクリアテスト"""
        # スコアを追加
        self.manager.add_score(180, 1000, "Player1")
        self.manager.add_score(60, 500, "Player2")
        
        # 特定モードをクリア
        self.manager.clear_highscores(180)
        self.assertEqual(len(self.manager.get_highscores(180)), 0)
        self.assertEqual(len(self.manager.get_highscores(60)), 1)
        
        # 全てクリア
        self.manager.clear_highscores()
        self.assertEqual(len(self.manager.get_highscores(60)), 0)
    
    def test_persistence(self):
        """データ永続化テスト"""
        # スコアを追加
        self.manager.add_score(180, 1000, "Player1")
        
        # 新しいマネージャーインスタンスを作成
        new_manager = HighScoreManager(self.temp_file.name)
        
        # データが正しく読み込まれているかチェック
        scores = new_manager.get_highscores(180)
        self.assertEqual(len(scores), 1)
        self.assertEqual(scores[0]["score"], 1000)
        self.assertEqual(scores[0]["player"], "Player1")

if __name__ == '__main__':
    unittest.main()
