import pytest
from unittest.mock import MagicMock, patch
from plate_recognizer import PlateRecognizer


class TestPlateRecognizer:
    def test_init_with_credentials(self):
        """测试用凭证初始化"""
        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        assert recognizer.app_id == "app_id"
        assert recognizer.api_key == "api_key"
        assert recognizer.secret_key == "secret_key"

    def test_init_with_empty_credentials(self):
        """测试空凭证初始化"""
        recognizer = PlateRecognizer("", "", "")
        assert recognizer.is_configured() is False

    def test_is_configured_true(self):
        """测试已配置状态"""
        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        assert recognizer.is_configured() is True

    @patch('plate_recognizer.AipOcr')
    def test_recognize_plate_success(self, mock_ocr_class):
        """测试成功识别车牌"""
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr

        mock_ocr.licensePlate.return_value = {
            'words_result': [{
                'number': '京A12345',
                'color': '蓝色',
                'probability': [0.98, 0.97, 0.96]
            }]
        }

        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        result = recognizer.recognize(b'fake_image_data')

        assert result is not None
        assert result['plate_number'] == '京A12345'
        assert result['color'] == '蓝色'
        assert result['confidence'] > 0

    @patch('plate_recognizer.AipOcr')
    def test_recognize_plate_no_result(self, mock_ocr_class):
        """测试未识别到车牌"""
        mock_ocr = MagicMock()
        mock_ocr_class.return_value = mock_ocr
        mock_ocr.licensePlate.return_value = {'words_result': []}

        recognizer = PlateRecognizer("app_id", "api_key", "secret_key")
        result = recognizer.recognize(b'fake_image_data')

        assert result is None

    def test_recognize_not_configured(self):
        """测试未配置时识别"""
        recognizer = PlateRecognizer("", "", "")
        result = recognizer.recognize(b'fake_image_data')
        assert result is None
