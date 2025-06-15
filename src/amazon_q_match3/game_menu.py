"""
Amazon Q Match3 ゲームメニューシステム
"""

import logging
from enum import Enum

import pygame

# Color definitions
COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "GRAY": (128, 128, 128),
    "LIGHT_GRAY": (200, 200, 200),
    "DARK_GRAY": (64, 64, 64),
    "BLUE": (100, 150, 255),
    "LIGHT_BLUE": (150, 200, 255),
    "GREEN": (100, 200, 100),
    "RED": (220, 100, 100),
    "YELLOW": (255, 255, 100),
    "ORANGE": (255, 165, 0),  # Better orange for buttons
    "PURPLE": (200, 100, 255),
    "DARK_BLUE": (50, 100, 200),  # Better contrast for buttons
    "DARK_GREEN": (50, 150, 50),  # Better contrast for buttons
    "DARK_RED": (180, 50, 50),  # Better contrast for buttons
}


class MenuState(Enum):
    """メニューの状態"""

    MAIN_MENU = "main_menu"
    TIME_SELECT = "time_select"
    HIGHSCORE = "highscore"
    GAME_OVER = "game_over"
    PLAYING = "playing"


class GameMenu:
    """ゲームメニュー管理クラス"""

    def __init__(self, screen, highscore_manager):
        self.screen = screen
        self.highscore_manager = highscore_manager
        self.logger = logging.getLogger("GameMenu")

        # Font initialization (English only, optimized sizes)
        try:
            # Try system fonts first with better sizes
            self.title_font = pygame.font.SysFont("arial,helvetica,sans-serif", 64)
            self.menu_font = pygame.font.SysFont("arial,helvetica,sans-serif", 40)
            self.text_font = pygame.font.SysFont("arial,helvetica,sans-serif", 32)
            self.small_font = pygame.font.SysFont("arial,helvetica,sans-serif", 20)
            self.button_font = pygame.font.SysFont(
                "arial,helvetica,sans-serif", 28
            )  # Special font for buttons
            self.logger.info("System fonts loaded successfully")
        except Exception:
            # Fallback to default fonts with better sizes
            self.title_font = pygame.font.Font(None, 64)
            self.menu_font = pygame.font.Font(None, 40)
            self.text_font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 20)
            self.button_font = pygame.font.Font(None, 28)  # Special font for buttons
            self.logger.warning("Using default fonts")

        # Menu state
        self.state = MenuState.MAIN_MENU
        self.selected_time = 180  # Default 3 minutes
        self.final_score = 0
        self.is_new_highscore = False

        # Button definitions
        self.buttons = {}
        self._setup_buttons()

        self.logger.info("Game menu initialized")

    def _setup_buttons(self):
        """Button setup with proper sizing"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        center_x = screen_width // 2

        # Main menu buttons (larger for better text fit)
        self.buttons["start"] = pygame.Rect(center_x - 120, 300, 240, 70)
        self.buttons["highscore"] = pygame.Rect(center_x - 120, 380, 240, 70)
        self.buttons["quit"] = pygame.Rect(center_x - 120, 460, 240, 70)

        # Time selection buttons (wider for text)
        self.buttons["time_30"] = pygame.Rect(center_x - 270, 300, 180, 70)
        self.buttons["time_60"] = pygame.Rect(center_x - 90, 300, 180, 70)
        self.buttons["time_180"] = pygame.Rect(center_x + 90, 300, 180, 70)
        self.buttons["back"] = pygame.Rect(50, screen_height - 80, 120, 60)

        # Game over buttons (wider for text)
        self.buttons["play_again"] = pygame.Rect(center_x - 180, 400, 160, 60)
        self.buttons["main_menu"] = pygame.Rect(center_x - 10, 400, 160, 60)
        self.buttons["quit_game"] = pygame.Rect(center_x + 160, 400, 160, 60)

    def _get_time_label(self, time_limit: int) -> str:
        """時間制限に応じたラベルを取得"""
        time_labels = {30: "30s", 60: "1min", 180: "3min"}
        return time_labels.get(time_limit, f"{time_limit}s")

    def handle_event(self, event) -> str | None:
        """
        イベントを処理

        Returns:
            str: アクション ('start_game', 'quit', 'main_menu', etc.)
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            if self.state == MenuState.MAIN_MENU:
                return self._handle_main_menu_click(mouse_pos)
            if self.state == MenuState.TIME_SELECT:
                return self._handle_time_select_click(mouse_pos)
            if self.state == MenuState.HIGHSCORE:
                return self._handle_highscore_click(mouse_pos)
            if self.state == MenuState.GAME_OVER:
                return self._handle_game_over_click(mouse_pos)

        return None

    def _handle_main_menu_click(self, mouse_pos) -> str | None:
        """メインメニューのクリック処理"""
        if self.buttons["start"].collidepoint(mouse_pos):
            self.state = MenuState.TIME_SELECT
            return "time_select"
        if self.buttons["highscore"].collidepoint(mouse_pos):
            self.state = MenuState.HIGHSCORE
            return "show_highscore"
        if self.buttons["quit"].collidepoint(mouse_pos):
            return "quit"
        return None

    def _handle_time_select_click(self, mouse_pos) -> str | None:
        """時間選択のクリック処理"""
        if self.buttons["time_30"].collidepoint(mouse_pos):
            self.selected_time = 30
            return "start_game"
        if self.buttons["time_60"].collidepoint(mouse_pos):
            self.selected_time = 60
            return "start_game"
        if self.buttons["time_180"].collidepoint(mouse_pos):
            self.selected_time = 180
            return "start_game"
        if self.buttons["back"].collidepoint(mouse_pos):
            self.state = MenuState.MAIN_MENU
            return "main_menu"
        return None

    def _handle_highscore_click(self, mouse_pos) -> str | None:
        """ハイスコア画面のクリック処理"""
        if self.buttons["back"].collidepoint(mouse_pos):
            self.state = MenuState.MAIN_MENU
            return "main_menu"
        return None

    def _handle_game_over_click(self, mouse_pos) -> str | None:
        """ゲームオーバー画面のクリック処理"""
        if self.buttons["play_again"].collidepoint(mouse_pos):
            self.state = MenuState.TIME_SELECT
            return "play_again"
        if self.buttons["main_menu"].collidepoint(mouse_pos):
            self.state = MenuState.MAIN_MENU
            return "main_menu"
        if self.buttons["quit_game"].collidepoint(mouse_pos):
            return "quit"
        return None

    def draw(self):
        """メニューを描画"""
        if self.state == MenuState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == MenuState.TIME_SELECT:
            self._draw_time_select()
        elif self.state == MenuState.HIGHSCORE:
            self._draw_highscore()
        elif self.state == MenuState.GAME_OVER:
            self._draw_game_over()

    def _draw_main_menu(self):
        """Draw main menu"""
        self.screen.fill(COLORS["BLACK"])

        # Title
        title_text = self.title_font.render("Amazon Q Match3", True, COLORS["WHITE"])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_text, title_rect)

        # Subtitle
        subtitle_text = self.text_font.render("Puzzle Game", True, COLORS["LIGHT_GRAY"])
        subtitle_rect = subtitle_text.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(subtitle_text, subtitle_rect)

        # Buttons with better color contrast
        self._draw_button("start", "Start Game", COLORS["DARK_GREEN"])
        self._draw_button("highscore", "High Score", COLORS["DARK_BLUE"])
        self._draw_button("quit", "Quit", COLORS["DARK_RED"])

        # Best score display
        best_score, best_mode = self.highscore_manager.get_all_time_best()
        if best_score > 0:
            best_text = self.small_font.render(
                f"Best Score: {best_score} ({best_mode})", True, COLORS["YELLOW"]
            )
            best_rect = best_text.get_rect(center=(self.screen.get_width() // 2, 550))
            self.screen.blit(best_text, best_rect)

    def _draw_time_select(self):
        """Draw time selection screen"""
        self.screen.fill(COLORS["BLACK"])

        # Title
        title_text = self.menu_font.render("Select Time Limit", True, COLORS["WHITE"])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(title_text, title_rect)

        # Time selection buttons with better color contrast
        self._draw_button("time_30", "30s", COLORS["DARK_RED"])
        self._draw_button("time_60", "1min", COLORS["ORANGE"])
        self._draw_button("time_180", "3min", COLORS["DARK_GREEN"])

        # Best scores for each mode
        y_pos = 380
        for time_limit, label in [(30, "30s"), (60, "1min"), (180, "3min")]:
            best_score = self.highscore_manager.get_best_score(time_limit)
            if best_score > 0:
                score_text = self.small_font.render(
                    f"{label}: {best_score}", True, COLORS["LIGHT_GRAY"]
                )
                score_rect = score_text.get_rect(center=(self.screen.get_width() // 2, y_pos))
                self.screen.blit(score_text, score_rect)
                y_pos += 25

        # Back button with better contrast
        self._draw_button("back", "Back", COLORS["DARK_GRAY"])

    def _draw_highscore(self):
        """Draw high score screen"""
        self.screen.fill(COLORS["BLACK"])

        # Title
        title_text = self.menu_font.render("High Scores", True, COLORS["WHITE"])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 50))
        self.screen.blit(title_text, title_rect)

        # High scores for each mode
        y_start = 120
        modes = [(30, "30s Mode"), (60, "1min Mode"), (180, "3min Mode")]

        for i, (time_limit, mode_name) in enumerate(modes):
            x_offset = i * 250 + 50

            # Mode name
            mode_text = self.text_font.render(mode_name, True, COLORS["YELLOW"])
            self.screen.blit(mode_text, (x_offset, y_start))

            # Score list
            scores = self.highscore_manager.get_highscores(time_limit, 5)
            for j, score_data in enumerate(scores):
                rank_text = f"{j + 1}. {score_data['score']}"
                score_text = self.small_font.render(rank_text, True, COLORS["WHITE"])
                self.screen.blit(score_text, (x_offset, y_start + 40 + j * 25))

            if not scores:
                no_score_text = self.small_font.render("No Records", True, COLORS["GRAY"])
                self.screen.blit(no_score_text, (x_offset, y_start + 40))

        # Back button with better contrast
        self._draw_button("back", "Back", COLORS["DARK_GRAY"])

    def _draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill(COLORS["BLACK"])

        # Game over title
        title_text = self.title_font.render("GAME OVER", True, COLORS["RED"])
        title_rect = title_text.get_rect(center=(self.screen.get_width() // 2, 150))
        self.screen.blit(title_text, title_rect)

        # Score display
        score_text = self.menu_font.render(f"Score: {self.final_score}", True, COLORS["WHITE"])
        score_rect = score_text.get_rect(center=(self.screen.get_width() // 2, 220))
        self.screen.blit(score_text, score_rect)

        # Time limit display
        time_label = self._get_time_label(self.selected_time)
        time_text = self.text_font.render(f"Mode: {time_label}", True, COLORS["LIGHT_GRAY"])
        time_rect = time_text.get_rect(center=(self.screen.get_width() // 2, 260))
        self.screen.blit(time_text, time_rect)

        # High score display
        if self.is_new_highscore:
            highscore_text = self.text_font.render("New Record!", True, COLORS["YELLOW"])
            highscore_rect = highscore_text.get_rect(center=(self.screen.get_width() // 2, 300))
            self.screen.blit(highscore_text, highscore_rect)
        else:
            rank = self.highscore_manager.get_rank(self.selected_time, self.final_score)
            if rank <= 10:
                rank_text = self.text_font.render(f"Rank: #{rank}", True, COLORS["LIGHT_BLUE"])
                rank_rect = rank_text.get_rect(center=(self.screen.get_width() // 2, 300))
                self.screen.blit(rank_text, rank_rect)

        # Best score display
        best_score = self.highscore_manager.get_best_score(self.selected_time)
        if best_score > 0:
            time_label = self._get_time_label(self.selected_time)
            best_text = self.small_font.render(
                f"{time_label} Best: {best_score}", True, COLORS["LIGHT_GRAY"]
            )
            best_rect = best_text.get_rect(center=(self.screen.get_width() // 2, 340))
            self.screen.blit(best_text, best_rect)

        # Buttons with better color contrast
        self._draw_button("play_again", "Play Again", COLORS["DARK_GREEN"])
        self._draw_button("main_menu", "Menu", COLORS["DARK_BLUE"])
        self._draw_button("quit_game", "Quit", COLORS["DARK_RED"])

    def _draw_button(self, button_name: str, text: str, color: tuple[int, int, int]):
        """Draw button with proper text sizing and contrast"""
        if button_name not in self.buttons:
            return

        button_rect = self.buttons[button_name]

        # Button background
        pygame.draw.rect(self.screen, color, button_rect)
        pygame.draw.rect(self.screen, COLORS["WHITE"], button_rect, 2)

        # Determine text color based on background brightness
        # Calculate brightness using standard formula
        brightness = color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114
        text_color = COLORS["WHITE"] if brightness < 128 else COLORS["BLACK"]

        # Button text with appropriate font size
        font = self.button_font  # Use consistent button font for all buttons

        # Check if text fits, if not use smaller font
        text_surface = font.render(text, True, text_color)
        if text_surface.get_width() > button_rect.width - 20:  # 20px padding
            font = self.small_font
            text_surface = font.render(text, True, text_color)

        text_rect = text_surface.get_rect(center=button_rect.center)
        self.screen.blit(text_surface, text_rect)

    def set_game_over(self, score: int, time_limit: int):
        """ゲームオーバー状態を設定"""
        self.final_score = score
        self.selected_time = time_limit
        self.is_new_highscore = self.highscore_manager.add_score(time_limit, score)
        self.state = MenuState.GAME_OVER

        self.logger.info(
            f"Game over: Score={score}, Time={time_limit}s, New highscore={self.is_new_highscore}"
        )

    def get_selected_time(self) -> int:
        """選択された制限時間を取得"""
        return self.selected_time

    def set_state(self, state: MenuState):
        """メニュー状態を設定"""
        self.state = state
        self.logger.debug(f"Menu state changed to {state.value}")
