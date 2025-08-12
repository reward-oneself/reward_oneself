# Copyright (C) 2025 陈子涵
# Contact information:
# Tel:18750386615
# Email:2502820816@qq.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import flask_login
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)

import settings
from auth_blueprint.auth_blueprint import auth_blueprint
from doc_blueprint.doc_blueprint import doc_blueprint
from extensions import csrf, db, error_handler, login_manager
from filehandle import FileHandler
from models import User
from system_blueprint.heartbeat import heartbeat_blueprint
from system_blueprint.hitokoto import hitokoto_blueprint
from system_blueprint.index import index_blueprint
from system_blueprint.settings import settings_blueprint

app = Flask(__name__)


app.register_blueprint(auth_blueprint)
app.register_blueprint(doc_blueprint)
app.register_blueprint(settings_blueprint)
app.register_blueprint(index_blueprint)
app.register_blueprint(hitokoto_blueprint)
app.register_blueprint(heartbeat_blueprint)


app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATA
app.config["SECRET_KEY"] = settings.KEY
app.config["PERMANENT_SESSION_LIFETIME"] = (
    60 * 60 * 24 * 30
)  # 每30天强制自动登录
app.config["WTF_CSRF_TIME_LIMIT"] = 60 * 60 * 2  # 会话限制两小时
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# 初始化扩展
csrf.init_app(app)
login_manager.init_app(app)
db.init_app(app)


# 初始化Flask-Migrate


def init_db():
    db.create_all()  # 创建所有表


# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    # 根据实际情况实现用户查询逻辑
    return User.query.get(int(user_id))


@app.route("/point", methods=["POST"])
@flask_login.login_required
@error_handler
def point():
    user = flask_login.current_user
    point_change = int(request.form.get("point_change"))
    name = request.form.get("name")
    repeat = request.form.get("repeat") == "True"
    from_page = request.form.get("from")

    time = int(request.form.get("time"))

    def process_point_change(type, repeat):
        """处理积分变更，返回结果"""

        if not point_change and name:
            raise ValueError(info="参数错误")

        # 处理积分变更
        updated_point = user.user_data.point + point_change
        if updated_point < 0:
            return ("失败，积分不足", False)

        user.user_data.point = updated_point

        if type == "reward" or repeat:
            return ("成功", False)

        try:
            task = dict(user.user_data.task)
            del task[name]
            user.user_data.task = task
            db.session.commit()
            return ("成功。该任务已自动删除", True)
        except KeyError:
            return ("成功。任务不存在", False)

    if point_change < 0:
        # 如果积分变化为负数，则是奖励，跳过处理任务的逻辑
        return_value = process_point_change(type="reward", repeat=repeat)
        result = return_value[0]
        return render_template(
            "point.html", result=result, name=name, point=user.user_data.point
        )

    if time == 0:
        result, delete = process_point_change(type="task", repeat=repeat)
        return render_template(
            "point.html", result=result, name=name, point=user.user_data.point
        )

    if from_page == "timer":
        result, delete = process_point_change(type="task", repeat=repeat)
        if delete:
            return render_template(
                "point.html",
                result=result,
                name=name,
                point=user.user_data.point,
            )
        else:
            return render_template(
                "point.html",
                result=result,
                name=name,
                point=user.user_data.point,
                from_page=from_page,
                value=point_change,
                time=time,
                repeat=repeat,
            )
    else:
        return timer(name=name, value=point_change, time=time, repeat=repeat)


# 计时器逻辑：首先来到/point路由，判断是否是定时任务（时间不为0）
# 如果是则调用timer函数跳转计时器
#   计时完成后再次回到/point路由，完成相应积分变更（非重复任务会在此时被删除）
#   如果任务被删除，则此时渲染正常的积分操作结果页面，自动跳转回主页
#   否则返回积分操作结果页面，传递from_page = "timer"，触发{% if from_page == "timer" %}，渲染一个包含询问是否继续的表单
#       如果继续，则发送post请求到/timer_submit路由，并将参数转到timer函数，开始计时
# 否则调用process_point_change函数处理积分变更。此时渲染正常的积分操作结果页面，自动跳转回主页


@app.route("/timer_submit", methods=["POST"])
@flask_login.login_required
def timer_submit():
    time = request.form.get("time")
    name = request.form.get("name")
    value = request.form.get("value")
    repeat = request.form.get("repeat")

    return timer(name=name, value=value, time=time, repeat=repeat)


# 抽离出单独的函数，处理来自服务器本身和网络的数据，让服务器的数据不用走网络
def timer(name, value, time, repeat):
    return render_template(
        "timer.html",
        name=name,
        value=value,
        time=time,
        repeat=repeat,
        rest_time_to_work_ratio=flask_login.current_user.user_data.rest_time_to_work_ratio,
    )


@app.route("/add_reward")
@flask_login.login_required
def add_reward():
    """
    渲染添加新奖励的页面
    """
    return render_template("add_new_reward.html")


@app.route("/add_task")
@flask_login.login_required
def add_task():
    """
    渲染添加新任务的页面
    """
    return render_template("add_new_task.html")


@app.route("/add_reward_submit", methods=["POST"])
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


@app.route("/add_task_submit", methods=["POST"])
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


@app.route("/remove", methods=["POST"])
@flask_login.login_required
@error_handler
def remove():
    """
    渲染移除任务或奖励的页面，根据提供的类型参数，并列出所有可移除的项。
    """
    type_name = request.form.get("type")
    if not type_name:
        raise ValueError(info="参数错误")

    user = flask_login.current_user

    if type_name == "reward":
        items = user.user_data.reward
    else:
        items = user.user_data.task

    text = ""
    file_handler = FileHandler("partials/remove_text.html")
    add_text = file_handler.read()
    for name in items.keys():
        text += add_text.format(name=name)
    return render_template("remove.html", type=type_name, text=text)


@app.route("/remove_submit", methods=["POST"])
@flask_login.login_required
@error_handler
def remove_submit() -> str:
    """
    处理删除任务/奖励的提交请求
    业务流程：
    1. 验证类型参数有效性
    2. 创建对应数据的副本并删除指定项
    3. 完全替换原有JSON字段触发数据库更新
    4. 提交事务或在出错时回滚

    安全要求：
    - 必须登录才能访问
    - 参数验证防止无效数据操作
    - 异常处理保证数据一致性
    """
    type_name = request.form.get("type")
    form_data = request.form.to_dict()

    if not type_name:
        raise ValueError()
    user = flask_login.current_user

    def instead_data(data, form_data=form_data):
        # 创建新对象确保SQLAlchemy检测到变化
        copy = dict(data)
        # 保留不在form_data中的项
        updated_data = {
            name: value
            for name, value in copy.items()
            if name not in form_data
        }

        return updated_data

    if type_name == "reward":
        data = user.user_data.reward
        user.user_data.reward = instead_data(data)
    else:
        data = user.user_data.task
        user.user_data.task = instead_data(data)

    db.session.commit()  # 提交数据库事务

    return redirect(url_for("index_blueprint.index"))


@login_manager.unauthorized_handler
def unauthorized():
    """
    未授权访问处理函数
    - 当未登录用户尝试访问受保护路由时触发
    - 重定向到登录页面保持用户体验一致性
    - 符合Flask-Login的认证规范要求
    """
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    """
    应用启动入口
    - 调试模式开启（开发环境）
    - 监听所有网络接口（便于容器部署）
    - 使用  默认端口5000
    """
    if settings.DEVELOPMENT == "True":
        app.run(host="0.0.0.0", port=8080, debug=True)
    else:
        print("生产环境下不宜使用开发服务器启动，请使用gunicorn启动程序")
        print("程序未启动")
