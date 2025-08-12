import flask_login
from flask import Blueprint, redirect, render_template, request, url_for

from extensions import db, error_handler

settings_blueprint = Blueprint("settings_blueprint", __name__, template_folder="templates")



@settings_blueprint.route("/settings")
@flask_login.login_required
def setting():
    return render_template("settings.html")


@settings_blueprint.route("/settings_submit", methods=["POST"])
@flask_login.login_required
@error_handler
def settings_submit():
    ratio = request.form.get("rest_time_to_work_ratio")
    ratio = int(ratio)
    if ratio <= 0:
        raise ValueError(info="比例必须为正整数")

    user = flask_login.current_user
    db.session.refresh(user.user_data)
    user.user_data.rest_time_to_work_ratio = ratio
    db.session.commit()
    return redirect(url_for("index_blueprint.index"))
