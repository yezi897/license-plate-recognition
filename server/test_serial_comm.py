import pytest
from unittest.mock import MagicMock, patch
from serial_comm import SerialComm


class TestSerialComm:
    def test_init_with_valid_config(self):
        """测试用有效配置初始化"""
        comm = SerialComm("COM3", 921600)
        assert comm.port == "COM3"
        assert comm.baud_rate == 921600

    def test_init_default_baud_rate(self):
        """测试默认波特率"""
        comm = SerialComm("COM3")
        assert comm.baud_rate == 921600

    @patch('serial_comm.serial.Serial')
    def test_connect(self, mock_serial):
        """测试连接串口"""
        comm = SerialComm("COM3", 921600)
        comm.connect()
        mock_serial.assert_called_once_with("COM3", 921600, timeout=2)

    @patch('serial_comm.serial.Serial')
    def test_capture_image_returns_bytes(self, mock_serial):
        """测试拍照返回图片字节数据"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn

        # 模拟串口返回：IMG_START + 长度(4字节) + 数据 + IMG_END
        test_data = b'\x89PNG_test'
        img_start = b'IMG_START'
        img_end = b'IMG_END'
        length_bytes = len(test_data).to_bytes(4, 'little')

        mock_conn.read.side_effect = [
            img_start,
            length_bytes,
            test_data,
            img_end
        ]
        mock_conn.in_waiting = True

        comm = SerialComm("COM3")
        comm.connect()
        result = comm.capture_image()

        assert result is not None
        assert isinstance(result, bytes)
        assert result == test_data

    @patch('serial_comm.serial.Serial')
    def test_capture_image_returns_none_on_fail(self, mock_serial):
        """测试拍照失败返回 None"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn
        mock_conn.read.return_value = b'CAPTURE_FAIL'

        comm = SerialComm("COM3")
        comm.connect()
        result = comm.capture_image()

        assert result is None

    @patch('serial_comm.serial.Serial')
    def test_is_connected(self, mock_serial):
        """测试连接状态检查"""
        comm = SerialComm("COM3")
        assert comm.is_connected() is False

        comm.connect()
        assert comm.is_connected() is True

    @patch('serial_comm.serial.Serial')
    def test_disconnect(self, mock_serial):
        """测试断开连接"""
        mock_conn = MagicMock()
        mock_serial.return_value = mock_conn

        comm = SerialComm("COM3")
        comm.connect()
        comm.disconnect()

        mock_conn.close.assert_called_once()
        assert comm.is_connected() is False
