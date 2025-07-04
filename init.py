import app
with app.app.app_context():
    app.init_db()
    print('数据库初始化成功')