import serial
import time


class SerialComm:
    def __init__(self, port, baud_rate=921600):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None

    def connect(self):
        self.serial_conn = serial.Serial(
            self.port, self.baud_rate, timeout=2
        )
        time.sleep(0.5)

    def is_connected(self):
        return self.serial_conn is not None and self.serial_conn.is_open

    def disconnect(self):
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None

    def capture_image(self):
        if not self.is_connected():
            return None

        self.serial_conn.reset_input_buffer()
        self.serial_conn.write(b'C')

        # 等待 IMG_START 标记
        header = self._read_until(b'IMG_START')
        if header is None:
            return None

        # 读取图片长度（4字节）
        length_bytes = self.serial_conn.read(4)
        if len(length_bytes) < 4:
            return None
        img_length = int.from_bytes(length_bytes, 'little')

        # 读取图片数据
        img_data = b''
        remaining = img_length
        while remaining > 0:
            chunk = self.serial_conn.read(min(remaining, 1024))
            if not chunk:
                break
            img_data += chunk
            remaining -= len(chunk)

        # 读取 IMG_END 标记
        self._read_until(b'IMG_END')

        if len(img_data) == img_length:
            return img_data
        return None

    def _read_until(self, marker, timeout=5):
        start = time.time()
        buffer = b''
        while time.time() - start < timeout:
            if self.serial_conn.in_waiting:
                buffer += self.serial_conn.read(self.serial_conn.in_waiting)
                if marker in buffer:
                    return marker
            time.sleep(0.01)
        return None
