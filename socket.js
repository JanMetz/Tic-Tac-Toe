let websocket;
let pieceMsgDelivered;
let openMsgDelivered;

/*
codes:
    A) sent by client:
        254 - reconnect
        246 - new connection
        110 - piece request

    B) sent by server:
        111 - piece information
        113 - piece type assignment
        223 - game over
        225 - move time
        227 - game id
        229 - invalid game id error
        231 - reconnect successful
*/

function initSocket() {
        pieceMsgDelivered = false;
        openMsgDelivered = false;

        websocket = new WebSocket("ws://127.0.0.1:8000");
        websocket.binaryType = "arraybuffer";
        websocket.onopen = function(e) { onOpen(e).then(_ => {}) };
        websocket.onclose = function(e) { onClose(e) };
        websocket.onmessage = function(e) { onMessage(e).then(_ => {}) };
        websocket.onerror = function(e) { onError(e) };
}

async function onOpen(_) {
    let buffer = new ArrayBuffer(4);
    const dv = new DataView(buffer);

    if (localStorage.getItem('game.id') !== null) {
        dv.setUint8(0, 254);  // reconnect
        dv.setUint16(1, parseInt(localStorage['game.id']));
        encodeType(dv, 3, localStorage['game.pieceType']);
    }
    else {
        dv.setUint8(0, 246);  // new connection
        dv.setUint16(1, 0);
        dv.setUint8(3, 0);
    }

    openMsgDelivered = false;

    while (!openMsgDelivered){
        websocket.send(buffer);
        await new Promise(r => setTimeout(r, 100));
    }
}

function decodeType(dv, offset){
    if (dv.getUint8(offset) === 0)
            return 'o';
    else if (dv.getUint8(offset) === 1)
        return 'x';
}

async function onMessage(e) {
    const dv = new DataView(e.data);

    switch (dv.getUint8(0)) {
        case 111: { //new piece information
            let row = dv.getUint8(1);
            let column = dv.getUint8(2);
            let type = decodeType(dv, 3)

            pieceMsgDelivered = true;
            placePiece(new Cell(row, column, type));
            await sendAck(e.data);
            break;
        }

        case 113: { //piece type assignment
            assignPieceType(decodeType(dv, 1));
            break;
        }

        case 223: { //game over
            if (dv.getUint8(1) === 0)
                endGame("Player O won!");
            else if (dv.getUint8(1) === 1)
                endGame("Player X won!");
            else if (dv.getUint8(1) === 2)
                endGame("Draw!");

            await sendAck(e.data);
            break;
        }

        case 225: { //move time
            setMoveEnabled(true);
            pieceMsgDelivered = true;
            await sendAck(e.data);
            break;
        }

        case 227: { //game id
            openMsgDelivered = true;
            assignGameId(dv.getUint16(1));
            break;
        }

        case 229: { //invalid game id error
            openMsgDelivered = true;
            localStorage.clear();
            location.reload();
            break;
        }

        case 231: {  //reconnect successful
            openMsgDelivered = true;
            setMoveEnabled(dv.getUint8(1) === 1);
            break;
        }
    }
}

async function sendAck(buffer) {
    const oldDv = new DataView(buffer);

    let expanded_buffer = new ArrayBuffer(buffer.byteLength + 1);
    const newDv = new DataView(expanded_buffer);
    newDv.setUint8(0, 222); //clients ACK

    for (let i = 0; i < buffer.byteLength; i++)
        newDv.setUint8(i + 1, oldDv.getUint8(i));

    websocket.send(expanded_buffer);
}

function onClose(_){
    console.log("Close");
}

function encodeType(dv, offset, type){
   if (type === 'x')
        dv.setUint8(offset, 1);
    else
        dv.setUint8(offset, 0);
}

async function sendPieceRequest(piece){
    let buffer = new ArrayBuffer(4);
    const dv = new DataView(buffer);
    dv.setUint8(0, 110); //piece request
    dv.setUint8(1, piece.row);
    dv.setUint8(2, piece.column);
    encodeType(dv, 3, piece.type);
    pieceMsgDelivered = false;
    setMoveEnabled(false);

    while (!pieceMsgDelivered) {
        websocket.send(buffer);
        await new Promise(r => setTimeout(r, 100));
    }
}

function onError(){
    console.log("error");
}