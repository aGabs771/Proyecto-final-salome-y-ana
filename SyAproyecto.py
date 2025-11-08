"""
TETRIS en Python con Pygame — 50% HECHO

Cómo ejecutar:
1) Instalar Pygame:  pip install pygame
2) Ejecutar:        python tetris_salome_ana.py

¿Qué ya funciona (base lista):
- Ventana, rejilla 10x20, dibujo y colores.
- Piezas (I, O, T, S, Z, J, L) con rotación básica.
- Movimiento izquierda/derecha/abajo, gravedad, y fijación de pieza al tocar suelo.
- Detección de “game over” si la pieza nueva colisiona al aparecer.

Qué falta (lo construyen Salomé y Ana):
- Limpieza de líneas + animación sencilla (ANA).
- Sistema de puntuación, niveles y velocidad progresiva (ANA).
- Vista lateral: siguiente pieza / hold, UI mínima (ANA).
- Randomizador 7‑bag para la secuencia de piezas (SALOMÉ).
- Rotación con wall‑kicks (SRS básico) para evitar atascos en paredes (SALOMÉ).
- Pausa/continuar y reinicio (SALOMÉ).
- Hard‑drop (barra espaciadora) con bonificación de puntos (ANA o SALOMÉ, ver notas).
- Sonidos opcionales (rotar, fijar, limpiar) (SALOMÉ).

En el código verás bloques marcados como:
### === TAREA ANA: ...
### === TAREA SALOMÉ: ...
con instrucciones paso a paso.
"""

import sys
import random
import pygame as pg
from dataclasses import dataclass

# ============================
# Configuración de juego
# ============================
CELL = 32              # tamaño de celda en px
COLS, ROWS = 10, 20    # Tetris clásico 10x20
SIDEBAR_W = 7          # ancho en celdas para el panel lateral (para futuras UI)
FPS = 60

# Colores (RGB)
BLACK = (10, 10, 14)
GRID_BG = (18, 18, 26)
GRID_LINE = (38, 38, 50)
WHITE = (235, 235, 235)

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
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]  # None o (kind)
        self.score = 0
        self.level = 1
        self.lines = 0
        self.gravity_ms = 800  # caer una fila cada X ms (ajustada por nivel)
        self.drop_timer = 0

        self.current = self._new_piece()
        self.next_piece = self._new_piece()
        self.game_over = False

        # Control repetición teclas
        self.move_cooldown = 120
        self.move_timer_l = 0
        self.move_timer_r = 0

    # --- Colisiones y límites ---
    def inside(self, x, y):
        return 0 <= x < COLS and 0 <= y < ROWS

    def collides(self, piece: Piece) -> bool:
        shape = piece.shape
        for r in range(4):
            for c in range(4):
                if shape[r][c]:
                    gx, gy = piece.x + c, piece.y + r
                    if not self.inside(gx, gy) or self.grid[gy][gx] is not None:
                        return True
        return False

    # --- Piezas ---
    def _random_kind_simple(self) -> str:
        return random.choice(list(SHAPES.keys()))

    def _new_piece(self) -> Piece:
        kind = self._random_kind_simple()
        # spawn centrado arriba (ajuste leve para 4x4)
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
        # Después de fijar la pieza: limpiar líneas (ANA) y spawnear nueva
        self._after_lock()

    def _after_lock(self):
        # === TAREA ANA: limpiar filas completas ===
        # 1) Detecta qué índices de fila (0..ROWS-1) están completamente llenos (sin None).
        # 2) Elimina esas filas y agrega por arriba la misma cantidad de filas vacías.
        # 3) Devuelve cuántas filas se limpiaron en este bloqueo.
        # 4) (Extra) Agrega una animación breve: pintar en blanco 100 ms antes de borrar.
        # Aquí mismo, una vez tengas el número de filas limpiadas (n), 
        #    - incrementa self.lines += n
        #    - calcula la puntuación según estándar Tetris (Single=100, Double=300, Triple=500, Tetris=800) * nivel
        #    - si self.lines cruza múltiplos de 10, sube de nivel y acelera self.gravity_ms (e.g., max(120, 800 - 70*(nivel-1))).
        # Por ahora, mientras ANA implementa, no haremos nada (juego sin clear):
        cleared = 0
        # TODO (ANA): reescribe esta parte para que funcione realmente.

        # Spawnear nueva pieza y revisar game over
        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if self.collides(self.current):
            self.game_over = True

    # --- Movimiento ---
    def try_move(self, dx: int, dy: int) -> bool:
        test = Piece(self.current.kind, self.current.x + dx, self.current.y + dy, self.current.rot)
        if not self.collides(test):
            self.current = test
            return True
        return False

    def try_rotate(self, dr: int) -> bool:
        test = self.current.rotated(dr)
        if not self.collides(test):
            self.current = test
            return True
        # === TAREA SALOMÉ: Wall‑kicks (SRS básico) ===
        # Si choca al rotar junto a pared o bloques, intenta desplazar la pieza
        # con pequeños offsets para permitir la rotación (p. ej., offsets = [(1,0),(-1,0),(2,0),(-2,0),(0,-1)]).
        # Recorre offsets y acepta el primero que no colisione.
        # Pseudocódigo:
        #   for (ox, oy) in offsets:
        #       test2 = Piece(kind, x+ox, y+oy, rot+dr)
        #       if not collides(test2): self.current = test2; return True
        return False

    def hard_drop(self):
        # === TAREA ANA (o SALOMÉ): Hard‑drop ===
        # 1) Mueve la pieza hacia abajo hasta que colisione (sin pasar el límite).
        # 2) (Si implementas puntuación) suma puntos por cada fila recorrida.
        # 3) Llama a lock_piece() al finalizar.
        # De momento, no se usa si no está implementado.
        while self.try_move(0, 1):
            pass
        self.lock_piece()

    # --- Lógica de gravedad ---
    def update(self, dt_ms: int):
        if self.game_over:
            return
        self.drop_timer += dt_ms
        if self.drop_timer >= self.gravity_ms:
            self.drop_timer = 0
            if not self.try_move(0, 1):
                self.lock_piece()

    # --- Dibujo ---
    def draw_cell(self, surf, x, y, color):
        rect = pg.Rect(x * CELL, y * CELL, CELL, CELL)
        pg.draw.rect(surf, color, rect)
        pg.draw.rect(surf, GRID_LINE, rect, 1)

    def draw_grid(self, surf):
        surf.fill(GRID_BG)
        # líneas de la rejilla (opcionales; ya dibujamos borde por celda)
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x] is not None:
                    self.draw_cell(surf, x, y, COLORS[self.grid[y][x]])
        # dibujar pieza activa
        s = self.current.shape
        for r in range(4):
            for c in range(4):
                if s[r][c]:
                    gx, gy = self.current.x + c, self.current.y + r
                    if 0 <= gy < ROWS:  # evita dibujar filas negativas
                        self.draw_cell(surf, gx, gy, COLORS[self.current.kind])

    def draw_sidebar(self, surf, font):
        # === TAREA ANA: Panel lateral (UI) ===
        # Objetivo: dibujar a la derecha un panel con:
        #   - Siguiente pieza (next)
        #   - (Opcional) Hold piece (si lo agrega SALOMÉ)
        #   - Score, Lines, Level
        # Pasos propuestos:
        # 1) Crear un Surface del ancho SIDE BAR en pixeles: SIDE_W = SIDE BAR_W*CELL.
        # 2) Dibujar título "Siguiente" y representar la matriz 4x4 de self.next_piece centrada.
        # 3) Renderizar texto de score/lines/level con font.render.
        # 4) Blittear al lado derecho del campo de juego (offset x = COLS*CELL).
        pass

# ============================
# Entrada principal y bucle
# ============================

def main():
    pg.init()
    pg.display.set_caption("Tetris — Base Salomé & Ana")

    game_w = COLS * CELL
    side_w = SIDEBAR_W * CELL
    game_h = ROWS * CELL

    screen = pg.display.set_mode((game_w + side_w, game_h))
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 20)

    game = TetrisGame()

    move_delay = 120  # ms entre repeticiones si tecla sostenida
    last_move_l = 0
    last_move_r = 0

    running = True
    while running:
        dt = clock.tick(FPS)

        # --- Eventos ---
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                elif e.key == pg.K_LEFT:
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
                    # Hard‑drop (cuando lo implementen)
                    game.hard_drop()
                elif e.key == pg.K_p:
                    # === TAREA SALOMÉ: Pausa/Continuar ===
                    # Implementa un flag game.paused. Si está pausado, no llamar a update.
                    # Alterna con la tecla P y muestra "PAUSA" en pantalla.
                    pass
                elif e.key == pg.K_r:
                    # === TAREA SALOMÉ: Reinicio ===
                    # Reinicia el estado del juego (grid vacía, score=0, nivel=1, etc.)
                    pass

        # Repetición de movimiento si tecla sostenida
        keys = pg.key.get_pressed()
        now = pg.time.get_ticks()
        if keys[pg.K_LEFT] and now - last_move_l > move_delay:
            if game.try_move(-1, 0):
                last_move_l = now
        if keys[pg.K_RIGHT] and now - last_move_r > move_delay:
            if game.try_move(1, 0):
                last_move_r = now

        # --- Actualización ---
        game.update(dt)

        # --- Dibujo ---
        screen.fill(BLACK)
        # campo de juego
        board = pg.Surface((COLS * CELL, ROWS * CELL))
        game.draw_grid(board)
        screen.blit(board, (0, 0))

        # sidebar (UI para ANA)
        sidebar = pg.Surface((side_w, game_h))
        sidebar.fill((24, 24, 32))
        # Referencia visual temporal (texto):
        txt = font.render("UI pendiente", True, WHITE)
        sidebar.blit(txt, (12, 12))
        screen.blit(sidebar, (COLS * CELL, 0))

        # cabecera
        title = font.render("TETRIS", True, WHITE)
        screen.blit(title, (8, 4))

        if game.game_over:
            over = font.render("GAME OVER — R para reiniciar", True, (255, 80, 80))
            screen.blit(over, (12, game_h//2 - 10))

        pg.display.flip()

    pg.quit()
    sys.exit()


# ============================
# Guía de trabajo (docente):
# ============================
# Dividir el trabajo 50/50 Salomé y Ana:
#
# ANA — Enfocada en experiencia de juego y progresión:
#  1) Implementar limpieza de líneas en TetrisGame._after_lock():
#     - Detectar filas llenas, borrarlas y añadir filas vacías arriba.
#     - Actualizar self.lines, self.score (Single=100, Double=300, Triple=500, Tetris=800)*nivel.
#     - Opcional: animación de parpadeo de filas antes de eliminar.
#  2) Velocidad por nivel: cada 10 líneas sube self.level y reduce self.gravity_ms.
#  3) UI lateral en draw_sidebar(): mostrar Score, Lines, Level y “Siguiente”.
#  4) Hard‑drop (game.hard_drop): sumar puntos por cada fila caída (p.ej., +2 por celda) antes de lock.
#
# SALOMÉ — Enfocada en control y pulido:
#  1) Secuencia 7‑bag: reemplazar _random_kind_simple() por una bolsa con las 7 piezas mezcladas.
#  2) Rotación con wall‑kicks (SRS básico) en try_rotate(): probar offsets para permitir giro junto a pared.
#  3) Pausa/Continuar (tecla P): detener update() y mostrar etiqueta "PAUSA".
#  4) Reinicio (tecla R): restaurar estado inicial (grid vacía, score/lines/level, pieza actual y next).
#  5) (Opcional) Sonidos: usar pg.mixer.Sound("ruta.wav").play() en rotar, lock y clear.
#
# Ambos pueden comentar su nombre en las funciones que toquen.
#
# Sugerencia de evaluación:
# - Funcional (50%): limpia líneas correctamente, sube nivel y muestra UI, 7‑bag, pausa/reinicio.
# - Extra (10–20%): animaciones, sonidos, hold, sombras (ghost), récord.
# ============================

if __name__ == "__main__":
    main()
