import os
import logging
from aip import AipOcr

# 绕过系统代理以连接百度 API
os.environ.setdefault('NO_PROXY', 'aip.baidubce.com')

logger = logging.getLogger(__name__)


class PlateRecognizer:
    def __init__(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.client = None
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)
            self.client._proxies = {}

    def is_configured(self):
        return bool(self.app_id and self.api_key and self.secret_key)

    def update_credentials(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)
            self.client._proxies = {}
        else:
            self.client = None

    def recognize(self, image_data):
        if not self.is_configured() or not self.client:
            logger.warning("百度 API 未配置")
            return None

        result = self.client.licensePlate(image_data)

        # 检查 API 错误
        if 'error_code' in result:
            logger.error("百度 API 错误: code=%s, msg=%s", result.get('error_code'), result.get('error_msg'))
            return None

        if 'words_result' not in result or not result['words_result']:
            return None

        # licensePlate API 返回 words_result 为字典，其他 OCR 接口返回列表
        words_result = result['words_result']
        plate_info = words_result if isinstance(words_result, dict) else words_result[0]
        probability = plate_info.get('probability', [0])

        # probability 可能是列表或单个数值
        if isinstance(probability, list):
            confidence = round(sum(probability) / len(probability) * 100, 2) if probability else 0
        else:
            confidence = round(float(probability) * 100, 2)

        return {
            'plate_number': plate_info['number'],
            'color': plate_info['color'],
            'confidence': confidence
        }
