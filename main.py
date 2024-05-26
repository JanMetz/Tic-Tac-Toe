from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
import sys

from twisted.python import log
from twisted.internet import reactor


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory("ws://0.0.0.0:8000/ws")
    factory.protocol = MyServerProtocol
    reactor.listenTCP(8000, factory)
    reactor.run()
