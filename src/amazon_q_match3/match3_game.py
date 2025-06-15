import contextlib
import logging
import math
import random
import sys
import time
from enum import Enum
from pathlib import Path

import pygame
from game_menu import GameMenu, MenuState
from highscore_manager import HighScoreManager

# 初期化
pygame.init()

# 定数
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 8
CELL_SIZE = 60
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50
FPS = 60

# ログ設定をインポート
sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from logging_config import get_game_logger, setup_logging

    # ログシステムを初期化（INFO レベル、ファイルとコンソール両方に出力）
    setup_logging(level=logging.INFO, log_to_file=True, log_to_console=False)
    logger = get_game_logger()
except ImportError:
    # フォールバック設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("amazon_q_match3.log"), logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("Match3Game")
GRID_SIZE = 8
CELL_SIZE = 60
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 50
FPS = 60

# アニメーション定数
SWAP_ANIMATION_SPEED = 8.0
FALL_ANIMATION_SPEED = 12.0
FADE_ANIMATION_SPEED = 5.0
PARTICLE_COUNT = 8

# 色定義（グラデーション用）
COLORS = {
    "RED": [(255, 100, 100), (200, 50, 50)],
    "BLUE": [(100, 150, 255), (50, 100, 200)],
    "GREEN": [(100, 255, 100), (50, 200, 50)],
    "YELLOW": [(255, 255, 100), (200, 200, 50)],
    "PURPLE": [(255, 100, 255), (200, 50, 200)],
    "ORANGE": [(255, 165, 0), (200, 120, 0)],
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GRAY": (128, 128, 128),
    "LIGHT_GRAY": (192, 192, 192),
}

# 単色版（UI用）
UI_COLORS = {
    "RED": (255, 100, 100),
    "BLUE": (100, 150, 255),
    "GREEN": (100, 255, 100),
    "YELLOW": (255, 255, 100),
    "PURPLE": (255, 100, 255),
    "ORANGE": (255, 165, 0),
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "GRAY": (128, 128, 128),
    "LIGHT_GRAY": (192, 192, 192),
}


class BlockType(Enum):
    RED = 0
    BLUE = 1
    GREEN = 2
    YELLOW = 3
    PURPLE = 4
    ORANGE = 5


class AnimationType(Enum):
    NONE = 0
    SWAP = 1
    FALL = 2
    FADE = 3
    SPAWN = 4


class ScorePopup:
    """スコア表示用のポップアップクラス"""

    def __init__(self, x, y, score, color=(255, 255, 0)):
        self.x = x
        self.y = y
        self.start_y = y
        self.score = score
        self.color = color
        self.life = 0.8  # 0.8秒間表示（1秒より少し短く）
        self.font_size = 24

    def update(self, dt):
        """ポップアップの更新"""
        self.life -= dt
        # 上に移動
        self.y = self.start_y - (1.0 - self.life) * 50

        return self.life > 0

    def draw(self, screen, font):
        """ポップアップの描画"""
        if self.life > 0:
            # フェードアウト効果（残りライフに応じて透明度を調整）
            alpha = min(255, int(255 * (self.life / 0.8)))  # 0.8秒でフェードアウト

            # 色にアルファ値を適用
            fade_color = (*self.color[:3], alpha) if len(self.color) == 4 else (*self.color, alpha)
            shadow_color = (0, 0, 0, alpha // 2)  # 影は半透明

            # スコアテキストを作成
            score_text = font.render(f"+{self.score}", True, fade_color[:3])
            shadow_text = font.render(f"+{self.score}", True, shadow_color[:3])

            # 透明度を適用するためのサーフェスを作成
            if alpha < 255:
                # 透明度付きサーフェスを作成
                text_surface = pygame.Surface(score_text.get_size(), pygame.SRCALPHA)
                shadow_surface = pygame.Surface(shadow_text.get_size(), pygame.SRCALPHA)

                text_surface.blit(score_text, (0, 0))
                shadow_surface.blit(shadow_text, (0, 0))

                text_surface.set_alpha(alpha)
                shadow_surface.set_alpha(alpha // 2)

                screen.blit(shadow_surface, (self.x + 2, self.y + 2))
                screen.blit(text_surface, (self.x, self.y))
            else:
                # 通常の描画
                screen.blit(shadow_text, (self.x + 2, self.y + 2))
                screen.blit(score_text, (self.x, self.y))


class Particle:
    """パーティクル効果用のクラス（強化版）"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.color = color

        # より派手な動きのパラメータ
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(50, 150)  # 速度を上げる
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(20, 60)  # 上向きの初速度

        # 重力と減衰
        self.gravity = 200  # 重力を強化
        self.friction = 0.98

        # 見た目の強化
        self.life = random.uniform(1.0, 2.0)  # 寿命を延長
        self.max_life = self.life
        self.size = random.uniform(3, 8)  # サイズをランダム化
        self.rotation = 0
        self.rotation_speed = random.uniform(-360, 360)  # 回転速度

    def update(self, dt):
        """パーティクルの更新（強化版）"""
        # 物理演算
        self.vx *= self.friction
        self.vy += self.gravity * dt

        self.x += self.vx * dt
        self.y += self.vy * dt

        # 回転
        self.rotation += self.rotation_speed * dt

        # 寿命の減少
        self.life -= dt

        return self.life > 0

    def draw(self, screen):
        """パーティクルの描画（強化版）"""
        try:
            if self.life > 0:
                # フェードアウト効果
                alpha_ratio = self.life / self.max_life

                # 色の計算（フェードアウト）
                if isinstance(self.color, list | tuple) and len(self.color) >= 3:
                    r, g, b = self.color[:3]
                else:
                    r, g, b = 255, 255, 255

                fade_color = (int(r * alpha_ratio), int(g * alpha_ratio), int(b * alpha_ratio))

                # サイズの変化（最初大きく、徐々に小さく）
                current_size = self.size * (0.5 + 0.5 * alpha_ratio)

                # 星形パーティクルを描画
                self._draw_star(screen, int(self.x), int(self.y), int(current_size), fade_color)
        except Exception:
            # エラー時は何もしない
            pass

    def _draw_star(self, screen, x, y, size, color):
        """星形パーティクルを描画"""
        try:
            # 簡単な星形（4つの線）
            points = []
            for i in range(8):
                angle = (i * math.pi / 4) + math.radians(self.rotation)
                if i % 2 == 0:
                    # 外側の点
                    px = x + math.cos(angle) * size
                    py = y + math.sin(angle) * size
                else:
                    # 内側の点
                    px = x + math.cos(angle) * size * 0.5
                    py = y + math.sin(angle) * size * 0.5
                points.append((px, py))

            # 星形を描画
            if len(points) >= 3:
                pygame.draw.polygon(screen, color, points)
            else:
                # フォールバック：円
                pygame.draw.circle(screen, color, (x, y), max(1, int(size)))

        except Exception:
            # エラー時のフォールバック：円
            with contextlib.suppress(Exception):
                pygame.draw.circle(screen, color, (x, y), max(1, int(size)))


class Block:
    def __init__(self, block_type, x, y, animate_spawn=False):
        self.type = block_type
        self.grid_x = x
        self.grid_y = y

        # 描画位置（アニメーション用）
        self.draw_x = x * CELL_SIZE
        self.draw_y = y * CELL_SIZE

        # アニメーション関連
        if animate_spawn:
            self.animation_type = AnimationType.SPAWN
            self.animation_progress = 0.0
            self.target_x = x * CELL_SIZE
            self.target_y = y * CELL_SIZE
            self.start_x = x * CELL_SIZE
            self.start_y = y * CELL_SIZE - CELL_SIZE  # 上から出現
        else:
            self.animation_type = AnimationType.NONE
            self.animation_progress = 1.0
            self.target_x = x * CELL_SIZE
            self.target_y = y * CELL_SIZE
            self.start_x = x * CELL_SIZE
            self.start_y = y * CELL_SIZE

        self.alpha = 255

    def get_colors(self):
        """グラデーション用の色を取得"""
        color_map = {
            BlockType.RED: COLORS["RED"],
            BlockType.BLUE: COLORS["BLUE"],
            BlockType.GREEN: COLORS["GREEN"],
            BlockType.YELLOW: COLORS["YELLOW"],
            BlockType.PURPLE: COLORS["PURPLE"],
            BlockType.ORANGE: COLORS["ORANGE"],
        }
        return color_map[self.type]

    def start_animation(self, anim_type, target_x=None, target_y=None):
        """アニメーションを開始"""
        self.animation_type = anim_type
        self.animation_progress = 0.0
        self.start_x = self.draw_x
        self.start_y = self.draw_y

        if target_x is not None:
            self.target_x = target_x * CELL_SIZE
        if target_y is not None:
            self.target_y = target_y * CELL_SIZE

    def update_animation(self, dt):
        """アニメーションを更新"""
        if self.animation_type == AnimationType.NONE:
            return True

        speed_map = {
            AnimationType.SWAP: SWAP_ANIMATION_SPEED,
            AnimationType.FALL: FALL_ANIMATION_SPEED,
            AnimationType.FADE: FADE_ANIMATION_SPEED,
            AnimationType.SPAWN: SWAP_ANIMATION_SPEED,
        }

        speed = speed_map.get(self.animation_type, SWAP_ANIMATION_SPEED)
        self.animation_progress += dt * speed

        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self.draw_x = self.target_x
            self.draw_y = self.target_y
            self.animation_type = AnimationType.NONE
            return True

        # イージング関数（スムーズな動き）
        t = self.animation_progress
        if self.animation_type == AnimationType.FALL:
            # 落下は重力を感じるイージング
            t = 1 - (1 - t) * (1 - t)
        else:
            # その他はスムーズなイージング
            t = t * t * (3 - 2 * t)

        # 位置を補間
        self.draw_x = self.start_x + (self.target_x - self.start_x) * t
        self.draw_y = self.start_y + (self.target_y - self.start_y) * t

        # フェードアニメーション
        if self.animation_type == AnimationType.FADE:
            self.alpha = int(255 * (1 - self.animation_progress))

        return False

    def draw_gradient_circle(self, screen, x, y, radius, colors, alpha=255):
        """グラデーション円を描画"""
        # メインの円
        main_color = colors[0]
        if alpha < 255:
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*main_color, alpha), (radius, radius), radius)
            screen.blit(surf, (x - radius, y - radius))
        else:
            pygame.draw.circle(screen, main_color, (int(x), int(y)), radius)

        # 内側のハイライト
        highlight_radius = int(radius * 0.7)
        highlight_color = [min(255, c + 50) for c in main_color]
        if alpha < 255:
            surf = pygame.Surface((highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                surf,
                (*highlight_color, alpha // 2),
                (highlight_radius, highlight_radius),
                highlight_radius,
            )
            screen.blit(surf, (x - highlight_radius, y - highlight_radius))
        else:
            pygame.draw.circle(screen, highlight_color, (int(x), int(y)), highlight_radius)

        # 光沢効果
        gloss_radius = int(radius * 0.3)
        gloss_x = x - radius * 0.3
        gloss_y = y - radius * 0.3
        gloss_alpha = alpha // 3 if alpha < 255 else 80
        if gloss_alpha > 0:
            surf = pygame.Surface((gloss_radius * 2, gloss_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                surf, (255, 255, 255, gloss_alpha), (gloss_radius, gloss_radius), gloss_radius
            )
            screen.blit(surf, (int(gloss_x - gloss_radius), int(gloss_y - gloss_radius)))


class Match3Game:
    def __init__(self, time_limit: int = 180):
        self.logger = logging.getLogger("Match3Game")
        self.logger.info("=== Amazon Q Match3 Game Starting ===")
        self.logger.info(f"Pygame version: {pygame.version.ver}")

        # Pygame初期化
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Amazon Q Match3 - Enhanced Edition")
        self.clock = pygame.time.Clock()

        # ハイスコア管理とメニューシステム
        self.highscore_manager = HighScoreManager()
        self.menu = GameMenu(self.screen, self.highscore_manager)

        # ゲーム状態
        self.reset_game(time_limit)

        # アニメーション関連
        self.animating = False
        self.particles = []
        self.score_popups = []  # スコアポップアップリスト
        self.dt = 0

        # 連鎖時の停止機能
        self.match_highlight_timer = 0.0
        self.highlighted_matches = []
        self.is_highlighting = False

        # ブロック落下前の待機機能
        self.drop_delay_timer = 0.0
        self.is_waiting_for_drop = False
        self.pending_drop = False

        # Fonts (English only, optimized sizes)
        try:
            # Try system fonts first with better sizes
            self.font = pygame.font.SysFont("arial,helvetica,sans-serif", 32)
            self.big_font = pygame.font.SysFont("arial,helvetica,sans-serif", 64)
            self.small_font = pygame.font.SysFont("arial,helvetica,sans-serif", 18)
            self.logger.info("System fonts loaded successfully")
        except Exception:
            # Fallback to default fonts with better sizes
            self.font = pygame.font.Font(None, 32)
            self.big_font = pygame.font.Font(None, 64)
            self.small_font = pygame.font.Font(None, 18)
            self.score_font = pygame.font.Font(None, 24)  # スコアポップアップ用
            self.logger.warning("Using default fonts")

        self.logger.info("Game initialization completed successfully")

    def reset_game(self, time_limit: int = 180):
        """ゲームをリセット"""
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.time_limit = time_limit
        self.time_left = time_limit
        self.selected_block = None
        self.game_over = False
        self.game_started = False
        self.pending_match_check = None

        # グリッドを初期化（ゲーム開始時のみ）
        if hasattr(self, "grid"):
            self.initialize_grid()

        self.logger.info(f"Game reset with {time_limit}s time limit")

    def initialize_grid(self):
        """グリッドを初期化（マッチしないように配置）"""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # 初期配置でマッチしないようにブロックタイプを選択
                valid_types = list(BlockType)

                # 左に2つ同じ色がある場合は除外
                if col >= 2 and (
                    self.grid[row][col - 1]
                    and self.grid[row][col - 2]
                    and self.grid[row][col - 1].type == self.grid[row][col - 2].type
                ):
                    valid_types.remove(self.grid[row][col - 1].type)

                # 上に2つ同じ色がある場合は除外
                if (
                    row >= 2
                    and (
                        self.grid[row - 1][col]
                        and self.grid[row - 2][col]
                        and self.grid[row - 1][col].type == self.grid[row - 2][col].type
                    )
                    and self.grid[row - 1][col].type in valid_types
                ):
                    valid_types.remove(self.grid[row - 1][col].type)

                block_type = random.choice(valid_types)
                self.grid[row][col] = Block(block_type, col, row)

    def draw_grid_only(self):
        """グリッドとブロックのみを描画（エフェクトは除く）"""
        self.logger.debug("Drawing grid only")

        # グリッドの背景を描画
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE

                # グリッドの枠を描画
                pygame.draw.rect(self.screen, UI_COLORS["GRAY"], (x, y, CELL_SIZE, CELL_SIZE), 2)

        # ブロックを描画
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid[row][col]:
                    self.grid[row][col].draw(self.screen)

        # 選択されたブロックのハイライト
        if self.selected_block:
            row, col = self.selected_block
            x = GRID_OFFSET_X + col * CELL_SIZE
            y = GRID_OFFSET_Y + row * CELL_SIZE
            pygame.draw.rect(self.screen, UI_COLORS["WHITE"], (x, y, CELL_SIZE, CELL_SIZE), 4)

        # 連鎖ハイライト（黄色の点滅）
        if self.is_highlighting and self.highlighted_matches:
            for row, col in self.highlighted_matches:
                x = GRID_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
                y = GRID_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2

                # 点滅効果
                alpha = int(128 + 127 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
                highlight_radius = CELL_SIZE // 3

                # 黄色の円でハイライト
                if alpha > 100:  # 一定の透明度以上の時のみ描画
                    try:
                        draw_x = x
                        draw_y = y
                        pygame.draw.circle(
                            self.screen,
                            UI_COLORS["WHITE"],
                            (int(draw_x), int(draw_y)),
                            highlight_radius,
                            3,
                        )
                    except Exception as e:
                        self.logger.warning(f"Error drawing highlight at ({row}, {col}): {e}")

    def draw_effects(self):
        """エフェクト（パーティクル、スコアポップアップ）を描画"""
        self.logger.debug("Drawing effects")

        # パーティクルを描画
        for particle in self.particles:
            particle.draw(self.screen)

        # スコアポップアップを描画
        for popup in self.score_popups:
            # score_fontの存在チェック
            font_to_use = getattr(self, "score_font", self.small_font)
            popup.draw(self.screen, font_to_use)

    def draw_grid(self):
        """グリッドとブロックを描画（アニメーション対応）"""
        self.logger.debug("Drawing grid")

        # グリッドの背景を描画
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE

                # グリッドの枠を描画
                pygame.draw.rect(self.screen, UI_COLORS["GRAY"], (x, y, CELL_SIZE, CELL_SIZE), 2)

        # ブロックを描画（アニメーション位置で）
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid[row][col]:
                    block = self.grid[row][col]

                    # アニメーション位置を計算
                    draw_x = GRID_OFFSET_X + block.draw_x + CELL_SIZE // 2
                    draw_y = GRID_OFFSET_Y + block.draw_y + CELL_SIZE // 2

                    # 選択されたブロックをハイライト
                    if self.selected_block == (row, col):
                        highlight_radius = CELL_SIZE // 2 + 4
                        pygame.draw.circle(
                            self.screen,
                            UI_COLORS["WHITE"],
                            (int(draw_x), int(draw_y)),
                            highlight_radius,
                            3,
                        )

                    # 連鎖ハイライト（点滅効果）
                    if self.is_highlighting and (row, col) in self.highlighted_matches:
                        # 点滅効果
                        flash_intensity = abs(math.sin(self.match_highlight_timer * 20)) * 0.5 + 0.5
                        highlight_color = (255, 255, 0)  # 黄色
                        highlight_radius = CELL_SIZE // 2 + 6

                        # 外側のリング
                        pygame.draw.circle(
                            self.screen,
                            highlight_color,
                            (int(draw_x), int(draw_y)),
                            highlight_radius,
                            int(4 * flash_intensity),
                        )

                        # 内側の光る効果
                        inner_radius = int(highlight_radius * 0.8 * flash_intensity)
                        if inner_radius > 0:
                            pygame.draw.circle(
                                self.screen,
                                (*highlight_color, int(100 * flash_intensity)),
                                (int(draw_x), int(draw_y)),
                                inner_radius,
                            )

                    # グラデーション円を描画
                    colors = block.get_colors()
                    radius = CELL_SIZE // 2 - 4
                    block.draw_gradient_circle(
                        self.screen, draw_x, draw_y, radius, colors, block.alpha
                    )

        # パーティクルを描画
        for particle in self.particles:
            particle.draw(self.screen)

        # スコアポップアップを描画
        for popup in self.score_popups:
            # score_fontの存在チェック
            font_to_use = getattr(self, "score_font", self.small_font)
            popup.draw(self.screen, font_to_use)

    def draw_ui(self):
        """Draw UI elements (Enhanced version with better time display)"""
        self.logger.info(f"Drawing UI elements - Score: {self.score}, Time: {self.time_left:.1f}")

        # Score display
        score_text = self.font.render(f"Score: {self.score}", True, UI_COLORS["WHITE"])
        self.screen.blit(score_text, (WINDOW_WIDTH - 200, 20))

        # Time remaining display (enhanced with better visibility)
        # ゲームオーバー時は時間を0に固定
        display_time = max(0, self.time_left) if not self.game_over else 0
        minutes = int(display_time) // 60
        seconds = int(display_time) % 60

        # Change color based on time remaining with more dramatic effects
        if display_time > 30:
            time_color = UI_COLORS["WHITE"]
            time_bg_color = None
        elif display_time > 10:
            time_color = UI_COLORS["YELLOW"]
            time_bg_color = (64, 64, 0)  # Dark yellow background
        else:
            time_color = UI_COLORS["RED"]
            time_bg_color = (64, 0, 0)  # Dark red background
            # Add blinking effect for critical time (but not when game over)
            if not self.game_over and int(time.time() * 2) % 2:  # Blink every 0.5 seconds
                time_color = UI_COLORS["WHITE"]

        # Create time text with background for better visibility
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        time_surface = self.font.render(time_text, True, time_color)

        self.logger.debug(f"Drawing time: {time_text} with color {time_color}")

        # Draw background for critical time
        if time_bg_color and not self.game_over:  # No background when game over
            time_rect = time_surface.get_rect()
            time_rect.topleft = (WINDOW_WIDTH - 200, 60)
            # Expand background slightly
            bg_rect = time_rect.inflate(10, 4)
            pygame.draw.rect(self.screen, time_bg_color, bg_rect)
            pygame.draw.rect(self.screen, time_color, bg_rect, 2)  # Border

        self.screen.blit(time_surface, (WINDOW_WIDTH - 200, 60))

        # Time limit mode display
        time_label = self._get_time_label(self.time_limit)
        mode_text = self.small_font.render(f"Mode: {time_label}", True, UI_COLORS["LIGHT_GRAY"])
        self.screen.blit(mode_text, (WINDOW_WIDTH - 200, 100))

        # Current best score display
        best_score = self.highscore_manager.get_best_score(self.time_limit)
        if best_score > 0:
            # 時間制限に応じた単位表示
            time_label = self._get_time_label(self.time_limit)
            best_text = self.small_font.render(
                f"Best ({time_label}): {best_score}", True, UI_COLORS["YELLOW"]
            )
            self.screen.blit(best_text, (WINDOW_WIDTH - 200, 120))

        # Progress bar for time remaining (visual indicator)
        progress_width = 180
        progress_height = 8
        progress_x = WINDOW_WIDTH - 200
        progress_y = 140  # 時間表示やベストスコアと重ならないように下に移動

        # Background bar
        pygame.draw.rect(
            self.screen,
            UI_COLORS["GRAY"],
            (progress_x, progress_y, progress_width, progress_height),
        )

        # Progress fill (0 when game over)
        progress_ratio = self.time_left / self.time_limit if not self.game_over else 0

        fill_width = int(progress_width * progress_ratio)

        # Color based on remaining time
        if progress_ratio > 0.5:
            progress_color = UI_COLORS["GREEN"]
        elif progress_ratio > 0.25:
            progress_color = UI_COLORS["YELLOW"]
        else:
            progress_color = UI_COLORS["RED"]

        if fill_width > 0:
            pygame.draw.rect(
                self.screen, progress_color, (progress_x, progress_y, fill_width, progress_height)
            )

        # Instructions
        help_text = self.small_font.render("Click blocks to swap", True, UI_COLORS["WHITE"])
        self.screen.blit(help_text, (20, WINDOW_HEIGHT - 60))

        # Menu hint
        menu_hint = self.small_font.render("ESC: Menu", True, UI_COLORS["LIGHT_GRAY"])
        self.screen.blit(menu_hint, (20, WINDOW_HEIGHT - 40))

    def get_grid_position(self, mouse_pos):
        """マウス座標をグリッド座標に変換"""
        x, y = mouse_pos
        col = (x - GRID_OFFSET_X) // CELL_SIZE
        row = (y - GRID_OFFSET_Y) // CELL_SIZE

        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return (row, col)
        return None

    def are_adjacent(self, pos1, pos2):
        """2つの位置が隣接しているかチェック"""
        row1, col1 = pos1
        row2, col2 = pos2
        return abs(row1 - row2) + abs(col1 - col2) == 1

    def swap_blocks(self, pos1, pos2, animate=True):
        """ブロックを交換（アニメーション対応版）"""
        row1, col1 = pos1
        row2, col2 = pos2

        block1 = self.grid[row1][col1]
        block2 = self.grid[row2][col2]

        if not block1 or not block2:
            return

        # ブロックを交換
        self.grid[row1][col1], self.grid[row2][col2] = block2, block1

        # グリッド座標を更新
        block1.grid_x, block1.grid_y = col2, row2
        block2.grid_x, block2.grid_y = col1, row1

        if animate:
            # アニメーションを開始
            block1.start_animation(AnimationType.SWAP, col2, row2)
            block2.start_animation(AnimationType.SWAP, col1, row1)
            self.logger.debug(f"Started swap animation: ({row1},{col1}) <-> ({row2},{col2})")
        else:
            # 即座に位置を更新
            block1.draw_x = col2 * CELL_SIZE
            block1.draw_y = row2 * CELL_SIZE
            block2.draw_x = col1 * CELL_SIZE
            block2.draw_y = row1 * CELL_SIZE

    def find_matches(self):
        """マッチするブロックを検出（ログ対応版）"""
        matches = set()
        horizontal_matches = 0
        vertical_matches = 0

        self.logger.debug("Starting match detection")

        # 横方向のマッチをチェック
        for row in range(GRID_SIZE):
            count = 1
            current_type = None
            start_col = 0

            for col in range(GRID_SIZE):
                if self.grid[row][col] and self.grid[row][col].type == current_type:
                    count += 1
                else:
                    if count >= 3 and current_type is not None:
                        # マッチを記録
                        match_positions = []
                        for c in range(start_col, col):
                            matches.add((row, c))
                            match_positions.append((row, c))
                        self.logger.debug(
                            f"Horizontal match found: {current_type.name} at {match_positions}"
                        )
                        horizontal_matches += 1

                    if self.grid[row][col]:
                        current_type = self.grid[row][col].type
                        start_col = col
                        count = 1
                    else:
                        current_type = None
                        count = 0

            # 行の最後でマッチチェック
            if count >= 3 and current_type is not None:
                match_positions = []
                for c in range(start_col, GRID_SIZE):
                    matches.add((row, c))
                    match_positions.append((row, c))
                self.logger.debug(
                    f"Horizontal match found (end of row): {current_type.name} at {match_positions}"
                )
                horizontal_matches += 1

        # 縦方向のマッチをチェック
        for col in range(GRID_SIZE):
            count = 1
            current_type = None
            start_row = 0

            for row in range(GRID_SIZE):
                if self.grid[row][col] and self.grid[row][col].type == current_type:
                    count += 1
                else:
                    if count >= 3 and current_type is not None:
                        # マッチを記録
                        match_positions = []
                        for r in range(start_row, row):
                            matches.add((r, col))
                            match_positions.append((r, col))
                        self.logger.debug(
                            f"Vertical match found: {current_type.name} at {match_positions}"
                        )
                        vertical_matches += 1

                    if self.grid[row][col]:
                        current_type = self.grid[row][col].type
                        start_row = row
                        count = 1
                    else:
                        current_type = None
                        count = 0

            # 列の最後でマッチチェック
            if count >= 3 and current_type is not None:
                match_positions = []
                for r in range(start_row, GRID_SIZE):
                    matches.add((r, col))
                    match_positions.append((r, col))
                self.logger.debug(
                    f"Vertical match found (end of column): {current_type.name} at {match_positions}"
                )
                vertical_matches += 1

        self.logger.debug(
            f"Match detection completed: {len(matches)} total matches "
            f"({horizontal_matches} horizontal, {vertical_matches} vertical)"
        )

        return matches

    def remove_matches(self, matches):
        """マッチしたブロックを削除してスコアを加算（強化版）"""
        if not matches:
            return False

        try:
            self.logger.info(f"Removing {len(matches)} matches: {matches}")

            # スコア計算
            match_count = len(matches)
            old_score = self.score
            score_gained = 0

            if match_count == 3:
                score_gained = 100
            elif match_count == 4:
                score_gained = 200
            elif match_count == 5:
                score_gained = 500
            else:
                score_gained = 100 * match_count

            self.score += score_gained

            self.logger.info(f"Score updated: {old_score} -> {self.score} (+{score_gained})")

            # マッチの中心位置を計算（スコア表示用）
            center_x = sum(col for row, col in matches) / len(matches)
            center_y = sum(row for row, col in matches) / len(matches)

            # スクリーン座標に変換
            screen_x = GRID_OFFSET_X + center_x * CELL_SIZE + CELL_SIZE // 2
            screen_y = GRID_OFFSET_Y + center_y * CELL_SIZE + CELL_SIZE // 2

            # スコアポップアップを作成
            score_popup = ScorePopup(screen_x, screen_y, score_gained)
            self.score_popups.append(score_popup)
            self.logger.info(
                f"Created score popup: +{score_gained} at ({screen_x}, {screen_y}), total popups: {len(self.score_popups)}"
            )

            # 安全にブロックを削除
            removed_count = 0
            for row, col in matches:
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    if self.grid[row][col]:
                        self.logger.debug(f"Removing block at ({row}, {col})")

                        # より派手なパーティクル効果を生成
                        try:
                            colors = self.grid[row][col].get_colors()
                            if colors and len(colors) > 0:
                                # パーティクル数を増やす
                                self.create_particles(col, row, colors, count=15)
                                self.logger.debug(f"Created particles for block at ({row}, {col})")
                        except Exception as e:
                            self.logger.warning(f"Particle creation failed for ({row}, {col}): {e}")

                        # ブロックを削除
                        self.grid[row][col] = None
                        removed_count += 1
                    else:
                        self.logger.warning(f"No block found at ({row}, {col})")
                else:
                    self.logger.error(f"Invalid coordinates ({row}, {col})")

            self.logger.info(f"Successfully removed {removed_count} blocks")

            # ブロック削除後、0.5秒待機してから落下開始
            self.drop_delay_timer = 0.5
            self.is_waiting_for_drop = True
            self.pending_drop = True

            return True

        except Exception as e:
            self.logger.error(f"Error in remove_matches: {e}", exc_info=True)
            return False

    def drop_blocks(self, animate=True):
        """ブロックを落下させる（アニメーション対応版）"""
        moved = False

        self.logger.debug("Starting block drop process")

        for col in range(GRID_SIZE):
            # 下から上に向かってチェック
            write_pos = GRID_SIZE - 1
            moves_in_column = 0

            for read_pos in range(GRID_SIZE - 1, -1, -1):
                if self.grid[read_pos][col] is not None:
                    if write_pos != read_pos:
                        # ブロックを移動
                        block = self.grid[read_pos][col]
                        block_type = block.type
                        self.logger.debug(
                            f"Moving block {block_type.name} from ({read_pos}, {col}) to ({write_pos}, {col})"
                        )

                        self.grid[write_pos][col] = block
                        self.grid[read_pos][col] = None

                        # グリッド座標を更新
                        block.grid_y = write_pos

                        if animate:
                            # 落下アニメーションを開始
                            block.start_animation(AnimationType.FALL, col, write_pos)
                        else:
                            # 即座に位置を更新
                            block.draw_y = write_pos * CELL_SIZE

                        moved = True
                        moves_in_column += 1
                    write_pos -= 1

            if moves_in_column > 0:
                self.logger.debug(f"Column {col}: moved {moves_in_column} blocks")

        self.logger.debug(f"Block drop completed. Any moves: {moved}")
        return moved

    def fill_empty_spaces(self, animate=True):
        """空いたスペースに新しいブロックを生成（アニメーション対応版）"""
        filled_count = 0

        self.logger.debug("Starting to fill empty spaces")

        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                if self.grid[row][col] is None:
                    block_type = random.choice(list(BlockType))
                    self.grid[row][col] = Block(block_type, col, row, animate_spawn=animate)
                    filled_count += 1
                    self.logger.debug(f"Created new {block_type.name} block at ({row}, {col})")

        self.logger.debug(f"Filled {filled_count} empty spaces")

    def process_matches_with_highlight(self):
        """マッチ処理（ハイライト機能付き）"""
        matches = self.find_matches()
        if not matches:
            return False

        # 連鎖時はハイライト表示
        if hasattr(self, "chain_count") and self.chain_count > 0:
            self.highlighted_matches = matches
            self.is_highlighting = True
            self.match_highlight_timer = 0.5  # 0.5秒間ハイライト
            return True
        # 初回マッチは即座に処理
        return self.remove_matches(matches)

    def update_drop_delay_timer(self, dt):
        """落下待機タイマーの更新"""
        if self.is_waiting_for_drop:
            self.drop_delay_timer -= dt
            if self.drop_delay_timer <= 0:
                # 待機終了、落下開始
                self.is_waiting_for_drop = False
                if self.pending_drop:
                    self.pending_drop = False
                    # ブロック落下と空スペース補充を実行
                    self.drop_blocks(animate=True)
                    self.fill_empty_spaces(animate=True)

                    # 落下完了後、新しいマッチがあるかチェック
                    # アニメーション完了後にチェックするため、フラグを設定
                    self.pending_cascade_check = True
                    return True
        return False

    def update_highlight_timer(self, dt):
        """ハイライトタイマーの更新"""
        if self.is_highlighting:
            self.match_highlight_timer -= dt
            if self.match_highlight_timer <= 0:
                # ハイライト終了、マッチを削除
                self.is_highlighting = False
                if self.highlighted_matches:
                    self.remove_matches(self.highlighted_matches)
                    self.highlighted_matches = []
                    return True
        return False

    def process_matches_complete_cycle(self):
        """マッチ処理の完全なサイクル（テスト用・待機なし）"""
        total_matches = 0
        iteration = 0

        try:
            self.logger.info("Starting complete match processing cycle")

            while True:
                iteration += 1
                self.logger.debug(f"Match processing iteration {iteration}")

                # 無限ループ防止
                if iteration > 10:
                    self.logger.warning(
                        f"Breaking match processing due to too many iterations ({iteration})"
                    )
                    break

                matches = self.find_matches()
                if not matches:
                    self.logger.debug("No more matches found")
                    break

                self.logger.info(f"Found {len(matches)} matches in iteration {iteration}")
                total_matches += len(matches)

                # 待機なしで即座に削除
                if not self._remove_matches_immediate(matches):
                    self.logger.error("remove_matches failed")
                    break

                self.logger.debug("Dropping blocks...")
                self.drop_blocks()

                self.logger.debug("Filling empty spaces...")
                self.fill_empty_spaces()

            self.logger.info(f"Complete match processing finished. Total matches: {total_matches}")
            return total_matches > 0

        except Exception as e:
            self.logger.error(f"Error in process_matches_complete_cycle: {e}", exc_info=True)
            return False

    def _remove_matches_immediate(self, matches):
        """マッチしたブロックを即座に削除（待機なし）"""
        if not matches:
            return False

        try:
            self.logger.info(f"Removing {len(matches)} matches immediately: {matches}")

            # スコア計算
            match_count = len(matches)
            old_score = self.score
            score_gained = 0

            if match_count == 3:
                score_gained = 100
            elif match_count == 4:
                score_gained = 200
            elif match_count == 5:
                score_gained = 500
            else:
                score_gained = 100 * match_count

            self.score += score_gained

            self.logger.info(f"Score updated: {old_score} -> {self.score} (+{score_gained})")

            # 安全にブロックを削除
            removed_count = 0
            for row, col in matches:
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    if self.grid[row][col]:
                        self.logger.debug(f"Removing block at ({row}, {col})")
                        self.grid[row][col] = None
                        removed_count += 1
                    else:
                        self.logger.warning(f"No block found at ({row}, {col})")
                else:
                    self.logger.error(f"Invalid coordinates ({row}, {col})")

            self.logger.info(f"Successfully removed {removed_count} blocks immediately")
            return True

        except Exception as e:
            self.logger.error(f"Error in _remove_matches_immediate: {e}", exc_info=True)
            return False

    def process_matches(self):
        """マッチ処理の完全なサイクル（待機機能対応版）"""
        total_matches = 0
        iteration = 0

        try:
            self.logger.info("Starting match processing cycle")

            while True:
                iteration += 1
                self.logger.debug(f"Match processing iteration {iteration}")

                # 無限ループ防止
                if iteration > 10:
                    self.logger.warning(
                        f"Breaking match processing due to too many iterations ({iteration})"
                    )
                    break

                matches = self.find_matches()
                if not matches:
                    self.logger.debug("No more matches found")
                    break

                self.logger.info(f"Found {len(matches)} matches in iteration {iteration}")
                total_matches += len(matches)

                if not self.remove_matches(matches):
                    self.logger.error("remove_matches failed")
                    break

                # remove_matchesで待機タイマーが設定されるため、
                # ここでは落下処理を行わない（待機タイマー終了後に自動実行される）
                self.logger.debug("Waiting for drop delay timer...")
                break  # 一度に一つのマッチセットのみ処理

            self.logger.info(f"Match processing completed. Total matches: {total_matches}")
            return total_matches > 0

        except Exception as e:
            self.logger.error(f"Error in process_matches: {e}", exc_info=True)
            return False

    def handle_click(self, mouse_pos):
        """マウスクリックを処理（ログ対応版）"""
        # アニメーション中は操作を無効化
        if self.animating:
            self.logger.debug("Click ignored - animation in progress")
            return

        grid_pos = self.get_grid_position(mouse_pos)
        if not grid_pos:
            self.logger.debug(f"Click outside grid: {mouse_pos}")
            return

        self.logger.debug(f"Grid click at {grid_pos}")

        if self.selected_block is None:
            # 最初のブロックを選択
            self.selected_block = grid_pos
            self.logger.debug(f"Selected first block: {grid_pos}")
        else:
            # 2番目のブロックを選択
            if grid_pos == self.selected_block:
                # 同じブロックをクリック - 選択解除
                self.selected_block = None
                self.logger.debug("Deselected block")
            elif self.are_adjacent(self.selected_block, grid_pos):
                # 隣接するブロック - 交換を試行
                self.logger.info(f"Attempting swap: {self.selected_block} <-> {grid_pos}")
                self.swap_blocks(self.selected_block, grid_pos, animate=True)

                # アニメーション完了後にマッチ処理を行うため、ここでは処理しない
                # 代わりにアニメーション完了を待つフラグを設定
                self.pending_match_check = (self.selected_block, grid_pos)
                self.selected_block = None
            else:
                # 隣接しないブロック - 新しい選択
                self.selected_block = grid_pos
                self.logger.debug(f"Selected new block: {grid_pos}")

    def run(self):
        """メインゲームループ（メニュー統合版）"""
        running = True
        frame_count = 0
        last_log_time = 0
        start_time = pygame.time.get_ticks() / 1000.0

        try:
            self.logger.info("Starting main game loop with menu system")

            while running:
                frame_count += 1
                dt = self.clock.tick(FPS) / 1000.0
                self.dt = dt

                # イベント処理
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.logger.info("Quit event received")
                        running = False
                    else:
                        # メニューまたはゲームのイベント処理
                        if self.menu.state == MenuState.PLAYING:
                            # ゲーム中のイベント処理
                            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                                self.logger.debug(f"Game mouse click at {event.pos}")
                                try:
                                    self.handle_click(event.pos)
                                except Exception as e:
                                    self.logger.error(f"Error in handle_click: {e}", exc_info=True)
                            elif event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_ESCAPE:
                                    # ESCキーでメニューに戻る
                                    self.logger.info("ESC pressed, returning to main menu")
                                    self.menu.set_state(MenuState.MAIN_MENU)
                        else:
                            # メニューのイベント処理
                            action = self.menu.handle_event(event)
                            if action:
                                running = self._handle_menu_action(action)

                # ゲーム更新（プレイ中のみ）
                if self.menu.state == MenuState.PLAYING and not self.game_over:
                    self._update_game(dt)

                # パーティクル更新（常時）
                self._update_particles(dt)

                # 定期ログ（プレイ中のみ）
                if self.menu.state == MenuState.PLAYING:
                    current_time = pygame.time.get_ticks() / 1000.0
                    if current_time - last_log_time > 5:
                        elapsed_time = current_time - start_time
                        self.logger.info(
                            f"Game status - Frame: {frame_count}, Score: {self.score}, "
                            f"Time left: {self.time_left:.1f}s, Elapsed: {elapsed_time:.1f}s, "
                            f"Particles: {len(self.particles)}, Game over: {self.game_over}"
                        )
                        last_log_time = current_time

                # 描画
                self._draw_game()
                pygame.display.flip()

            total_elapsed = (pygame.time.get_ticks() / 1000.0) - start_time
            self.logger.info(
                f"Game loop ended normally after {frame_count} frames ({total_elapsed:.1f}s elapsed)"
            )

        except Exception as e:
            self.logger.critical(
                f"Fatal error in main loop (frame {frame_count}): {e}", exc_info=True
            )
        finally:
            self.logger.info("Cleaning up and exiting...")
            pygame.quit()
            sys.exit()

    def _handle_menu_action(self, action: str) -> bool:
        """メニューアクションを処理"""
        if action == "quit":
            return False
        if action == "start_game":
            time_limit = self.menu.get_selected_time()
            self.reset_game(time_limit)
            self.initialize_grid()
            self.menu.set_state(MenuState.PLAYING)
            self.game_started = True
            self.logger.info(f"Starting new game with {time_limit}s time limit")
        elif action == "play_again":
            # 同じ時間設定でもう一度プレイ
            pass  # 時間選択画面に戻る
        elif action == "main_menu":
            self.menu.set_state(MenuState.MAIN_MENU)

        return True

    def _update_game(self, dt: float):
        """ゲーム状態を更新"""
        if not self.game_over:
            old_time = self.time_left
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.game_over = True
                self.logger.info(f"Game over due to time limit - Final score: {self.score}")
                # ゲームオーバー画面に移行
                self.menu.set_game_over(self.score, self.time_limit)

            # 時間の大幅な変化をログ
            if abs(old_time - self.time_left) > 1.0:
                self.logger.warning(
                    f"Large time change detected: {old_time:.2f} -> {self.time_left:.2f}"
                )

        # アニメーション更新
        self._update_animations(dt)

        # エフェクトの更新（ゲームオーバー後も継続）
        self._update_particles(dt)
        self._update_score_popups(dt)

    def _update_animations(self, dt: float):
        """すべてのブロックのアニメーションを更新"""
        any_animating = False

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid[row][col] and not self.grid[row][col].update_animation(dt):
                    any_animating = True

        # アニメーション状態の更新
        was_animating = self.animating
        self.animating = any_animating

        # アニメーション完了時の処理
        if was_animating and not self.animating:
            self._handle_animation_complete()

    def _handle_animation_complete(self):
        """アニメーション完了時の処理"""
        if self.pending_match_check:
            pos1, pos2 = self.pending_match_check
            self.pending_match_check = None

            # マッチをチェックして処理
            if not self.process_matches():
                # マッチしなかった場合は元に戻す
                self.logger.info("No matches found, reverting swap")
                self.swap_blocks(pos1, pos2, animate=True)
            else:
                self.logger.info("Matches found and processed")
                # 連鎖処理を開始
                self._start_cascade_processing()

        # 連鎖チェック処理
        self._handle_cascade_check()

    def _start_cascade_processing(self):
        """連鎖処理を開始"""
        # ブロックを落下させる
        if self.drop_blocks(animate=True):
            # 空いたスペースを埋める
            self.fill_empty_spaces(animate=True)
            # アニメーション完了後に再度マッチチェックが必要
            self.pending_cascade_check = True
        else:
            # 落下がない場合は空いたスペースのみ埋める
            self.fill_empty_spaces(animate=True)

    def _handle_cascade_check(self):
        """連鎖チェック処理"""
        if hasattr(self, "pending_cascade_check") and self.pending_cascade_check:
            self.pending_cascade_check = False
            # 新しいマッチがあるかチェック
            if self.process_matches():
                # 新しいマッチがあれば連鎖を続ける
                self._start_cascade_processing()

    def _get_time_label(self, time_limit: int) -> str:
        """時間制限に応じたラベルを取得"""
        time_labels = {30: "30s", 60: "1min", 180: "3min"}
        return time_labels.get(time_limit, f"{time_limit}s")

    def _update_score_popups(self, dt):
        """スコアポップアップの更新"""
        try:
            old_count = len(self.score_popups)
            if old_count > 0:
                self.logger.info(f"Updating {old_count} score popups with dt={dt:.3f}")

            # 各ポップアップを更新し、生きているものだけを残す
            updated_popups = []
            for i, popup in enumerate(self.score_popups):
                old_life = popup.life
                still_alive = popup.update(dt)
                self.logger.info(
                    f"Popup {i}: life {old_life:.3f} -> {popup.life:.3f}, alive: {still_alive}"
                )
                if still_alive:
                    updated_popups.append(popup)

            self.score_popups = updated_popups
            new_count = len(self.score_popups)

            if old_count != new_count:
                self.logger.info(f"Score popups updated: {old_count} -> {new_count}")
        except Exception as e:
            self.logger.warning(f"Error updating score popups: {e}")
            self.score_popups = []

    def _update_particles(self, dt: float):
        """パーティクルを更新"""
        try:
            old_particle_count = len(self.particles)
            self.particles = [p for p in self.particles if p.update(dt)]
            if old_particle_count != len(self.particles) and old_particle_count > 0:
                self.logger.debug(
                    f"Particles updated: {old_particle_count} -> {len(self.particles)}"
                )
        except Exception as e:
            self.logger.warning(f"Error updating particles: {e}")
            self.particles = []

    def _draw_game(self):
        """ゲーム画面を描画"""
        try:
            self.logger.info(
                f"Drawing game, menu state: {self.menu.state}, game_over: {self.game_over}"
            )

            if self.menu.state == MenuState.PLAYING:
                self.logger.info("Drawing PLAYING screen")
                # ゲーム画面を描画
                self.screen.fill(UI_COLORS["BLACK"])

                # 1. グリッドとブロックを描画
                self.draw_grid()

                # 2. UIを描画
                self.draw_ui()

                # ゲームオーバー表示
                if self.game_over:
                    self.logger.info("Game is over but still in PLAYING state")
                    # ゲームオーバー時でもUIを表示し続ける
                    # メニューシステムがゲームオーバー画面を処理
            elif self.menu.state == MenuState.GAME_OVER:
                # ゲームオーバー画面でも基本UIを表示
                self.logger.info("Drawing GAME_OVER screen with UI")
                self.screen.fill(UI_COLORS["BLACK"])

                # グリッドとブロックを薄く表示
                self.draw_grid()

                # UIを表示（時間は0:00で固定）
                self.draw_ui()

                # メニューシステムがゲームオーバー画面を上に描画
                self.menu.draw()
            else:
                self.logger.info(f"Drawing menu screen for state: {self.menu.state}")
                # メニュー画面を描画
                self.menu.draw()

        except Exception as e:
            self.logger.error(f"Error in drawing: {e}", exc_info=True)

    def update_animations(self, dt):
        """アニメーションを更新"""
        any_animating = False

        # ブロックアニメーションを更新
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid[row][col] and not self.grid[row][col].update_animation(dt):
                    any_animating = True

        # 落下待機タイマーを更新
        self.update_drop_delay_timer(dt)

        # ハイライトタイマーを更新
        if self.update_highlight_timer(dt) and not self.is_waiting_for_drop:
            # ハイライト終了後の処理（落下待機タイマーが設定されていない場合のみ）
            self.drop_blocks(animate=True)
            self.fill_empty_spaces(animate=True)

        # アニメーション状態を更新
        was_animating = self.animating
        self.animating = any_animating

        # アニメーション完了時の処理
        if was_animating and not self.animating:
            self.on_animation_complete()

    def on_animation_complete(self):
        """アニメーション完了時の処理（簡素版）"""
        # 現在は何もしない（安定性のため）

    def create_particles(self, x, y, colors, count=PARTICLE_COUNT):
        """パーティクルを生成（ログ対応版）"""
        try:
            screen_x = GRID_OFFSET_X + x * CELL_SIZE + CELL_SIZE // 2
            screen_y = GRID_OFFSET_Y + y * CELL_SIZE + CELL_SIZE // 2

            # 色の安全な取得
            if isinstance(colors, list | tuple) and len(colors) > 0:
                if isinstance(colors[0], list | tuple) and len(colors[0]) >= 3:
                    particle_color = colors[0][:3]  # RGB値のみ取得
                else:
                    particle_color = (255, 255, 255)  # デフォルト色
            else:
                particle_color = (255, 255, 255)  # デフォルト色

            created_count = 0
            for _ in range(count):
                try:
                    particle = Particle(screen_x, screen_y, particle_color)
                    self.particles.append(particle)
                    created_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to create individual particle: {e}")

            self.logger.debug(f"Created {created_count}/{count} particles at ({x}, {y})")

        except Exception as e:
            self.logger.warning(f"Failed to create particles at ({x}, {y}): {e}")


def main():
    """Main execution function (complete integration)"""
    print("=== Amazon Q Match3 Enhanced Edition ===")
    print("Features:")
    print("- Time limit selection (30s/1min/3min)")
    print("- High score recording & display")
    print("- Game restart functionality")
    print("- ESC key to return to menu")
    print("- Comprehensive logging")
    print("=" * 40)

    # Initialize logging system (integrated version)
    try:
        from logging_config import setup_logging

        setup_logging(
            level=logging.INFO,
            log_to_file=True,
            log_to_console=False,  # Disable console output
        )
        logger = logging.getLogger("Match3GameRunner")
        logger.info("Starting Amazon Q Match3 Enhanced Edition with integrated logging")
        print("Logging enabled. Detailed logs will be recorded in amazon_q_match3.log")
    except ImportError:
        # Fallback when logging config is not available
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("amazon_q_match3.log", encoding="utf-8"),
            ],
        )
        logger = logging.getLogger("Match3GameRunner")
        logger.info("Starting Amazon Q Match3 (fallback logging)")
        print("Basic logging enabled.")

    try:
        game = Match3Game()
        game.run()

    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
        print("\nGame terminated.")
    except Exception as e:
        logger.error(f"Game crashed: {e}", exc_info=True)
        print(f"\nGame error occurred: {e}")
        print("Check the log file (amazon_q_match3.log) for details.")
    finally:
        logger.info("Game session ended")


if __name__ == "__main__":
    main()
