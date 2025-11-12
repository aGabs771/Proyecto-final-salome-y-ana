import sys
import random
import pygame as pg
from dataclasses import dataclass

# ============================
# Configuración de juego
# ============================
CELL = 32           # tamaño de celda en px
COLS, ROWS = 10, 20 # Tetris clásico 10x20
SIDEBAR_W = 7       # ancho en celdas para el panel lateral (para futuras UI)
FPS = 60

# Colores (RGB)
BLACK = (10, 10, 14)
GRID_BG = (18, 18, 26)
GRID_LINE = (38, 38, 50)
WHITE = (235, 235, 235)
CLEAR_FLASH_COLOR = (255, 255, 255) # Color para la animación de línea limpia

# Paleta por tetrominó
COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (160, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
    'J': (0, 0, 240),
    'L': (240, 160, 0)
}

# Rotaciones por pieza (matrices 4x4)
SHAPES = {
    'I': [
        [
            [0,0,0,0],
            [1,1,1,1],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,0,1,0],
            [0,0,1,0],
            [0,0,1,0],
            [0,0,1,0]
        ],
    ],
    'O': [
        [
            [0,1,1,0],
            [0,1,1,0],
            [0,0,0,0],
            [0,0,0,0]
        ]
    ],
    'T': [
        [
            [0,1,0,0],
            [1,1,1,0],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,1,0,0],
            [0,1,1,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
        [
            [0,0,0,0],
            [1,1,1,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
        [
            [0,1,0,0],
            [1,1,0,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
    ],
    'S': [
        [
            [0,1,1,0],
            [1,1,0,0],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,1,0,0],
            [0,1,1,0],
            [0,0,1,0],
            [0,0,0,0]
        ],
    ],
    'Z': [
        [
            [1,1,0,0],
            [0,1,1,0],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,0,1,0],
            [0,1,1,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
    ],
    'J': [
        [
            [1,0,0,0],
            [1,1,1,0],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,1,1,0],
            [0,1,0,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
        [
            [0,0,0,0],
            [1,1,1,0],
            [0,0,1,0],
            [0,0,0,0]
        ],
        [
            [0,1,0,0],
            [0,1,0,0],
            [1,1,0,0],
            [0,0,0,0]
        ],
    ],
    'L': [
        [
            [0,0,1,0],
            [1,1,1,0],
            [0,0,0,0],
            [0,0,0,0]
        ],
        [
            [0,1,0,0],
            [0,1,0,0],
            [0,1,1,0],
            [0,0,0,0]
        ],
        [
            [0,0,0,0],
            [1,1,1,0],
            [1,0,0,0],
            [0,0,0,0]
        ],
        [
            [1,1,0,0],
            [0,1,0,0],
            [0,1,0,0],
            [0,0,0,0]
        ],
    ],
}


SCORE_TABLE = {
    1: 100,
    2: 300,
    3: 500,
    4: 800, # Tetris
}
LINES_PER_LEVEL = 10

@dataclass
class Piece:
    kind: str
    x: int
    y: int
    rot: int = 0

    @property
    def shape(self):
        rotations = SHAPES[self.kind]
        return rotations[self.rot % len(rotations)]

    def rotated(self, dr: int):
        return Piece(self.kind, self.x, self.y, self.rot + dr)

class TetrisGame:
    def __init__(self):
        self._init_state()

    def _init_state(self):
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)] 
        self.score = 0
        self.level = 1
        self.lines = 0
        self.gravity_ms = 800 
        self.drop_timer = 0
        self.game_over = False

        self.current = self._new_piece()
        self.next_piece = self._new_piece()


        self.move_cooldown = 120
        self.move_timer_l = 0
        self.move_timer_r = 0


        self.clearing_rows = []
        self.clear_timer = 0
        self.CLEAR_DURATION_MS = 150 

        # === TAREA SALOMÉ: Pausa ===
        self.paused = False
        
        self._update_gravity() # Asegura la gravedad correcta para el nivel 1

    def _update_gravity(self):
        """Ajusta la gravedad en función del nivel."""
        # Fórmula: max(min_speed, initial_speed - step * (level - 1))
        # Nivel 1: 800ms, Nivel 2: 730ms, Nivel 3: 660ms, etc.
        # Mínimo de 120ms (o el que se decida)
        self.gravity_ms = max(120, 800 - 70 * (self.level - 1))
        self.drop_timer = 0 # Reiniciar el timer de drop para aplicar la nueva velocidad

    def inside(self, x, y):
        return 0 <= x < COLS and 0 <= y < ROWS

    def collides(self, piece: Piece) -> bool:
        shape = piece.shape
        for r in range(4):
            for c in range(4):
                if shape[r][c]:
                    gx, gy = piece.x + c, piece.y + r
                    # Colisión con límites o con la cuadrícula
                    if not self.inside(gx, gy) or self.grid[gy][gx] is not None:
                        return True
        return False

    # --- Piezas ---
    def _random_kind_simple(self) -> str:
        # === TAREA SALOMÉ: 7-bag randomizer (mantengo el simple por ahora) ===
        return random.choice(list(SHAPES.keys()))

    def _new_piece(self) -> Piece:
        kind = self._random_kind_simple()

        x = COLS // 2 - 2
        y = 0
        piece = Piece(kind, x, y)
        return piece

    def lock_piece(self):
        s = self.current.shape
        for r in range(4):
            for c in range(4):
                if s[r][c]:
                    gx, gy = self.current.x + c, self.current.y + r
                    if self.inside(gx, gy):
                        self.grid[gy][gx] = self.current.kind
        self._after_lock()

    def _after_lock(self):

        filled_rows = []
        for r in range(ROWS):
            if all(self.grid[r]):
                filled_rows.append(r)
        
        num_cleared = len(filled_rows)

        if num_cleared > 0:
            self.clearing_rows = filled_rows
            self.clear_timer = self.CLEAR_DURATION_MS

        else:

            self._spawn_next()


    def _process_clear(self):
        """Ejecuta la limpieza de la rejilla, la puntuación y la progresión."""
        num_cleared = len(self.clearing_rows)
        if num_cleared == 0:
            return

        score_base = SCORE_TABLE.get(num_cleared, 0)
        self.score += score_base * self.level

        new_grid = [[None for _ in range(COLS)] for _ in range(num_cleared)]
        
        
        for r in range(ROWS):
            if r not in self.clearing_rows:
                new_grid.append(self.grid[r])
        
        
        self.grid = new_grid[num_cleared:ROWS] 

        old_lines = self.lines
        self.lines += num_cleared
        
        new_level = (self.lines // LINES_PER_LEVEL) + 1
        if new_level > self.level:
            self.level = new_level
            self._update_gravity()


        self._spawn_next()
        self.clearing_rows = []


    def _spawn_next(self):
        """Mueve la pieza 'next' a 'current' y genera una nueva 'next'."""
        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if self.collides(self.current):
            self.game_over = True
            
    
    def try_move(self, dx: int, dy: int) -> bool:
        if self.game_over or self.paused or self.clear_timer > 0:
            return False
        
        test = Piece(self.current.kind, self.current.x + dx, self.current.y + dy, self.current.rot)
        if not self.collides(test):
            self.current = test
            return True
        return False

    def try_rotate(self, dr: int) -> bool:
        if self.game_over or self.paused or self.clear_timer > 0:
            return False
        
        test = self.current.rotated(dr)
        if not self.collides(test):
            self.current = test
            return True
        
        # === TAREA SALOMÉ: Wall‑kicks (SRS básico) ===
        # ... (dejar aquí el código de Salomé para wall-kicks) ...
        return False

    def hard_drop(self):
       
        if self.game_over or self.paused or self.clear_timer > 0:
            return

       
        drop_distance = 0
        while self.try_move(0, 1):
            drop_distance += 1
        

        self.score += drop_distance * 2 
        
       
        self.lock_piece()

    
    def update(self, dt_ms: int):
        if self.game_over or self.paused:
            return

        
        if self.clear_timer > 0:
            self.clear_timer -= dt_ms
            if self.clear_timer <= 0:
                self._process_clear() 
            return

       
        self.drop_timer += dt_ms
        if self.drop_timer >= self.gravity_ms:
            self.drop_timer = 0
            if not self.try_move(0, 1):
                self.lock_piece()

   
    def draw_cell(self, surf, x, y, color):
        rect = pg.Rect(x * CELL, y * CELL, CELL, CELL)
        pg.draw.rect(surf, color, rect)
        pg.draw.rect(surf, GRID_LINE, rect, 1)

    def draw_grid(self, surf):
        surf.fill(GRID_BG)
        
       
        for y in range(ROWS):
            for x in range(COLS):
                kind = self.grid[y][x]
                if kind is not None:
                    color = COLORS[kind]
                    
                    
                    if y in self.clearing_rows:
 
                        if self.clear_timer > self.CLEAR_DURATION_MS / 2:
                             color = CLEAR_FLASH_COLOR
                        else:
                             color = GRID_BG 

                    self.draw_cell(surf, x, y, color)


        if self.clear_timer <= 0:
            s = self.current.shape
            for r in range(4):
                for c in range(4):
                    if s[r][c]:
                        gx, gy = self.current.x + c, self.current.y + r
                        if 0 <= gy < ROWS: 
                            self.draw_cell(surf, gx, gy, COLORS[self.current.kind])

    def draw_next_piece(self, surf, piece: Piece, offset_x: int, offset_y: int):
        """Dibuja una pieza 4x4 centrada en un área."""
        s = piece.shape
        kind = piece.kind

        center_offset_x = offset_x + (SIDEBAR_W * CELL - 4 * CELL) // 2 
        center_offset_y = offset_y 

        for r in range(4):
            for c in range(4):
                if s[r][c]:
                    
                    self.draw_cell(surf, center_offset_x // CELL + c, center_offset_y // CELL + r, COLORS[kind])


    def draw_sidebar(self, surf, font):

        side_w = SIDEBAR_W * CELL
        surf.fill((24, 24, 32)) 

        x_start = 10 

        y_pos = 10 
        
        title_next = font.render("NEXT", True, WHITE)
        surf.blit(title_next, (x_start, y_pos))
        y_pos += title_next.get_height() + 5
        
        frame_rect = pg.Rect(x_start - 5, y_pos - 5, 5*CELL, 5*CELL)
        pg.draw.rect(surf, GRID_BG, frame_rect)
        pg.draw.rect(surf, GRID_LINE, frame_rect, 1)


        cell_x_offset = int(SIDEBAR_W / 2) - 2
        cell_y_offset = int((y_pos + 5) / CELL) 

        s = self.next_piece.shape
        kind = self.next_piece.kind
        
        for r in range(4):
            for c in range(4):
                if s[r][c]:
                    
                    draw_x = cell_x_offset + c
                    draw_y = cell_y_offset + r
                    self.draw_cell(surf, draw_x, draw_y, COLORS[kind])

        y_pos = frame_rect.bottom + 20

        
       
        txt_score = font.render("SCORE", True, WHITE)
        surf.blit(txt_score, (x_start, y_pos))
        score_val = font.render(f"{self.score:07}", True, WHITE)
        surf.blit(score_val, (x_start, y_pos + txt_score.get_height() + 5))
        y_pos += txt_score.get_height() + score_val.get_height() + 15

        
        txt_lines = font.render("LINES", True, WHITE)
        surf.blit(txt_lines, (x_start, y_pos))
        lines_val = font.render(f"{self.lines:03}", True, WHITE)
        surf.blit(lines_val, (x_start, y_pos + txt_lines.get_height() + 5))
        y_pos += txt_lines.get_height() + lines_val.get_height() + 15

        
        txt_level = font.render("LEVEL", True, WHITE)
        surf.blit(txt_level, (x_start, y_pos))
        level_val = font.render(f"{self.level}", True, WHITE)
        surf.blit(level_val, (x_start, y_pos + txt_level.get_height() + 5))
        y_pos += txt_level.get_height() + level_val.get_height() + 15
        
        
        txt_speed = font.render(f"Speed: {self.gravity_ms}ms", True, GRID_LINE)
        surf.blit(txt_speed, (x_start, surf.get_height() - txt_speed.get_height() - 10))



def main():
    pg.init()
    pg.display.set_caption("Tetris — Base Salomé & Ana")

    game_w = COLS * CELL
    side_w = SIDEBAR_W * CELL
    game_h = ROWS * CELL

    screen = pg.display.set_mode((game_w + side_w, game_h))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 20)
    font_large = pg.font.SysFont("consolas", 40, bold=True)


    game = TetrisGame()

    move_delay = 120 
    last_move_l = 0
    last_move_r = 0

    running = True
    while running:
        dt = clock.tick(FPS)

        
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                
                
                if e.key == pg.K_p:
                    
                    if not game.game_over:
                        game.paused = not game.paused
                elif e.key == pg.K_r:
                    
                    game._init_state()
                    last_move_l = last_move_r = 0 

                if not game.game_over and not game.paused and game.clear_timer <= 0:
                    if e.key == pg.K_LEFT:
                        game.try_move(-1, 0)
                        last_move_l = pg.time.get_ticks()
                    elif e.key == pg.K_RIGHT:
                        game.try_move(1, 0)
                        last_move_r = pg.time.get_ticks()
                    elif e.key == pg.K_DOWN:
                        game.try_move(0, 1)
                    elif e.key == pg.K_UP:
                        game.try_rotate(1)
                    elif e.key == pg.K_SPACE:
                        
                        game.hard_drop()

        keys = pg.key.get_pressed()
        now = pg.time.get_ticks()
        
        if not game.game_over and not game.paused and game.clear_timer <= 0:
            if keys[pg.K_LEFT] and now - last_move_l > move_delay:
                if game.try_move(-1, 0):
                    last_move_l = now
            if keys[pg.K_RIGHT] and now - last_move_r > move_delay:
                if game.try_move(1, 0):
                    last_move_r = now

            if keys[pg.K_DOWN]:
                game.update(dt * 5) 

        game.update(dt)

        screen.fill(BLACK)

        board = pg.Surface((COLS * CELL, ROWS * CELL))
        game.draw_grid(board)
        screen.blit(board, (0, 0))

        sidebar = pg.Surface((side_w, game_h))
        game.draw_sidebar(sidebar, font)
        screen.blit(sidebar, (COLS * CELL, 0))

        title = font.render("TETRIS", True, WHITE)
        screen.blit(title, (8, 4))
        
        if game.paused:
            pause_text = font_large.render("PAUSA", True, (0, 240, 240))
            center_x = game_w // 2 - pause_text.get_width() // 2
            center_y = game_h // 2 - pause_text.get_height() // 2
            screen.blit(pause_text, (center_x, center_y))
        
        if game.game_over:
            over = font_large.render("GAME OVER", True, (255, 80, 80))
            restart = font.render("R para reiniciar", True, WHITE)
            
            center_x_over = game_w // 2 - over.get_width() // 2
            center_y_over = game_h // 2 - over.get_height()
            center_x_restart = game_w // 2 - restart.get_width() // 2
            
            screen.blit(over, (center_x_over, center_y_over))
            screen.blit(restart, (center_x_restart, center_y_over + over.get_height() + 10))

        pg.display.flip()

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
