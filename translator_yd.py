import json
import time
import uuid
import requests
import hashlib
from mi_exception import TranslateError
from model import TransFile


class TranslateYd:
    YOUDAO_URL = "https://openapi.youdao.com/translate_html"
    APP_KEY = "0c2ae4dbbb4f5169"
    APP_SECRET = "GRMET5t4HcEQbN6aoX3D4MY6IoWnSxIL"

    def __init__(self):
        self.current_file = TransFile()

    @staticmethod
    def encrypt(sign_str):
        hash_algorithm = hashlib.sha256()
        hash_algorithm.update(sign_str.encode('utf-8'))
        return hash_algorithm.hexdigest()

    @staticmethod
    def truncate(q):
        if q is None:
            return None
        size = len(q)
        return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

    @classmethod
    def do_request(cls, data):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        return requests.post(cls.YOUDAO_URL, data=data, headers=headers)

    def connect(self):
        """
        q = "待输入的文字"
        """
        with open(self.current_file.path, 'r', encoding='UTF-8') as f:
            q = f.read()

        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        sign = self.encrypt(self.APP_KEY + self.truncate(q) + salt + curtime + self.APP_SECRET)
        data = {
            "from": "en",
            "to": "zh-CHS",
            "signType": "v3",
            "curtime": curtime,
            "appKey": self.APP_KEY,
            "salt": salt,
            "sign": sign,
            "q": q
        }
        response = self.do_request(data)
        content_type = response.headers['Content-Type']
        if content_type == "audio/mp3":
            millis = int(round(time.time() * 1000))
            with open(self.current_file.path_save_as_other(str(millis), "mp3"), 'wb') as fo:
                fo.write(response.content)
        else:
            result = json.loads(response.content)
            if result["errorMessage"] == "success" and result["errorCode"] == "0":
                with open(self.current_file.path_save_as('zh'), 'w', encoding='UTF-8') as f:
                    f.write(result["data"]["translation"])
            else:
                raise TranslateError(
                    "{}: {}".format(result["errorMessage"], result["errorCode"])
                )
