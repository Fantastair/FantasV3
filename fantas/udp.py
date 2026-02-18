"""
fantas.udp 的 Docstring
"""

import socket

__all__ = (
    "create_udp_socket",
    "get_socket_port",
    "udp_send_data",
    "udp_receive_data",
)


def create_udp_socket(
    host: str = "127.0.0.1", port: int = 0, timeout: float | None = None
) -> socket.socket:
    """
    创建并返回一个 UDP 套接字。
    Args:
        host (str, optional): 绑定的主机地址，默认为 '127.0.0.1'。
        port (int, optional): 绑定的端口号，默认为 0，表示自动分配端口。
        timeout (float, optional): 套接字超时时间，默认为 None，表示阻塞模式。
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((host, port))
    udp_socket.settimeout(timeout)
    return udp_socket


def get_socket_port(sk: socket.socket) -> int:
    """
    获取 UDP 套接字绑定的端口号。
    Args:
        sk (socket.socket): 目标 UDP 套接字。
    Returns:
        int: 绑定的端口号。
    """
    return sk.getsockname()[1]  # type: ignore[no-any-return]


def udp_send_data(
    udp_socket: socket.socket, data: bytes, addr: tuple[str, int]
) -> None:
    """
    通过 UDP 套接字发送数据。
    Args:
        udp_socket (socket.socket): 目标 UDP 套接字。
        data (bytes): 要发送的数据字节。
        addr (tuple[str, int]): 目标地址，包含主机和端口号。
    """
    udp_socket.sendto(data, addr)


def udp_receive_data(
    udp_socket: socket.socket, buffer_size: int = 65535
) -> tuple[bytes | None, tuple[str, int] | None]:
    """
    通过 UDP 套接字接收数据。
    Args:
        udp_socket (socket.socket): 目标 UDP 套接字。
        buffer_size (int, optional): 接收缓冲区大小，默认为 65535 字节。
    Returns:
        tuple[bytes, tuple[str, int]]: 接收到的数据字节和发送方地址。
    """
    try:
        data, addr = udp_socket.recvfrom(buffer_size)
    except socket.timeout:
        return None, None
    except ConnectionResetError:
        return None, None
    return data, addr
