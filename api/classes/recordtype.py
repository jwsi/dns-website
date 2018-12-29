import enum
import re

retype = type(re.compile("hello, world"))
ip_reg = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
ip6_reg = str
domain_reg = str


optstr = "OPTSTR"


class RecordType(enum.Enum):
    A     = "A"
    AAAA  = "AAAA (V6)"
    CAA   = "CAA"
    CNAME = "CNAME"
    MX    = "MX"
    NAPTR = "NAPTR"
    NS    = "Name Servers (NS)"
    SOA   = "SOA"
    SRV   = "SRV"
    TXT   = "TXT"

    def __str__(self):
        return self.name

    def check_structure(self, struct):
        def __check_structure(value, schema):
            if schema == optstr:
                return value is None or isinstance(value, str)
            elif isinstance(schema, dict) and isinstance(value, dict):
                return all(k in value and __check_structure(value[k], schema[k]) for k in schema)
            elif isinstance(schema, list) and isinstance(value, list):
                return all(__check_structure(c, schema[0]) for c in value)
            elif isinstance(schema, retype):
                return schema.match(value)
            elif isinstance(schema, type):
                return isinstance(value, schema)
            else:
                return False

        ENTRY_TYPES = {
            "A":     { "ttl": int, "value": [ip_reg] },
            "AAAA":  { "ttl": int, "value": [ip6_reg] },
            "CAA":   { "ttl": int, "value": [{"flags": int, "tag": str, "value": str }]},
            "CNAME": { "ttl": int, "domain": domain_reg },
            "MX":    { "ttl": int, "value": [{ "domain": domain_reg, "preference": int }] },
            "NAPTR": { "ttl": int, "value": [{ "order": int, "preference": int, "flags": str, "service": str, "regexp": optstr, "replacement": str }]},
            "NS":    { "ttl": int, "value": [domain_reg] },
            "SOA":   { "ttl": int, "times": [int], "mname": str, "rname": str },
            "SRV":   { "ttl": int, "value": [{ "priority": int, "weight": int, "port": int, "target": str }] },
            "TXT":   { "ttl": int, "value": str },
        }
        return __check_structure(struct, ENTRY_TYPES[self.name])

    @classmethod
    def check_stucture_for_type(struct, type):
        return RecordType.get(type).check_structure(struct)

    @classmethod
    def get(cls, name):
        try:
            return RecordType[name.upper()]
        except KeyError:
            return None

    @classmethod
    def choices(cls):
        return [(choice, choice.value) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return item if type(item) == RecordType else RecordType[item]
