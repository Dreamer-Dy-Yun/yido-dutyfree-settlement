import asyncio
import uvicorn
from uvicorn import Config, Server

async def start_web_server():
    """비동기로 uvicorn 서버 실행"""
    config = Config(
        "WEB_SERVER.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    server = Server(config)
    print("Server started")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(start_web_server())