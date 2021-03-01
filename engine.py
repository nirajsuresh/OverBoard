from stockfish import Stockfish

def stockfish_move(position, to_play):
    stockfish = Stockfish("/usr/games/stockfish")
    fen_line = position + " " + to_play + " KQkq - 0 0"
    stockfish.set_fen_position(fen_line)
    return stockfish.get_best_move_time(1000)