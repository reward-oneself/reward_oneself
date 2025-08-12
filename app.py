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
from point_and_timer_blueprint.point import point_blueprint
from point_and_timer_blueprint.timer_submit import timer_submit_blueprint



app = Flask(__name__)


app.register_blueprint(auth_blueprint)
app.register_blueprint(doc_blueprint)
app.register_blueprint(settings_blueprint)
app.register_blueprint(index_blueprint)
app.register_blueprint(hitokoto_blueprint)
app.register_blueprint(heartbeat_blueprint)
app.register_blueprint(point_blueprint)
app.register_blueprint(timer_submit_blueprint)



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
