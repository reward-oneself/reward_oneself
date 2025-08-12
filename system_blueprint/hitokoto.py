from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import settings
from extensions import db, error_handler

hitokoto_blueprint = Blueprint("hitokoto_blueprint", __name__)


@hitokoto_blueprint.route("/hitokoto")
@login_required
def hitokoto():
    if settings.LOCAL_MODE:
        return render_template(
            "error.html",
            type="服务器一言设置为local模式，只支持显示存储在服务器上的诗词库",
        )
    return render_template("hitokoto.html")


@hitokoto_blueprint.route("/hitokoto_submit", methods=["POST"])
@login_required
@error_handler
def hitokoto_submit():

    hitokoto = request.form.to_dict()
    hitokoto_text = ""
    for k, v in hitokoto.items():
        if k != "csrf_token":
            hitokoto_text += v

    user = current_user
    db.session.refresh(user.user_data)
    user.user_data.love = hitokoto_text
    db.session.commit()
    return redirect(url_for("index_blueprint.index"))
