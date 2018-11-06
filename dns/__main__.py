import socketserver, dnslib, binascii
from threading import Thread
from time import sleep


def threaded_handler(datagram):
    request = dnslib.DNSRecord.parse(datagram)
    print(request)
    print(request.questions)
    for question in request.questions:
        print("Record print")
        print(question.qname)
        print(dnslib.QTYPE[question.qtype])
        # Do some search on these params.
    sleep(5)


class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        thread = Thread(target=threaded_handler, args=(data, ))
        thread.start()
        # socket.sendto(data.upper(), self.client_address)


if __name__ == "__main__":
    server = socketserver.UDPServer(("0.0.0.0", 8000), MyUDPHandler)
    server.serve_forever()
