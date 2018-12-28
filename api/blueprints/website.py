from flask import Blueprint, render_template, request, abort
from api.decorators.authentication import requires_auth
from api.classes.db import db
from api.classes.recordtype import RecordType
from api import menu, current_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, Length


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
        print(RecordType.choices())
        ret = [{ "name": key[0].name, "data": record[key[0].name]} for key in RecordType.choices() if key[0].name in record]
        return ret

    return render_template("records.html", records=records, getRTypes=getRTypes, domain=domain)


class RecordForm(FlaskForm):
    domain = StringField("Domain", [InputRequired(), Length(1, 40)])
    type   = SelectField("Type", [InputRequired()], choices=RecordType.choices(), coerce=RecordType.coerce, default=RecordType.A)
    ttl    = IntegerField("TTL", default=10)
    value  = StringField("Value", [InputRequired(), Length(0, 1000)])
    submit = SubmitField("Save")


@website.route("/sites/<domain>/new/", methods=["GET", "POST"])
@requires_auth("user")
def site_records_new(domain):
    form = RecordForm(formdata=request.form)

    if request.method == "GET":
        form.domain.data = domain
    else:
        res = form.type.data.build(form.ttl.data, form.value.data)
        print(res)

    return render_template("record_newedit.html", form=form)
