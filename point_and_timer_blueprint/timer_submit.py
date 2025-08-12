import flask_login
from flask import Blueprint, request

from .timer_render import timer

timer_submit_blueprint = Blueprint(
    "timer_submit", __name__, template_folder="templates"
)


@timer_submit_blueprint.route("/timer_submit", methods=["POST"])
@flask_login.login_required
def timer_submit():
    time = request.form.get("time")
    name = request.form.get("name")
    value = request.form.get("value")
    repeat = request.form.get("repeat")

    return timer(name=name, value=value, time=time, repeat=repeat)
