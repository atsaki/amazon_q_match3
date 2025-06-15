import os
import sys
import unittest
from unittest.mock import patch

# テスト対象のモジュールをインポートするためのパス設定
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "amazon_q_match3"))

# pygameの初期化をモック化してテスト環境で実行可能にする
with patch("pygame.init"), patch("pygame.display.set_mode"), patch("pygame.font.Font"):
    from match3_game import Block, BlockType, Match3Game


class TestBlock(unittest.TestCase):
    """Blockクラスのテスト"""

    def test_block_creation(self):
        """ブロックの作成テスト"""
        block = Block(BlockType.RED, 2, 3)
        self.assertEqual(block.type, BlockType.RED)
        self.assertEqual(block.grid_x, 2)
        self.assertEqual(block.grid_y, 3)
        # 描画位置も確認
        self.assertEqual(block.draw_x, 2 * 60)  # CELL_SIZE = 60
        self.assertEqual(block.draw_y, 3 * 60)
        # アニメーション関連の初期値確認
        self.assertEqual(block.alpha, 255)

    def test_get_color(self):
        """色取得テスト"""
        block = Block(BlockType.BLUE, 0, 0)
        colors = block.get_colors()
        # グラデーション色が返されることを確認
        self.assertIsInstance(colors, (list, tuple))
        self.assertEqual(len(colors), 2)  # メインカラーとシャドウカラー
        # 青色系であることを確認
        main_color = colors[0]
        self.assertEqual(len(main_color), 3)  # RGB値


class TestMatch3Game(unittest.TestCase):
    """Match3Gameクラスのテスト"""

    def setUp(self):
        """各テストの前に実行される初期化"""
        with (
            patch("pygame.display.set_mode"),
            patch("pygame.font.Font"),
            patch("pygame.display.set_caption"),
            patch("pygame.init"),
        ):
            self.game = Match3Game()
            # テスト用にグリッドを空にする
            self.game.grid = [[None for _ in range(8)] for _ in range(8)]

    def test_game_initialization(self):
        """ゲーム初期化テスト"""
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.time_left, 180)
        self.assertIsNone(self.game.selected_block)
        self.assertFalse(self.game.game_over)

        # グリッドを初期化してからチェック
        self.game.initialize_grid()

        # グリッドが正しく初期化されているかチェック
        for row in range(8):
            for col in range(8):
                self.assertIsNotNone(self.game.grid[row][col])
                self.assertIsInstance(self.game.grid[row][col], Block)

    def test_get_grid_position(self):
        """マウス座標からグリッド座標への変換テスト"""
        # 有効な座標
        pos = self.game.get_grid_position((110, 110))  # GRID_OFFSET + CELL_SIZE
        self.assertEqual(pos, (1, 1))

        # 無効な座標（範囲外）
        pos = self.game.get_grid_position((10, 10))
        self.assertIsNone(pos)

        pos = self.game.get_grid_position((1000, 1000))
        self.assertIsNone(pos)

    def test_are_adjacent(self):
        """隣接判定テスト"""
        # 隣接している場合
        self.assertTrue(self.game.are_adjacent((0, 0), (0, 1)))  # 右隣
        self.assertTrue(self.game.are_adjacent((0, 0), (1, 0)))  # 下隣
        self.assertTrue(self.game.are_adjacent((1, 1), (0, 1)))  # 上隣
        self.assertTrue(self.game.are_adjacent((1, 1), (1, 0)))  # 左隣

        # 隣接していない場合
        self.assertFalse(self.game.are_adjacent((0, 0), (0, 2)))  # 2つ離れている
        self.assertFalse(self.game.are_adjacent((0, 0), (2, 0)))  # 2つ離れている
        self.assertFalse(self.game.are_adjacent((0, 0), (1, 1)))  # 斜め

    def test_swap_blocks(self):
        """ブロック交換テスト"""
        # テスト用のブロックを設定
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[0][1] = Block(BlockType.BLUE, 1, 0)

        # 初期状態を保存
        block1 = self.game.grid[0][0]
        block2 = self.game.grid[0][1]

        # ブロックを交換（アニメーション無効）
        self.game.swap_blocks((0, 0), (0, 1), animate=False)

        # 交換されているかチェック
        self.assertEqual(self.game.grid[0][0], block2)
        self.assertEqual(self.game.grid[0][1], block1)

        # 座標が更新されているかチェック
        self.assertEqual(self.game.grid[0][0].grid_x, 0)
        self.assertEqual(self.game.grid[0][0].grid_y, 0)
        self.assertEqual(self.game.grid[0][1].grid_x, 1)
        self.assertEqual(self.game.grid[0][1].grid_y, 0)

        # 描画位置も更新されているかチェック
        self.assertEqual(self.game.grid[0][0].draw_x, 0 * 60)
        self.assertEqual(self.game.grid[0][0].draw_y, 0 * 60)
        self.assertEqual(self.game.grid[0][1].draw_x, 1 * 60)
        self.assertEqual(self.game.grid[0][1].draw_y, 0 * 60)

    def test_find_matches_horizontal(self):
        """横方向のマッチ検出テスト"""
        # テスト用のグリッドを設定（横に3つ同じ色）
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[0][1] = Block(BlockType.RED, 1, 0)
        self.game.grid[0][2] = Block(BlockType.RED, 2, 0)
        self.game.grid[0][3] = Block(BlockType.BLUE, 3, 0)

        matches = self.game.find_matches()

        # 3つのマッチが検出されるかチェック
        expected_matches = {(0, 0), (0, 1), (0, 2)}
        self.assertEqual(matches, expected_matches)

    def test_find_matches_vertical(self):
        """縦方向のマッチ検出テスト"""
        # テスト用のグリッドを設定（縦に3つ同じ色）
        self.game.grid[0][0] = Block(BlockType.GREEN, 0, 0)
        self.game.grid[1][0] = Block(BlockType.GREEN, 0, 1)
        self.game.grid[2][0] = Block(BlockType.GREEN, 0, 2)
        self.game.grid[3][0] = Block(BlockType.YELLOW, 0, 3)

        matches = self.game.find_matches()

        # 3つのマッチが検出されるかチェック
        expected_matches = {(0, 0), (1, 0), (2, 0)}
        self.assertEqual(matches, expected_matches)

    def test_find_matches_no_match(self):
        """マッチなしのテスト"""
        # 確実にマッチしないパターンを作成
        # チェッカーボード風の配置で3つ以上連続しないようにする
        for row in range(8):
            for col in range(8):
                if (row + col) % 2 == 0:
                    self.game.grid[row][col] = Block(BlockType.RED, col, row)
                else:
                    self.game.grid[row][col] = Block(BlockType.BLUE, col, row)

        matches = self.game.find_matches()
        self.assertEqual(len(matches), 0)

    def test_remove_matches(self):
        """マッチ削除とスコア加算テスト"""
        initial_score = self.game.score
        matches = {(0, 0), (0, 1), (0, 2)}  # 3つのマッチ

        result = self.game.remove_matches(matches)

        self.assertTrue(result)
        self.assertEqual(self.game.score, initial_score + 100)  # 3つマッチで100点

        # ブロックが削除されているかチェック
        for row, col in matches:
            self.assertIsNone(self.game.grid[row][col])

    def test_remove_matches_different_sizes(self):
        """異なるサイズのマッチでのスコアテスト"""
        # 4つマッチ
        matches_4 = {(0, 0), (0, 1), (0, 2), (0, 3)}
        initial_score = self.game.score
        self.game.remove_matches(matches_4)
        self.assertEqual(self.game.score, initial_score + 200)

        # 5つマッチ
        matches_5 = {(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)}
        initial_score = self.game.score
        self.game.remove_matches(matches_5)
        self.assertEqual(self.game.score, initial_score + 500)

    def test_drop_blocks(self):
        """ブロック落下テスト"""
        # グリッドを初期化してから、上部にブロック、下部を空にする
        self.game.initialize_grid()
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[1][0] = None
        self.game.grid[2][0] = None

        moved = self.game.drop_blocks(animate=False)

        self.assertTrue(moved)
        self.assertIsNone(self.game.grid[0][0])
        self.assertIsNone(self.game.grid[1][0])
        self.assertIsNotNone(self.game.grid[2][0])
        self.assertEqual(self.game.grid[2][0].type, BlockType.RED)
        self.assertEqual(self.game.grid[2][0].grid_y, 2)  # 座標が更新されている
        self.assertEqual(self.game.grid[2][0].draw_y, 2 * 60)  # 描画位置も更新

    def test_fill_empty_spaces(self):
        """空スペース補充テスト"""
        # いくつかのスペースを空にする
        self.game.grid[0][0] = None
        self.game.grid[1][1] = None
        self.game.grid[2][2] = None

        self.game.fill_empty_spaces(animate=False)

        # 空スペースが埋められているかチェック
        self.assertIsNotNone(self.game.grid[0][0])
        self.assertIsNotNone(self.game.grid[1][1])
        self.assertIsNotNone(self.game.grid[2][2])

        # 新しいブロックが正しい座標を持っているかチェック
        self.assertEqual(self.game.grid[0][0].grid_x, 0)
        self.assertEqual(self.game.grid[0][0].grid_y, 0)
        self.assertEqual(self.game.grid[1][1].grid_x, 1)
        self.assertEqual(self.game.grid[1][1].grid_y, 1)
        self.assertEqual(self.game.grid[2][2].grid_x, 2)
        self.assertEqual(self.game.grid[2][2].grid_y, 2)


class TestGameIntegration(unittest.TestCase):
    """統合テスト"""

    def setUp(self):
        with (
            patch("pygame.display.set_mode"),
            patch("pygame.font.Font"),
            patch("pygame.display.set_caption"),
            patch("pygame.init"),
        ):
            self.game = Match3Game()
            # テスト用にグリッドを空にする
            self.game.grid = [[None for _ in range(8)] for _ in range(8)]

    def test_complete_match_cycle(self):
        """完全なマッチサイクルのテスト"""
        # 確実にマッチするパターンを設定
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[0][1] = Block(BlockType.RED, 1, 0)
        self.game.grid[0][2] = Block(BlockType.RED, 2, 0)

        # 他の部分は異なる色で埋める
        for row in range(8):
            for col in range(8):
                if (row, col) not in [(0, 0), (0, 1), (0, 2)]:
                    self.game.grid[row][col] = Block(BlockType.BLUE, col, row)

        initial_score = self.game.score
        result = self.game.process_matches()

        self.assertTrue(result)
        self.assertGreater(self.game.score, initial_score)

        # グリッドが完全に埋まっているかチェック
        for row in range(8):
            for col in range(8):
                self.assertIsNotNone(self.game.grid[row][col])


if __name__ == "__main__":
    # テスト実行時にpygameの初期化エラーを回避
    with patch("pygame.mixer.pre_init"), patch("pygame.mixer.quit"), patch("pygame.quit"):
        unittest.main()
