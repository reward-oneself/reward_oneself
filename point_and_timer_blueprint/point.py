import flask_login
from flask import Blueprint, render_template, request

from extensions import db, error_handler

from .timer_render import timer

point_blueprint = Blueprint("point", __name__, template_folder="templates")


@point_blueprint.route("/point", methods=["POST"])
@flask_login.login_required
@error_handler
def point():
    user = flask_login.current_user
    point_change = int(request.form.get("point_change"))
    name = request.form.get("name")
    repeat = request.form.get("repeat") == "True"
    from_page = request.form.get("from")

    time = request.form.get("time")
    if time:
        time = int(time)

    def process_point_change(type, repeat):
        """处理积分变更，返回结果"""

        if not point_change and name:
            raise ValueError(info="参数错误")

        # 处理积分变更
        updated_point = user.user_data.point + point_change
        if updated_point < 0:
            return ("失败，积分不足", False)

        user.user_data.point = updated_point
        db.session.commit()  # 提交积分更新

        if type == "reward" or repeat:
            return ("成功", False)

        try:
            task = dict(user.user_data.task)
            del task[name]
            user.user_data.task = task
            db.session.commit()
            return ("成功。该任务已自动删除", True)
        except KeyError:
            return ("成功。任务不存在", False)

    if point_change < 0:
        # 如果积分变化为负数，则是奖励，跳过处理任务的逻辑
        return_value = process_point_change(type="reward", repeat=repeat)
        result = return_value[0]
        return render_template(
            "point.html", result=result, name=name, point=user.user_data.point
        )

    if time == 0:
        result, delete = process_point_change(type="task", repeat=repeat)
        return render_template(
            "point.html", result=result, name=name, point=user.user_data.point
        )

    if from_page == "timer":
        result, delete = process_point_change(type="task", repeat=repeat)
        if delete:
            return render_template(
                "point.html",
                result=result,
                name=name,
                point=user.user_data.point,
            )
        else:
            return render_template(
                "point.html",
                result=result,
                name=name,
                point=user.user_data.point,
                from_page=from_page,
                value=point_change,
                time=time,
                repeat=repeat,
            )
    else:
        return timer(name=name, value=point_change, time=time, repeat=repeat)
