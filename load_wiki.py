import os.path
import time
import requests
import bs4 as bs
from model import WikiUrlPrefix
from mi_exception import GetLinkFailed


class WikiDocument(bs.BeautifulSoup):
    def __init__(self, html_document: str, title: str):
        super().__init__(html_document, "html5lib")
        self.title = title

    @classmethod
    def load_from(cls, link: str):
        pass


class ImgsDownloader:
    def __init__(self, file_prefix: str, soup: bs.BeautifulSoup):
        self.file_prefix = file_prefix
        self.soup = soup
        self.failed_urls = []

    def imgs_download(self):
        results = self.soup.find_all("img", {"class": "mw-file-element"})
        for num, element in enumerate(results, start=1):
            if int(element.attrs["width"]) < 100 and int(element.attrs["height"]) < 100:
                continue
            url = "https:{}".format(element.attrs["src"])
            data = requests.get(url, headers={"Referer": WikiUrlPrefix})
            if data.status_code == 200:
                try:
                    extend = url[url.rindex("."):].lower()
                    assert len(extend) < 10
                except (ValueError, AssertionError):
                    extend = ".jpg"
                with open("infomation/{}-{}{}".format(self.file_prefix, num, extend), 'wb') as f:
                    for chunk in data.iter_content():
                        f.write(chunk)
            else:
                self.failed_urls.append([url, "img", f"{self.file_prefix}-{num}"])
            time.sleep(0.1)


class WikiDownloader:
    def __init__(self, link: str):
        self.title = link[link.rfind("/") + 1:]
        self.cookie = None
        self.soup = BeautifulSoup()
        if os.path.exists(self.download_fpath):
            if os.path.exists(self.translated_fpath):
                self.state = 2
            else:
                self.state = 1
        else:
            self.state = 0

    @classmethod
    def getting(cls, link: str):
        obj = cls(link)
        if obj.state == 0:
            with open("project/wiki_cookie.txt", 'r', encoding="UTF-8") as f:
                cookie = f.read()
            html = requests.get(link, headers={"Cookie": cookie})
            if html.status_code == 200:
                obj.soup = BeautifulSoup(html.text, "html5lib")
            else:
                raise GetLinkFailed(link, "html", obj.title)

    @property
    def download_fpath(self):
        return "infomation/{}.html".format(self.title)

    @property
    def translated_fpath(self):
        return "infomation/{}_zh.html".format(self.title)

    def text_anlysis(self):
        main_tag = self.soup.find("main")
        title = main_tag.find("header").find("h1")
        title = self.delete_tags(title)
        title = self.delete_attrs(title)

        content = main_tag.find("div", {"id": "bodyContent"}).find("div", {"class": "mw-parser-output"})
        content = self.delete_tags(content)

        with open(self.download_fpath, 'w+', encoding="UTF-8") as f:
            f.write("<html><head><title>{}</title></head><body>".format(title.get_text()))
            f.write(title.prettify(formatter="html"))
            for tag in filter(lambda x: isinstance(x, Tag), content.children):
                if self.exit_node(tag):
                    break
                if self.skip_node(tag):
                    continue
                tag = self.delete_attrs(tag)
                f.write(tag.prettify(formatter="html"))
            f.write("</body></html>")

    @staticmethod
    def exit_node(ctag: Tag):
        flag = False
        if ctag.name == "h2" and ctag.find(attrs={"id": "Notes"}) is not None:
            flag = True
        if ctag.name == "h2" and ctag.find(attrs={"id": "References"}) is not None:
            flag = True
        elif ctag.name == "div" and "class" in ctag.attrs and ctag.attrs["class"] == "navbox-styles":
            flag = True
        return flag

    @staticmethod
    def skip_node(ctag: Tag):
        flag = False
        if ctag.name == "style":
            flag = True
        return flag

    @staticmethod
    def delete_tags(ctag: Tag):
        for param in [{"name": "span", "attrs": {"class": "mw-editsection"}},
                      {"name": "sup", "attrs": {"class": "reference"}},
                      {"name": "table", "attrs": {"class": "infobox"}}]:
            for _t in ctag.find_all(**param):
                _t.extract()
        return ctag

    @staticmethod
    def delete_attrs(ctag: Tag):
        for _t in filter(lambda x: isinstance(x, Tag), ctag.descendants):
            if _t.name == "img":
                continue
            else:
                _t.attrs.clear()
        return ctag
