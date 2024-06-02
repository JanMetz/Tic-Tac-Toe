import websockets
import asyncio

from utility import *
from game_mechanics import *


class UnconfirmedMsg:
    msg_arr = None
    packed = None
    socket = None

    def __init__(self, socket, msg_arr, packed):
        self.msg_arr = msg_arr
        self.socket = socket
        self.packed = packed


unconfirmed_msgs = dict([])  # key is game id, value is an array of UnconfirmedMsg to keep track of ACK


async def handleConnection(websocket, _):
    print(f'Client connected {websocket.remote_address}')

    game_id = ''

    try:
        while True:
            async with asyncio.timeout(200):
                msg_arr = unpackMessage(await websocket.recv())

                if msg_arr[-1] == 222:  # ACK
                    await handleACK(msg_arr, game_id, websocket)
                elif msg_arr[-1] == 110:  # new piece request
                    await handleNewPieceRequest(msg_arr, websocket, game_id)
                elif msg_arr[-1] == 246:  # new connection
                    game_id = await handleNewClient(websocket)
                elif msg_arr[-1] == 254:  # reconnect
                    game_id = await handleClientsReconnect(websocket, msg_arr)
                else:
                    raise Exception(f'Unknown message type! {msg_arr}')

            await retransmitMsgs(game_id)

    except websockets.exceptions.ConnectionClosedOK:
        print(f'Client disconnected {websocket.remote_address}')


async def retransmitMsgs(game_id):
    if game_id not in unconfirmed_msgs:
        return

    for unconfirmed_msg in unconfirmed_msgs[game_id]:
        socket = unconfirmed_msg.socket

        await socket.send(unconfirmed_msg.packed)


# ACK needed as response for new piece, game over and move time
async def handleACK(msg_arr, game_id, socket):
    idxs_to_pop = []
    for i in range(len(unconfirmed_msgs[game_id])):
        ucnmsg = unconfirmed_msgs[game_id][i]
        if ucnmsg.msg_arr == msg_arr[:-1] and areIdenticalSocks(socket, ucnmsg.socket):
            idxs_to_pop.append(i)

    for i in range(len(idxs_to_pop)):
        idx = idxs_to_pop[i] - i
        # if msg_arr[-2] == 223:  # todo post game end cleanup
        #    cleanupGame(game_id)

        del unconfirmed_msgs[game_id][idx]


# need to update sock info because it will most likely use different port after reconnect
def updateSockInUnconfirmedMsgs(game_id, socket):
    for i in range(len(unconfirmed_msgs[game_id])):
        ucnmsg = unconfirmed_msgs[game_id][i]
        if areIdenticalSocks(ucnmsg.socket, socket):
            unconfirmed_msgs[game_id][i].socket = socket


async def handleClientsReconnect(websocket, msg_arr):
    game_id = msg_arr[2] << 8 | msg_arr[1]

    if game_id in games:
        found_player = False
        for i in range(len(players[game_id])):
            player = players[game_id][i]

            if areIdenticalSocks(player, websocket):
                players[game_id][i] = websocket
                found_player = True
                break

        if not found_player:
            await websocket.send(packMessage([229]))  # invalid game id
        else:
            updateSockInUnconfirmedMsgs(game_id, websocket)
            if whoseMove(game_id) == decodePieceType(msg_arr[0]):
                await websocket.send(packMessage([1, 231]))  # reconnect successful + move time
            else:
                await websocket.send(packMessage([0, 231]))  # reconnect successful
    else:
        await websocket.send(packMessage([229]))  # invalid game id

    return game_id


async def handleNewClient(websocket):
    if len(games) != 0 and len(players[games[-1]]) < 2:
        game_id = games[-1]
        players[game_id].append(websocket)
        await websocket.send(packMessage([encodePieceType('x'), 113]))  # piece type assignment
        await websocket.send(packMessage([225]))  # move time
    else:
        game_id = generateGameId()
        setupNewGame(game_id, websocket)
        unconfirmed_msgs[game_id] = []
        await websocket.send(packMessage([encodePieceType('o'), 113]))  # piece type assignment

    await websocket.send(packMessage([game_id & 255, game_id >> 8,  227]))  # game id

    return game_id


async def sendToEverybody(game_id, msg_arr):
    packed = packMessage(msg_arr)
    for player in players[game_id]:
        unconfirmed_msgs[game_id].append(UnconfirmedMsg(player, msg_arr, packed))
        await player.send(packed)


async def handleNewPieceRequest(msg_arr, player_socket, game_id):
    piece = Piece(msg_arr)

    if game_id in games and canPlacePiece(piece, game_id):
        pieces[game_id].append(piece)
        msg_arr[3] = 111  # new piece

        await sendToEverybody(game_id, msg_arr)

        winner = whoWon(piece, game_id)
        if winner == 3:  # no one won yet

            if len(players[game_id]) == 2:
                msg = [225]  # move time
                packed = packMessage(msg)
                other_player = getOtherPlayer(game_id, player_socket)
                unconfirmed_msgs[game_id].append(UnconfirmedMsg(other_player, msg, packed))
                await other_player.send(packed)
        else:  # game is over

            await sendToEverybody(game_id, [winner, 223])  # game end

    else:  # canPlacePiece(piece, game_id)
        # no need for confirmation - client takes care of it
        await player_socket.send(packMessage([225]))  # move time


if __name__ == '__main__':
    start_server = websockets.serve(handleConnection, "localhost", 8000)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
