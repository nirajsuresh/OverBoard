from niraj_fish import *

if __name__ == "__main__":
    STOCKFISH_PATH = "/usr/games/stockfish"
    moves = []
    chessEngine = Engine(STOCKFISH_PATH, param={'Threads': 2, 'Ponder': 'true'})
    chessEngine.ucinewgame()
    while True:
        moveA = raw_input("Enter move: ")
        moves.append(moveA)
        chessEngine.setposition(moves)
        moveB = chessEngine.bestmove().get('bestmove')
        print(moveB)
        moves.append(moveB)
        chessEngine.setposition(moves)
        print(chessEngine.eval())