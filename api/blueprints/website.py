from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from api.decorators.authentication import requires_auth
from api.classes.db import db, get_root_domain
from api.classes.recordtype import RecordType
from api.classes.customjsonencoder import CustomJSONEncoder
from api.classes.livechecker import LiveChecker
from api.classes.errors import ControlledException
from api.classes.status import ReturnCode
from api import menu, current_user
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import InputRequired, Length
import json, validators


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

    root_record = None
    for record in records:
        if record["domain"] == domain + ".":
            root_record = record

    def getRTypes(record):
        print(RecordType.choices())
        ret = [{ "name": key[0].name, "data": record[key[0].name]} for key in RecordType.choices() if key[0].name in record]
        return ret

    return render_template("records.html", records=records, getRTypes=getRTypes, \
            domain=domain, root_record=root_record)

def Domain(form, field):
    data = field.data
    if data[-1:] == ".":
        data = data[:-1]

    if validators.domain(data) != True:
        raise ValidationError("Invalid domain name")

class DomainForm(FlaskForm):
    domain = StringField("Domain", [InputRequired(), Length(1, 40), Domain])
    submit = SubmitField("Save")


@website.route("/domains/new/", methods=["GET", "POST"])
@requires_auth("user")
def domain_new():
    form = DomainForm(formdata=request.form)
    if form.validate_on_submit():
        domain = get_root_domain(form.domain.data)
        records = db.get_records_for_root_domain(domain, current_user.user_id)
        if domain[-1:] != ".":
            domain = domain + "."

        if len(records) > 0:
            flash("Domain already exists", "warning")
        elif len(db.get_live_records_by_domain(domain)) > 0:
            flash("Domain already created by another user", "warning")
        else:

            item = {
                "domain":  domain,
                "user_id": current_user.user_id,
                "NS": { "ttl": 3600, "value": ["ns1.uh-dns.com.", "ns2.uh-dns.com."] },
                "SOA": { "ttl": 900, "times": [2018122100,7200,900,1209600,86400], "mname": "ns1.uh-dns.com.", "rname": "engineering.ultra-horizon.com." },
            }

            assert(RecordType.NS.check_structure(item["NS"]))
            assert(RecordType.SOA.check_structure(item["SOA"]))

            db.put_record(item)

            return redirect(url_for("website.domain_records", domain=domain[:-1]))

    return render_template("domain_new.html", form=form)


@website.route("/domains/<domain>/check/", methods=["POST"])
@requires_auth("user")
def domain_check(domain):
    root = db.get_record(domain + ".", current_user.user_id)
    if root is None:
        abort(404)

    try:
        if not LiveChecker.check(root, domain + "."):
            raise ControlledException(ReturnCode.UNKNOWN)

        root["live"] = True
        db.put_record(root)
    except ControlledException as e:
        flash("Failed. Error: " + e.status.name, "danger")

    return redirect(url_for("website.domain_records", domain=domain))

class RecordForm(FlaskForm):
    domain = StringField("Hostname", [InputRequired(), Length(1, 40), Domain])
    type   = SelectField("Type", [InputRequired()], choices=RecordType.choices(), coerce=RecordType.coerce, default=RecordType.A)
    ttl    = IntegerField("TTL", default=10)
    value  = StringField("Value", [Length(0, 1000)])
    mname  = StringField("MNAME (Primary Master Nameserver)", [Length(0, 1000)])
    rname  = StringField("RNAME (Email address with @ replaced with .)", [Length(0, 1000)])
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

    suc, msg = form.type.data.validate_put(item, record_entry)
    if not suc:
        return False, msg

    # Add
    item[form.type.data.name] = record_entry

    db.put_record(item)
    return True, None


@website.route("/domains/<domain>/<hostname>/delete/", methods=["POST"])
@website.route("/domains/<domain>/<hostname>/<record>/delete/", methods=["POST"])
@requires_auth("user")
def domain_record_delete(domain, hostname, record=None):
    item = db.get_record(hostname, current_user.user_id)
    if item is None:
        abort(404)

    if record is None:
        db.delete_record(hostname, current_user.user_id)
        flash("Deleted " + hostname, "success")

    else:
        record = RecordType.get(record)
        if record is None:
            abort(404)

        del item[record.name]
        db.put_record(item)

        flash("Deleted " + record.name + " from " + hostname, "success")

    return redirect(url_for("website.domain_records", domain=domain))


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
                form.mname.data = item[type.name].get("mname")
                form.rname.data = item[type.name].get("rname")

                if type == RecordType.CNAME:
                    form.value.data = item[type.name]["domain"]
                elif type == RecordType.TXT:
                    form.value.data = item[type.name]["value"]
                else:
                    form.value.data = json.dumps(item[type.name], cls=CustomJSONEncoder)

    elif form.validate_on_submit():
        suc, msg = do_domain_records_new(domain, form)
        if suc:
            return redirect(url_for("website.domain_records", domain=domain))
        elif msg:
            flash(msg, "danger")

    return render_template("record_newedit.html", form=form, \
        domain=domain, hostname=hostname, record=record, is_edit=record is not None)
