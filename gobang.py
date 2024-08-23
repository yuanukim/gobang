"""
    @author yuanluo2

    @desc This is a gobang game with a simple AI. 
          AI uses 5-tuple algorithm, just a little smart(This is such a simple program, 
          so I don't want to use alpha-beta pruning).
"""

import pygame
import random

# constants.
BOARD_COL_NUM = 15
BOARD_ROW_NUM = 15
BOARD_EXTRA_PADDING = 1

SQUARE_RENDER_WIDTH = 45
PIECE_RENDER_CIRCLE_RADIUS = 15
PIECE_RENDER_CIRCLE_WIDTH = 1

BOARD_RENDER_PADDING = 30
BOARD_RENDER_WIDTH = SQUARE_RENDER_WIDTH * (BOARD_COL_NUM - 1)
BOARD_RENDER_HEIGHT = SQUARE_RENDER_WIDTH * (BOARD_ROW_NUM - 1)

SCREEN_RENDER_WIDTH = BOARD_RENDER_WIDTH + 2 * BOARD_RENDER_PADDING
SCREEN_RENDER_HEIGHT = BOARD_RENDER_HEIGHT + 2 * BOARD_RENDER_PADDING

BACKGROUND_COLOR = (255, 255, 255)
LINE_COLOR = (0, 0, 0)
USER_PIECE_COLOR = (0, 0, 0)
AI_PIECE_COLOR = (255, 0, 0)

PYGAME_LEFT_MOUSEBUTTON_NUMBER = 1
PYGAME_RIGHT_MOUSEBUTTON_NUMBER = 3

FONT_NAME = 'simfang.ttf'

GAME_FPS = 30

# pieces enumerations.
P_EMPTY = 0
P_OUT   = 1
P_USER  = 2
P_AI    = 3

# show what.
SHOW_PAGE_WELCOME  = 0
SHOW_PAGE_BOARD    = 1
SHOW_PAGE_YOU_WIN  = 2
SHOW_PAGE_YOU_LOSE = 3

# fps control.
game_clock = pygame.time.Clock()

game_running = True
game_remake_board = False
game_current_page = SHOW_PAGE_WELCOME

class Board:
    def __init__(self):
        self.history = []
        self.row_num = BOARD_ROW_NUM + 2 * BOARD_EXTRA_PADDING
        self.col_num = BOARD_COL_NUM + 2 * BOARD_EXTRA_PADDING

        """
            create a 2D array as the chess board.

            board size is not just row_num x col_num, extra rows and 
            columns will be added to accelerate the subscript checking.
            so the first row, last row, first column, last column would 
            be all P_OUT.
        """
        self.data = []

        for r in range(self.row_num):
            if r == 0 or r == self.row_num - 1:
                li = [P_OUT for _ in range(self.col_num)]
                self.data.append(li)
            else:
                li = []
                for c in range(self.col_num):
                    if c == 0 or c == self.col_num - 1:
                        li.append(P_OUT)
                    else:
                        li.append(P_EMPTY)

                self.data.append(li)

    def get(self, row, col):
        return self.data[row][col]
    
    def set(self, row, col, piece):
        self.data[row][col] = piece
        self.history.append((row, col))
    
    def undo(self):
        if len(self.history) != 0:
            self.history.pop()
            self.history.pop()
    
    def has_piece_at(self, row, col):
        return self.get(row, col) != P_EMPTY

    def render(self, target_screen):
        width_begin = BOARD_RENDER_PADDING
        width_end = BOARD_RENDER_PADDING + BOARD_RENDER_WIDTH

        height_begin = BOARD_RENDER_PADDING
        height_end = BOARD_RENDER_PADDING + BOARD_RENDER_HEIGHT

        # render vertical lines.
        for i in range(self.row_num):
            pygame.draw.line(target_screen, 
                             LINE_COLOR, 
                             (i * SQUARE_RENDER_WIDTH + BOARD_RENDER_PADDING, height_begin), 
                             (i * SQUARE_RENDER_WIDTH + BOARD_RENDER_PADDING, height_end))

        # render horizontal lines.
        for i in range(self.col_num):
            pygame.draw.line(target_screen, 
                             LINE_COLOR, 
                             (width_begin, i * SQUARE_RENDER_WIDTH + BOARD_RENDER_PADDING), 
                             (width_end, i * SQUARE_RENDER_WIDTH + BOARD_RENDER_PADDING))
            
        # render pieces.
        for hist in self.history:
            r, c = hist
            p = self.get(r, c)

            if p == P_USER:
                # draw solid circle.
                pygame.draw.circle(target_screen, 
                                   USER_PIECE_COLOR, 
                                   (BOARD_RENDER_PADDING + (r - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH, 
                                    BOARD_RENDER_PADDING + (c - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH), 
                                   PIECE_RENDER_CIRCLE_RADIUS)
                
                # draw outer circle.
                pygame.draw.circle(target_screen, 
                                   LINE_COLOR, 
                                   (BOARD_RENDER_PADDING + (r - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH, 
                                    BOARD_RENDER_PADDING + (c - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH), 
                                   PIECE_RENDER_CIRCLE_RADIUS,
                                   PIECE_RENDER_CIRCLE_WIDTH)
            elif p == P_AI:
                pygame.draw.circle(target_screen, 
                                   AI_PIECE_COLOR, 
                                   (BOARD_RENDER_PADDING + (r - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH, 
                                    BOARD_RENDER_PADDING + (c - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH), 
                                   PIECE_RENDER_CIRCLE_RADIUS)
                
                pygame.draw.circle(target_screen, 
                                   LINE_COLOR, 
                                   (BOARD_RENDER_PADDING + (r - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH, 
                                    BOARD_RENDER_PADDING + (c - BOARD_EXTRA_PADDING) * SQUARE_RENDER_WIDTH), 
                                   PIECE_RENDER_CIRCLE_RADIUS,
                                   PIECE_RENDER_CIRCLE_WIDTH)


def convert_mouse_pos_to_board_pos(pos):
    x = round((pos[0] - BOARD_RENDER_PADDING) / SQUARE_RENDER_WIDTH)
    y = round((pos[1] - BOARD_RENDER_PADDING) / SQUARE_RENDER_WIDTH)

    return (x + BOARD_EXTRA_PADDING, y + BOARD_EXTRA_PADDING)


def check_one_direction_if_has_5(target_board, row, col, rowGap, colGap):
    num = 1
    p = target_board.get(row, col)

    tempRow = row
    tempCol = col

    while True:
        tempRow += rowGap
        tempCol += colGap
        tempP = target_board.get(tempRow, tempCol)

        if tempP == p and tempP != P_OUT:
            num += 1
        else:
            break

    tempRow = row
    tempCol = col

    while True:
        tempRow -= rowGap
        tempCol -= colGap
        tempP = target_board.get(tempRow, tempCol)

        if tempP == p and tempP != P_OUT:
            num += 1
        else:
            break

    return num >= 5


def check_if_has_5(target_board, row, col):
    return check_one_direction_if_has_5(target_board, row, col, -1, -1) or \
            check_one_direction_if_has_5(target_board, row, col, -1, 0) or \
            check_one_direction_if_has_5(target_board, row, col, -1, 1) or \
            check_one_direction_if_has_5(target_board, row, col, 0, -1)


# user score is positive, ai score is negative.
def evaluate_one_kind_of_chess_type(user_piece_num, ai_piece_num):
    if user_piece_num == 0 and ai_piece_num == 0:
        return 0
    
    if user_piece_num > 0 and ai_piece_num > 0:
        return 0
    
    if user_piece_num > 0:
        if user_piece_num == 1:
            return 15
        elif user_piece_num == 2:
            return 400
        elif user_piece_num == 3:
            return 1800
        elif user_piece_num == 4:
            return 100000
        else:
            return 1000000
        
    if ai_piece_num > 0:
        if ai_piece_num == 1:
            return -15
        elif ai_piece_num == 2:
            return -400
        elif ai_piece_num == 3:
            return -1800
        elif ai_piece_num == 4:
            return -100000
        else:
            return -1000000
        
    return 0


def evaluate_one_direction(target_board, score_map, rowGap, colGap):
    for r in range(BOARD_EXTRA_PADDING, BOARD_EXTRA_PADDING + BOARD_ROW_NUM):
        for c in range(BOARD_EXTRA_PADDING, BOARD_EXTRA_PADDING + BOARD_COL_NUM):
            user_num = 0
            ai_num = 0

            total = 5
            tempRow = r
            tempCol = c

            while total > 0:
                p = target_board.get(tempRow, tempCol)

                if p == P_OUT:
                    break
                elif p == P_USER:
                    user_num += 1
                elif p == P_AI:
                    ai_num += 1
                
                total -= 1
                tempRow += rowGap
                tempCol += colGap

            score = evaluate_one_kind_of_chess_type(user_num, ai_num)

            total = 5
            tempRow = r
            tempCol = c

            while total > 0:
                p = target_board.get(tempRow, tempCol)

                if p == P_OUT:
                    break
                elif p == P_EMPTY:
                    score_map[tempRow][tempCol] += score

                total -= 1
                tempRow += rowGap
                tempCol += colGap


def evaluate_board(target_board):
    # score is a 2D array.
    score_map = []

    for _ in range(BOARD_ROW_NUM + 2 * BOARD_EXTRA_PADDING):
        li = []
        for _ in range(BOARD_COL_NUM + 2 * BOARD_EXTRA_PADDING):
            li.append(0)
        score_map.append(li)

    # calculate score.
    evaluate_one_direction(target_board, score_map,  0,  1)
    evaluate_one_direction(target_board, score_map,  0, -1)
    evaluate_one_direction(target_board, score_map,  1,  0)
    evaluate_one_direction(target_board, score_map, -1,  0)
    evaluate_one_direction(target_board, score_map,  1,  1)
    evaluate_one_direction(target_board, score_map,  1, -1)
    evaluate_one_direction(target_board, score_map, -1,  1)
    evaluate_one_direction(target_board, score_map, -1, -1)

    return score_map


def ai_random_gen_a_move():
    row = random.randint(BOARD_EXTRA_PADDING, BOARD_ROW_NUM + BOARD_EXTRA_PADDING - 1)
    col = random.randint(BOARD_EXTRA_PADDING, BOARD_COL_NUM + BOARD_EXTRA_PADDING - 1)
    
    return (row, col)


def ai_gen_best_move(target_board):
    # low score is better for ai, high score is better for user.
    score = evaluate_board(target_board)

    bestRow = 0
    bestCol = 0
    minScore = 9999999

    for r, row in enumerate(score):
        for c, value in enumerate(row):
            if value <= minScore:
                bestRow = r
                bestCol = c
                minScore = value

    return (bestRow, bestCol)


def draw_text(surface, text, text_color, text_size, centerx, top):
    font = pygame.font.Font(FONT_NAME, text_size)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect()
    text_rect.centerx = centerx
    text_rect.top = top
    surface.blit(text_surface, text_rect)


def show_page_welcome(target_screen):
    global game_running
    global game_current_page

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
            return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game_current_page = SHOW_PAGE_BOARD
            return

    screen.fill(BACKGROUND_COLOR)
    draw_text(target_screen, 'Gobang', (131, 139, 139), 50, SCREEN_RENDER_WIDTH // 2, SCREEN_RENDER_HEIGHT * 2 // 5)
    draw_text(target_screen, 'just use mouse buttons, right button to undo.', (108, 123, 139), 20, SCREEN_RENDER_WIDTH // 2, SCREEN_RENDER_HEIGHT * 4 // 5)
    pygame.display.flip()


def show_page_board(target_board):
    global game_running
    global game_current_page
    global game_remake_board

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
            return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == PYGAME_LEFT_MOUSEBUTTON_NUMBER:
                r, c = convert_mouse_pos_to_board_pos(pygame.mouse.get_pos())
                if target_board.has_piece_at(r, c):
                    continue

                target_board.set(r, c, P_USER)
                if check_if_has_5(target_board, r, c):
                    game_current_page = SHOW_PAGE_YOU_WIN
                    game_remake_board = True
                    return

                r, c = ai_gen_best_move(target_board)
                target_board.set(r, c, P_AI)
                if check_if_has_5(target_board, r, c):
                    game_current_page = SHOW_PAGE_YOU_LOSE
                    game_remake_board = True
                    return
            elif event.button == PYGAME_RIGHT_MOUSEBUTTON_NUMBER:
                target_board.undo()

    # clear screen and render.
    screen.fill(BACKGROUND_COLOR)
    board.render(screen)
    pygame.display.flip()


def show_page_you_win(target_screen):
    global game_running
    global game_current_page

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
            return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game_current_page = SHOW_PAGE_WELCOME
            return

    screen.fill(BACKGROUND_COLOR)
    draw_text(target_screen, 'You Win!', (72, 118, 255), 50, SCREEN_RENDER_WIDTH // 2, SCREEN_RENDER_HEIGHT // 2)
    pygame.display.flip()


def show_page_you_lose(target_screen):
    global game_running
    global game_current_page

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
            return
        elif event.type == pygame.MOUSEBUTTONDOWN:
            game_current_page = SHOW_PAGE_WELCOME
            return

    screen.fill(BACKGROUND_COLOR)
    draw_text(target_screen, 'You Lose!', (255, 0, 0), 50, SCREEN_RENDER_WIDTH // 2, SCREEN_RENDER_HEIGHT // 2)
    pygame.display.flip()


# init.
board = Board()
pygame.init()
screen = pygame.display.set_mode((SCREEN_RENDER_WIDTH, SCREEN_RENDER_HEIGHT))

# ai first.
ai_row, ai_col = ai_random_gen_a_move()
board.set(ai_row, ai_col, P_AI)

while game_running:
    game_clock.tick(GAME_FPS)

    if game_current_page == SHOW_PAGE_WELCOME:
        show_page_welcome(screen)
    elif game_current_page == SHOW_PAGE_BOARD:
        if game_remake_board:
            board = Board()

            # ai first.
            ai_row, ai_col = ai_random_gen_a_move()
            board.set(ai_row, ai_col, P_AI)
            game_remake_board = False

        show_page_board(board)
    elif game_current_page == SHOW_PAGE_YOU_WIN:
        show_page_you_win(screen)
    elif game_current_page == SHOW_PAGE_YOU_LOSE:
        show_page_you_lose(screen)
    else:
        break

pygame.quit()
