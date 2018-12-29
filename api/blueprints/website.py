from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from api.decorators.authentication import requires_auth
from api.classes.db import db
from api.classes.recordtype import RecordType
from api import menu, current_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, Length
import json


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
    value  = StringField("Value", [Length(0, 1000)])
    mname  = StringField("MNAME (Primary Master Nameserver)", [Length(0, 1000)])
    rname  = StringField("RNAME (Email address)", [Length(0, 1000)])
    submit = SubmitField("Save")


def do_site_records_new(domain, form):
    record_entry = {}

    type = form.type.data.name
    if type == "CNAME":
        record_entry["domain"] = form.value.data.strip()
    elif type == "TXT":
        record_entry["value"] = form.value.data.strip()
    else:
        record_entry = json.loads(form.value.data)

    record_entry["ttl"] = form.ttl.data

    if type == "SOA":
        record_entry["mname"] = form.mname.data
        record_entry["rname"] = form.rname.data


    # Validate record entry
    print(record_entry)
    if not form.type.data.check_structure(record_entry):
        return False, "Invalid record entry"

    # Retrieve record
    item = db.get_record(form.domain.data, current_user.user_id)
    if item is None:
        return False, "Unable to find a record"

    if not form.type.data.validate_put(item, record_entry):
        return False, "Validation failed."

    # Add
    item[form.type.data.name] = record_entry

    db.put_record(item)
    return True, None


@website.route("/sites/<domain>/new/", methods=["GET", "POST"])
@requires_auth("user")
def site_records_new(domain):
    form = RecordForm(formdata=request.form)

    if request.method == "GET":
        form.domain.data = domain
    else:
        suc, msg = do_site_records_new(domain, form)
        if suc:
            return redirect(url_for("website.site_records", domain=domain))
        elif msg:
            flash(msg, "danger")

    return render_template("record_newedit.html", form=form)
