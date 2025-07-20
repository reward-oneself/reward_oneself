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


import json
import sys
from typing import Any, Dict, Optional  # 添加缺失的类型导入

import flask_login
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import DatabaseError
from werkzeug.security import check_password_hash, generate_password_hash

from hitokoto import get_hitokoto

app = Flask(__name__)
try:
    with open("settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        DATA = settings["data"]
        KEY = settings["key"]
        DEVELOPMENT = settings["development"]
except FileNotFoundError:
    with open("settings.json", "w", encoding="utf-8") as f:
        settings = {
            "data": "sqlite:///data.db",
            "key": "key",
            "development": "True",
            "hitokoto_url": "https://v1.hitokoto.cn/",
        }
        json.dump(settings, f, ensure_ascii=False, indent=4)
        sys.exit()

app.config["SQLALCHEMY_DATABASE_URI"] = DATA
app.config["SECRET_KEY"] = KEY
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# 初始化CSRF保护
csrf = CSRFProtect(app)

# 初始化LoginManager
login_manager = LoginManager(app)


# 初始化Flask-Migrate
def init_db():
    db.create_all()  # 创建所有表


# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    # 根据实际情况实现用户查询逻辑
    return User.query.get(int(user_id))  # 假设使用SQLAlchemy的User模型


class User(db.Model, UserMixin):
    """
    用户模型，继承SQLAlchemy Model基类和Flask-Login UserMixin
    - id: 主键，自增整数
    - username: 用户名，唯一且非空
    - password: 加密后的密码，长度128位
    - get_id(): 返回字符串类型的用户ID（符合UserMixin要求）
    - user_data: 与UserData的一对一关系，级联删除
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def get_id(self):
        return str(self.id)


class UserData(db.Model):
    """
    用户数据模型，存储积分、任务和奖励信息
    - id: 主键，自增整数
    - user_id: 外键，关联User.id，级联删除
    - reward: JSON字段，存储奖励信息，默认空对象
    - point: 积分余额，默认0
    - task: JSON字段，存储任务信息，默认空对象
    - user: 反向关联User模型，配置级联删除
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    reward = db.Column(db.JSON, nullable=False, default=lambda: {})
    point = db.Column(db.Integer, nullable=False, default=0)
    task = db.Column(db.JSON, nullable=False, default=lambda: {})
    love = db.Column(db.String(60), nullable=False, default="")
    rest_time_to_work_ratio = db.Column(db.Integer, nullable=False, default=5)
    user = db.relationship(
        "User",
        backref=db.backref("user_data", uselist=False,
                           cascade="all, delete-orphan"),
    )


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(app.static_folder, "favicon.ico")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login_submit", methods=["POST"])
def login_submit():
    input_username = request.form.get("username")
    input_password = request.form.get("password")
    user = User.query.filter_by(username=input_username).first()
    if user and check_password_hash(user.password, input_password):
        flask_login.login_user(user)
        return redirect(url_for("index"))
    else:
        return render_template("error.html", type="用户名或密码错误")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register_submit", methods=["POST"])
def register_submit():
    input_username = request.form.get("username")
    input_password = request.form.get("password")
    if not input_username or not input_password:
        flash("用户名和密码不能为空")
        return redirect(url_for("register"))
    if len(input_password) < 6:
        flash("密码长度至少为6位")
        return redirect(url_for("register"))
    if User.query.filter_by(username=input_username).first():
        flash("用户名已存在")
        return redirect(url_for("register"))
    # 创建用户实例并手动赋值字段
    # 第一步：创建用户并获取ID
    user = User()
    user.username = input_username
    user.password = generate_password_hash(input_password)
    db.session.add(user)
    db.session.flush()  # 获取生成的user.id

    # 第二步：创建关联数据
    user_data = UserData()
    user_data.user_id = user.id
    user_data.point = 0
    user_data.reward = {}
    user_data.task = {}
    db.session.add(user_data)

    # 最终提交
    db.session.commit()
    flash("注册成功，请登录")
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for("login"))


@app.route("/")
@flask_login.login_required
def index():
    user = flask_login.current_user
    db.session.refresh(user.user_data)
    point_value = user.user_data.point
    reward = user.user_data.reward
    task = user.user_data.task

    reward_text = ""
    with open("partials/reward_text.html") as f:
        add_text = f.read()
    for name, value in reward.items():
        reward_text += add_text.format(name=name, value=value)

    def sort_task():
        task_name_priority = {}
        for name, value in task.items():
            for n, v in value.items():
                if n == "priority":
                    if v == "max":
                        task_name_priority[name] = float("inf")
                    else:
                        task_name_priority[name] = v
                    break
        sorted_task = sorted(
            task_name_priority.items(), key=lambda x: x[1], reverse=True
        )  # 正序排列，返回包含元组的列表
        sort_task_name_list = []
        for i in sorted_task:
            sort_task_name_list.append(i[0])  # 将元组中的元素取出
        return sort_task_name_list

    task_text = ""
    sort_task_name_list = sort_task()
    with open("partials/task_text.html") as f:
        add_text = f.read()
    for i in sort_task_name_list:
        task_data = task.get(i)
        task_text += add_text.format(
            points=task_data["points"],
            time=task_data["time"],
            priority=task_data["priority"],
            repeat=task_data["repeat"],
            i=i,
        )

    love = user.user_data.love
    hitokoto = get_hitokoto(love)
    return render_template(
        "index.html",
        username=user.username,
        point=point_value,
        hitokoto=hitokoto,
        reward=reward_text,
        task=task_text,
    )


@app.route("/hitokoto")
@flask_login.login_required
def hitokoto():
    return render_template("hitokoto.html")


@app.route("/hitokoto_submit", methods=["POST"])
@flask_login.login_required
def hitokoto_submit():
    hitokoto = request.form.to_dict()
    hitokoto_text = ""
    for k, v in hitokoto.items():
        if k != "csrf_token":
            hitokoto_text = hitokoto_text + v

    user = flask_login.current_user
    db.session.refresh(user.user_data)

    user.user_data.love = hitokoto_text

    try:
        db.session.commit()
        return redirect(url_for("index"))

    except DatabaseError:
        db.session.rollback()
        return render_template("error.html", type="数据库错误")
    except Exception:
        return render_template("error.html", type="其他错误")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/point")
@flask_login.login_required
def point():
    user = flask_login.current_user
    point_change = request.args.get("point_change")
    name = request.args.get("name")
    repeat = request.args.get("repeat")

    if not point_change and name:
        return render_template("error.html", type="参数错误")

    try:
        point_change = int(point_change)
        # 一样的坑
        if repeat == "False":
            repeat = False
        else:
            repeat = True
    except ValueError:
        return render_template("error.html", type="数据格式错误")

    updated_point = user.user_data.point + point_change
    if updated_point >= 0:
        user.user_data.point = updated_point
        db.session.commit()
        result = "成功"
    else:
        result = "失败，积分不足"

    if point_change <0:
        # 如果积分变化为负数，则是奖励，跳过处理任务的逻辑
        return render_template(
            "point.html", result=result, name=name, point=user.user_data.point
        )
    
    
    if not repeat:
        try:
            task = dict(user.user_data.task)
            del task[name]
            user.user_data.task = task
            db.session.commit()
            result = "成功。因为没有重复，所以该任务已自动删除"
        except DatabaseError:
            result = "兑换成功，但是因为删除任务时数据库出错，该任务没有被删除"
        except Exception:
            result = "兑换成功，但是因为删除任务时出现未知错误，该任务没有被删除"

    return render_template(
        "point.html", result=result, name=name, point=user.user_data.point
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
    points = request.form.get("points")

    try:
        changed_points = int(points)
    except ValueError:
        return render_template("error.html", type="数据格式错误")

    if not changed_points > 0:
        return render_template("error.html", type="参数错误或参数不符合要求")

    user = flask_login.current_user
    # 创建当前奖励数据的副本并完全替换原有字段
    reward = dict(user.user_data.reward)  # 创建新对象确保SQLAlchemy检测到变化
    reward[name] = changed_points
    user.user_data.reward = reward  # 完全替换字典触发数据库更新

    try:
        db.session.commit()  # 提交数据库事务
        return redirect(url_for("index"))
    except Exception:
        db.session.rollback()  # 回滚事务
        return render_template("error.html", type="数据库错误")


@app.route("/add_task_submit", methods=["POST"])
@flask_login.login_required
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
    points = request.form.get("points")
    time = request.form.get("time")
    importance = request.form.get("importance")
    value = request.form.get("value")
    urgent = request.form.get("urgent")
    repeat = request.form.get("repeat")

    def check():
        global changed_points
        global changed_time
        global changed_value
        global changed_urgent
        global changed_repeat
        try:
            changed_points = int(points)
            changed_time = int(time)
            changed_value = int(value)
            changed_urgent = int(urgent)
            # 踩过的坑：这里的转化不能用bool()，Python 中所有非空字符串都会被视为 True，与字符串内容无关。
            if repeat == "True":
                changed_repeat = True
            else:
                changed_repeat = False
        except ValueError:
            return False
        else:
            return (
                name
                and name != ""
                and changed_points > 0
                and changed_time > 0
                and changed_value > 0
                and changed_value <= 3
                and changed_urgent > 0
                and changed_urgent <= 3
                and importance in ["0", "3", "4", "max"]
            )

    if not check():
        return render_template("error.html", type="参数错误或参数不符合要求")

    user = flask_login.current_user
    # 创建当前任务数据的副本并完全替换原有字段
    task = dict(user.user_data.task)  # 创建新对象确保SQLAlchemy检测到变化
    # 构建任务对象

    if importance == "max":
        priority = "max"
    else:
        priority = round(
            int(importance) * 4
            + changed_urgent * 2
            + changed_value * 3
            - changed_time / 10
        )

    task[name] = {
        "points": changed_points,
        "time": changed_time,
        "priority": priority,
        "repeat": changed_repeat,
    }

    user.user_data.task = task  # 完全替换字典触发数据库更新

    try:
        db.session.commit()  # 提交数据库事务
        return redirect(url_for("index"))
    except DatabaseError:
        db.session.rollback()  # 回滚事务
        return render_template("error.html", type="数据库错误")
    except Exception:
        db.session.rollback()  # 回滚事务
        return render_template("error.html", type="未知错误")


@app.route("/remove")
@flask_login.login_required
def remove():
    """
    渲染移除任务或奖励的页面，根据提供的类型参数，并列出所有可移除的项。
    """
    type_name = request.args.get("type")
    if not type_name:
        return render_template("error.html", type="参数错误")

    user = flask_login.current_user

    if type_name == "reward":
        items = user.user_data.reward
    else:
        items = user.user_data.task

    text = ""
    with open("partials/remove_text.html", encoding="utf-8") as f:
        add_text = f.read()
    for name in items.keys():
        text += add_text.format(name=name)
    return render_template("remove.html", type=type_name, text=text)


@app.route("/remove_submit", methods=["POST", "GET"])
@flask_login.login_required
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
    type_name: Optional[str] = request.args.get("type")
    form_data: Dict[str, str] = request.form.to_dict()

    if not type_name:
        return render_template("error.html", type="参数错误或参数不符合要求")
    user = flask_login.current_user

    def instead_data(data, form_data=form_data):

        # 创建新对象确保SQLAlchemy检测到变化
        copy: Dict[str, Any] = dict(data)
        # 保留不在form_data中的项
        updated_data: Dict[str, Any] = {
            name: value for name, value in copy.items() if name not in form_data
        }

        return updated_data

    try:
        if type_name == "reward":
            data = user.user_data.reward
            user.user_data.reward = instead_data(data)
        else:
            data = user.user_data.task
            user.user_data.task = instead_data(data)

        db.session.commit()  # 提交数据库事务

        return redirect(url_for("index"))
    except DatabaseError:
        db.session.rollback()  # 回滚事务
        return render_template("error.html", type="数据库错误")
    except Exception:
        return render_template("error.html", type="未知错误")


@app.route("/delete_account")
@flask_login.login_required
def delete_account():
    """
    显示注销账户确认页面
    - 需要登录才能访问
    - 提供安全提示
    """
    return render_template("delete_account.html")


@app.route("/delete_account_submit", methods=["POST"])
@flask_login.login_required
def delete_account_submit():
    """
    处理账户注销请求
    业务流程:
    1. 获取当前用户
    2. 删除用户记录（级联删除关联数据）
    3. 清除用户会话
    4. 重定向到首页

    安全要求:
    - 必须登录才能访问
    - 使用POST方法防止CSRF攻击
    - 确保级联删除机制正常工作
    """
    user = flask_login.current_user
    try:
        db.session.delete(user)
        db.session.commit()
        flask_login.logout_user()
        flash("您的账户已成功注销")
        return redirect(url_for("index"))
    except DatabaseError:
        db.session.rollback()
        return render_template("error.html", type="注销失败，数据库错误")
    except Exception:
        return render_template("error.html", type="注销失败，未知错误")


@login_manager.unauthorized_handler
def unauthorized():
    """
    未授权访问处理函数
    - 当未登录用户尝试访问受保护路由时触发
    - 重定向到登录页面保持用户体验一致性
    - 符合Flask-Login的认证规范要求
    """
    return redirect(url_for("login"))


if __name__ == "__main__":
    """
    应用启动入口
    - 调试模式开启（开发环境）
    - 监听所有网络接口（便于容器部署）
    - 使用默认端口5000
    """
    if DEVELOPMENT == "True":
        app.run(host="0.0.0.0", port=8080, debug=True)
    else:
        print("生产环境下不宜使用开发服务器启动，请使用gunicorn启动程序")
        print("程序未启动")
