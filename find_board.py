import subprocess
import cv2
import numpy as np
import pickle

def write_square_map(squares):
    with open('square_map.pkl', 'wb') as f:
        pickle.dump(squares, f, pickle.HIGHEST_PROTOCOL)

def read_square_map():
    with open('square_map.pkl', 'rb') as f:
        return pickle.load(f)

def capture_image(file_name, shot_time='1000'):
    print("Capturing image...")
    cmd = "raspistill -vf -o ./" + file_name + " -t " + shot_time
    subprocess.call(cmd, shell=True)
    print("Complete!")

def resize_img(img):
    height, width, channels = img.shape
    new_h = int(height / 5)
    new_w = int(width / 5)
    new_img = cv2.resize(img, (new_w, new_h))
    new_img = cv2.flip(new_img, 1)
    return new_img


def get_mask(img, display=False):
    gray= cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    blur = cv2.GaussianBlur(img, (5,5), 0)
    blur = cv2.GaussianBlur(blur, (5,5), 0)
    blue = img[:,:,0]
    green = img[:,:,1]
    red = img[:,:,2]
    mask1 = np.full((img.shape), False)
    mask1[blue > 1.3 * green] = True
    mask1[blue < 1.5 * red] = False
    mask2 = np.zeros((img.shape))
    mask2[mask1] = 255
    if display:
        cv2.imshow('mask', mask2)
        cv2.waitKey(0)
    cv2.imwrite('mask.jpg', mask2)
    return mask2

def find_board(img):
    mask = get_mask(img, display=True)
    #may need to change depending on lighting
    thresh = 110
    #find top
    h = 0
    try:
        while np.mean(mask[h,:]) < thresh:
            h += 1

        while np.mean(mask[h,:]) > thresh:
            h += 1

        board_top = h

        #find bottom
        while np.mean(mask[h,:]) < thresh:
            h += 1

        board_bottom = h
    except:
        print("Board not found. Exiting.")
        exit()

    #find left
    w = 0
    try:
        while np.mean(mask[:,w]) < thresh:
            w += 1

        while np.mean(mask[:,w]) > thresh:
            w += 1

        board_left = w

        #find bottom
        while np.mean(mask[:,w]) < thresh:
            w += 1

        board_right = w
    except:
        print("Board not found. Exiting.")
        exit()
    return [board_top, board_bottom, board_left, board_right], img[board_top:board_bottom, board_left:board_right]


def get_square_points(board):
    height, width, channels = board.shape
    point_xs = np.linspace(0, width - 1, 9).astype(int)
    point_ys = np.linspace(0, height - 1, 9).astype(int)
    for x_i in range(len(point_xs) - 1):
        for y_i in range(len(point_ys) - 1):
            x_inds = [x_i, x_i + 1, x_i + 1, x_i]
            y_inds = [y_i, y_i, y_i + 1, y_i + 1]
            square = np.array([[point_xs[x_inds[i]], point_ys[y_inds[i]]] for i in range(4)])
            num = str(8 - y_i)
            coord = letters[x_i] + num
            squares.update({coord: square})
            # board[y, x] = [0, 0, 255]


if __name__ == "__main__":
    squares = {}
    image_path = "test_image.jpg"
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    capture_image(image_path, shot_time='10000')
    img = cv2.imread(image_path, 1)
    img = resize_img(img)
    cv2.imshow('Board', img)
    cv2.waitKey(0)
    board_boundaries, board = find_board(img)
    cv2.imwrite('board.jpg', board)
    get_square_points(board)
    squares.update({'Boundaries': board_boundaries})
    write_square_map(squares)
    # for coord in ['a3', 'b4', 'c5', 'd6', 'e7', 'f8', 'g7', 'h6']:
    #     print(get_square_value(board, squares.get(coord)))
    # print()
    for letter in letters:
        for num in range(1,9):
            coord = letter + str(num)
            board = cv2.drawContours(board, [squares.get(coord)], 0, (0,0,255), 1)
    cv2.imwrite('board_squares.jpg', board)
    cv2.imshow('Board', board)
    cv2.waitKey(0)