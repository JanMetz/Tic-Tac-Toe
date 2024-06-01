import websockets

from utility import *
from game_mechanics import *


async def handle_client(websocket, _):
    print(f'Client connected {websocket.remote_address}')

    game_id = ''

    try:
        while True:
            msg_arr = unpackMessage(await websocket.recv())
            print(f'Received: {debugMsg(msg_arr)} {msg_arr}')

            if msg_arr[-1] == 222:  # ACK
                pass
            elif msg_arr[-1] == 110:  # new piece request
                await handleNewPieceRequest(msg_arr, websocket, game_id)
            elif msg_arr[-1] == 246:  # new connection
                game_id = await handleNewClient(websocket)
            elif msg_arr[-1] == 254:  # reconnect
                game_id = await handleReconnect(websocket, msg_arr)
            else:
                print(msg_arr)
                raise Exception('Unknown message type!')

    except websockets.exceptions.ConnectionClosedOK:
        print(f'Client disconnected {websocket.remote_address}')


async def handleReconnect(websocket, msg_arr):
    game_id = msg_arr[-2] << 8 | msg_arr[-1]
    if game_id in games:
        piece_type = None
        for i in range(len(players[game_id])):
            player = players[game_id][i]
            if player.socket.remote_address[0] == websocket.remote_address[0]:
                piece_type = player.piece_type
                players[game_id][i] = websocket
                break

        if piece_type is None:
            await sendTillACK(websocket, [229])  # invalid game id
        else:
            await sendTillACK(websocket, [encodePieceType(piece_type), 113])  # piece type assignment
            if whoseMove(game_id) == piece_type:
                await sendTillACK(websocket, [225])  # move time
    else:
        await sendTillACK(websocket, [229])  # invalid game id


async def handleNewClient(websocket):
    if len(games) != 0 and len(players[games[-1]]) < 2:
        game_id = games[-1]
        players[game_id].append(websocket)
        await sendTillACK(websocket, [encodePieceType('x'), 113])  # piece type assignment
        await sendTillACK(websocket, [225])  # move time
    else:
        game_id = generateGameId()
        setupNewGame(game_id, websocket)
        await sendTillACK(websocket, [encodePieceType('o'), 113])  # piece type assignment

    await sendTillACK(websocket, [game_id & 255, game_id >> 8,  227])  # game id

    return game_id


async def handleNewPieceRequest(msg_arr, player_socket, game_id):
    piece = Piece(msg_arr)
    if canPlacePiece(piece, game_id):
        pieces[game_id].append(piece)
        for player in players[game_id]:
            msg_arr[3] = 111
            await sendTillACK(player, msg_arr)  # new piece

        if canContinueGame(game_id):
            if len(players[game_id]) == 2:
                if players[game_id][0] == player_socket:
                    other_player = players[game_id][1]
                else:
                    other_player = players[game_id][0]

                await sendTillACK(other_player, [225])  # move time
        else:
            for player in players[game_id]:
                await sendTillACK(player, [whoWon(piece, game_id), 223])  # game end
    else:
        await sendTillACK(player_socket, [225])  # move time


if __name__ == '__main__':
    start_server = websockets.serve(handle_client, "localhost", 8000)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
