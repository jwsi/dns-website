import json, decimal

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)

        return super(CustomJSONEncoder, self).default(o)
