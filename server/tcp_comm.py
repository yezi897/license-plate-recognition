import socket
import time
import select
import logging

logger = logging.getLogger(__name__)


class TcpComm:
    def __init__(self, host, port=8080):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(None)
        logger.info("TCP 连接成功: %s:%d", self.host, self.port)

    def is_connected(self):
        if self.sock is None:
            return False
        try:
            # 检查 socket 是否仍然可读（非阻塞探测）
            readable, _, _ = select.select([self.sock], [], [], 0)
            if readable:
                # 尝试 peek 数据，如果返回空说明连接已断开
                data = self.sock.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
                if not data:
                    return False
            return True
        except (OSError, BlockingIOError):
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def _read_exactly(self, size, deadline):
        """保证读满 size 字节，无新数据超过 0.5 秒则提前放弃"""
        data = b''
        last_progress = time.time()
        while len(data) < size:
            if time.time() > deadline:
                break
            if time.time() - last_progress > 0.5:
                break
            remaining = size - len(data)
            timeout = min(0.1, deadline - time.time())
            if timeout <= 0:
                break
            try:
                ready, _, _ = select.select([self.sock], [], [], timeout)
                if not ready:
                    continue
                chunk = self.sock.recv(remaining)
                if not chunk:
                    break
                data += chunk
                last_progress = time.time()
            except Exception:
                break
        return data

    def capture_image(self, cmd=b'C', timeout=10):
        if not self.is_connected():
            logger.warning("capture_image: TCP 未连接")
            return None

        try:
            self.sock.send(cmd)
        except Exception as e:
            logger.warning("capture_image: 发送命令失败: %s", e)
            return None
        logger.info("capture_image: 已发送命令 %s, 等待响应 (timeout=%ds)", cmd, timeout)

        deadline = time.time() + timeout

        # 第一阶段: 寻找 IMG_START 标记
        marker = b''
        while time.time() < deadline:
            timeout_val = min(0.1, deadline - time.time())
            if timeout_val <= 0:
                break
            try:
                ready, _, _ = select.select([self.sock], [], [], timeout_val)
                if not ready:
                    continue
                byte = self.sock.recv(1)
            except Exception:
                logger.warning("capture_image: 读取中断")
                return None
            if not byte:
                continue
            marker += byte
            if len(marker) > 9:
                marker = marker[-9:]
            if marker == b'IMG_START':
                break
        else:
            logger.warning("capture_image: 超时未找到 IMG_START, 已收: %s", marker.decode('ascii', errors='replace'))
            return None

        # 第二阶段: 读取 4 字节长度头
        len_bytes = self._read_exactly(4, deadline)
        if len(len_bytes) < 4:
            logger.warning("capture_image: 读取长度头不完整")
            return None
        img_length = int.from_bytes(len_bytes, 'little')
        logger.info("capture_image: 图片大小 %d bytes", img_length)

        # 第三阶段: 读取图片数据
        image_data = self._read_exactly(img_length, deadline)
        logger.info("capture_image: 实际读取 %d / %d bytes", len(image_data), img_length)

        # 验证 JPEG 数据有效性
        if len(image_data) < 10 or image_data[:2] != b'\xff\xd8':
            if len(image_data) < img_length:
                logger.warning("capture_image: 数据不完整且无效, 需要 %d bytes, 收到 %d bytes", img_length, len(image_data))
            else:
                logger.warning("JPEG 数据校验失败: size=%d, head=%s", len(image_data), image_data[:4].hex())
            return None

        # TCP 传输理论上不应丢数据，但仍容忍少量缺失
        if len(image_data) < img_length:
            ratio = len(image_data) / img_length
            if ratio < 0.95:
                logger.warning("capture_image: 数据缺失过多, 需要 %d bytes, 收到 %d bytes (%.1f%%)", img_length, len(image_data), ratio * 100)
                return None
            logger.warning("capture_image: 数据略有缺失 %d bytes (%.1f%%), 继续使用", img_length - len(image_data), ratio * 100)

        # 截断到 FFD9 结束标记之后
        ffd9_pos = image_data.rfind(b'\xff\xd9')
        if ffd9_pos >= 0:
            image_data = image_data[:ffd9_pos + 2]

        logger.info("capture_image: 成功获取图片 %d bytes", len(image_data))
        return image_data
