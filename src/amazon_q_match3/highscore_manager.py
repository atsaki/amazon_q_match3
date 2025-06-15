"""
Amazon Q Match3 ハイスコア管理システム
"""

import json
import logging
from datetime import datetime
from pathlib import Path


class HighScoreManager:
    """ハイスコア管理クラス"""

    def __init__(self, data_file: str = "highscores.json"):
        self.logger = logging.getLogger("HighScoreManager")
        self.data_file = Path(data_file)
        self.highscores = self._load_highscores()

    def _load_highscores(self) -> dict[str, list[dict]]:
        """ハイスコアデータを読み込み"""
        try:
            if self.data_file.exists():
                with open(self.data_file, encoding="utf-8") as f:
                    data = json.load(f)
                    self.logger.info(f"Loaded highscores from {self.data_file}")
                    return data
            else:
                self.logger.info("No existing highscore file found, creating new one")
                return self._create_default_highscores()
        except Exception as e:
            self.logger.error(f"Error loading highscores: {e}")
            return self._create_default_highscores()

    def _create_default_highscores(self) -> dict[str, list[dict]]:
        """デフォルトのハイスコア構造を作成"""
        return {
            "30": [],  # 30秒モード
            "60": [],  # 1分モード
            "180": [],  # 3分モード
        }

    def _save_highscores(self):
        """ハイスコアデータを保存"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.highscores, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved highscores to {self.data_file}")
        except Exception as e:
            self.logger.error(f"Error saving highscores: {e}")

    def add_score(self, time_limit: int, score: int, player_name: str = "Player") -> bool:
        """
        新しいスコアを追加

        Args:
            time_limit: 制限時間（秒）
            score: スコア
            player_name: プレイヤー名

        Returns:
            bool: ハイスコアかどうか
        """
        time_key = str(time_limit)
        if time_key not in self.highscores:
            self.highscores[time_key] = []

        # 新しいスコアエントリ
        new_entry = {
            "score": score,
            "player": player_name,
            "date": datetime.now().isoformat(),
            "time_limit": time_limit,
        }

        # スコアを追加してソート
        self.highscores[time_key].append(new_entry)
        self.highscores[time_key].sort(key=lambda x: x["score"], reverse=True)

        # 上位10位まで保持
        self.highscores[time_key] = self.highscores[time_key][:10]

        # ハイスコアかどうかチェック
        is_highscore = any(
            entry["score"] == score and entry["date"] == new_entry["date"]
            for entry in self.highscores[time_key]
        )

        self._save_highscores()

        if is_highscore:
            rank = next(
                i + 1
                for i, entry in enumerate(self.highscores[time_key])
                if entry["score"] == score and entry["date"] == new_entry["date"]
            )
            self.logger.info(
                f"New highscore! Rank {rank} with {score} points in {time_limit}s mode"
            )

        return is_highscore

    def get_highscores(self, time_limit: int, count: int = 10) -> list[dict]:
        """
        指定された制限時間のハイスコアを取得

        Args:
            time_limit: 制限時間（秒）
            count: 取得する件数

        Returns:
            List[Dict]: ハイスコアリスト
        """
        time_key = str(time_limit)
        if time_key not in self.highscores:
            return []

        return self.highscores[time_key][:count]

    def get_best_score(self, time_limit: int) -> int:
        """指定された制限時間の最高スコアを取得"""
        scores = self.get_highscores(time_limit, 1)
        return scores[0]["score"] if scores else 0

    def is_highscore(self, time_limit: int, score: int) -> bool:
        """スコアがハイスコアかどうかチェック"""
        scores = self.get_highscores(time_limit, 10)
        if len(scores) < 10:
            return True
        return score > scores[-1]["score"]

    def get_rank(self, time_limit: int, score: int) -> int:
        """スコアの順位を取得（1-based）"""
        scores = self.get_highscores(time_limit, 10)
        for i, entry in enumerate(scores):
            if score >= entry["score"]:
                return i + 1
        return len(scores) + 1

    def get_all_time_best(self) -> tuple[int, str]:
        """全モード通しての最高スコアを取得"""
        best_score = 0
        best_mode = ""

        for time_limit, scores in self.highscores.items():
            if scores and scores[0]["score"] > best_score:
                best_score = scores[0]["score"]
                best_mode = f"{time_limit}秒"

        return best_score, best_mode

    def clear_highscores(self, time_limit: int = None):
        """ハイスコアをクリア"""
        if time_limit is None:
            # 全てクリア
            self.highscores = self._create_default_highscores()
            self.logger.info("Cleared all highscores")
        else:
            # 指定モードのみクリア
            time_key = str(time_limit)
            if time_key in self.highscores:
                self.highscores[time_key] = []
                self.logger.info(f"Cleared highscores for {time_limit}s mode")

        self._save_highscores()


# テスト用の関数
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)

    # テスト
    manager = HighScoreManager("test_highscores.json")

    # テストスコアを追加
    manager.add_score(180, 1500, "テストプレイヤー1")
    manager.add_score(180, 2000, "テストプレイヤー2")
    manager.add_score(60, 800, "テストプレイヤー3")

    # ハイスコア表示
    print("=== 3分モード ハイスコア ===")
    for i, score in enumerate(manager.get_highscores(180), 1):
        print(f"{i}. {score['player']}: {score['score']}点")

    print("\n=== 1分モード ハイスコア ===")
    for i, score in enumerate(manager.get_highscores(60), 1):
        print(f"{i}. {score['player']}: {score['score']}点")

    # 全体最高スコア
    best_score, best_mode = manager.get_all_time_best()
    print(f"\n全体最高スコア: {best_score}点 ({best_mode}モード)")
