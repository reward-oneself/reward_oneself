from flask import Blueprint, render_template, request, redirect, url_for
from extensions import db, error_handler
import flask_login



task_blueprint = Blueprint(
    "task_blueprint", __name__, template_folder="templates"
)


@task_blueprint.route("/add_task")
@flask_login.login_required
def add_task():
    """
    渲染添加新任务的页面
    """
    return render_template("add_new_task.html")


@task_blueprint.route("/add_task_submit", methods=["POST"])
@flask_login.login_required
@error_handler
def add_task_submit():
    """
    处理添加新任务的提交请求
    业务流程：
    1. 验证参数有效性（名称、积分值、时间、重要性等）
    2. 创建任务数据副本并更新
    3. 完全替换原有JSON字段触发数据库更新
    4. 提交事务或在出错时回滚
    """
    name = request.form.get("name")
    points = int(request.form.get("points"))
    time = int(request.form.get("time"))
    importance = request.form.get("importance")
    value = int(request.form.get("value"))
    urgent = int(request.form.get("urgent"))
    repeat = request.form.get("repeat") == "True"

    def check():
        return (
            name
            and name != ""
            and points > 0
            and time >= 0
            and value > 0
            and value <= 3
            and urgent > 0
            and urgent <= 3
            and importance in ["0", "3", "4", "max"]
        )

    if not check():
        raise ValueError()

    user = flask_login.current_user
    # 创建当前任务数据的副本并完全替换原有字段
    task = dict(user.user_data.task)  # 创建新对象确保SQLAlchemy检测到变化
    # 构建任务对象

    if importance == "max":
        priority = "max"
    else:
        if time == 0:
            priority = round(int(importance) * 4 + urgent * 2 + value * 3)
        else:
            priority = round(
                int(importance) * 4 + urgent * 2 + value * 3 - time / 10
            )

    task[name] = {
        "points": points,
        "time": time,
        "priority": priority,
        "repeat": repeat,
    }

    user.user_data.task = task  # 完全替换字典触发数据库更新

    db.session.commit()  # 提交数据库事务
    return redirect(url_for("index_blueprint.index"))
