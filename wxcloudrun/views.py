from flask import render_template
from run import app

# 导入各个功能模块
from wxcloudrun.views import db_views, user_views, chat_views

@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')