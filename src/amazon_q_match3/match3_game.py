import pygame
import random
import sys
from enum import Enum

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

import pygame
import random
import sys
import math
import logging
from enum import Enum
from pathlib import Path

# ログ設定をインポート
sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from logging_config import setup_logging, get_game_logger
    # ログシステムを初期化（INFO レベル、ファイルとコンソール両方に出力）
    setup_logging(level=logging.INFO, log_to_file=True, log_to_console=False)
    logger = get_game_logger()
except ImportError:
    # フォールバック設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('amazon_q_match3.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger('Match3Game')

# 新しいモジュールをインポート
from highscore_manager import HighScoreManager
from game_menu import GameMenu, MenuState

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

# アニメーション定数
SWAP_ANIMATION_SPEED = 8.0
FALL_ANIMATION_SPEED = 12.0
FADE_ANIMATION_SPEED = 5.0
PARTICLE_COUNT = 8

# 色定義（グラデーション用）
COLORS = {
    'RED': [(255, 100, 100), (200, 50, 50)],
    'BLUE': [(100, 150, 255), (50, 100, 200)],
    'GREEN': [(100, 255, 100), (50, 200, 50)],
    'YELLOW': [(255, 255, 100), (200, 200, 50)],
    'PURPLE': [(255, 100, 255), (200, 50, 200)],
    'ORANGE': [(255, 165, 0), (200, 120, 0)],
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'GRAY': (128, 128, 128)
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

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = 1.0
        self.color = color
        self.size = random.uniform(2, 4)
    
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.2  # 重力
        self.life -= dt * 2
        return self.life > 0
    
    def draw(self, screen):
        """パーティクルを描画（安全版）"""
        try:
            if self.life > 0:
                alpha = max(0, min(255, int(self.life * 255)))
                size = max(1, int(self.size * self.life))
                
                if size > 0 and alpha > 0:
                    # 安全な色の処理
                    if isinstance(self.color, (list, tuple)) and len(self.color) >= 3:
                        color_rgb = self.color[:3]
                    else:
                        color_rgb = (255, 255, 255)
                    
                    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*color_rgb, alpha), (size, size), size)
                    screen.blit(surf, (int(self.x - size), int(self.y - size)))
        except Exception:
            pass  # 描画エラーは無視

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
            BlockType.RED: COLORS['RED'],
            BlockType.BLUE: COLORS['BLUE'],
            BlockType.GREEN: COLORS['GREEN'],
            BlockType.YELLOW: COLORS['YELLOW'],
            BlockType.PURPLE: COLORS['PURPLE'],
            BlockType.ORANGE: COLORS['ORANGE']
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
            AnimationType.SPAWN: SWAP_ANIMATION_SPEED
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
            pygame.draw.circle(surf, (*highlight_color, alpha // 2), (highlight_radius, highlight_radius), highlight_radius)
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
            pygame.draw.circle(surf, (255, 255, 255, gloss_alpha), (gloss_radius, gloss_radius), gloss_radius)
            screen.blit(surf, (int(gloss_x - gloss_radius), int(gloss_y - gloss_radius)))

class Match3Game:
    def __init__(self, time_limit: int = 180):
        self.logger = logging.getLogger('Match3Game')
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
        self.dt = 0
        
        # Fonts (English only, optimized sizes)
        try:
            # Try system fonts first with better sizes
            self.font = pygame.font.SysFont('arial,helvetica,sans-serif', 32)
            self.big_font = pygame.font.SysFont('arial,helvetica,sans-serif', 64)
            self.small_font = pygame.font.SysFont('arial,helvetica,sans-serif', 18)
            self.logger.info("System fonts loaded successfully")
        except:
            # Fallback to default fonts with better sizes
            self.font = pygame.font.Font(None, 32)
            self.big_font = pygame.font.Font(None, 64)
            self.small_font = pygame.font.Font(None, 18)
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
        
        # グリッドを初期化（ゲーム開始時のみ）
        if hasattr(self, 'grid'):
            self.initialize_grid()
        
        self.logger.info(f"Game reset with {time_limit}s time limit")
        
    def initialize_grid(self):
        """グリッドを初期化（マッチしないように配置）"""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # 初期配置でマッチしないようにブロックタイプを選択
                valid_types = list(BlockType)
                
                # 左に2つ同じ色がある場合は除外
                if col >= 2:
                    if (self.grid[row][col-1] and self.grid[row][col-2] and 
                        self.grid[row][col-1].type == self.grid[row][col-2].type):
                        valid_types.remove(self.grid[row][col-1].type)
                
                # 上に2つ同じ色がある場合は除外
                if row >= 2:
                    if (self.grid[row-1][col] and self.grid[row-2][col] and 
                        self.grid[row-1][col].type == self.grid[row-2][col].type):
                        if self.grid[row-1][col].type in valid_types:
                            valid_types.remove(self.grid[row-1][col].type)
                
                block_type = random.choice(valid_types)
                self.grid[row][col] = Block(block_type, col, row)
    
    def draw_grid(self):
        """グリッドとブロックを描画（アニメーション対応）"""
        # グリッドの背景を描画
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE
                
                # グリッドの枠を描画
                pygame.draw.rect(self.screen, COLORS['GRAY'], 
                               (x, y, CELL_SIZE, CELL_SIZE), 2)
        
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
                        pygame.draw.circle(self.screen, COLORS['WHITE'], 
                                         (int(draw_x), int(draw_y)), highlight_radius, 3)
                    
                    # グラデーション円を描画
                    colors = block.get_colors()
                    radius = CELL_SIZE // 2 - 4
                    block.draw_gradient_circle(self.screen, draw_x, draw_y, radius, colors, block.alpha)
        
        # パーティクルを描画
        for particle in self.particles:
            particle.draw(self.screen)
    
    def draw_ui(self):
        """Draw UI elements (English version)"""
        # Score display
        score_text = self.font.render(f"Score: {self.score}", True, COLORS['WHITE'])
        self.screen.blit(score_text, (WINDOW_WIDTH - 200, 20))
        
        # Time remaining display (color-coded)
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        
        # Change color based on time remaining
        if self.time_left > 30:
            time_color = COLORS['WHITE']
        elif self.time_left > 10:
            time_color = COLORS['YELLOW']
        else:
            time_color = COLORS['RED']
        
        time_text = self.font.render(f"Time: {minutes:02d}:{seconds:02d}", True, time_color)
        self.screen.blit(time_text, (WINDOW_WIDTH - 200, 60))
        
        # Time limit mode display
        mode_text = self.small_font.render(f"Mode: {self.time_limit}s", True, COLORS['LIGHT_GRAY'])
        self.screen.blit(mode_text, (WINDOW_WIDTH - 200, 100))
        
        # Current best score display
        best_score = self.highscore_manager.get_best_score(self.time_limit)
        if best_score > 0:
            best_text = self.small_font.render(f"Best: {best_score}", True, COLORS['YELLOW'])
            self.screen.blit(best_text, (WINDOW_WIDTH - 200, 120))
        
        # Instructions
        help_text = self.small_font.render("Click blocks to swap", True, COLORS['WHITE'])
        self.screen.blit(help_text, (20, WINDOW_HEIGHT - 60))
        
        # Menu hint
        menu_hint = self.small_font.render("ESC: Menu", True, COLORS['LIGHT_GRAY'])
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
    
    def swap_blocks(self, pos1, pos2):
        """ブロックを交換（簡素版）"""
        row1, col1 = pos1
        row2, col2 = pos2
        
        # ブロックを交換
        self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]
        
        # グリッド座標を更新
        if self.grid[row1][col1]:
            self.grid[row1][col1].grid_x, self.grid[row1][col1].grid_y = col1, row1
            self.grid[row1][col1].draw_x = col1 * CELL_SIZE
            self.grid[row1][col1].draw_y = row1 * CELL_SIZE
        if self.grid[row2][col2]:
            self.grid[row2][col2].grid_x, self.grid[row2][col2].grid_y = col2, row2
            self.grid[row2][col2].draw_x = col2 * CELL_SIZE
            self.grid[row2][col2].draw_y = row2 * CELL_SIZE
    
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
                        self.logger.debug(f"Horizontal match found: {current_type.name} at {match_positions}")
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
                self.logger.debug(f"Horizontal match found (end of row): {current_type.name} at {match_positions}")
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
                        self.logger.debug(f"Vertical match found: {current_type.name} at {match_positions}")
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
                self.logger.debug(f"Vertical match found (end of column): {current_type.name} at {match_positions}")
                vertical_matches += 1
        
        self.logger.debug(f"Match detection completed: {len(matches)} total matches "
                         f"({horizontal_matches} horizontal, {vertical_matches} vertical)")
        
        return matches
    
    def remove_matches(self, matches):
        """マッチしたブロックを削除してスコアを加算（ログ対応版）"""
        if not matches:
            return False
        
        try:
            self.logger.info(f"Removing {len(matches)} matches: {matches}")
            
            # スコア計算
            match_count = len(matches)
            old_score = self.score
            if match_count == 3:
                self.score += 100
            elif match_count == 4:
                self.score += 200
            elif match_count == 5:
                self.score += 500
            else:
                self.score += 100 * match_count
            
            self.logger.info(f"Score updated: {old_score} -> {self.score} (+{self.score - old_score})")
            
            # 安全にブロックを削除
            removed_count = 0
            for row, col in matches:
                if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                    if self.grid[row][col]:
                        self.logger.debug(f"Removing block at ({row}, {col})")
                        
                        # パーティクル効果を生成（安全版）
                        try:
                            colors = self.grid[row][col].get_colors()
                            if colors and len(colors) > 0:
                                self.create_particles(col, row, colors)
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
            return True
            
        except Exception as e:
            self.logger.error(f"Error in remove_matches: {e}", exc_info=True)
            return False
    
    def drop_blocks(self):
        """ブロックを落下させる（ログ対応版）"""
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
                        block_type = self.grid[read_pos][col].type
                        self.logger.debug(f"Moving block {block_type.name} from ({read_pos}, {col}) to ({write_pos}, {col})")
                        
                        self.grid[write_pos][col] = self.grid[read_pos][col]
                        self.grid[read_pos][col] = None
                        
                        # グリッド座標と描画位置を更新
                        self.grid[write_pos][col].grid_y = write_pos
                        self.grid[write_pos][col].draw_y = write_pos * CELL_SIZE
                        moved = True
                        moves_in_column += 1
                    write_pos -= 1
            
            if moves_in_column > 0:
                self.logger.debug(f"Column {col}: moved {moves_in_column} blocks")
        
        self.logger.debug(f"Block drop completed. Any moves: {moved}")
        return moved
    
    def fill_empty_spaces(self):
        """空いたスペースに新しいブロックを生成（ログ対応版）"""
        filled_count = 0
        
        self.logger.debug("Starting to fill empty spaces")
        
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                if self.grid[row][col] is None:
                    block_type = random.choice(list(BlockType))
                    self.grid[row][col] = Block(block_type, col, row, animate_spawn=False)
                    filled_count += 1
                    self.logger.debug(f"Created new {block_type.name} block at ({row}, {col})")
        
        self.logger.debug(f"Filled {filled_count} empty spaces")
    
    def process_matches(self):
        """マッチ処理の完全なサイクル（ログ対応版）"""
        total_matches = 0
        iteration = 0
        
        try:
            self.logger.info("Starting match processing cycle")
            
            while True:
                iteration += 1
                self.logger.debug(f"Match processing iteration {iteration}")
                
                # 無限ループ防止
                if iteration > 10:
                    self.logger.warning(f"Breaking match processing due to too many iterations ({iteration})")
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
                
                self.logger.debug("Dropping blocks...")
                self.drop_blocks()
                
                self.logger.debug("Filling empty spaces...")
                self.fill_empty_spaces()
            
            self.logger.info(f"Match processing completed. Total matches: {total_matches}, Iterations: {iteration}")
            return total_matches > 0
            
        except Exception as e:
            self.logger.error(f"Error in process_matches: {e}", exc_info=True)
            return False
    
    def handle_click(self, mouse_pos):
        """マウスクリックを処理（ログ対応版）"""
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
                self.swap_blocks(self.selected_block, grid_pos)
                
                # マッチをチェックして処理（同期処理）
                if not self.process_matches():
                    # マッチしなかった場合は元に戻す
                    self.logger.info("No matches found, reverting swap")
                    self.swap_blocks(self.selected_block, grid_pos)
                else:
                    self.logger.info("Matches found and processed")
                
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
                        self.logger.info(f"Game status - Frame: {frame_count}, Score: {self.score}, "
                                       f"Time left: {self.time_left:.1f}s, Elapsed: {elapsed_time:.1f}s, "
                                       f"Particles: {len(self.particles)}, Game over: {self.game_over}")
                        last_log_time = current_time
                
                # 描画
                self._draw_game()
                pygame.display.flip()
            
            total_elapsed = (pygame.time.get_ticks() / 1000.0) - start_time
            self.logger.info(f"Game loop ended normally after {frame_count} frames ({total_elapsed:.1f}s elapsed)")
            
        except Exception as e:
            self.logger.critical(f"Fatal error in main loop (frame {frame_count}): {e}", exc_info=True)
        finally:
            self.logger.info("Cleaning up and exiting...")
            pygame.quit()
            sys.exit()
    
    def _handle_menu_action(self, action: str) -> bool:
        """メニューアクションを処理"""
        if action == 'quit':
            return False
        elif action == 'start_game':
            time_limit = self.menu.get_selected_time()
            self.reset_game(time_limit)
            self.initialize_grid()
            self.menu.set_state(MenuState.PLAYING)
            self.game_started = True
            self.logger.info(f"Starting new game with {time_limit}s time limit")
        elif action == 'play_again':
            # 同じ時間設定でもう一度プレイ
            pass  # 時間選択画面に戻る
        elif action == 'main_menu':
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
                self.logger.warning(f"Large time change detected: {old_time:.2f} -> {self.time_left:.2f}")
    
    def _update_particles(self, dt: float):
        """パーティクルを更新"""
        try:
            old_particle_count = len(self.particles)
            self.particles = [p for p in self.particles if p.update(dt)]
            if old_particle_count != len(self.particles) and old_particle_count > 0:
                self.logger.debug(f"Particles updated: {old_particle_count} -> {len(self.particles)}")
        except Exception as e:
            self.logger.warning(f"Error updating particles: {e}")
            self.particles = []
    
    def _draw_game(self):
        """ゲーム画面を描画"""
        try:
            if self.menu.state == MenuState.PLAYING:
                # ゲーム画面を描画
                self.screen.fill(COLORS['BLACK'])
                self.draw_grid()
                self.draw_ui()
                
                # ゲームオーバー表示
                if self.game_over:
                    # メニューシステムがゲームオーバー画面を処理するので、
                    # ここでは簡単な表示のみ
                    pass
            else:
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
                if self.grid[row][col]:
                    if not self.grid[row][col].update_animation(dt):
                        any_animating = True
        
        # パーティクルを更新
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # アニメーション状態を更新
        was_animating = self.animating
        self.animating = any_animating
        
        # アニメーション完了時の処理
        if was_animating and not self.animating:
            self.on_animation_complete()
    
    def on_animation_complete(self):
        """アニメーション完了時の処理（簡素版）"""
        # 現在は何もしない（安定性のため）
        pass
    
    def create_particles(self, x, y, colors, count=PARTICLE_COUNT):
        """パーティクルを生成（ログ対応版）"""
        try:
            screen_x = GRID_OFFSET_X + x * CELL_SIZE + CELL_SIZE // 2
            screen_y = GRID_OFFSET_Y + y * CELL_SIZE + CELL_SIZE // 2
            
            # 色の安全な取得
            if isinstance(colors, (list, tuple)) and len(colors) > 0:
                if isinstance(colors[0], (list, tuple)) and len(colors[0]) >= 3:
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
            log_to_console=False  # Disable console output
        )
        logger = logging.getLogger('Match3GameRunner')
        logger.info("Starting Amazon Q Match3 Enhanced Edition with integrated logging")
        print("Logging enabled. Detailed logs will be recorded in amazon_q_match3.log")
    except ImportError:
        # Fallback when logging config is not available
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('amazon_q_match3.log', encoding='utf-8'),
            ]
        )
        logger = logging.getLogger('Match3GameRunner')
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
