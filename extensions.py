import functools

from flask import render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import DatabaseError

# 初始化数据库
db = SQLAlchemy()

# 初始化CSRF保护
csrf = CSRFProtect()

# 初始化LoginManager
login_manager = LoginManager()


def error_handler(func):
    """
    错误处理装饰器，用于捕获并处理视图函数中的异常
    - 处理数据库错误
    - 处理值错误
    - 处理其他未知错误
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            db.session.rollback()
            error_info = "抱歉，系统与数据库交互时出现问题，请稍后再试。"
            print(f"Database error: {str(e)}")
            return render_template("error.html", type=error_info)
        except ValueError as e:
            error_info = getattr(
                e, "info", "输入的值格式不正确，请检查后重新操作。"
            )
            print(f"Validation error: {str(e)}")
            return render_template("error.html", type=error_info)
        except Exception as e:
            error_info = "很抱歉，系统出现未知错误，请稍后再试。"
            print(f"Unexpected error: {str(e)}")
            return render_template("error.html", type=error_info)

    return wrapper
