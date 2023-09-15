from bs4 import BeautifulSoup


class Infomation(BeautifulSoup):
    def __init__(self, name: str, html_context: str):
        super().__init__(html_context, "html5lib")
        self.name = name

    @classmethod
    def read_local(cls, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            context = f.read()
            s = path.rfind("/")
            e = path.rfind(".")
            name = path[s + 1: e]
            return cls(name,  context)

    def change_images(self, prefix: str):
        for i, img in enumerate(self.find_all("img")):
            print(type(img.attrs["style"]), img.attrs["style"])
            extend = str(img.attrs["src"])
            extend = extend[extend.rfind("."):]
            img.attrs["src"] = "{}{}-{}{}".format(prefix, self.name, i, extend)

    def show_images(self):
        for img in self.find_all("img"):
            print(img.attrs)


if __name__ == '__main__':
    a = Infomation.read_local("format_html/Abducens_nerve.html")
    a.change_images("../infomation/")
    a.show_images()
