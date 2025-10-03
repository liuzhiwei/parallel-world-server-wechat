# 视图模块初始化文件
# 导入所有视图模块，确保蓝图被注册
# 注意：导入顺序很重要，避免循环导入
try:
    from . import db_views
    from . import user_views  
    from . import chat_views
    from . import chat_views_react
    print("所有视图模块导入成功")
except Exception as e:
    print(f"视图模块导入失败: {e}")
    raise e
