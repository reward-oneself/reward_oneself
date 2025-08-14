from flask import Blueprint, Response, render_template

from filehandle import FileHandler

doc_blueprint = Blueprint(
    "doc_blueprint", __name__, template_folder="templates"
)


@doc_blueprint.route("/LICENSE")
def license():
    """
    提供LICENSE文件内容
    :return: LICENSE文件的文本响应
    """
    license_file = FileHandler("LICENSE")
    license_text = license_file.read()

    return Response(license_text, mimetype="text/plain")


@doc_blueprint.route("/LICENSES")
def licenses():
    """
    提供LICENSES文件内容
    :return: LICENSES文件的文本响应
    """
    license_file = FileHandler("LICENSES")
    # 使用utf-16编码读取文件，因为文件以0xff开头
    licenses_text = license_file.read(encoding="utf-16")
    return Response(licenses_text, mimetype="text/plain")


@doc_blueprint.route("/LICENSES_NOT_SOFTWARE")
def licenses_not_software():
    """
    提供LICENSES_NOT_SOFTWARE文件内容
    :return: LICENSES_NOT_SOFTWARE文件的文本响应
    """
    license_file = FileHandler("LICENSES_NOT_SOFTWARE")
    licenses_not_software_text = license_file.read()
    return Response(licenses_not_software_text, mimetype="text/plain")


@doc_blueprint.route("/about")
def about():
    return render_template("about.html")
