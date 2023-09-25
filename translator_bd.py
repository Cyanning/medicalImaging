import json
import time
import hmac
import base64
import hashlib
import requests
from translate_model import TransFile


class TransFileBd(TransFile):
    def __init__(self):
        super().__init__()
        self.request_id = 0
        self.file_id = 0


class TranslateBd:
    appid = "20221009001379715"
    seckey = "dMZ4LZfLU9zyVDN9EatA"

    def __init__(self):
        self.current_file = TransFileBd()

    def _create_quote_job(self):
        url = 'https://fanyi-api.baidu.com/transapi/doctrans/createjob/quote'
        with open(self.current_file.path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        input_data = {
            'from': 'en',
            'to': 'zh',
            'input': {
                'content': content,
                'format': self.current_file.extend,
                'filename': self.current_file.fname
            }
        }
        timestamp = int(time.time())
        sign = self._create_sign(timestamp, input_data)
        headers = self._create_headers(timestamp, sign)
        response = requests.post(url, headers=headers, json=input_data)
        return response.text

    def _query_quote(self):
        url = 'https://fanyi-api.baidu.com/transapi/doctrans/query/quote'
        input_data = {'fileId': self.current_file.file_id}
        timestamp = int(time.time())
        sign = self._create_sign(timestamp, input_data)
        headers = self._create_headers(timestamp, sign)
        response = requests.post(url, headers=headers, json=input_data)
        return response.text

    def _create_trans_job(self):
        url = 'https://fanyi-api.baidu.com/transapi/doctrans/createjob/trans'
        with open(self.current_file.path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        input_data = {
            'from': 'en',
            'to': 'zh',
            'input': {
                'content': content,
                'format': self.current_file.extend,
                'filename': self.current_file.fname
            },
            'output': {
                'format': self.current_file.extend
            }
        }
        timestamp = int(time.time())
        sign = self._create_sign(timestamp, input_data)
        headers = self._create_headers(timestamp, sign)
        response = requests.post(url, headers=headers, json=input_data)
        return response.text

    def _query_trans(self):
        url = 'https://fanyi-api.baidu.com/transapi/doctrans/query/trans'
        input_data = {'requestId': self.current_file.request_id}
        timestamp = int(time.time())
        sign = self._create_sign(timestamp, input_data)
        headers = self._create_headers(timestamp, sign)
        response = requests.post(url, headers=headers, json=input_data)
        return response.text

    def _create_sign(self, timestamp, input_data):
        query_str = json.dumps(input_data)
        sign_str = '{}{}{}'.format(self.appid, timestamp, query_str)
        sign = base64.b64encode(
            hmac.new(
                self.seckey.encode('utf-8'), sign_str.encode('utf-8'), digestmod=hashlib.sha256
            ).digest()
        )
        return sign

    def _create_headers(self, timestamp, sign):
        return {
            'Content-Type': 'application/json',
            'X-Appid': self.appid,
            'X-Sign': sign,
            'X-Timestamp': str(timestamp),
        }

    def create_trans_handle(self):
        result = self._create_trans_job()
        result = json.loads(result)
        if result["code"] == 0 and result["msg"] == "success":
            self.current_file.request_id = result["data"]["requestId"]
        else:
            raise Exception(result["msg"])

    def query_trans_handle(self) -> bool:
        result = self._query_trans()
        result = json.loads(result)
        if result["code"] == 0 and result["msg"] == "success":
            if result["data"]["status"] == 1:
                if result["data"]["name"].lower() != self.current_file.fname.lower():
                    raise Exception("The requested file does not match the current file.")
                result_file = requests.get(result["data"]["fileSrcUrl"])
                with open(self.current_file.path_save_as(result["data"]["to"]), 'wb') as f:
                    f.write(result_file.content)
                return True
            elif result["data"]["status"] == 2:
                raise Exception(result["data"]["reason"])
            else:
                return False
        else:
            raise Exception(result["msg"])
