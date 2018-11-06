import threading, socket, logging, dnslib

class UDPHandler():

    def __init__(self):
        logging.info("Initializing UDP Handler")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 8000))
        self.clients_list = []


    def respond_to_client(self, datagram, ip):
        request = dnslib.DNSRecord.parse(datagram)
        recursion_desired = request.header.rd
        id = request.header.id
        for question in request.questions:
            domain = question.qname
            record_type = dnslib.QTYPE[question.qtype]
            response = dnslib.DNSRecord(dnslib.DNSHeader(id=id, qr=1, aa=1, ra=0, rd=recursion_desired),
                                        questions=[dnslib.DNSQuestion(domain)],
                                        rr=[dnslib.RR(domain,rdata=dnslib.A("1.2.3.4"))],
                                        auth = [dnslib.RR(domain, rdata=dnslib.A("1.2.3.4"))])
            self.sock.sendto(response.pack(), ip)
            import time
            time.sleep(10)


    def listen(self):
        while True:
            question, client = self.sock.recvfrom(1024)
            t = threading.Thread(target=self.respond_to_client, args=(question, client,))
            t.start()

if __name__ == '__main__':
    # Make sure all log messages show up
    logging.getLogger().setLevel(logging.DEBUG)
    handler = UDPHandler()
    handler.listen()
