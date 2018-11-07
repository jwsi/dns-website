import threading, socket, dnslib
from dns.search import search

class UDPHandler():

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 8000))
        self.clients_list = []


    def respond_to_client(self, datagram, ip):
        request = dnslib.DNSRecord.parse(datagram)
        recursion_desired = request.header.rd
        id = request.header.id
        rr_list, auth_list, aa = [], [], 0
        for question in request.questions:
            domain = question.qname.idna()
            record_type = dnslib.QTYPE[question.qtype]
            value, authority = search(domain, record_type)
            if value is not None:
                aa = 1
                rr_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.A, rdata=value))
                auth_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.NS, rdata=authority[0], ttl=172800))
                auth_list.append(dnslib.RR(domain, rtype=dnslib.QTYPE.NS, rdata=authority[1], ttl=172800))

        response = dnslib.DNSRecord(dnslib.DNSHeader(id = id, qr = 1, aa = aa, ra = 0, rd = recursion_desired),
                                    questions = request.questions,
                                    rr = rr_list,
                                    auth = auth_list)
        self.sock.sendto(response.pack(), ip)


    def listen(self):
        while True:
            question, client = self.sock.recvfrom(1024)
            t = threading.Thread(target=self.respond_to_client, args=(question, client,))
            t.start()

if __name__ == '__main__':
    # Make sure all log messages show up
    handler = UDPHandler()
    handler.listen()
