import argparse
import copy
import sys
import time
from copy import deepcopy

cache = {}  # you can use this to implement state caching!
MAX_VAL = float('inf')
MIN_VAL = float('-inf')
DEPTH_LIMIT = 10


class State:
    # This class is used to represent a state.
    # board : a list of lists that represents the 8*8 board
    def __init__(self, board, turn):

        self.board = board

        self.width = 8
        self.height = 8
        self.turn = turn

    def display(self):
        for i in self.board:
            for j in i:
                print(j, end="")
            print("")
        print("")

    def __str__(self):
        write = ""
        for i in self.board:
            for j in i:
                write += j
            write += "\n"
        write += "\n"
        return write

    def terminal(self):
        black_pieces = ['b', 'B']
        red_pieces = ['r', 'R']
        black_left = False
        red_left = False

        for i in self.board:
            for j in i:
                if j in black_pieces:
                    black_left = True
                if j in red_pieces:
                    red_left = True
                if black_left and red_left:
                    return False
        return True

    def __hash__(self) -> int:
        return hash(str(self))

    def __lt__(self, other):
        return evaluation_function(self) < evaluation_function(other)


def get_opp_char(player):
    if player in ['b', 'B']:
        return ['r', 'R']
    else:
        return ['b', 'B']


def get_next_turn(curr_turn):
    if curr_turn == 'r':
        return 'b'
    else:
        return 'r'


def inside_board(y, x):
    # Helper to check if a coordinate is inside the board
    return y >= 0 and y < 8 and x >= 0 and x < 8


def empty(board, y, x):
    # Helper to check if board[y][x] is empty
    return board[y][x] == '.'


def jumpable(y, x, vector, board, turn):
    # Helper to check if it is possible to jump from a position
    if inside_board(y + vector[0] * 2, x + vector[1] * 2):
        if board[y + vector[0]][x + vector[1]] in get_opp_char(turn) and board[y + vector[0] * 2][x + vector[1] * 2] == '.':
            return True
    return False


def get_vectors(board, y, x):
    # Helper to return the vectors in which a piece can move
    # y + vector [0] should give the new y position, x + vector[1] should give the new x position
    red_vectors = [(-1, 1), (-1, -1)]
    black_vectors = [(1, 1), (1, -1)]
    king_vectors = red_vectors + black_vectors

    if board[y][x] == 'r':
        return red_vectors
    elif board[y][x] == 'b':
        return black_vectors
    else:
        return king_vectors


def promotion(board, y, x):
    # Helper to promote pieces

    if y == 0 and board[y][x] == 'r':
        board[y][x] = 'R'
    elif y == 7 and board[y][x] == 'b':
        board[y][x] = 'B'


def get_simple(state, board, y, x):
    # Helper to get simple moves from a position

    successors = []

    for vector in get_vectors(board, y, x):
        new_y, new_x = y + vector[0], x + vector[1]
        if inside_board(new_y, new_x):
            if empty(board, new_y, new_x):
                new_board = [list(x) for x in board]
                new_board[new_y][new_x], new_board[y][x] = new_board[y][x], new_board[new_y][new_x]
                promotion(new_board, new_y, new_x)
                successors.append(State(new_board, get_next_turn(state.turn)))

    return successors


def get_jump(state, board, y, x, successors, jumped=False):
    # Recursive function to get jump moves from a position

    done_jumping = True

    for vector in get_vectors(board, y, x):

        # Check if inside board

        if inside_board(y + 2 * vector[0], x + 2 * vector[1]):

            # Check if 1 over is an opposing piece, and 2 over is an empty space
            if board[y + vector[0]][x + vector[1]] in get_opp_char(state.turn) and empty(board, y + 2 * vector[0], x + 2 * vector[1]):

                new_board = [list(x) for x in board]

                new_board[y + 2 * vector[0]][x + 2 * vector[1]] = board[y][x]
                new_board[y + vector[0]][x + vector[1]] = '.'
                new_board[y][x] = '.'

                promotion(new_board, y + 2 * vector[0], x + 2 * vector[1])

                get_jump(state, new_board, y + 2 *
                         vector[0], x + 2 * vector[1], successors, True)
                done_jumping = False

    if done_jumping and jumped:
        successors.append(State(board, get_next_turn(state.turn)))


def generate_succesors(state):

    successors = []
    for y in range(0, 8):
        for x in range(0, 8):
            if state.board[y][x].lower() == state.turn:
                get_jump(state, state.board, y, x, successors)
    if successors == []:
        for y in range(0, 8):
            for x in range(0, 8):
                if state.board[y][x].lower() == state.turn:
                    successors += get_simple(state, state.board, y, x)
    return successors


def evaluation_function(state):
    if state.terminal == True:  # terminal
        if state.turn == 'r':
            return MIN_VAL
        else:
            return MAX_VAL

    worth = {
        'r': 4.0,
        'b': -4.0,
        'R': 7.5,
        'B': -7.5
    }

    # multiplier by location
    def multiplier(y, x, piece):
        val = 1
        if x == 0 or x == 7 or y == 0 or y == 7:  # if they hug walls its better
            val = val * 1.1

        if x > 1 and x < 6 and y > 1 and y < 6:  # if closer to centre better
            val = val * 1.3
            if y > 2 and y < 5:
                val = val * 1.075

        if piece == 'r':
            val = val * (1 + (7 - float(y))*0.1)
        elif piece == 'b':
            val = val * (1 + float(y)*0.1)

        return val

    value = 0

    for y in range(0, 8):
        for x in range(0, 8):
            if state.board[y][x] in worth:
                value += worth[state.board[y][x]] * \
                    multiplier(y, x, state.board[y][x])

    return value


def cut_off(state, depth):
    if state.terminal() == True or depth == DEPTH_LIMIT:
        return True
    else:
        return False


def alpha_beta_max(state, alpha, beta, depth):
    if state in cache and cache[state][2] <= depth:
        return (cache[state][0], cache[state][1])
    if cut_off(state, depth):
        return (evaluation_function(state), None)
    if len(generate_succesors(state)) == 0:
        cache[state] = (MIN_VAL, None, depth)
        return (MIN_VAL, None)

    children = sorted(generate_succesors(state), reverse=True)

    v = MIN_VAL
    best = state
    for child in children:
        tempval, tempstate = alpha_beta_min(child, alpha, beta, depth + 1)
        if tempval > v:
            v = tempval
            best = child
        if tempval > beta:
            cache[state] = (v, child, depth)
            return (v, child)
        alpha = max(alpha, tempval)
        cache[state] = (v, best, depth)
    return (v, best)


def alpha_beta_min(state, alpha, beta, depth):
    if state in cache and cache[state][2] <= depth:
        return (cache[state][0], cache[state][1])
    if cut_off(state, depth):
        return (evaluation_function(state), None)
    if len(generate_succesors(state)) == 0:
        cache[state] = (MAX_VAL, None, depth)
        return (MAX_VAL, None)

    children = sorted(generate_succesors(state))

    v = MAX_VAL
    best = state
    for child in children:
        tempval, tempstate = alpha_beta_max(child, alpha, beta, depth + 1)
        if tempval < v:
            v = tempval
            best = child
        if tempval < alpha:
            cache[state] = (v, child, depth)
            return (v, child)
        beta = min(beta, tempval)
        cache[state] = (v, best, depth)
    return (v, best)


def read_from_file(filename):

    f = open(filename)
    lines = f.readlines()
    board = [[str(x) for x in l.rstrip()] for l in lines]
    f.close()

    return board


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzles."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    args = parser.parse_args()

    initial_board = read_from_file(args.inputfile)
    turn = 'r'
    state = State(initial_board, turn)
    ctr = 0

    sys.stdout = open(args.outputfile, 'w')

    while state.terminal() == False:
        ctr += 1
        sys.stdout.write(str(state))
        if turn == 'r':
            v, best = alpha_beta_max(state, MIN_VAL, MAX_VAL, 0)
            state = best
            turn = 'b'
        elif turn == 'b':
            v, best = alpha_beta_min(state, MIN_VAL, MAX_VAL, 0)
            state = best
            turn = 'r'
    sys.stdout.write(str(state))
