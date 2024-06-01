import uuid

from utility import encodePieceType

# Store all connected clients
pieces = dict([])  # key is game id, value is an array of all the pieces placed in this game
players = dict([])  # key is game id, value is an array of all the players of this game
games = []


class Piece:
    row = None
    column = None
    type = None

    def __init__(self, msg):
        self.row = msg[2]
        self.column = msg[1]
        self.type = msg[0]


class Player:
    socket = None
    piece_type = None

    def __init__(self, socket, piece_type):
        self.socket = socket
        self.piece_type = piece_type


def canPlacePiece(new_piece, game_id):
    for piece in pieces[game_id]:
        if new_piece.row == piece.row and new_piece.column == piece.column:
            return False
    return True


def canContinueGame(game_id):
    return len(pieces[game_id]) != 9  # todo change the magic number?


def whoWon(new_piece, game_id):
    horizontal = 0
    vertical = 0
    across = 0

    for piece in pieces[game_id]:
        if piece.type == new_piece.type:
            if piece.row == new_piece.row:
                horizontal += 1

            if piece.column == new_piece.column:
                vertical += 1

            if piece.column == piece.row:
                across += 1

    if horizontal == 3 or vertical == 3 or across == 3:
        return encodePieceType(new_piece.type)


def whoseMove(game_id):
    x_cnt = 0
    o_cnt = 0

    for piece in pieces[game_id]:
        if piece.type == 'x':
            x_cnt += 1
        elif piece.type == 'o':
            o_cnt += 1

    if x_cnt < o_cnt:
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