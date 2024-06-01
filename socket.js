let websocket;
let pieceMsgDelivered;

/*
codes:
    A) sent by client:
        254 - reconnect
        246 - new connection
        222 - ACK
        110 - piece request

    B) sent by server:
        111 - piece information
        113 - piece type assignment
        223 - game over
        225 - move time
        227 - game id
        229 - invalid game id error
*/

function initSocket() {
        pieceMsgDelivered = false;
        websocket = new WebSocket("ws://127.0.0.1:8000");
        websocket.binaryType = "arraybuffer";
        websocket.onopen = function(e) { onOpen(e) };
        websocket.onclose = function(e) { onClose(e) };
        websocket.onmessage = function(e) { onMessage(e) };
        websocket.onerror = function(e) { onError(e) };
}

function onOpen(e) {
    let buffer = new ArrayBuffer(3);
    const dv = new DataView(buffer);

    if (localStorage.getItem('game.id') !== null) {
        dv.setUint8(0, 254);  // reconnect
        dv.setUint16(1, parseInt(localStorage['game.id']));
    }
    else {
        dv.setUint8(0, 246);  // new connection
        dv.setUint16(1, 0);
    }

    websocket.send(buffer);
}

function decodeType(dv, offset){
    if (dv.getUint8(offset) === 0)
            return 'o';
        else if (dv.getUint8(offset) === 1)
            return 'x';
}

async function onMessage(e) {
    const dv = new DataView(e.data);
    if (dv.getUint8(0) === 111) { //new piece information
        let row = dv.getUint8( 1);
        let column = dv.getUint8( 2);
        let type = decodeType(dv,   3)

        pieceMsgDelivered = true;
        placePiece(new Cell(row, column, type));
        await sendAck(e.data);
    }

    if (dv.getUint8(0) === 113) { //piece type assignment
        assignPieceType(decodeType(dv,   1));

        await sendAck(e.data);
    }

    if (dv.getUint8(0) === 223) { //game over
        if (dv.getUint8( 1) === 0)
            endGame("Player O won!");
        else if (dv.getUint8( 1) === 1)
            endGame("Player X won!");
        else if (dv.getUint8(1) === 2)
            endGame("Draw!");

        await sendAck(e.data);
    }

    if (dv.getUint8(0) === 225) { //move time
        setMoveEnabled(true);
        pieceMsgDelivered = true;
        alert('Your move!');

        await sendAck(e.data);
    }

     if (dv.getUint8(0) === 227) { //game id
        localStorage['game_id'] = dv.getUint16(1);

        await sendAck(e.data);
    }

     if (dv.getUint8(0) === 229) { //invalid game id error
        localStorage.removeItem('game.id')

        await sendAck(e.data);
        alert('Refresh site!');
     }
}

async function sendAck(buffer) {
    const dv = new DataView(buffer);
    dv.setUint8(0, 222); //clients ACK

    for (let i = 0; i < 3; i++) {
        websocket.send(buffer);
        await new Promise(r => setTimeout(r, 100));
    }
}

function onClose(e){
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

    while (!pieceMsgDelivered) {
        websocket.send(buffer);
        await new Promise(r => setTimeout(r, 100));
    }
}

function onError(){
    console.log("error");
}