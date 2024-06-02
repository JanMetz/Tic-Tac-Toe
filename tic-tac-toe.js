let kBoardWidth = 3;
let kBoardHeight= 3;
let kPieceWidth = 50;
let kPieceHeight= 50;
let kPixelWidth = 1 + (kBoardWidth * kPieceWidth);
let kPixelHeight= 1 + (kBoardHeight * kPieceHeight);

let gPieceType;
let gCanvasElement;
let gDrawingContext;

let gPieces;
let gGameInProgress;
let gMoveEnabled;

function Cell(row, column, type) {
    this.row = row;
    this.column = column;
    this.type = type;
}

function getCursorPosition(e) {
    /* returns Cell if click is inside board and null if not*/
    let x;
    let y;
    if (e.pageX != undefined && e.pageY != undefined) {
        x = e.pageX;
        y = e.pageY;
    }
    else {
        x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
        y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }

    x -= gCanvasElement.offsetLeft;
    y -= gCanvasElement.offsetTop;

    if ((x > kBoardWidth * kPieceWidth) || (y >  kBoardHeight * kPieceHeight))
        return null

    return new Cell(Math.floor(y/kPieceHeight), Math.floor(x/kPieceWidth), gPieceType);
}

async function gameOnClick(e) {
    if (!gMoveEnabled)
        return;

    let cell = getCursorPosition(e);

    if (cell == null)
        return;

    for (let i = 0; i < gPieces.length; i++) {
        if ((gPieces[i].row === cell.row) && (gPieces[i].column === cell.column)) {
            return;
        }
    }

    await sendPieceRequest(cell);
}

function setMoveEnabled(val){
    gMoveEnabled = val;

    if (gGameInProgress) {
        if (val)
            document.getElementById('msg_box').innerHTML = 'Your move!';
        else
            document.getElementById('msg_box').innerHTML = 'Wait for opponents move...';
    }
}

function placePiece(piece) {
    for (let i = 0; i < gPieces.length; i++) {
        if ((gPieces[i].row === piece.row) && (gPieces[i].column === piece.column)) {
            return;
        }
    }

    gPieces.push(piece);

    drawBoard();
}

function assignPieceType(symbol){
    localStorage["game.pieceType"] = symbol;
    gPieceType = symbol;

    if (gGameInProgress) {
        if (symbol === 'o')
            document.getElementById('msg_box').innerHTML = 'Waiting for opponent to join the game...';
    }
}

function assignGameId(game_id){
    localStorage['game.id'] = game_id;
}

function drawBoard() {
    gDrawingContext.clearRect(0, 0, kPixelWidth, kPixelHeight);

    gDrawingContext.beginPath();

    /* vertical lines */
    for (let x = 0; x <= kPixelWidth; x += kPieceWidth) {
        gDrawingContext.moveTo(0.5 + x, 0);
        gDrawingContext.lineTo(0.5 + x, kPixelHeight);
    }

    /* horizontal lines */
    for (let y = 0; y <= kPixelHeight; y += kPieceHeight) {
        gDrawingContext.moveTo(0, 0.5 + y);
        gDrawingContext.lineTo(kPixelWidth, 0.5 +  y);
    }

    gDrawingContext.strokeStyle = "#ccc";
    gDrawingContext.stroke();

    /* pieces */
    for (let i = 0; i < gPieces.length; i++) {
        if (gPieces[i].type === 'o')
	        drawCircle(gPieces[i]);
        else
            drawX(gPieces[i]);
    }

    saveGameState();
}

function drawCircle(p) {
    let x = (p.column * kPieceWidth) + (kPieceWidth/2);
    let y = (p.row * kPieceHeight) + (kPieceHeight/2);
    let margin = kPieceHeight * 0.1;
    let radius = (kPieceWidth/2) - margin;

    gDrawingContext.beginPath();
    gDrawingContext.arc(x, y, radius, 0, Math.PI*2, false);
    gDrawingContext.closePath();
    gDrawingContext.strokeStyle = "#000";
    gDrawingContext.stroke();
}

function drawX(p){
    let x = (p.column * kPieceWidth);
    let y = (p.row * kPieceHeight);
    let margin = kPieceHeight * 0.1;

    gDrawingContext.beginPath();
    gDrawingContext.moveTo(x + margin, y + margin);
    gDrawingContext.lineTo(x + kPieceWidth - margin, y + kPieceHeight - margin);
    gDrawingContext.closePath();
    gDrawingContext.strokeStyle = "#000";
    gDrawingContext.stroke();

    gDrawingContext.beginPath();
    gDrawingContext.moveTo(x + margin, y + kPieceHeight - margin);
    gDrawingContext.lineTo(x + kPieceWidth - margin, y + margin);
    gDrawingContext.closePath();

    gDrawingContext.strokeStyle = "#000";
    gDrawingContext.stroke();
}

function supportsLocalStorage() {
    return ('localStorage' in window) && window['localStorage'] !== null;
}

function saveGameState() {
    if (!supportsLocalStorage()) {
        return;
    }

    localStorage["game.gameInProgress"] = gGameInProgress;
    for (let i = 0; i < gPieces.length; i++) {
        localStorage["game.piece." + i + ".row"] = gPieces[i].row;
        localStorage["game.piece." + i + ".column"] = gPieces[i].column;
        localStorage["game.piece." + i + ".type"] = gPieces[i].type;
    }

    localStorage["game.pieceType"] = gPieceType;
    localStorage["game.piecesNum"] = gPieces.length;
}

function resumeGame() {
    if (!supportsLocalStorage()) {
        return false;
    }

    gGameInProgress = (localStorage["game.gameInProgress"] === "true");
    if (!gGameInProgress) {
        return false;
    }

    gPieces = new Array(parseInt(localStorage["game.piecesNum"]));
    for (let i = 0; i < gPieces.length; i++) {
        let row = parseInt(localStorage["game.piece." + i + ".row"]);
        let column = parseInt(localStorage["game.piece." + i + ".column"]);
        let type = localStorage["game.piece." + i + ".type"];
        gPieces[i] = new Cell(row, column, type);
    }

    gPieceType = localStorage["game.pieceType"];
    drawBoard();

    return true;
}

function newGame() {
    gPieces = [];
    gGameInProgress = true;
    drawBoard();
}

function endGame(whoWonMsg) {
    gGameInProgress = false;
    localStorage.clear();
    gCanvasElement.removeEventListener("click", gameOnClick, false);
    document.getElementById('msg_box').innerHTML = "Game over! " + whoWonMsg;
}

function initGame(canvasElement) {
    if (!canvasElement) {
        canvasElement = document.createElement("canvas");
        canvasElement.id = "game_canvas";
        document.body.appendChild(canvasElement);
    }

    gCanvasElement = canvasElement;
    gCanvasElement.width = kPixelWidth;
    gCanvasElement.height = kPixelHeight;
    gCanvasElement.addEventListener("click", gameOnClick, false);
    gDrawingContext = gCanvasElement.getContext("2d");

    if (!resumeGame()) {
	    newGame();
    }
}
