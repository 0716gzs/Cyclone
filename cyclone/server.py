"""
Cyclone 异步HTTP服务器模块

基于asyncio的高性能HTTP服务器
"""

import asyncio
import logging
import signal
import socket
from typing import Callable, Dict, Optional, Tuple, Any
from .request import Request
from .response import Response
from .utils import parse_headers, build_http_response
from .exceptions import HTTPException, HTTPInternalServerError


class HTTPProtocol(asyncio.Protocol):
    """HTTP协议处理器"""
    
    def __init__(self, request_handler: Callable, max_request_size: int = 10 * 1024 * 1024):
        self.request_handler = request_handler
        self.max_request_size = max_request_size
        self.transport = None
        self.buffer = b""
        self.headers_complete = False
        self.request_complete = False
        self.content_length = 0
        self.headers = {}
        self.body = b""
        self.request_line = ""
        self.logger = logging.getLogger(__name__)
    
    def connection_made(self, transport):
        """连接建立"""
        self.transport = transport
        self.client_address = transport.get_extra_info('peername')
        self.logger.debug(f"连接建立: {self.client_address}")
    
    def data_received(self, data: bytes):
        """接收数据"""
        self.buffer += data
        
        if len(self.buffer) > self.max_request_size:
            self._send_error(413, "Request Entity Too Large")
            return
        
        try:
            self._process_buffer()
        except Exception as e:
            self.logger.error(f"处理请求数据时发生错误: {e}", exc_info=True)
            self._send_error(500, "Internal Server Error")
    
    def _process_buffer(self):
        """处理缓冲区数据"""
        if not self.headers_complete:
            self._parse_headers()
        
        if self.headers_complete and not self.request_complete:
            self._parse_body()
        
        if self.request_complete:
            asyncio.create_task(self._handle_request())
    
    def _parse_headers(self):
        """解析HTTP头部"""
        if b'\r\n\r\n' not in self.buffer:
            return
        
        header_end = self.buffer.find(b'\r\n\r\n')
        header_data = self.buffer[:header_end].decode('utf-8')
        self.buffer = self.buffer[header_end + 4:]
        
        lines = header_data.split('\r\n')
        if not lines:
            self._send_error(400, "Bad Request")
            return
        
        self.request_line = lines[0]
        try:
            method, path, version = self.request_line.split(' ', 2)
        except ValueError:
            self._send_error(400, "Bad Request")
            return
        
        self.method = method.upper()
        self.path = path
        self.version = version
        
        self.headers = parse_headers(lines[1:])
        self.content_length = int(self.headers.get('content-length', 0))
        
        self.headers_complete = True
        
        if self.content_length == 0:
            self.request_complete = True
    
    def _parse_body(self):
        """解析请求体"""
        if len(self.buffer) >= self.content_length:
            self.body = self.buffer[:self.content_length]
            self.buffer = self.buffer[self.content_length:]
            self.request_complete = True
    
    async def _handle_request(self):
        """处理HTTP请求"""
        try:
            if '?' in self.path:
                path, query_string = self.path.split('?', 1)
            else:
                path, query_string = self.path, ""
            
            request = Request(
                method=self.method,
                path=path,
                query_string=query_string,
                headers=self.headers,
                body=self.body,
                version=self.version.split('/')[-1] if '/' in self.version else "1.1"
            )
            
            response = await self.request_handler(request)
            await self._send_response(response)
            
        except HTTPException as e:
            self._send_error(e.status_code, e.message, e.headers)
        except Exception as e:
            self.logger.error(f"处理请求时发生错误: {e}", exc_info=True)
            self._send_error(500, "Internal Server Error")
        finally:
            self._reset_state()
    
    async def _send_response(self, response: Response):
        """发送HTTP响应"""
        try:
            response_data = build_http_response(response.status, response.headers, response.body)
            self.transport.write(response_data)
        except Exception as e:
            self.logger.error(f"发送响应时发生错误: {e}", exc_info=True)
    
    def _send_error(self, status_code: int, message: str, headers: Dict[str, str] = None):
        """发送错误响应"""
        error_headers = headers or {}
        error_headers.setdefault('Content-Type', 'text/plain; charset=utf-8')
        
        error_body = f"HTTP {status_code} {message}".encode('utf-8')
        response_data = build_http_response(status_code, error_headers, error_body)
        
        self.transport.write(response_data)
        self.transport.close()
    
    def _reset_state(self):
        """重置状态"""
        self.headers_complete = False
        self.request_complete = False
        self.content_length = 0
        self.headers = {}
        self.body = b""
        self.request_line = ""
    
    def connection_lost(self, exc):
        """连接丢失"""
        if exc:
            self.logger.debug(f"连接丢失: {self.client_address}, 错误: {exc}")
        else:
            self.logger.debug(f"连接关闭: {self.client_address}")


class AsyncHTTPServer:
    """异步HTTP服务器"""
    
    def __init__(self, request_handler: Callable, host: str = "127.0.0.1", 
                 port: int = 8000, backlog: int = 2048,
                 max_request_size: int = 10 * 1024 * 1024):
        self.request_handler = request_handler
        self.host = host
        self.port = port
        self.backlog = backlog
        self.max_request_size = max_request_size
        self.server = None
        self.loop = None
        self.logger = logging.getLogger(__name__)
        
        self.is_running = False
        self.start_time = None
        self.connections_count = 0
        self.requests_count = 0
    
    async def start(self):
        """启动服务器"""
        if self.is_running:
            return
        
        self.loop = asyncio.get_event_loop()
        
        def protocol_factory():
            return HTTPProtocol(self.request_handler, self.max_request_size)
        
        self.server = await self.loop.create_server(
            protocol_factory,
            self.host,
            self.port,
            backlog=self.backlog,
            reuse_address=True,
            reuse_port=True
        )
        
        self.is_running = True
        self.start_time = asyncio.get_event_loop().time()
        
        socket_infos = []
        for sock in self.server.sockets:
            socket_infos.append(sock.getsockname())
        
        self.logger.info(f"Cyclone服务器启动在 {self.host}:{self.port}")
        self.logger.info(f"绑定地址: {socket_infos}")
        
        self._setup_signal_handlers()
    
    async def stop(self):
        """停止服务器"""
        if not self.is_running:
            return
        
        self.logger.info("正在关闭服务器...")
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        self.is_running = False
        self.logger.info("服务器已关闭")
    
    async def serve_forever(self):
        """持续运行服务器"""
        await self.start()
        
        try:
            await self.server.serve_forever()
        except asyncio.CancelledError:
            self.logger.info("服务器被取消")
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
        finally:
            await self.stop()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        if not self.loop:
            return
        
        for sig in [signal.SIGINT, signal.SIGTERM]:
            try:
                self.loop.add_signal_handler(sig, self._signal_handler, sig)
            except NotImplementedError:
                pass
    
    def _signal_handler(self, sig):
        """信号处理器"""
        self.logger.info(f"收到信号 {sig}，正在关闭服务器...")
        asyncio.create_task(self.stop())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        uptime = 0
        if self.start_time:
            uptime = asyncio.get_event_loop().time() - self.start_time
        
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "uptime": uptime,
            "connections_count": self.connections_count,
            "requests_count": self.requests_count,
        }
    
    def __repr__(self) -> str:
        return f"<AsyncHTTPServer {self.host}:{self.port}>"


def create_server(request_handler: Callable, host: str = "127.0.0.1", 
                 port: int = 8000, **kwargs) -> AsyncHTTPServer:
    """创建HTTP服务器"""
    return AsyncHTTPServer(request_handler, host, port, **kwargs)


def run_server(request_handler: Callable, host: str = "127.0.0.1", 
               port: int = 8000, **kwargs):
    """运行HTTP服务器"""
    server = create_server(request_handler, host, port, **kwargs)
    
    try:
        asyncio.run(server.serve_forever())
    except KeyboardInterrupt:
        print("服务器被中断")
    except Exception as e:
        print(f"服务器错误: {e}")


async def run_server_async(request_handler: Callable, host: str = "127.0.0.1", 
                          port: int = 8000, **kwargs):
    """异步运行HTTP服务器"""
    server = create_server(request_handler, host, port, **kwargs)
    await server.serve_forever()
