import uuid, base64, hashlib

def _short_id() -> str:
    """uuid4 → 22字符的urlsafe短ID（去掉'='）"""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode().rstrip('=')

def new_session_id() -> str:
    return f"ses_{_short_id()}"            # 形如: ses_VfWlY7ZlQy2TqU6cM0m8rQ

def new_message_id() -> str:
    return f"msg_{_short_id()}"            # 形如: msg_Ys7x1b6ZQK25b1V7v1bI8A

def new_name_id(name: str, salt: str = "") -> str:
    """
    name提供→生成“稳定ID”（同name+salt恒定）；
    name不提供→随机ID。
    """
    if name:
        # 8字节哈希→urlsafe base64 → 11~12字符
        h = hashlib.blake2s(f"{name}#{salt}".encode(), digest_size=8).digest()
        sid = base64.urlsafe_b64encode(h).decode().rstrip('=')
        return f"prt_{sid}"                 # 形如: prt_X3Pz1y8Kc2Y
    return f"prt_{_short_id()}"            # 随机: prt_...

# 示例
if __name__ == "__main__":
    print(new_session_id())
    print(new_message_id())
    print(new_name_id("小白", "prod"))    # 稳定
