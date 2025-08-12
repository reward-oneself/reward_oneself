from flask import Blueprint, Response

from filehandle import FileHandler

doc_blueprint = Blueprint("doc_blueprint", __name__)


@doc_blueprint.route("/LICENSE")
def license():
    license_file = FileHandler("LICENSE")
    license_text = license_file.read()

    return Response(license_text, mimetype="text/plain")


@doc_blueprint.route("/LICENSES")
def licenses():
    license_file = FileHandler("LICENSES")
    licenses_text = license_file.read()
    return Response(licenses_text, mimetype="text/plain")


@doc_blueprint.route("/LICENSES_NOT_SOFTWARE")
def licenses_not_software():
    license_file = FileHandler("LICENSES_NOT_SOFTWARE")
    licenses_not_software_text = license_file.read()
    return Response(licenses_not_software_text, mimetype="text/plain")
