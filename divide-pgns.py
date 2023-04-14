import chess
import chess.pgn

pgn_path = "2500+2020.pgn"

pgn = open(pgn_path)

game_counter = 0
start_idx = 1
end_idx = 50
while True:
    game: chess.pgn.Game = chess.pgn.read_game(pgn)
    if game is None:
        break
    print(game, file=open(
        f"2020/2500+/{start_idx:05d}-{end_idx:05d}.pgn", "a"), end="\n\n")
    game_counter += 1
    if game_counter == 50:
        start_idx += 50
        end_idx += 50
        game_counter = 0
