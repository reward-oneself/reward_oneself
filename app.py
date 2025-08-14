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


from flask import (
    Flask,
    redirect,
    url_for,
)

import settings
from auth_blueprint.auth_blueprint import auth_blueprint
from doc_blueprint.doc_blueprint import doc_blueprint
from extensions import csrf, db, login_manager
from models import User
from point_and_timer_blueprint.point import point_blueprint
from point_and_timer_blueprint.timer_submit import timer_submit_blueprint
from reward_and_task_blueprint.reward_blueprint import reward_blueprint
from reward_and_task_blueprint.task_blueprint import task_blueprint
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
app.register_blueprint(point_blueprint)
app.register_blueprint(timer_submit_blueprint)
app.register_blueprint(reward_blueprint)

app.register_blueprint(task_blueprint)


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
