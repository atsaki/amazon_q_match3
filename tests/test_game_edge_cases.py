import unittest
import sys
import os
from unittest.mock import patch

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'amazon_q_match3'))

with patch('pygame.init'), patch('pygame.display.set_mode'), patch('pygame.font.Font'):
    from match3_game import Match3Game, Block, BlockType

class TestGameEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""
    
    def setUp(self):
        with patch('pygame.display.set_mode'), \
             patch('pygame.font.Font'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.init'):
            self.game = Match3Game()
            # テスト用にグリッドを空にする
            self.game.grid = [[None for _ in range(8)] for _ in range(8)]
    
    def test_boundary_coordinates(self):
        """境界座標のテスト"""
        # グリッドの境界でのマウス座標変換
        # 左上角
        pos = self.game.get_grid_position((50, 50))  # GRID_OFFSET
        self.assertEqual(pos, (0, 0))
        
        # 右下角
        pos = self.game.get_grid_position((49 + 8*60, 49 + 8*60))  # ギリギリ範囲内
        self.assertEqual(pos, (7, 7))
        
        # 範囲外（負の座標）
        pos = self.game.get_grid_position((-10, -10))
        self.assertIsNone(pos)
    
    def test_large_matches(self):
        """大きなマッチのテスト"""
        # チェッカーボードパターンで初期化（マッチしない）
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    self.game.grid[row][col] = Block(BlockType.YELLOW, col, row)
                else:
                    self.game.grid[row][col] = Block(BlockType.PURPLE, col, row)
        
        # 一列全体をマッチさせる（8個）
        for col in range(8):
            self.game.grid[0][col] = Block(BlockType.RED, col, 0)
        
        matches = self.game.find_matches()
        self.assertEqual(len(matches), 8)
        
        # スコア計算
        initial_score = self.game.score
        self.game.remove_matches(matches)
        expected_score = initial_score + (100 * 8)  # 8個なので800点
        self.assertEqual(self.game.score, expected_score)
    
    def test_multiple_matches_same_time(self):
        """同時に複数のマッチが発生するテスト"""
        # チェッカーボードパターンで初期化（マッチしない）
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    self.game.grid[row][col] = Block(BlockType.YELLOW, col, row)
                else:
                    self.game.grid[row][col] = Block(BlockType.PURPLE, col, row)
        
        # 横マッチを作成
        for col in range(3):
            self.game.grid[0][col] = Block(BlockType.RED, col, 0)
        
        # 縦マッチを作成（重複しない位置）
        for row in range(3):
            self.game.grid[row][5] = Block(BlockType.BLUE, 5, row)
        
        matches = self.game.find_matches()
        self.assertEqual(len(matches), 6)  # 3 + 3
    
    def test_l_shaped_match(self):
        """L字型のマッチテスト"""
        # L字型に同じ色を配置
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)]
        for row, col in positions:
            self.game.grid[row][col] = Block(BlockType.GREEN, col, row)
        
        matches = self.game.find_matches()
        # 横3つと縦3つが検出される（重複あり）
        self.assertGreaterEqual(len(matches), 3)
    
    def test_empty_grid_operations(self):
        """空のグリッドでの操作テスト"""
        # グリッドを空にする
        for row in range(8):
            for col in range(8):
                self.game.grid[row][col] = None
        
        # マッチ検出（空の場合）
        matches = self.game.find_matches()
        self.assertEqual(len(matches), 0)
        
        # 落下処理（何も起こらない）
        moved = self.game.drop_blocks()
        self.assertFalse(moved)
        
        # 空スペース補充
        self.game.fill_empty_spaces()
        
        # 全て埋まっているかチェック
        for row in range(8):
            for col in range(8):
                self.assertIsNotNone(self.game.grid[row][col])
    
    def test_single_column_operations(self):
        """単一列での操作テスト"""
        # 1列目だけにブロックを配置
        for row in range(8):
            if row < 4:
                self.game.grid[row][0] = Block(BlockType.YELLOW, 0, row)
            else:
                self.game.grid[row][0] = None
        
        # 他の列は空にする
        for row in range(8):
            for col in range(1, 8):
                self.game.grid[row][col] = None
        
        # 落下処理
        moved = self.game.drop_blocks()
        self.assertTrue(moved)
        
        # 下4つにブロックが移動しているかチェック
        for row in range(4):
            self.assertIsNone(self.game.grid[row][0])
        for row in range(4, 8):
            self.assertIsNotNone(self.game.grid[row][0])
    
    def test_game_time_management(self):
        """ゲーム時間管理のテスト"""
        # 初期時間
        self.assertEqual(self.game.time_left, 180)
        
        # 時間を減らす
        self.game.time_left = 1.5
        
        # ゲームオーバーでない状態
        self.assertFalse(self.game.game_over)
        
        # 時間を0以下にする
        self.game.time_left = -1
        
        # まだゲームオーバーフラグは手動で設定する必要がある
        # （実際のゲームループで処理される）
    
    def test_score_edge_cases(self):
        """スコアのエッジケーステスト"""
        initial_score = self.game.score
        
        # 空のマッチセット
        result = self.game.remove_matches(set())
        self.assertFalse(result)
        self.assertEqual(self.game.score, initial_score)
        
        # 非常に大きなマッチ（理論上の最大）
        large_matches = {(row, col) for row in range(8) for col in range(8)}
        self.game.remove_matches(large_matches)
        expected_score = initial_score + (100 * 64)  # 全64マス
        self.assertEqual(self.game.score, expected_score)

class TestGameStateConsistency(unittest.TestCase):
    """ゲーム状態の整合性テスト"""
    
    def setUp(self):
        with patch('pygame.display.set_mode'), \
             patch('pygame.font.Font'), \
             patch('pygame.display.set_caption'), \
             patch('pygame.init'):
            self.game = Match3Game()
            # テスト用にグリッドを空にする
            self.game.grid = [[None for _ in range(8)] for _ in range(8)]
    
    def test_grid_consistency_after_operations(self):
        """操作後のグリッド整合性テスト"""
        # 初期状態の確認
        self.assert_grid_valid()
        
        # いくつかの操作を実行
        self.game.swap_blocks((0, 0), (0, 1))
        self.assert_grid_valid()
        
        # マッチ処理
        self.game.process_matches()
        self.assert_grid_valid()
    
    def assert_grid_valid(self):
        """グリッドが有効な状態かチェック"""
        for row in range(8):
            for col in range(8):
                block = self.game.grid[row][col]
                if block is not None:
                    # ブロックの座標が正しいかチェック
                    self.assertEqual(block.grid_x, col)
                    self.assertEqual(block.grid_y, row)
                    # ブロックタイプが有効かチェック
                    self.assertIsInstance(block.type, BlockType)
                    # 描画位置も確認
                    self.assertEqual(block.draw_x, col * 60)
                    self.assertEqual(block.draw_y, row * 60)
    
    def test_no_infinite_loops(self):
        """無限ループが発生しないかテスト"""
        # 連鎖が発生しやすい状況を作成
        for row in range(8):
            for col in range(8):
                # 交互に配置して連鎖を誘発
                if row < 4:
                    self.game.grid[row][col] = Block(BlockType.RED, col, row)
                else:
                    self.game.grid[row][col] = Block(BlockType.BLUE, col, row)
        
        # 一部を変更してマッチを作成
        for col in range(3):
            self.game.grid[4][col] = Block(BlockType.RED, col, 4)
        
        # process_matchesが終了することを確認
        result = self.game.process_matches()
        # 結果に関係なく、処理が完了すればOK
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()
