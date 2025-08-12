import flask_login
from flask import Blueprint, render_template

import settings
from extensions import db
from filehandle import FileHandler
from hitokoto import get_hitokoto

index_blueprint = Blueprint("index_blueprint", __name__)


@index_blueprint.route("/")
@flask_login.login_required
def index():
    user = flask_login.current_user
    db.session.refresh(user.user_data)
    point_value = user.user_data.point
    reward = user.user_data.reward
    task = user.user_data.task

    reward_text = ""
    file_handler = FileHandler("partials/reward_text.html")
    add_text = file_handler.read()
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
    file_handler = FileHandler("partials/task_text.html")
    add_text = file_handler.read()
    for i in sort_task_name_list:
        task_data = task.get(i)
        if task_data["repeat"]:
            repeat_icon = "🔁"
        else:
            repeat_icon = "🚫"
        task_text += add_text.format(
            points=task_data["points"],
            time=task_data["time"],
            priority=task_data["priority"],
            repeat=task_data["repeat"],
            repeat_icon=repeat_icon,
            i=i,
        )

    love = user.user_data.love
    hitokoto = get_hitokoto(settings.HITOKOTO_URL, love, settings.LOCAL_MODE)
    return render_template(
        "index.html",
        username=user.username,
        point=point_value,
        hitokoto=hitokoto,
        reward=reward_text,
        task=task_text,
    )
