# Match3パズルゲーム

Amazon Q Developerを使って作成したPygameベースのMatch3パズルゲームです。

## 🎮 ゲーム概要

- **ジャンル**: パズルゲーム（マッチ3系）
- **プレイ時間**: 3分間
- **目標**: 同じ色のブロックを3つ以上揃えて高スコアを目指す

## 🎯 ゲームルール

1. 隣接する2つのブロックをクリックして交換
2. 同じ色のブロックを縦または横に3つ以上揃える
3. マッチしたブロックが消えて得点獲得
4. 上からブロックが落下して新しいマッチが発生する可能性
5. 連鎖でボーナス得点
6. 3分間でできるだけ高スコアを狙う

## 🎨 ゲーム要素

- **8×8のゲームグリッド**
- **6色のカラフルなブロック**（赤、青、緑、黄、紫、オレンジ）
- **スコアシステム**: 3個=100点、4個=200点、5個=500点
- **連鎖システム**: 連続消去で追加得点
- **制限時間**: 3分間のタイマー

## 🚀 セットアップ

### 前提条件
- Python 3.8以上
- uv（パッケージマネージャー）

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd q_example

# 依存関係をインストール
uv sync
```

## 🎮 ゲーム実行

```bash
# ゲームを起動
uv run python src/q_example/match3_game.py
```

## 🧪 テスト

このプロジェクトには包括的なテストスイートが含まれています。

### テスト実行方法

```bash
# 基本テスト実行
uv run pytest tests/

# 詳細出力付きテスト実行
uv run pytest tests/ -v

# カバレッジ測定付きテスト実行
uv run pytest tests/ --cov=src/q_example --cov-report=term-missing

# HTMLカバレッジレポート生成
uv run pytest tests/ --cov=src/q_example --cov-report=html

# 特定のテストファイルのみ実行
uv run pytest tests/test_match3_game.py -v

# 特定のテストケースのみ実行
uv run pytest tests/test_match3_game.py::TestBlock::test_block_creation -v
```

### テスト構成

- **総テスト数**: 24個
- **テストカバレッジ**: 73%
- **テストファイル**:
  - `tests/test_match3_game.py` - 基本機能テスト
  - `tests/test_game_edge_cases.py` - エッジケーステスト

### テスト内容

#### 基本機能テスト
- ブロック作成と色管理
- グリッド座標変換
- 隣接判定とブロック交換
- マッチ検出（横・縦方向）
- スコア計算とブロック削除
- ブロック落下と空スペース補充

#### エッジケーステスト
- 境界値処理
- 大きなマッチ（8個同時）
- 複数同時マッチ
- 空グリッド操作
- ゲーム状態の整合性

詳細なテスト結果は `TEST_SUMMARY.md` を参照してください。

## 📁 プロジェクト構造

```
q_example/
├── src/
│   └── q_example/
│       └── match3_game.py      # メインゲームファイル
├── tests/
│   ├── __init__.py
│   ├── test_match3_game.py     # 基本機能テスト
│   └── test_game_edge_cases.py # エッジケーステスト
├── pyproject.toml              # プロジェクト設定
├── uv.lock                     # 依存関係ロック
├── README.md                   # このファイル
└── TEST_SUMMARY.md             # テスト詳細レポート
```

## 🛠️ 開発

### 依存関係の追加

```bash
# 新しい依存関係を追加
uv add <package-name>

# 開発用依存関係を追加
uv add --dev <package-name>
```

### コード品質チェック

```bash
# テスト実行
uv run pytest tests/

# カバレッジチェック
uv run pytest tests/ --cov=src/q_example --cov-report=term-missing
```

## 🎯 Amazon Q Developerでの開発体験

このプロジェクトは、Amazon Q Developerを使用して以下の機能を実装しました：

### 実装した機能
- **ゲームロジック**: マッチ検出アルゴリズム
- **UI描画**: Pygameを使った2Dグラフィックス
- **イベント処理**: マウス操作とゲーム状態管理
- **テストスイート**: 包括的な単体・統合テスト
- **デバッグ**: 問題の特定と修正

### 学んだこと
- ゲーム開発におけるテスト駆動開発
- エッジケースの重要性
- テストデータの制御方法
- デバッグ技術とツールの活用

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能提案は、GitHubのIssueでお知らせください。

---

**楽しいゲーム体験を！** 🎮✨
