import asyncio
import json
import websockets
import uuid
import base64
import hashlib
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = "4e4af2d1f874879ebff1ad2e593686e8aae8f4708263a0dd"


async def chat_with_openclaw(message: str, token: str = TOKEN):
    # uri = "ws://60.205.136.51:18789"
    uri = "ws://host.docker.internal:18789"
    # uri = "ws://10.1.130.133:18789"
    # uri = "ws://10.1.130.133:18789"

    # 生成密钥对
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    device_id = hashlib.sha256(public_key_bytes).hexdigest()

    async with websockets.connect(uri) as ws:
        # 1. 等待 challenge
        challenge_resp = await ws.recv()
        challenge = json.loads(challenge_resp)
        nonce = challenge["payload"]["nonce"]

        # 2. 构建签名载荷
        signed_at = int(datetime.now().timestamp() * 1000)
        payload_parts = [
            "v2",
            device_id,
            "cli",
            "cli",
            "operator",
            "operator.admin",
            str(signed_at),
            token or "",
            nonce
        ]
        payload = "|".join(payload_parts)

        # 3. 签名
        signature = private_key.sign(payload.encode())

        # 4. 发送握手（只使用 token 认证，不发送 device）
        handshake = {
            "type": "req",
            "id": "1",
            "method": "connect",
            "params": {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": "cli",
                    "displayName": "python-client",
                    "version": "1.0.0",
                    "platform": "python",
                    "mode": "cli"
                },
                "role": "operator",
                "scopes": ["operator.admin"]
            }
        }
        # 只使用 token 认证
        if token:
            handshake["params"]["auth"] = {"token": token}
        await ws.send(json.dumps(handshake))

        # 5. 等待握手响应
        while True:
            resp = await ws.recv()
            data = json.loads(resp)

            if data.get("type") == "res" and data.get("id") == "1":
                if not data.get("ok"):
                    raise Exception(f"握手失败: {data}")
                print("✅ 握手成功")
                break

        # 6. 发送聊天消息（添加 idempotencyKey，移除 stream）
        request = {
            "type": "req",
            "id": "2",
            "method": "agent",
            "params": {
                "message": message,
                "sessionKey": "main",  # 添加这行
                "idempotencyKey": str(uuid.uuid4())
            }
        }
        await ws.send(json.dumps(request))

        # 7. 接收响应
        full_response = ""
        final_res = None

        while True:
            resp = await ws.recv()
            data = json.loads(resp)
            print(f"resp: {resp}")

            if data.get("type") == "event" and data.get("event") == "agent":
                # 处理流式输出
                content = data.get("payload", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
                    full_response += content
            elif data.get("type") == "res" and data.get("id") == "2":
                # 检查是否是最终响应（不是accepted）
                if data.get("payload", {}).get("status") != "accepted":
                    final_res = data
                    if data.get("ok"):
                        print(f"\n✅ 完成: {data.get('payload')}")
                        print("-" * 80)
                        answer_payloads = data.get('payload', {}).get('result', {}).get('payloads', [])
                        answer="\n".join([p.get('text', '') for p in answer_payloads])
                        print(f"\n✅ ✅ 最终答案: \n{answer}")
                    else:
                        print(f"\n❌ 错误: {data.get('error')}")
                    break


if __name__ == "__main__":
    asyncio.run(chat_with_openclaw(
        message="请查看一下/opt目录下有哪些文件"
    ))
