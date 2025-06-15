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

# 色定義
COLORS = {
    'RED': (255, 100, 100),
    'BLUE': (100, 100, 255),
    'GREEN': (100, 255, 100),
    'YELLOW': (255, 255, 100),
    'PURPLE': (255, 100, 255),
    'ORANGE': (255, 165, 0),
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

class Block:
    def __init__(self, block_type, x, y):
        self.type = block_type
        self.x = x
        self.y = y
        self.falling = False
        self.fall_speed = 0
        
    def get_color(self):
        color_map = {
            BlockType.RED: COLORS['RED'],
            BlockType.BLUE: COLORS['BLUE'],
            BlockType.GREEN: COLORS['GREEN'],
            BlockType.YELLOW: COLORS['YELLOW'],
            BlockType.PURPLE: COLORS['PURPLE'],
            BlockType.ORANGE: COLORS['ORANGE']
        }
        return color_map[self.type]

class Match3Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Match 3 Puzzle Game")
        self.clock = pygame.time.Clock()
        
        # ゲーム状態
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.time_left = 180  # 3分 = 180秒
        self.selected_block = None
        self.game_over = False
        
        # フォント
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        # ゲーム初期化
        self.initialize_grid()
        
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
        """グリッドとブロックを描画"""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = GRID_OFFSET_X + col * CELL_SIZE
                y = GRID_OFFSET_Y + row * CELL_SIZE
                
                # グリッドの枠を描画
                pygame.draw.rect(self.screen, COLORS['GRAY'], 
                               (x, y, CELL_SIZE, CELL_SIZE), 2)
                
                # ブロックを描画
                if self.grid[row][col]:
                    block = self.grid[row][col]
                    color = block.get_color()
                    
                    # 選択されたブロックをハイライト
                    if self.selected_block == (row, col):
                        pygame.draw.rect(self.screen, COLORS['WHITE'], 
                                       (x-2, y-2, CELL_SIZE+4, CELL_SIZE+4))
                    
                    pygame.draw.rect(self.screen, color, 
                                   (x+2, y+2, CELL_SIZE-4, CELL_SIZE-4))
    
    def draw_ui(self):
        """UI要素を描画"""
        # スコア表示
        score_text = self.font.render(f"Score: {self.score}", True, COLORS['WHITE'])
        self.screen.blit(score_text, (WINDOW_WIDTH - 200, 20))
        
        # 残り時間表示
        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        time_text = self.font.render(f"Time: {minutes:02d}:{seconds:02d}", True, COLORS['WHITE'])
        self.screen.blit(time_text, (WINDOW_WIDTH - 200, 60))
        
        # 操作説明
        help_text = self.font.render("Click blocks to swap", True, COLORS['WHITE'])
        self.screen.blit(help_text, (20, WINDOW_HEIGHT - 40))
    
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
        """ブロックを交換"""
        row1, col1 = pos1
        row2, col2 = pos2
        self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]
        
        # 座標を更新
        if self.grid[row1][col1]:
            self.grid[row1][col1].x, self.grid[row1][col1].y = col1, row1
        if self.grid[row2][col2]:
            self.grid[row2][col2].x, self.grid[row2][col2].y = col2, row2
    
    def find_matches(self):
        """マッチするブロックを検出"""
        matches = set()
        
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
                        for c in range(start_col, col):
                            matches.add((row, c))
                    
                    if self.grid[row][col]:
                        current_type = self.grid[row][col].type
                        start_col = col
                        count = 1
                    else:
                        current_type = None
                        count = 0
            
            # 行の最後でマッチチェック
            if count >= 3 and current_type is not None:
                for c in range(start_col, GRID_SIZE):
                    matches.add((row, c))
        
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
                        for r in range(start_row, row):
                            matches.add((r, col))
                    
                    if self.grid[row][col]:
                        current_type = self.grid[row][col].type
                        start_row = row
                        count = 1
                    else:
                        current_type = None
                        count = 0
            
            # 列の最後でマッチチェック
            if count >= 3 and current_type is not None:
                for r in range(start_row, GRID_SIZE):
                    matches.add((r, col))
        
        return matches
    
    def remove_matches(self, matches):
        """マッチしたブロックを削除してスコアを加算"""
        if not matches:
            return False
        
        # スコア計算
        match_count = len(matches)
        if match_count == 3:
            self.score += 100
        elif match_count == 4:
            self.score += 200
        elif match_count == 5:
            self.score += 500
        else:
            self.score += 100 * match_count
        
        # ブロックを削除
        for row, col in matches:
            self.grid[row][col] = None
        
        return True
    
    def drop_blocks(self):
        """ブロックを落下させる"""
        moved = False
        
        for col in range(GRID_SIZE):
            # 下から上に向かってチェック
            write_pos = GRID_SIZE - 1
            
            for read_pos in range(GRID_SIZE - 1, -1, -1):
                if self.grid[read_pos][col] is not None:
                    if write_pos != read_pos:
                        self.grid[write_pos][col] = self.grid[read_pos][col]
                        self.grid[read_pos][col] = None
                        # 座標を更新
                        self.grid[write_pos][col].y = write_pos
                        moved = True
                    write_pos -= 1
        
        return moved
    
    def fill_empty_spaces(self):
        """空いたスペースに新しいブロックを生成"""
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                if self.grid[row][col] is None:
                    block_type = random.choice(list(BlockType))
                    self.grid[row][col] = Block(block_type, col, row)
    
    def process_matches(self):
        """マッチ処理の完全なサイクル"""
        total_matches = 0
        
        while True:
            matches = self.find_matches()
            if not matches:
                break
            
            total_matches += len(matches)
            self.remove_matches(matches)
            self.drop_blocks()
            self.fill_empty_spaces()
        
        return total_matches > 0
    
    def handle_click(self, mouse_pos):
        """マウスクリックを処理"""
        grid_pos = self.get_grid_position(mouse_pos)
        if not grid_pos:
            return
        
        if self.selected_block is None:
            # 最初のブロックを選択
            self.selected_block = grid_pos
        else:
            # 2番目のブロックを選択
            if grid_pos == self.selected_block:
                # 同じブロックをクリック - 選択解除
                self.selected_block = None
            elif self.are_adjacent(self.selected_block, grid_pos):
                # 隣接するブロック - 交換を試行
                self.swap_blocks(self.selected_block, grid_pos)
                
                # マッチをチェックして処理
                if not self.process_matches():
                    # マッチしなかった場合は元に戻す
                    self.swap_blocks(self.selected_block, grid_pos)
                
                self.selected_block = None
            else:
                # 隣接しないブロック - 新しい選択
                self.selected_block = grid_pos
    
    def run(self):
        """メインゲームループ"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # デルタタイム（秒）
            
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game_over:
                        self.handle_click(event.pos)
            
            # ゲーム更新
            if not self.game_over:
                self.time_left -= dt
                if self.time_left <= 0:
                    self.time_left = 0
                    self.game_over = True
            
            # 描画
            self.screen.fill(COLORS['BLACK'])
            self.draw_grid()
            self.draw_ui()
            
            # ゲームオーバー表示
            if self.game_over:
                game_over_text = self.big_font.render("GAME OVER", True, COLORS['WHITE'])
                text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                self.screen.blit(game_over_text, text_rect)
                
                final_score_text = self.font.render(f"Final Score: {self.score}", True, COLORS['WHITE'])
                score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 50))
                self.screen.blit(final_score_text, score_rect)
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Match3Game()
    game.run()
