import flask_login
from flask import redirect, render_template, url_for

from extensions import db, error_handler
from filehandle import FileHandler


@error_handler
def remove(type_name):
    """
    渲染移除任务或奖励的页面，根据提供的类型参数，并列出所有可移除的项。
    """

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


@error_handler
def remove_submit(type_name, form_data) -> str:
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
