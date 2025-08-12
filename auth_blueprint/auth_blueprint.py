import flask_login
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, error_handler
from models import User

auth_blueprint = Blueprint("auth", __name__, template_folder="templates")


@auth_blueprint.route("/login")
@error_handler
def login():
    return render_template("login.html")


@auth_blueprint.route("/login_submit", methods=["POST"])
@error_handler
def login_submit():
    def wrapped_login_submit():
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        if not input_username or not input_password:
            raise ValueError(info="用户名和密码不能为空")

        user = User.query.filter_by(username=input_username).first()
        if not user or not check_password_hash(user.password, input_password):
            raise ValueError(info="用户名或密码错误")

        flask_login.login_user(user)
        return redirect(url_for("index_blueprint.index"))

    return wrapped_login_submit()


@auth_blueprint.route("/register")
@error_handler
def register():
    return render_template("register.html")


@auth_blueprint.route("/register_submit", methods=["POST"])
@error_handler
def register_submit():
    from app import User, UserData

    def wrapped_register_submit():
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        if not input_username or not input_password:
            raise ValueError(info="用户名和密码不能为空")
        if len(input_password) < 6:
            raise ValueError(info="密码长度至少为6位")
        if User.query.filter_by(username=input_username).first():
            raise ValueError(info="用户名已存在")

        user = User(
            username=input_username,
            password=generate_password_hash(input_password),
        )
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
        return redirect(url_for("auth.login"))

    return wrapped_register_submit()


@auth_blueprint.route("/logout")
@error_handler
def logout():

    def wrapped_logout():
        flask_login.logout_user()
        return redirect(url_for("auth.login"))

    return wrapped_logout()


@auth_blueprint.route("/delete_account")
@flask_login.login_required
@error_handler
def delete_account():
    """
    显示注销账户确认页面
    - 需要登录才能访问
    - 提供安全提示
    """
    return render_template("delete_account.html")


@auth_blueprint.route("/delete_account_submit", methods=["POST"])
@flask_login.login_required
@error_handler
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

    def wrapped_delete_account_submit():
        user = flask_login.current_user
        db.session.delete(user)
        db.session.commit()
        flask_login.logout_user()
        flash("您的账户已成功注销")
        return redirect(url_for("index_blueprint.index"))

    return wrapped_delete_account_submit()
