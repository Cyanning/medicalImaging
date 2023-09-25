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
