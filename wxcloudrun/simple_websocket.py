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
        logger.info(f"[WEBSOCKET] ========== 客户端连接开始 ==========")
        logger.info(f"[WEBSOCKET] 客户端IP: {request.remote_addr}")
        logger.info(f"[WEBSOCKET] WebSocket对象: {ws}")
        
        # 发送连接确认消息
        try:
            welcome_msg = {"type": "connection", "data": {"message": "WebSocket连接成功"}}
            ws.send(json.dumps(welcome_msg, ensure_ascii=False))
            logger.info(f"[WEBSOCKET] 连接确认消息已发送")
        except Exception as welcome_error:
            logger.error(f"[WEBSOCKET] 连接确认消息发送失败: {welcome_error}")
            return
        
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
                try:
                    ws.send(json.dumps(msg, ensure_ascii=False))
                    logger.info(f"[WEBSOCKET] 消息 {i+1} 发送成功")
                except Exception as send_error:
                    logger.error(f"[WEBSOCKET] 消息 {i+1} 发送失败: {send_error}")
                    break
                
            logger.info(f"[WEBSOCKET] 所有消息发送完成")
            
        except Exception as e:
            logger.error(f"[WEBSOCKET] 连接异常: {e}")
    
    logger.info("[WEBSOCKET] 简单 WebSocket 路由已注册: /ws/stream")
