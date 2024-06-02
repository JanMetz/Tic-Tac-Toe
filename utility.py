import asyncio


async def sendTillACK(socket, msg_arr):
    packed = packMessage(msg_arr)
    while True:
        print(f'Sending: {debugMsg(msg_arr)} {msg_arr}')
        await socket.send(packed)
        break
        '''async with asyncio.timeout(200):
            received = unpackMessage(await socket.recv())
            if received[-1] == 222 and msg_arr == received[:-1]:  # ACK
                break'''


def unpackMessage(payload):
    decimal_number = int.from_bytes(payload, byteorder='big', signed=False)

    translated = []
    while decimal_number > 0:
        translated.append(decimal_number & 255)
        decimal_number = decimal_number >> 8

    return translated


def packMessage(message):
    packed = 0
    for idx, decimal in enumerate(message):
        packed += decimal << (idx * 8)

    return packed.to_bytes(len(message), byteorder='big', signed=False)


def encodePieceType(piece_type):
    if piece_type == 'o':
        return 0
    else:
        return 1


def debugMsg(msg):
    if msg[-1] == 254:
        return 'reconnect'
    if msg[-1] == 246:
        return 'new connection'
    if msg[-1] == 222:
        return 'ACK'
    if msg[-1] == 110:
        return 'piece request'

    if msg[-1] == 111:
        return 'piece information'
    if msg[-1] == 113:
        return 'piece type assignment'
    if msg[-1] == 223:
        return 'game over'
    if msg[-1] == 225:
        return 'move time'
    if msg[-1] == 227:
        return 'game id'
    if msg[-1] == 229:
        return 'invalid game id error'


