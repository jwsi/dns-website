import os
from authlib.flask.client import OAuth as vanilla_OAuth


class OAuth(vanilla_OAuth):
    """
    Extends the vanilla OAuth class to specify Auth0 as the provider.
    """
    def __init__(self, app):
        super().__init__(app)
        self.auth0 = self.register(
            'auth0',
            client_id='MR3c9T4pmw3wKXm2YfMloTKpeiVhQgpQ',
            client_secret=os.environ["AUTH0_CLIENT_SECRET"],
            api_base_url='https://uh-dns.eu.auth0.com',
            access_token_url='https://uh-dns.eu.auth0.com/oauth/token',
            authorize_url='https://uh-dns.eu.auth0.com/authorize',
            client_kwargs={
                'scope': 'openid profile',
            },
        )


class Authentication:
    """
    Used to allow for a global way to access Auth0 authentication functions.
    """
    auth0 = None

    @classmethod
    def initialize(cls, app):
        cls.auth0 = OAuth(app).auth0