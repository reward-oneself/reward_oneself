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


from typing import Optional, Dict, Any  # 添加缺失的类型导入

import flask_login
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect  # 新增CSRF扩展

app = Flask(__name__)
data = os.environ.get('DATA', 'sqlite:///data.db')
key = os.environ.get('KEY', 'key')
app.config['SQLALCHEMY_DATABASE_URI'] = data
app.config['SECRET_KEY'] = key  # 建议通过环境变量强制配置
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 初始化CSRF保护
csrf = CSRFProtect(app)

# 初始化LoginManager
login_manager = LoginManager(app)

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
                        unique=True, nullable=False)
    reward = db.Column(db.JSON, nullable=False, default=lambda: {})
    point = db.Column(db.Integer, nullable=False, default=0)
    task = db.Column(db.JSON, nullable=False, default=lambda: {})
    user = db.relationship('User', backref=db.backref('user_data', uselist=False, cascade='all, delete-orphan'))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/login_submit', methods=['POST'])
def login_submit():
    input_username = request.form.get('username')
    input_password = request.form.get('password')
    user = User.query.filter_by(username=input_username).first()
    if user and check_password_hash(user.password, input_password):
        flask_login.login_user(user)
        return redirect(url_for('index'))
    else:
        return render_template('error.html', type="用户名或密码错误")


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register_submit', methods=['POST'])
def register_submit():
    input_username = request.form.get('username')
    input_password = request.form.get('password')
    if not input_username or not input_password:
        flash('用户名和密码不能为空')
        return redirect(url_for('register'))
    if len(input_password) < 6:
        flash('密码长度至少为6位')
        return redirect(url_for('register'))
    if User.query.filter_by(username=input_username).first():
        flash('用户名已存在')
        return redirect(url_for('register'))
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
    flash('注册成功，请登录')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


@app.route('/')
@flask_login.login_required
def index():
    user = flask_login.current_user
    db.session.refresh(user.user_data)
    point_value = user.user_data.point
    rewards = user.user_data.reward
    tasks = user.user_data.task

    rewards_text = ""
    for name, value in rewards.items():
        rewards_text += f"<tr><td><a href='point?point_change=-{value}&name={name}'>{name}</a></td><td>{value}</td></tr>"

    tasks_text = ""
    for name, value in tasks.items():
        tasks_text += f"<tr><td><a href='point?point_change={value}&name={name}'>{name}</a></td><td>{value}</td></tr>"

    return render_template('index.html', username=user.username, point=point_value, rewards=rewards_text,
                           tasks=tasks_text)


@app.route('/point')
@flask_login.login_required
def point():
    user = flask_login.current_user
    point_change = request.args.get('point_change')
    name = request.args.get('name')

    if point_change and name:
        try:
            point_change = int(point_change)
        except ValueError:
            return render_template('error.html', type="数据格式错误")

        updated_point = user.user_data.point + point_change
        if updated_point >= 0:
            user.user_data.point = updated_point
            db.session.commit()
            result = "成功"
        else:
            result = "失败，积分不足"

        return render_template('point.html',
                               result=result,
                               name=name,
                               point=user.user_data.point)
    else:
        return render_template('error.html', type="参数错误")


@app.route('/add_new')
@flask_login.login_required
def add_new():
    """
    渲染添加新任务或奖励的页面，根据提供的类型参数。
    """
    type_name = request.args.get('type')
    if type_name:
        return render_template('add_new.html', type=type_name)
    else:
        return render_template('error.html', type="参数错误")


@app.route('/add_new_submit', methods=['POST', 'GET'])
@flask_login.login_required
def add_new_submit():
    """
    处理添加新任务/奖励的提交请求
    业务流程：
    1. 验证参数有效性（名称、类型、积分值）
    2. 创建对应数据的副本并更新
    3. 完全替换原有JSON字段触发数据库更新
    4. 提交事务或在出错时回滚
    
    安全要求：
    - 必须登录才能访问
    - 参数验证防止无效数据写入
    - 异常处理保证数据一致性
    """
    type_name = request.args.get('type')
    name = request.form.get('name')
    points = request.form.get('points')

    try:
        changed_points = int(points)
    except ValueError:
        return render_template('error.html', type="数据格式错误")

    if type_name and changed_points > 0:
        user = flask_login.current_user

        if type_name == "reward":
            # 创建当前奖励数据的副本并完全替换原有字段
            rewards = dict(user.user_data.reward)  # 创建新对象确保SQLAlchemy检测到变化
            rewards[name] = changed_points
            user.user_data.reward = rewards  # 完全替换字典触发数据库更新
        else:
            # 创建当前任务数据的副本并完全替换原有字段
            tasks = dict(user.user_data.task)  # 创建新对象确保SQLAlchemy检测到变化
            tasks[name] = changed_points
            user.user_data.task = tasks  # 完全替换字典触发数据库更新
        try:
            db.session.commit()  # 提交数据库事务
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # 回滚事务
            print(f"数据库错误: {str(e)}")  # 记录详细错误信息
            return render_template('error.html', type=f"数据库错误: {str(e)}")
    else:
        return render_template('error.html', type="参数错误或参数不符合要求")


@app.route('/remove')
@flask_login.login_required
def remove():
    """
    渲染移除任务或奖励的页面，根据提供的类型参数，并列出所有可移除的项。
    """
    type_name = request.args.get('type')
    if type_name:
        user = flask_login.current_user

        if type_name == "reward":
            items = user.user_data.reward
        else:
            items = user.user_data.task

        text = ""
        for name in items.keys():
            text += f"<input type='checkbox' name='{name}'><label>{name}</label><br>"
        return render_template('remove.html', type=type_name, text=text)
    else:
        return render_template('error.html', type="参数错误")


@app.route('/remove_submit', methods=['POST', 'GET'])
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
    type_name: Optional[str] = request.args.get('type')
    form_data: Dict[str, str] = request.form.to_dict()

    if type_name:
        user = flask_login.current_user

        try:
            if type_name == "reward":
                # 创建当前奖励数据的副本并完全替换原有字段
                rewards: Dict[str, Any] = dict(user.user_data.reward)  # 创建新对象确保SQLAlchemy检测到变化
                # 保留不在form_data中的项
                updated_rewards: Dict[str, Any] = {
                    name: value for name, value in rewards.items()
                    if name not in form_data
                }
                user.user_data.reward = updated_rewards  # 完全替换字典触发数据库更新
                print("删除了奖励：", ", ".join(set(rewards.keys()) - set(updated_rewards.keys())))
            else:
                # 创建当前任务数据的副本并完全替换原有字段
                tasks: Dict[str, Any] = dict(user.user_data.task)  # 创建新对象确保SQLAlchemy检测到变化
                # 保留不在form_data中的项
                updated_tasks: Dict[str, Any] = {
                    name: value for name, value in tasks.items()
                    if name not in form_data
                }
                user.user_data.task = updated_tasks  # 完全替换字典触发数据库更新
                print("删除了任务：", ", ".join(set(tasks.keys()) - set(updated_tasks.keys())))

            db.session.commit()  # 提交数据库事务
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()  # 回滚事务
            print(f"数据库错误: {str(e)}")  # 记录详细错误信息
            return render_template('error.html', type=f"数据库错误: {str(e)}")
    else:
        return render_template('error.html', type="参数错误或参数不符合要求")


@app.route('/delete_account')
@flask_login.login_required
def delete_account():
    """
    显示注销账户确认页面
    - 需要登录才能访问
    - 提供安全提示
    """
    return render_template('delete_account.html')


@app.route('/delete_account_submit', methods=['POST'])
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
        flash('您的账户已成功注销')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        print(f"注销错误: {str(e)}")
        return render_template('error.html', type="注销失败")


@login_manager.unauthorized_handler
def unauthorized():
    """
    未授权访问处理函数
    - 当未登录用户尝试访问受保护路由时触发
    - 重定向到登录页面保持用户体验一致性
    - 符合Flask-Login的认证规范要求
    """
    return redirect(url_for('login'))


if __name__ == '__main__':
    """
    应用启动入口
    - 调试模式开启（开发环境）
    - 监听所有网络接口（便于容器部署）
    - 使用默认端口5000
    """
    app.run(host='0.0.0.0', port=80)
