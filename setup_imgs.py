import os
import time
import shutil
import sqlite3
import requests
from bs4 import BeautifulSoup


class Infomation(BeautifulSoup):
    absolute_path = "http://obs.xlhcq.com/wankang/ct_infomations/"
    headers = {
        "Dnt": "1",
        "Referer": "https://en.wikipedia.org/",
        "Sec-Ch-Ua": '"Google Chrome";v="117","Not;A=Brand";v ="8","Chromium";v ="117"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Windows",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0;Win64; x64) AppleWebKit/"
            "537.36(KHTML, likeGecko) Chrome/117.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, name: str, html_context: str):
        super().__init__(html_context, "html5lib")
        self.name = name
        if not os.path.exists(file := "D:/medicalimages/{}".format(name)):
            os.mkdir(file)
        self.filepath = file + "/"

    def save_images(self):
        for i, img in enumerate(self.find_all("img")):
            if not self.image_right_size(img.attrs):
                continue
            extend = str(img.attrs["src"])
            extend = extend[extend.rfind("."):]
            if len(extend) > 5:
                extend = ".jpg"
            oldfilename = "{}-{}{}".format(self.name, i, extend)
            newfilename = "{}_{}".format(self.name, i) + extend

            if not os.path.exists(self.filepath + newfilename):
                if os.path.exists(oldpath := "infomation/{}".format(oldfilename)):
                    print("{} transfered".format(newfilename))
                    shutil.copy(oldpath, self.filepath + newfilename)
                else:
                    url = str(img.attrs["src"])
                    if not url.startswith("http"):
                        url = "https:{}".format(url)
                    try:
                        data = requests.get(url, headers=self.headers)
                        print("{} downloaded".format(newfilename), data.status_code)
                        if data.status_code < 400:
                            with open(self.filepath + newfilename, 'wb') as f:
                                for chunk in data.iter_content():
                                    f.write(chunk)
                    except requests.RequestException as e:
                        print("Image download failed:", e)
                    finally:
                        time.sleep(1)

            img.attrs["src"] = "{}{}/{}".format(self.absolute_path, self.name, newfilename)

    def save_html(self):
        if not os.path.exists(newpath := self.filepath + self.name + ".html"):
            with open(newpath, 'w', encoding='UTF-8') as f:
                f.write(self.prettify(formatter='html'))

    def change_legends(self):
        with sqlite3.connect("database/medicalimages.db") as db:
            cur = db.cursor()
            cur.execute(
                "SELECT value, infomation FROM mi_legends WHERE infomation LIKE ? AND infomation NOT LIKE ?",
                (f"%{self.name}%", f"{self.absolute_path}%")
            )
            for value, origin_link in cur.fetchall():
                cur.execute(
                    "INSERT INTO mi_legend_infomation_history (legend_value, origin_link) VALUES (?,?)",
                    (value, origin_link)
                )
                cur.execute(
                    "UPDATE mi_legends SET infomation=? WHERE value=?",
                    ("{}{}/{}.html".format(self.absolute_path, self.name, self.name), value)
                )
                db.commit()

    @classmethod
    def read_local(cls, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            context = f.read()
            s = path.rfind("/")
            e = path.rfind(".")
            name = path[s + 1: e]
            return cls(name, context)

    @staticmethod
    def image_right_size(attrs: dict):
        if "width" in attrs and "height" in attrs:
            return int(attrs["width"]) > 100 or int(attrs["height"]) > 100
        elif "style" in attrs:
            w = h = 0
            for css in attrs['style'].split(';'):
                css = css.strip()
                try:
                    if css.startswith("height"):
                        w = int(css[css.index(":") + 1:css.index("px")])
                    elif css.startswith("width"):
                        h = int(css[css.index(":") + 1:css.index("px")])
                except ValueError:
                    w = h = 101
            return w > 100 or h > 100


def reduction():
    with sqlite3.connect("database/medicalimages.db") as db:
        cur = db.cursor()
        cur.execute("SELECT value FROM mi_legends WHERE infomation IS NULL OR infomation=''")
        for value, in cur.fetchall():
            cur.execute("SELECT origin_link FROM mi_legend_infomation_history WHERE legend_value=?", (value,))
            res = cur.fetchone()
            if res is not None:
                cur.execute("UPDATE mi_legends SET infomation=? WHERE value=?", (res[0], value))
                db.commit()


if __name__ == '__main__':
    for fn in os.listdir("format_html/"):
        a = Infomation.read_local("format_html/{}".format(fn))
        a.save_images()
        a.save_html()
        a.change_legends()
