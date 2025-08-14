# 从extensions.py导入db实例
from flask_login import UserMixin

from extensions import db


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
    - rest_time_to_work_ratio: 休息时间与工作时间的比例，默认5
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
        backref=db.backref(
            "user_data", uselist=False, cascade="all, delete-orphan"
        ),
    )
