import sqlite3
from datetime import datetime
from collections.abc import Iterable


WikiUrlPrefix = "https://en.wikipedia.org/"


class MedicalImage:
    def __init__(self):
        self._db = sqlite3.connect("database/medicalimages.db")
        self.date_tamp = datetime.today().strftime("%Y-%m-%d")

    def generate_infomations(self):
        cur = self._db.cursor()
        cur.execute(
            "SELECT DISTINCT infomation FROM mi_legends WHERE infomation LIKE ?",
            (f"%{WikiUrlPrefix}%",)
        )
        for info_url, in cur.fetchall():
            yield info_url
        cur.close()

    def saving_failed_link(self, link: str, kind: str, name: str):
        cur = self._db.cursor()
        cur.execute(
            "INSERT INTO failed_links (link,kind,name,date_temp) VALUES (?,?,?,?)",
            (link, kind, name, self.date_tamp)
        )
        self._db.commit()
        cur.close()

    def saving_failed_links(self, _iterable: Iterable[str, str, str]):
        """
        link, kind, name
        """
        cur = self._db.cursor()
        cur.executemany(
            "INSERT INTO failed_links (link,kind,name,date_temp) VALUES (?,?,?,?)",
            ((*_item, self.date_tamp) for _item in _iterable)
        )
        self._db.commit()
        cur.close()

    def check_in_failed_link(self, **kwargs) -> int:
        cur = self._db.cursor()
        if len(kwargs):
            cur.execute("PRAGMA table_info(failed_links)")
            fields = [x[1] for x in cur.fetchall()]
            if any(kw not in fields for kw in kwargs):
                raise ValueError
            sql = " WHERE {}".format(" AND ".join(f"{kw}=:{kw}" for kw in kwargs))
        else:
            sql = ""
        cur.execute("SELECT COUNT(*) FROM failed_links" + sql, kwargs)
        return cur.fetchone()[0]

    def close(self):
        self._db.close()


class TransFile:
    def __init__(self):
        self._path_prefix = ''
        self._name = ''
        self._extend = ''

    @classmethod
    def create(cls, file_path: str):
        tf = cls()
        name_idx = max(file_path.rfind("/"), file_path.rfind("\\")) + 1
        extend_idx = file_path.rfind(".")
        tf._path_prefix = file_path[:name_idx]
        tf._name = file_path[name_idx:extend_idx]
        tf._extend = file_path[extend_idx + 1:]
        return tf

    @property
    def extend(self) -> str:
        return self._extend

    @property
    def fname(self) -> str:
        return "{}.{}".format(self._name, self._extend)

    @property
    def path(self) -> str:
        return "{}{}.{}".format(self._path_prefix, self._name, self._extend)

    def path_save_as(self, symbol: str):
        return "{}{}_{}.{}".format(self._path_prefix, self._name, symbol, self._extend)

    def path_save_as_other(self, symbol: str, extend: str):
        return "{}{}_{}.{}".format(self._path_prefix, self._name, symbol, extend)


if __name__ == '__main__':
    pass
