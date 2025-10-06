from flask import Flask

def register_api_routes(app):
    """注册API路由"""
    
    @app.get("/ping")
    def ping():
        return "pong"
