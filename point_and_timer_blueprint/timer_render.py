import flask_login
from flask import render_template

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