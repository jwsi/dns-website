from flask import session, redirect, url_for, request
from functools import wraps


def requires_auth(tier):
    """
    Decorator function to check whether a user is authenticated on the site.
    :param tier: Tier to enforce.
    :return: Either the result of the decorated function or a redirect to the login page.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'profile' not in session or tier not in session["scopes"]:
                # Redirect to Login page here
                return redirect(url_for('authentication.login', redirect_uri=request.url))
            return f(*args, **kwargs)
        return decorated
    return decorator
