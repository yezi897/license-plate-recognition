from aip import AipOcr


class PlateRecognizer:
    def __init__(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        self.client = None
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)

    def is_configured(self):
        return bool(self.app_id and self.api_key and self.secret_key)

    def update_credentials(self, app_id, api_key, secret_key):
        self.app_id = app_id
        self.api_key = api_key
        self.secret_key = secret_key
        if self.is_configured():
            self.client = AipOcr(app_id, api_key, secret_key)
        else:
            self.client = None

    def recognize(self, image_data):
        if not self.is_configured() or not self.client:
            return None

        result = self.client.licensePlate(image_data)

        if 'words_result' not in result or not result['words_result']:
            return None

        plate_info = result['words_result'][0]
        probabilities = plate_info.get('probability', [0])

        return {
            'plate_number': plate_info['number'],
            'color': plate_info['color'],
            'confidence': round(sum(probabilities) / len(probabilities) * 100, 2)
        }
