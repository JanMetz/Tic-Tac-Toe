import uuid

from utility import encodePieceType, decodePieceType

pieces = dict([])  # key is game id, value is an array of all the pieces placed in this game
players = dict([])  # key is game id, value is an array of all the players of this game
games = []  # stores game_ids


class Piece:
    row = None
    column = None
    type = None

    def __init__(self, msg):
        self.row = msg[2]
        self.column = msg[1]
        self.type = decodePieceType(msg[0])


def canPlacePiece(new_piece, game_id):
    for piece in pieces[game_id]:
        if new_piece.row == piece.row and new_piece.column == piece.column:
            return False
    return True


def whoWon(new_piece, game_id):
    horizontal = 0
    vertical = 0
    across_down = 0
    across_up = 0

    for piece in pieces[game_id]:
        if piece.type == new_piece.type:
            if piece.row == new_piece.row:
                horizontal += 1

            if piece.column == new_piece.column:
                vertical += 1

            if piece.column == piece.row:
                across_down += 1

            if piece.column == (3 - piece.row):
                across_up += 1

    if horizontal == 3 or vertical == 3 or across_down == 3 or across_up == 3:
        return encodePieceType(new_piece.type)  # new_piece.type is a winner
    elif len(pieces[game_id]) == 9:
        return 2  # draw
    else:
        return 3  # no winners yet


def whoseMove(game_id):
    x_cnt = 0
    o_cnt = 0

    for piece in pieces[game_id]:
        if piece.type == 'x':
            x_cnt += 1
        elif piece.type == 'o':
            o_cnt += 1

    if x_cnt <= o_cnt:
        return 'x'
    else:
        return 'o'


def generateGameId():
    while True:
        game_id = uuid.uuid4().time_mid  # 16 bits = enough ids to run 65536 games at once
        if game_id not in games:
            return game_id


def setupNewGame(game_id, websocket):
    games.append(game_id)
    pieces[game_id] = []
    players[game_id] = [websocket]


def getOtherPlayer(game_id, player1):
    if players[game_id][0] == player1:
        return players[game_id][1]
    else:
        return players[game_id][0]


def cleanupGame(game_id):
    games.remove(game_id)
    players.pop(game_id)
    pieces.pop(game_id)
