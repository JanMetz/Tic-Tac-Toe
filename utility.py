
def unpackMessage(payload):  # turns bytes object to an array of ints treating each set of 8 bits as a different number
    decimal_number = int.from_bytes(payload, byteorder='big', signed=False)

    translated = []
    while decimal_number > 0:
        translated.append(decimal_number & 255)
        decimal_number = decimal_number >> 8

    return translated


def packMessage(message):  # turns array of ints into a bytes object making each number into next set of 8 bits
    packed = 0
    for idx, decimal in enumerate(message):
        packed += decimal << (idx * 8)

    return packed.to_bytes(len(message), byteorder='big', signed=False)


def encodePieceType(piece_type):
    if piece_type == 'o':
        return 0
    else:
        return 1


def decodePieceType(piece_type):
    if piece_type == 0:
        return 'o'
    else:
        return 'x'


# compares addresses of the sockets, omits port numbers
def areIdenticalSocks(addr1, addr2):
    return addr1.remote_address[0] == addr2.remote_address[0]


def debugMsg(msg):
    if msg[-1] == 254:
        return 'reconnect'
    elif msg[-1] == 246:
        return 'new connection'
    elif msg[-1] == 110:
        return 'piece request'
    elif msg[-1] == 222:
        return 'ACK'

    elif msg[-1] == 111:
        return 'piece information'
    elif msg[-1] == 113:
        return 'piece type assignment'
    elif msg[-1] == 223:
        return 'game over'
    elif msg[-1] == 225:
        return 'move time'
    elif msg[-1] == 227:
        return 'game id'
    elif msg[-1] == 229:
        return 'invalid game id error'
    elif msg[-1] == 231:
        return 'reconnect successful'
