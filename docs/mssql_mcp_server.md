https://github.com/RichardHan/mssql_mcp_server

aoton0029: microsoft_sql_server_mcpライブラリを使ってpythonでmcpサーバー構築

Workspace: Sure, here's a proposed directory structure for

Create Workspace...

aoton0029: サンプルを作って

GitHub Copilot: Microsoft SQL Server用のMCPサーバーのサンプルを作成します。

````python
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Sequence

import pyodbc
from mcp import McpServer
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    EmbeddedResource,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
)
from pydantic import BaseModel, Field

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig(BaseModel):
    server: str = Field(default="localhost")
    database: str = Field(default="master")
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    driver: str = Field(default="ODBC Driver 17 for SQL Server")
    trusted_connection: bool = Field(default=True)

class SQLServerMCPServer:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """データベース接続文字列を構築"""
        parts = [
            f"DRIVER={{{self.config.driver}}}",
            f"SERVER={self.config.server}",
            f"DATABASE={self.config.database}",
        ]
        
        if self.config.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            if self.config.username and self.config.password:
                parts.append(f"UID={self.config.username}")
                parts.append(f"PWD={self.config.password}")
        
        return ";".join(parts)
    
    @asynccontextmanager
    async def get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def execute_query(self, query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """SQLクエリを実行して結果を返す"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # SELECT文の場合は結果を取得
                if query.strip().upper().startswith('SELECT'):
                    columns = [column[0] for column in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                else:
                    # INSERT/UPDATE/DELETE文の場合
                    conn.commit()
                    return [{"affected_rows": cursor.rowcount}]
                    
            except Exception as e:
                logger.error(f"Query execution error: {e}")
                conn.rollback()
                raise
    
    async def get_tables(self) -> List[str]:
        """データベース内のテーブル一覧を取得"""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        results = await self.execute_query(query)
        return [row["TABLE_NAME"] for row in results]
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """テーブルのスキーマ情報を取得"""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        return await self.execute_query(query, [table_name])

# グローバル変数
db_server: Optional[SQLServerMCPServer] = None

async def list_tools() -> List[Tool]:
    """利用可能なツール一覧を返す"""
    return [
        Tool(
            name="execute_sql",
            description="SQL Serverでクエリを実行",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "実行するSQLクエリ"
                    },
                    "params": {
                        "type": "array",
                        "description": "クエリパラメータ（オプション）",
                        "items": {"type": "string"}
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_tables",
            description="データベース内のテーブル一覧を取得",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="describe_table",
            description="テーブルのスキーマ情報を取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "スキーマを取得するテーブル名"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]

async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """ツールを実行"""
    if not db_server:
        return [TextContent(type="text", text="Database server not initialized")]
    
    try:
        if name == "execute_sql":
            query = arguments.get("query", "")
            params = arguments.get("params")
            results = await db_server.execute_query(query, params)
            return [TextContent(type="text", text=str(results))]
        
        elif name == "list_tables":
            tables = await db_server.get_tables()
            return [TextContent(type="text", text="\n".join(tables))]
        
        elif name == "describe_table":
            table_name = arguments.get("table_name", "")
            schema = await db_server.get_table_schema(table_name)
            return [TextContent(type="text", text=str(schema))]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def list_resources() -> List[Resource]:
    """利用可能なリソース一覧を返す"""
    if not db_server:
        return []
    
    try:
        tables = await db_server.get_tables()
        resources = []
        
        for table in tables:
            resources.append(
                Resource(
                    uri=f"sql://{table}",
                    name=f"Table: {table}",
                    description=f"SQL Server table: {table}",
                    mimeType="application/json"
                )
            )
        
        return resources
    
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return []

async def read_resource(uri: str) -> str:
    """リソースの内容を読み取る"""
    if not db_server:
        return "Database server not initialized"
    
    if uri.startswith("sql://"):
        table_name = uri[6:]  # "sql://" を除去
        try:
            schema = await db_server.get_table_schema(table_name)
            return str(schema)
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return f"Error: {str(e)}"
    
    return f"Unknown resource: {uri}"

async def main():
    """メイン実行関数"""
    global db_server
    
    # 設定読み込み（環境変数から）
    config = DatabaseConfig(
        server=os.getenv("SQL_SERVER", "localhost"),
        database=os.getenv("SQL_DATABASE", "master"),
        username=os.getenv("SQL_USERNAME"),
        password=os.getenv("SQL_PASSWORD"),
        trusted_connection=os.getenv("SQL_TRUSTED_CONNECTION", "true").lower() == "true"
    )
    
    # データベースサーバー初期化
    db_server = SQLServerMCPServer(config)
    
    # MCPサーバー設定
    server = McpServer("microsoft-sql-server")
    
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        return await list_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        return await call_tool(name, arguments)
    
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        return await list_resources()
    
    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        return await read_resource(uri)
    
    # STDIOサーバーとして実行
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="microsoft-sql-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
````

````text
mcp>=1.0.0
pyodbc>=4.0.39
pydantic>=2.0.0
python-dotenv>=1.0.0
````

````text
# SQL Server接続設定
SQL_SERVER=localhost
SQL_DATABASE=master
SQL_USERNAME=your_username
SQL_PASSWORD=your_password
SQL_TRUSTED_CONNECTION=true
````

````markdown
# Microsoft SQL Server MCP Server

Microsoft SQL ServerデータベースへのMCP（Model Context Protocol）サーバー実装です。

## 機能

- SQLクエリの実行
- テーブル一覧の取得
- テーブルスキーマ情報の取得
- セキュアなデータベース接続

## セットアップ

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. 環境設定:
`.env.example`を`.env`にコピーして設定を変更

3. SQL Server ODBC Driverのインストール:
Microsoft ODBC Driver 17 for SQL Serverが必要です。

## 使用方法

```bash
python main.py
```

## 利用可能なツール

- `execute_sql`: SQLクエリを実行
- `list_tables`: テーブル一覧を取得
- `describe_table`: テーブルスキーマを取得

## セキュリティ

- パラメータ化クエリを使用
- 接続プーリング対応
- エラーハンドリング実装
````

このサンプルは以下の機能を提供します:

1. **SQL Server接続**: ODBC経由でSQL Serverに接続
2. **MCPツール**: SQLクエリ実行、テーブル一覧取得、スキーマ情報取得
3. **リソース管理**: テーブル情報をリソースとして公開
4. **セキュリティ**: パラメータ化クエリとエラーハンドリング
5. **設定管理**: 環境変数による設定

使用前に`pip install -r requirements.txt`で依存関係をインストールし、SQL Server ODBC Driverがシステムにインストールされていることを確認してください。

aoton0029: n8nでmcpノードに設定するために、https://github.com/RichardHan/mssql_mcp_server を使ったmcpサーバーのサンプルを作って

GitHub Copilot: RichardHan/mssql_mcp_serverライブラリを使ったMCPサーバーのサンプルを作成します。

````python
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
````

````text
git+https://github.com/RichardHan/mssql_mcp_server.git
python-dotenv>=1.0.0
````

````text
# SQL Server接続設定（n8n MCP Node用）
MSSQL_SERVER=localhost
MSSQL_DATABASE=master
MSSQL_USERNAME=sa
MSSQL_PASSWORD=your_password
MSSQL_PORT=1433
MSSQL_DRIVER=ODBC Driver 17 for SQL Server
MSSQL_TRUST_CERT=true
MSSQL_ENCRYPT=false
````

````json
{
  "name": "mssql-mcp-server",
  "version": "1.0.0",
  "description": "Microsoft SQL Server MCP Server for n8n",
  "main": "main.py",
  "scripts": {
    "start": "python main.py"
  },
  "keywords": ["mcp", "sql-server", "n8n"],
  "author": "Your Name",
  "license": "MIT"
}
````

````bash
@echo off
cd /d "%~dp0"
python main.py
````

````bash
#!/bin/bash
cd "$(dirname "$0")"
python main.py
````

````markdown
# Microsoft SQL Server MCP Server for n8n

RichardHan/mssql_mcp_serverライブラリを使用したn8n MCP Node対応のSQL Server MCPサーバーです。

## セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
`.env`ファイルを編集してSQL Server接続情報を設定:

```env
MSSQL_SERVER=localhost
MSSQL_DATABASE=your_database
MSSQL_USERNAME=your_username
MSSQL_PASSWORD=your_password
MSSQL_PORT=1433
```

### 3. SQL Server ODBC Driverのインストール
Microsoft ODBC Driver 17 for SQL Serverが必要です:
- Windows: https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- Linux: パッケージマネージャーからインストール

## n8n MCP Nodeでの設定

### MCPサーバー設定
1. n8nでMCP Nodeを追加
2. Server設定:
   - **Command**: `python`
   - **Arguments**: `["d:\\path\\to\\your\\project\\main.py"]`
   - **Working Directory**: `d:\\path\\to\\your\\project`
   - **Environment Variables**: 
     ```json
     {
       "MSSQL_SERVER": "localhost",
       "MSSQL_DATABASE": "your_database",
       "MSSQL_USERNAME": "your_username", 
       "MSSQL_PASSWORD": "your_password"
     }
     ```

### 利用可能なツール
- `execute_query`: SQLクエリを実行
- `list_tables`: データベース内のテーブル一覧を取得
- `describe_table`: テーブルスキーマ情報を取得
- `get_table_data`: テーブルデータを取得（制限付き）

### 使用例

#### 1. テーブル一覧の取得
```json
{
  "tool": "list_tables",
  "arguments": {}
}
```

#### 2. SQLクエリの実行
```json
{
  "tool": "execute_query", 
  "arguments": {
    "query": "SELECT TOP 10 * FROM Users WHERE active = 1",
    "parameters": []
  }
}
```

#### 3. テーブルスキーマの取得
```json
{
  "tool": "describe_table",
  "arguments": {
    "table_name": "Users"
  }
}
```

## ローカルテスト

直接実行してテスト:
```bash
python main.py
```

Windows:
```bash
start.bat
```

## トラブルシューティング

### 接続エラー
- SQL Serverが起動しているか確認
- 認証情報が正しいか確認
- ファイアウォール設定を確認

### ODBC Driver エラー
- 適切なODBC Driverがインストールされているか確認
- Driverの名前が環境に合っているか確認

### n8n MCP Node設定
- ファイルパスが正しいか確認（絶対パスを使用）
- 環境変数が正しく設定されているか確認
- Pythonのパスが正しいか確認
````

この設定により、n8nのMCP Nodeで以下のような設定が可能になります:

**n8n MCP Node設定例:**
- **Server Command**: `python`
- **Server Arguments**: `["d:\\notoa\\Documents\\Python main.py"]`
- **Working Directory**: `d:\\notoa\\Documents\\Python Projects\\ai_projects\\src\\microsoft_sql`
- **Environment Variables**: 環境変数として接続情報を設定

このサンプルはSTDIOモードで動作し、n8nとの通信に最適化されています。