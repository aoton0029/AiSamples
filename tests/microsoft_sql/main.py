import asyncio
import os
import sys
from pathlib import Path

# mssql_mcp_serverライブラリのインポート
from mssql_mcp_server.server import create_server
from mssql_mcp_server.database import DatabaseConfig

async def main():
    """
    n8n MCP Node用のSQL Server MCPサーバー
    """
    # 環境変数から設定を読み込み
    config = DatabaseConfig(
        server=os.getenv("MSSQL_SERVER", "localhost"),
        database=os.getenv("MSSQL_DATABASE", "master"),
        username=os.getenv("MSSQL_USERNAME", "sa"),
        password=os.getenv("MSSQL_PASSWORD", ""),
        port=int(os.getenv("MSSQL_PORT", "1433")),
        driver=os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server"),
        trust_server_certificate=os.getenv("MSSQL_TRUST_CERT", "true").lower() == "true",
        encrypt=os.getenv("MSSQL_ENCRYPT", "false").lower() == "true"
    )
    
    # MCPサーバーを作成して起動
    server = create_server(config)
    
    # STDIOモードで実行（n8nとの通信用）
    await server.run_stdio()

if __name__ == "__main__":
    # Windows環境でのイベントループポリシー設定
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)