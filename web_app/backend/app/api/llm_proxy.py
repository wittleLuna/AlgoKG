# app/api/llm_proxy.py
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
import aiohttp, asyncio, json, re
import os

router = APIRouter()

# 可用环境变量切换 Ollama 地址（默认本机）
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 兜底去除 <think> ... </think>
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
def strip_think(text: str) -> str:
    return THINK_RE.sub("", text).strip()

@router.post("/chat")
async def chat(request: Request):
    """
    非流式：转发到 Ollama /api/chat，并去掉 <think>。
    请求体与 OpenAI Chat 格式一致：{ model, messages, temperature, max_tokens, ... }
    """
    body = await request.json()
    model = body.get("model", "qwen3:8b")
    messages = body.get("messages", [])
    temperature = body.get("temperature", 0.2)
    max_tokens = body.get("max_tokens", 1024)
    keepalive = body.get("keepalive")  # 可选：模型保活秒

    # 注入 system 抑制 think（多一层保险）
    if not messages or messages[0].get("role") != "system":
        messages = [{"role":"system","content":"只输出最终答案，不要输出任何思考或 <think> 内容。"}] + messages

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "think": False,    # Ollama 原生选项（支持就生效，不支持也不报错）
        }
    }
    if keepalive is not None:
        payload["keep_alive"] = f"{int(keepalive)}s"

    url = f"{OLLAMA_HOST}/api/chat"
    timeout = aiohttp.ClientTimeout(total=120)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as sess:
            async with sess.post(url, json=payload) as r:
                if r.status != 200:
                    txt = await r.text()
                    raise HTTPException(status_code=r.status, detail=txt)
                data = await r.json()
                content = data.get("message", {}).get("content", "") or ""
                return {
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {"role":"assistant","content": strip_think(content)}
                    }]
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama 调用失败: {e}")

@router.post("/chat/stream")
async def chat_stream(request: Request):
    """
    流式：SSE 风格输出，逐段转发 Ollama /api/chat 的流式响应，最后统一去掉 <think>。
    前端可用 EventSource / fetch+ReadableStream 接。
    """
    body = await request.json()
    model = body.get("model", "qwen3:8b")
    messages = body.get("messages", [])
    temperature = body.get("temperature", 0.2)
    max_tokens = body.get("max_tokens", 1024)

    if not messages or messages[0].get("role") != "system":
        messages = [{"role":"system","content":"只输出最终答案，不要输出任何思考或 <think> 内容。"}] + messages

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "think": False,
        }
    }

    url = f"{OLLAMA_HOST}/api/chat"
    timeout = aiohttp.ClientTimeout(total=120)

    async def streamer():
        buf = []
        try:
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.post(url, json=payload) as r:
                    if r.status != 200:
                        txt = await r.text()
                        yield f"event: error\ndata: {json.dumps({'error': txt}, ensure_ascii=False)}\n\n"
                        return
                    async for raw in r.content:
                        if not raw:
                            continue
                        try:
                            data = json.loads(raw.decode("utf-8"))
                        except Exception:
                            continue
                        part = data.get("message", {}).get("content", "")
                        if part:
                            buf.append(part)
                            # 先原样推给前端（让它实时看到），也可以选择这里就 strip
                            yield f"data: {json.dumps({'delta': part}, ensure_ascii=False)}\n\n"
                        if data.get("done"):
                            # 结束时再发一次“清洗后”的最终文本
                            full = strip_think("".join(buf))
                            yield f"data: {json.dumps({'final': full, 'done': True}, ensure_ascii=False)}\n\n"
                            return
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        streamer(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","Connection":"keep-alive"}
    )
