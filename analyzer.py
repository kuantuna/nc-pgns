"""
Camel Analyzer v0.1
Created by Tuna Tuncer
Date: Mar 31, 2023
Contact: tuna.tuncer@ozu.edu.tr
"""

import argparse
import asyncio
import chess
import chess.engine
import chess.pgn
import json

from datetime import datetime
from tqdm import tqdm


parser = argparse.ArgumentParser()
parser.add_argument("-ep", "--enginepath", dest="engine_path",
                    default="lc0/build/release/", help="Engine path")
parser.add_argument("-pp", "--pgnpath", dest="pgn_path",
                    default="nc-pgns/2500+2020.pgn", help="Pgn path")
parser.add_argument("-n", "--nodes", dest="nodes",
                    help="Number of nodes to analyze", type=int)
args = parser.parse_args()
if not args.nodes:
    parser.error('Number of nodes is not specified, please add -n')


cache = {}


async def main() -> None:
    print(f'Camel Analyzer v0.1')
    """Load the engine and pgn"""
    _, engine = await chess.engine.popen_uci(args.engine_path)
    pgn = open(args.pgn_path)

    """Read every game"""
    while True:
        game: chess.pgn.Game = chess.pgn.read_game(pgn)
        if game is None:
            break
        game_data = {
            'white_player_name': game.headers['White'].split(',')[0],
            'white_player_surname': game.headers['White'].split(',')[1].strip(),
            'black_player_name': game.headers['Black'].split(',')[0],
            'black_player_surname': game.headers['Black'].split(',')[1].strip(),
            'result': game.headers['Result'],
            'event': game.headers['Event'],
            'date': game.headers['Date'],
            'white_elo': game.headers['WhiteElo'],
            'black_elo': game.headers['BlackElo'],
            'positions': []
        }
        position: chess.Board = game.board()
        """Iterate through every move in a game and extract evaluations for every position"""
        for game_move in tqdm(game.mainline_moves()):
            fen: str = position.fen()

            """Check whether the position is already in the cache or in db"""
            if cache.get(fen) is not None or False:
                # (instead of checking 'or False' the check should be 'db.get(fen) is not None')
                position.push(game_move)
                continue

            cache[fen] = True
            if is_game_finished(position):
                break

            info = None
            with await engine.analysis(position, multipv=500) as analysis:
                async for a in analysis:
                    info = analysis.multipv
                    if a['nodes'] > args.nodes:
                        break
            game_data['positions'].append({
                'ply': position.ply(),
                'fen': fen,
                'multipv': []
            })
            for i in info:
                move = i['pv'][0]
                color = i['score'].turn
                wdl = i['wdl'].pov(color)
                game_data['positions'][-1]['multipv'].append({
                    'move': {
                        'piece': position.piece_at(move.from_square).symbol(),
                        'from_square': chess.square_name(move.from_square),
                        'to_square': chess.square_name(move.to_square),
                        'promotion': chess.piece_symbol(move.promotion) if move.promotion else None,
                        'color': color
                    },
                    'wins': wdl.wins,
                    'draws': wdl.draws,
                    'losses': wdl.losses,
                    'expectation': wdl.expectation(),
                    'nodes': i['nodes']
                })
            position.push(game_move)

        print(
            f"[{game.headers['White']} - {game.headers['Black']}] analysis completed.\n")
        """Write evaluations to json file"""
        with open(f'nc-data/{int(datetime.timestamp(datetime.now()))}.json', 'w', encoding='utf-8') as f:
            json.dump(game_data, f, ensure_ascii=False, indent=4)

    """Clean-up"""
    await engine.quit()


def is_game_finished(position: chess.Board):
    return position.is_checkmate() or position.is_stalemate() or position.is_insufficient_material()


if __name__ == '__main__':
    await main()
