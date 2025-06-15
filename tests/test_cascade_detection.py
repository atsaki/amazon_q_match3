#!/usr/bin/env python3
"""
連鎖とマッチ検出のテスト
新しいブロック生成後のマッチ検出問題の回帰テスト
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# プロジェクトのsrcディレクトリをパスに追加
src_path = Path(__file__).parent.parent / "src" / "amazon_q_match3"
sys.path.insert(0, str(src_path))

from match3_game import Block, BlockType, Match3Game  # noqa: E402


class TestCascadeDetection(unittest.TestCase):
    """連鎖とマッチ検出のテストクラス"""

    def setUp(self):
        """テスト前の準備"""
        self.game = Match3Game(time_limit=180)

    def test_match_detection_after_fill_empty_spaces_no_animation(self):
        """新ブロック生成後のマッチ検出テスト（アニメーションなし）"""
        # グリッドを空にする
        for row in range(8):
            for col in range(8):
                self.game.grid[row][col] = None

        # 特定の配置でマッチが発生するように設定
        # 横一列に同じ色のブロックを配置（意図的にマッチを作る）
        with patch("random.choice") as mock_choice:
            # 最初の3つは赤、残りは他の色
            mock_choice.side_effect = [
                BlockType.RED,
                BlockType.RED,
                BlockType.RED,  # 横マッチ
                BlockType.BLUE,
                BlockType.GREEN,
                BlockType.YELLOW,
                BlockType.PURPLE,
                BlockType.ORANGE,
            ] * 10  # 十分な数を用意

            initial_score = self.game.score

            # アニメーションなしで空スペースを埋める
            self.game.fill_empty_spaces(animate=False)

            # マッチが検出されて削除されたかチェック
            # スコアが増加していればマッチが処理された証拠
            self.assertGreater(
                self.game.score, initial_score, "新ブロック生成後にマッチが検出されていない"
            )

    def test_cascade_check_after_animation_complete(self):
        """アニメーション完了後の連鎖チェックテスト"""
        # pending_cascade_checkフラグを設定
        self.game.pending_cascade_check = True

        # 意図的にマッチを作成
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[0][1] = Block(BlockType.RED, 1, 0)
        self.game.grid[0][2] = Block(BlockType.RED, 2, 0)

        initial_score = self.game.score

        # アニメーション完了処理を実行
        self.game.on_animation_complete()

        # マッチが処理されたかチェック
        self.assertGreater(
            self.game.score, initial_score, "アニメーション完了後の連鎖チェックが機能していない"
        )

        # フラグがリセットされたかチェック
        self.assertFalse(
            getattr(self.game, "pending_cascade_check", False),
            "pending_cascade_checkフラグがリセットされていない",
        )

    def test_handle_cascade_check_with_matches(self):
        """連鎖チェック処理でマッチがある場合のテスト"""
        # pending_cascade_checkフラグを設定
        self.game.pending_cascade_check = True

        # 縦マッチを作成
        self.game.grid[0][0] = Block(BlockType.BLUE, 0, 0)
        self.game.grid[1][0] = Block(BlockType.BLUE, 0, 1)
        self.game.grid[2][0] = Block(BlockType.BLUE, 0, 2)

        initial_score = self.game.score

        # 連鎖チェック処理を実行
        self.game._handle_cascade_check()

        # マッチが処理されたかチェック
        self.assertGreater(self.game.score, initial_score, "連鎖チェックでマッチが処理されていない")

    def test_handle_cascade_check_without_matches(self):
        """連鎖チェック処理でマッチがない場合のテスト"""
        # pending_cascade_checkフラグを設定
        self.game.pending_cascade_check = True

        # グリッド全体をクリア
        for row in range(8):
            for col in range(8):
                self.game.grid[row][col] = None

        # マッチしない配置を作成
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[0][1] = Block(BlockType.BLUE, 1, 0)
        self.game.grid[0][2] = Block(BlockType.GREEN, 2, 0)

        initial_score = self.game.score

        # 連鎖チェック処理を実行
        self.game._handle_cascade_check()

        # スコアが変わらないことを確認
        self.assertEqual(self.game.score, initial_score, "マッチがないのにスコアが変化した")

        # フラグがリセットされたかチェック
        self.assertFalse(
            getattr(self.game, "pending_cascade_check", False),
            "pending_cascade_checkフラグがリセットされていない",
        )

    def test_multiple_cascade_cycles(self):
        """複数回の連鎖サイクルテスト"""
        # 複雑な連鎖を作成するための配置
        # 最初のマッチが削除されると、落下により新しいマッチが発生する配置

        # 上部に赤ブロックを配置（落下後にマッチを形成）
        self.game.grid[0][0] = Block(BlockType.RED, 0, 0)
        self.game.grid[1][0] = Block(BlockType.BLUE, 0, 1)
        self.game.grid[2][0] = Block(BlockType.RED, 0, 2)
        self.game.grid[3][0] = Block(BlockType.RED, 0, 3)

        # 下部に最初のマッチを配置
        self.game.grid[5][0] = Block(BlockType.GREEN, 0, 5)
        self.game.grid[6][0] = Block(BlockType.GREEN, 0, 6)
        self.game.grid[7][0] = Block(BlockType.GREEN, 0, 7)

        initial_score = self.game.score

        # 最初のマッチを処理
        matches = self.game.find_matches()
        if matches:
            self.game.remove_matches(matches)

            # ブロック落下
            self.game.drop_blocks(animate=False)

            # 空スペース補充（アニメーションなしなので即座にマッチチェック）
            self.game.fill_empty_spaces(animate=False)

        # 複数回の処理でスコアが増加することを確認
        self.assertGreater(self.game.score, initial_score, "複数回の連鎖処理が機能していない")

    def test_animation_complete_integration(self):
        """アニメーション完了の統合テスト"""
        # アニメーション状態を設定
        self.game.animating = True
        self.game.pending_cascade_check = True

        # マッチを作成
        self.game.grid[3][3] = Block(BlockType.YELLOW, 3, 3)
        self.game.grid[3][4] = Block(BlockType.YELLOW, 4, 3)
        self.game.grid[3][5] = Block(BlockType.YELLOW, 5, 3)

        initial_score = self.game.score

        # アニメーション更新でアニメーション完了をシミュレート
        self.game._update_animations(0.016)  # 1フレーム分

        # アニメーション状態を手動で終了
        was_animating = self.game.animating
        self.game.animating = False

        # アニメーション完了処理をシミュレート
        if was_animating and not self.game.animating:
            self.game.on_animation_complete()

        # マッチが処理されたかチェック
        self.assertGreater(
            self.game.score, initial_score, "アニメーション完了統合処理が機能していない"
        )

    def test_regression_new_blocks_match_detection(self):
        """回帰テスト: 新ブロック生成後のマッチ検出"""
        # このテストは今回修正した具体的な問題をテスト

        # 特定の状況を再現：
        # 1. ブロックが削除される
        # 2. 新しいブロックが降ってくる
        # 3. 新しいブロックが3つ並ぶ
        # 4. マッチが検出されて削除される

        # 最下段に空スペースを作る
        for col in range(3):
            self.game.grid[7][col] = None

        # 新しいブロックが同じ色になるように制御
        with patch("random.choice") as mock_choice:
            mock_choice.return_value = BlockType.PURPLE

            initial_score = self.game.score

            # 空スペースを埋める（アニメーションなし）
            self.game.fill_empty_spaces(animate=False)

            # 3つの紫ブロックが生成され、即座にマッチ検出・削除されるはず
            self.assertGreater(
                self.game.score, initial_score, "新ブロック生成後の即座マッチ検出が機能していない"
            )

            # 該当位置のブロックが削除されているかチェック
            deleted_blocks = 0
            for col in range(3):
                if self.game.grid[7][col] is None:
                    deleted_blocks += 1

            self.assertGreater(deleted_blocks, 0, "マッチしたブロックが削除されていない")


if __name__ == "__main__":
    unittest.main()
