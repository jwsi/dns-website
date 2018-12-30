import socket, dnslib
from api.classes.status import ReturnCode
from api.classes.errors import ControlledException
from api.classes.db import db

class LiveChecker:
    @classmethod
    def check(cls, record, domain):
        if record is None:
            raise ControlledException(ReturnCode.DOMAIN_NOT_FOUND)
        LiveChecker._check_glue_records(domain)
        LiveChecker._check_no_live_domain(domain)
        return True

    @classmethod
    def _check_glue_records(cls, domain):
        """
        Checks the glue records for a particular name.
        :param domain: Domain to check
        :return: True if glue records are correct. Otherwise a glue error is raised.
        """
        try:
            question = dnslib.DNSRecord.question(domain, qtype="NS")
        except UnicodeError:
            raise ControlledException(ReturnCode.CHECK_FAILED)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", 0)) # Bind to any available IP and port.
        sock.settimeout(1)
        server = "k.root-servers.net" # First query the RIPE root server
        while True:
            sock.sendto(question.pack(), (socket.gethostbyname(server), 53))
            res = dnslib.DNSRecord.parse(sock.recv(4096))
            nameservers = set([str(record.rdata) for record in res.auth if record.rtype == 2])
            if nameservers == set(["ns1.uh-dns.com.", "ns2.uh-dns.com."]):
                return True
            elif nameservers == set([]) or res.rr != []:
                raise ControlledException(ReturnCode.INCORRECT_GLUE)
            server = nameservers.pop()

    @classmethod
    def _check_no_live_domain(cls, domain):
        """
        Check that no live domain exists already.
        :param domain: domain to check.
        """
        already_live = db.get_live_records_by_domain(domain)
        if len(already_live) > 0:
            raise ControlledException(ReturnCode.DOMAIN_ALREADY_LIVE)
