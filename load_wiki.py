import os
import time
import requests
import sqlite3
import bs4 as bs
from settings import *


class WikiDocument(bs.BeautifulSoup):
    def __init__(self, html_document: str, title: str, state=0):
        super().__init__(html_document, "html5lib")
        self.title = title
        self.state = state
        if not os.path.exists(file := "D:/medical_images/ct_infomations/{}".format(title)):
            os.mkdir(file)
        self.filepath = file + "/"  # 本地真实路径

    def origin_text_downloading(self):
        main_tag = self.soup.find("main")
        title = main_tag.find("header").find("h1")
        title = self._delete_tags(title)
        title = self.delete_attrs(title)

        content = main_tag.find("div", {"id": "bodyContent"}).find("div", {"class": "mw-parser-output"})
        content = self._delete_tags(content)

        with open(f"{ORIGIN_FILE_PATH}{self.title}.html", 'w+', encoding="UTF-8") as f:
            f.write("<html><head><title>{}</title></head><body>".format(title.get_text()))
            f.write(title.prettify(formatter="html"))
            for tag in filter(lambda x: isinstance(x, bs.Tag), content.children):
                if self._exit_node(tag):
                    break
                if self._skip_node(tag):
                    continue
                tag = self._delete_attrs(tag)
                f.write(tag.prettify(formatter="html"))
            f.write("</body></html>")

    def save_images(self):
        """
        保存图片
        """
        for i, img in enumerate(filter(self.image_right_size, self.find_all("img"))):
            url = str(img.attrs["src"])
            try:
                extend = url[url.rindex("."):]
                assert len(extend) < 5
            except (ValueError, AssertionError):
                extend = ".jpg"
            filename = "{}_{}{}".format(self.title, i, extend)

            if not os.path.exists(self.filepath + filename):
                if not url.startswith("http"):
                    url = "https:{}".format(url)
                try:
                    if 'wikipedia' in url:
                        data = requests.get(url, headers=WIKI_HEADERS)
                    else:
                        data = requests.get(url)
                    print("{} downloaded".format(filename), data.status_code)
                    if data.status_code < 400:
                        with open(self.filepath + filename, 'wb') as f:
                            for chunk in data.iter_content():
                                f.write(chunk)
                except requests.RequestException as e:
                    print("Image download failed:", e)
                finally:
                    time.sleep(1)

            img.attrs["src"] = "{}{}/{}".format(self.absolute_path, self.title, filename)

    def change_legends(self):
        """
        改变legends数据infomaton地址
        """
        with sqlite3.connect(DB_PATH) as db:
            cur = db.cursor()
            cur.execute(
                "SELECT value, infomation FROM mi_legends WHERE infomation LIKE ? AND infomation NOT LIKE ?",
                (f"%{self.title}%", f"{self.absolute_path}%")
            )
            for value, origin_link in cur.fetchall():
                cur.execute(
                    "INSERT INTO mi_legend_infomation_history (legend_value, origin_link) VALUES (?,?)",
                    (value, origin_link)
                )
                cur.execute(
                    "UPDATE mi_legends SET infomation=? WHERE value=?",
                    ("{}{}/{}.html".format(self.absolute_path, self.title, self.title), value)
                )
                db.commit()

    def save_html(self):
        """
        保存修改当富文本
        """
        if not os.path.exists(newpath := self.filepath + self.title + ".html"):
            with open(newpath, 'w', encoding='UTF-8') as f:
                f.write(self.prettify(formatter='html'))

    @classmethod
    def load_from_get(cls, link: str, name: str):
        html = requests.get(link, headers=WIKI_HEADERS)
        if html.status_code == 200:
            return cls(html.text, name, 1)
        else:
            raise requests.RequestException("Status_code: {}".format(html.status_code))

    @classmethod
    def load_from_local(cls, path: str, name: str, state: int):
        with open(path, 'w', encoding='utf-8') as f:
            context = f.read().strip()
            return cls(context, name, state)

    @staticmethod
    def _exit_node(ctag: bs.Tag):
        flag = False
        if ctag.name == "h2" and ctag.find(attrs={"id": "Notes"}) is not None:
            flag = True
        if ctag.name == "h2" and ctag.find(attrs={"id": "References"}) is not None:
            flag = True
        elif ctag.name == "div" and "class" in ctag.attrs and ctag.attrs["class"] == "navbox-styles":
            flag = True
        return flag

    @staticmethod
    def _skip_node(ctag: bs.Tag):
        flag = False
        if ctag.name == "style":
            flag = True
        return flag

    @staticmethod
    def _delete_tags(ctag: bs.Tag):
        for param in [{"name": "span", "attrs": {"class": "mw-editsection"}},
                      {"name": "sup", "attrs": {"class": "reference"}},
                      {"name": "table", "attrs": {"class": "infobox"}}]:
            for _t in ctag.find_all(**param):
                _t.extract()
        return ctag

    @staticmethod
    def _delete_attrs(ctag: bs.Tag):
        for _t in filter(lambda x: isinstance(x, bs.Tag), ctag.descendants):
            if _t.name == "img":
                continue
            else:
                _t.attrs.clear()
        return ctag

    @staticmethod
    def image_right_size(img: bs.Tag):
        """
        检测img标签合法性
        """
        if "width" in img.attrs and "height" in img.attrs:
            return int(img.attrs["width"]) > 100 or int(img.attrs["height"]) > 100
        elif "style" in img.attrs:
            w = h = 0
            for css in img.attrs['style'].split(';'):
                css = css.strip()
                try:
                    if css.startswith("height"):
                        w = int(css[css.index(":") + 1:css.index("px")])
                    elif css.startswith("width"):
                        h = int(css[css.index(":") + 1:css.index("px")])
                except ValueError:
                    w = h = 101
            return w > 100 or h > 100
