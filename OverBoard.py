import subprocess
import cv2
import numpy as np
import pickle
from find_board import *
import os
from engine import *
from time import sleep
import RPi.GPIO as GPIO
import I2C_LCD_driver

def condense_position(position):
    position_split = position.split('/')
    fixed_position_split = []
    for line in position_split:
        count = 0
        new_line = ""
        for ch in line:
            if ch == '_':
                count += 1
            else:
                if count != 0:
                    new_line += str(count)
                    count = 0
                new_line += ch
        if count != 0:
            new_line += str(count)
        fixed_position_split.append(new_line)
    return "/".join(fixed_position_split)

def square_value(board, square):
    count = 0
    ys = square[0,1]
    ye = square[2,1]
    xs = square[0,0]
    xe = square[1,0]
    shrink_y = int((ye - ys) / 10)
    shrink_x = int((xe - xs) / 10)
    board_square = board[ys + shrink_y:ye - shrink_y, xs + shrink_x:xe - shrink_x]
    square_avg = np.mean(board_square, axis=(0,1))
    std = np.abs(board_square - square_avg)
    std_avg = np.mean(std, axis=(0,1))
    count += 1
    return std_avg

def get_square_values(board, squares):
    square_vals = {}
    for key in list(squares):
        if key != 'Boundaries':
            val = square_value(board, squares.get(key))
            square_vals.update({key: val})
    return square_vals

def get_max_diff(prev, current):
    prev_vals = np.array(list(prev.values()))
    current_vals = np.array(list(current.values()))
    keys = list(current.keys())
    diffs = np.mean(np.abs(current_vals - prev_vals), axis=1)
    idx = (-diffs).argsort()[:4]
    sorted_inds = np.argsort(diffs)
    for i in range(1, 5):
        print(keys[sorted_inds[-i]], diffs[sorted_inds[-i]])
    return [keys[i] for i in idx]


def update_position(move_played, position):
    position_split = position.split('/')
    if move_played == 'O-O':
        if to_play == 'w':
            position_split[7] = position_split[7][0:4] + "_RK_"
        else:
            position_split[0] = position_split[0][0:4] + "_rk_"
    elif move_played == 'O-O-O':
        if to_play == 'w':
            position_split[7] = "__KR_" + position_split[7][5:]
        else:
            position_split[0] = "__kl_" + position_split[0][5:]
    else:
        if len(move_played) == 5:
            move_played = move_played[1:]
        rank_1 = 8 - int(move_played[1])
        file_1 = ord(move_played[0]) - 97
        piece_1 = position_split[rank_1][file_1]

        rank_2 = 8 - int(move_played[3])
        file_2 = ord(move_played[2]) - 97
        piece_2 = position_split[rank_2][file_2]

        rank_1_list = list(position_split[rank_1])
        rank_2_list = list(position_split[rank_2])
        if rank_1 == rank_2:
            rank_2_list = rank_1_list
        if piece_1 == '_':
            rank_1_list[file_1] = piece_2
            rank_2_list[file_2] = '_'
        elif piece_2 == '_':
            rank_1_list[file_1] = '_'
            rank_2_list[file_2] = piece_1
        else:
            if to_play == 'w':
                if piece_1.isupper():
                    rank_1_list[file_1] = '_'
                    rank_2_list[file_2] = piece_1
                else:
                    rank_1_list[file_1] = piece_2
                    rank_2_list[file_2] = '_'
            else:
                if piece_1.isupper():
                    rank_1_list[file_1] = piece_2
                    rank_2_list[file_2] = '_'
                else:
                    rank_1_list[file_1] = '_'
                    rank_2_list[file_2] = piece_1
        position_split[rank_1] = "".join(rank_1_list)
        position_split[rank_2] = "".join(rank_2_list)
    position = "/".join(position_split)
    return position


def get_move(diff, to_play, position):
    position_split = position.split('/')
    if set(diff) == w_OO or set(diff) == b_OO:
        to_return = ['O-O']
    elif set(diff) == w_OOO or set(diff) == b_OOO:
        to_return = ['O-O-O']
    else:
        rank_1 = 8 - int(diff[0][1])
        file_1 = ord(diff[0][0]) - 97
        piece_1 = position_split[rank_1][file_1]

        rank_2 = 8 - int(diff[1][1])
        file_2 = ord(diff[1][0]) - 97
        piece_2 = position_split[rank_2][file_2]

        if piece_1 == '_':
            to_return = [diff[1], diff[0]]
        elif piece_2 == '_':
            to_return = [diff[0], diff[1]]
        else:
            if to_play == 'w':
                if piece_1.isupper():
                    to_return = [diff[0], diff[1]]
                else:
                    to_return = [diff[1], diff[0]]
            else:
                if piece_1.isupper():
                    to_return = [diff[1], diff[0]]
                else:
                    to_return = [diff[0], diff[1]]
    move_played = "".join(to_return)
    if move_played[0].upper() == 'P':
        move_played = move_played[1:]
    return move_played

def input_button(text):
    print(text)
    while GPIO.input(11) == GPIO.LOW:
        pass
    sleep(0.5)


def display_board_diff(prev_board, board):
    p = cv2.cvtColor(prev_board, cv2.COLOR_BGR2GRAY)
    c = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)
    blur_prev = cv2.GaussianBlur(p, (5,5), 0)
    blur_prev = cv2.GaussianBlur(blur_prev, (5,5), 0)
    blur_curr = cv2.GaussianBlur(c, (5,5), 0)
    blur_curr = cv2.GaussianBlur(blur_curr, (5,5), 0)
    diff_board = blur_curr - blur_prev
    diff_board[diff_board < 0] = 0
    cv2.imshow('diff', diff_board)
    cv2.waitKey()

if __name__ == "__main__":
    u_play = 'w'
    comp_play = 'b'
    mylcd = I2C_LCD_driver.lcd()
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    squares = read_square_map()
    [board_top, board_bottom, board_left, board_right] = squares.get('Boundaries')
    initial = True
    w_OO = set(['e1', 'f1', 'g1', 'h1'])
    b_OO = set(['e8', 'f8', 'g8', 'h8'])
    w_OOO = set(['a1', 'c1', 'd1', 'e1'])
    b_OOO = set(['a8', 'c8', 'd8', 'e8'])
    position = "rnbqkbnr/pppppppp/________/________/________/________/PPPPPPPP/RNBQKBNR"
    move = 0
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    to_play = 'w'
    mylcd.lcd_display_string("Reset board", 1)
    input_button("Reset board...")
    while(True):
        image_path = "positions/move_{}.jpg".format(move)
        if not os.path.isfile(image_path):
            capture_image(image_path)
        img = cv2.imread(image_path, 1)
        img = resize_img(img)
        board = img[board_top:board_bottom, board_left:board_right]
        current = get_square_values(board, squares)
        if initial:
            mylcd.lcd_display_string("Init. done!", 1)
            mylcd.lcd_display_string("W to play", 2)
            initial = False
            prev = current
        else:
            print("Move number:{}".format(move))
            diff = get_max_diff(prev, current)
            # for coord in diff:
            #     temp = cv2.drawContours(board, [squares.get(coord)], 0, (0,0,255), 1)
            # cv2.imshow("temp", temp)
            # cv2.waitKey()
            # pieces = update_position(position, diff, to_play)
            if move > 1:
                prev_move = move_played
            move_played = get_move(diff, to_play, position)
            print(to_play, move_played)
            position = update_position(move_played, position)
            print(condense_position(position))
            prev = current
            if to_play != comp_play:
                print('Calculating...')
                comp_played = stockfish_move(condense_position(position), comp_play)
                to_write1 = to_play.upper() + ": " + move_played
                to_write2 = comp_play.upper() + " to play (" + comp_played + ")"
                mylcd.lcd_clear()
                mylcd.lcd_display_string(to_write1, 1)
                mylcd.lcd_display_string(to_write2, 2)
            else:
                to_write1 = u_play.upper() + ": " + prev_move + " " + comp_play.upper() + ": " + move_played
                to_write2 = u_play.upper() + " to play"
                mylcd.lcd_clear()
                mylcd.lcd_display_string(to_write1, 1)
                mylcd.lcd_display_string(to_write2, 2)
            if to_play == 'w':
                to_play = 'b'
            else:
                to_play = 'w' 
        move += 1
        input_button("Press enter after move is played.")
        # cv2.imshow('initial', board)
        # cv2.waitKey()