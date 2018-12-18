from api import app

from .authentication import authentication
app.register_blueprint(authentication)

from .website import website
app.register_blueprint(website)

from .api import api
app.register_blueprint(api)
