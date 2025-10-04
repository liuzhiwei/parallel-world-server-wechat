"""
简单的原生 WebSocket 实现
"""
from flask import Flask, request
from flask_sockets import Sockets
import json
import time
import logging

# 初始化日志
logger = logging.getLogger('log')

def init_simple_websocket(app):
    """初始化简单 WebSocket"""
    sockets = Sockets(app)
    
    @sockets.route('/ws/stream')
    def stream(ws):
        logger.info(f"[WEBSOCKET] 客户端连接: {request.remote_addr}")
        
        try:
            # 模拟大模型流式输出
            messages = [
                {"type": "message", "data": {"speaker_type": "avatar", "message": "你好！", "name": "旅行分身"}},
                {"type": "message", "data": {"speaker_type": "avatar", "message": "我是你的旅行分身", "name": "旅行分身"}},
                {"type": "message", "data": {"speaker_type": "avatar", "message": "很高兴为你规划这次旅行！", "name": "旅行分身"}},
                {"type": "complete", "data": {"total_messages": 3}}
            ]
            
            for i, msg in enumerate(messages):
                logger.info(f"[WEBSOCKET] 发送消息 {i+1}: {msg}")
                ws.send(json.dumps(msg, ensure_ascii=False))
                time.sleep(1)  # 模拟延迟
                
            logger.info(f"[WEBSOCKET] 所有消息发送完成")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] 连接异常: {e}")
    
    logger.info("[WEBSOCKET] 简单 WebSocket 路由已注册: /ws/stream")
