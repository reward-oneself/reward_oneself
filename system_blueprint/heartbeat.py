import flask_login
from flask import Blueprint

heartbeat_blueprint = Blueprint("heartbeat_blueprint", __name__)


@heartbeat_blueprint.route("/heartbeat")
@flask_login.login_required
def heartbeat():
    """
    心跳保活接口
    用于计时器页面保持会话活跃，防止长时间计时期间会话过期
    """
    return "", 204  # 返回空内容和204状态码
