from __future__ import annotations
from typing import List, Set, Dict, Tuple, Optional

import pygame
import pygame_gui

from player import HumanPlayer
import paths
from game_board_util import scale_position
from definitions import roll_dice
from log_book_ui import LogBookPanel

class PlayerRoll:
    
    ### Static
    def _is_adjacent(p1, p2):
        return (abs(p1[0] - p2[0]) == 1 and p1[1] == p2[1]) \
            or (abs(p1[1] - p2[1]) == 1 and p1[0] == p2[0])

    def _valid_position(pos):
        return pos[0] >= 0 and pos[0] < 25 and pos[1] >= 0 and pos[1] < 24 \
            and paths.board_spaces[pos[0]][pos[1]] != 0

    player: HumanPlayer
    surface: pygame.Surface
    on_end_turn: Callable
    _rolling: bool
    _distance: int
    _positions: List[Tuple[int, int]]
    _rects: List[pygame.Rect]
    _drawn_rects: List[pygame.Rect]

    def __init__(self, surface: pygame.Surface, player: HumanPlayer, on_end_turn: Callable):
        self.surface = surface
        self._rolling = False
        self.player = player
        self.on_end_turn = on_end_turn

    def roll(self):
        self._rolling = True
        self._distance = roll_dice()
        print("rolled a " + str(self._distance))

        self._calculate_positions()

    def _calculate_positions(self):
        start = self.player.position

        self._positions = []

        # from left to right, scale up to down for space that fix within 
        # the roll and are valid positions
        x_offset = -1 * self._distance
        while x_offset <= self._distance:
            y_offset = 0

            while abs(y_offset) + abs(x_offset) <= self._distance:
                # up
                pos = (start[0] + x_offset, start[1] + y_offset)
                if PlayerRoll._valid_position(pos):
                    self._positions.append(pos)

                # down
                pos = (start[0] + x_offset, start[1] + y_offset * -1)
                if PlayerRoll._valid_position(pos):                 
                    self._positions.append(pos)

                y_offset += 1

            x_offset += 1

        self._remove_invalid_positions()

        self._rects = list(map(scale_position, self._positions))
        self._rects = list(map(lambda p: pygame.Rect((p[0] - 5, p[1] - 5), (11, 11)), self._rects))

    # remove positions that don't actually correct to the rest of them
    def _remove_invalid_positions(self):
        no_dupe_positions = []

        # remove duplicates
        for position in self._positions:
            dupe = False
            for cmp in no_dupe_positions:
                if position[0] == cmp[0] and position[1] == cmp[1]:
                    dupe = True
                    break

            if not dupe:
                no_dupe_positions.append(position)

        good_positions = []
        for position in no_dupe_positions:
            for cmp in no_dupe_positions:
                if position[0] == cmp[0] and position[1] == cmp[1]:
                    continue

                if PlayerRoll._is_adjacent(position, cmp):
                    good_positions.append(position)
                    break               

        self._positions = good_positions

    def draw(self):
        if not self._rolling:
            return      
        
        self._drawn_rects = list(map(lambda rect: pygame.draw.rect(self.surface, (120, 120, 120), rect), self._rects)) 

    def process_events(self, event):
        if not self._rolling:
            return

        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()

            i = 0
            for rect in self._drawn_rects:
                rect = rect.move(LogBookPanel.PANEL_WIDTH, 0)

                if rect.collidepoint(pos):
                    self._click_move(self._positions[i])
                    break
                i += 1

    def _click_move(self, pos):
        self.player.move(pos)
        self._rolling = False
        self.on_end_turn()
