from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from api.decorators.authentication import requires_auth
from api.classes.db import db
from api.classes.recordtype import RecordType
from api.classes.customjsonencoder import CustomJSONEncoder
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


@website.route("/domains/")
@menu.register_menu(website, ".domains", "Domains")
@requires_auth("user")
def domains():
    return render_template("domains.html", domains=db.get_root_domains(current_user.user_id))


@website.route("/domains/<domain>/")
@requires_auth("user")
def domain_records(domain):
    records = db.get_records_for_root_domain(domain, current_user.user_id)
    if len(records) == 0:
        abort(404)

    def getRTypes(record):
        print(RecordType.choices())
        ret = [{ "name": key[0].name, "data": record[key[0].name]} for key in RecordType.choices() if key[0].name in record]
        return ret

    return render_template("records.html", records=records, getRTypes=getRTypes, domain=domain)


class RecordForm(FlaskForm):
    domain = StringField("Hostname", [InputRequired(), Length(1, 40)])
    type   = SelectField("Type", [InputRequired()], choices=RecordType.choices(), coerce=RecordType.coerce, default=RecordType.A)
    ttl    = IntegerField("TTL", default=10)
    value  = StringField("Value", [Length(0, 1000)])
    mname  = StringField("MNAME (Primary Master Nameserver)", [Length(0, 1000)])
    rname  = StringField("RNAME (Email address)", [Length(0, 1000)])
    submit = SubmitField("Save")


def do_domain_records_new(domain, form):
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
    if form.domain.data[-1:] != ".":
        form.domain.data = form.domain.data + "."

    item = db.get_record(form.domain.data, current_user.user_id)
    if item is None:
        item = {
            "user_id": current_user.user_id,
            "domain": form.domain.data
        }

    if not form.type.data.validate_put(item, record_entry):
        return False, "Validation failed."

    # Add
    item[form.type.data.name] = record_entry

    db.put_record(item)
    return True, None


@website.route("/domains/<domain>/new/", methods=["GET", "POST"])
@website.route("/domains/<domain>/<hostname>/new/", methods=["GET", "POST"])
@website.route("/domains/<domain>/<hostname>/<record>/edit/", methods=["GET", "POST"])
@requires_auth("user")
def domain_record_newedit(domain, hostname=None, record=None):
    form = RecordForm(formdata=request.form)

    if record is not None:
        form.domain.data = hostname
        form.type.data = RecordType.get(record)
        if form.type.data is None:
            abort(404)

    if request.method == "GET":
        form.domain.data = hostname or domain
        if form.domain.data[-1:] != ".":
            form.domain.data = form.domain.data + "."

        if record is not None:
            item = db.get_record(form.domain.data, current_user.user_id)
            if item is None:
                abort(404)

            type = form.type.data

            if type.name in item:
                form.ttl.data = item[type.name]["ttl"]

                if type == RecordType.CNAME:
                    form.value.data = item[type.name]["domain"]
                elif type == RecordType.TXT:
                    form.value.data = item[type.name]["value"]
                else:
                    form.value.data = json.dumps(item[type.name], cls=CustomJSONEncoder)


    else:
        suc, msg = do_domain_records_new(domain, form)
        if suc:
            return redirect(url_for("website.domain_records", domain=domain))
        elif msg:
            flash(msg, "danger")

    return render_template("record_newedit.html", form=form, is_edit=record is not None)
