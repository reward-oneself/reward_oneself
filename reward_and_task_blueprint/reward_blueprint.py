import flask_login
from flask import Blueprint, redirect, render_template, request, url_for

from extensions import db, error_handler

reward_blueprint = Blueprint(
    "reward_blueprint", __name__, template_folder="templates"
)


@reward_blueprint.route("/add_reward")
@flask_login.login_required
def add_reward():
    """
    渲染添加新奖励的页面
    """
    return render_template("add_new_reward.html")


@reward_blueprint.route("/add_reward_submit", methods=["POST"])
@flask_login.login_required
@error_handler
def add_reward_submit():
    """
    处理添加新奖励的提交请求
    业务流程：
    1. 验证参数有效性（名称、积分值）
    2. 创建奖励数据副本并更新
    3. 完全替换原有JSON字段触发数据库更新
    4. 提交事务或在出错时回滚
    """
    name = request.form.get("name")
    points = int(request.form.get("points"))

    if not points > 0:
        raise ValueError(info="积分值必须为正整数")

    user = flask_login.current_user
    # 创建当前奖励数据的副本并完全替换原有字段
    reward = dict(user.user_data.reward)  # 创建新对象确保SQLAlchemy检测到变化
    reward[name] = points
    user.user_data.reward = reward  # 完全替换字典触发数据库更新

    db.session.commit()  # 提交数据库事务
    return redirect(url_for("index_blueprint.index"))
