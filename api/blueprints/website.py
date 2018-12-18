from flask import Blueprint, render_template, request, abort
from api.decorators.authentication import requires_auth
from api.classes.db import db
from api import menu, current_user

website = Blueprint('website', __name__)

def should_return_JSON():
    return "application/json" in request.accept_mimetypes and \
        not "text/html" in request.accept_mimetypes


@website.route("/")
@menu.register_menu(website, ".", "Home")
def index():
    return render_template("index.html")


@website.route("/sites/")
@menu.register_menu(website, ".sites", "Sites")
@requires_auth("user")
def sites():
    return render_template("sites.html", domains=db.get_root_domains(current_user.user_id))


@website.route("/sites/<domain>/")
@requires_auth("user")
def site_records(domain):
    records = db.get_records_for_root_domain(domain, current_user.user_id)
    if len(records) == 0:
        abort(404)

    def getRTypes(record):
        from .api import ENTRY_TYPES
        ret = [{ "name": key, "data": record.get(key)} for key in ENTRY_TYPES if key in record]
        return ret

    return render_template("records.html", records=records, getRTypes=getRTypes)
