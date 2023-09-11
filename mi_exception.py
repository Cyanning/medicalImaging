class TranslateError(Exception):
    def __init__(self, msg: str):
        self._msg = msg

    def __repr__(self):
        return "Translate error: {}".format(self._msg)

    def __str__(self):
        return self._msg


class GetLinkFailed(Exception):
    def __init__(self, link: str, kind: str, name: str):
        self.link = link
        self.kind = kind
        self.name = name

    def __repr__(self):
        return "{} link({}): {} get failed.".format(self.name, self.kind, self.link)
