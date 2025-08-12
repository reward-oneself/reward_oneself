import json
import os


class FileHandler:
    def __init__(self, file_name):
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.file_name = file_name

    def path(self):
        return f"{self.dir}/{self.file_name}"

    def check(self):
        dir = self.path().split("/")[-2]
        if not os.path.exists(dir):
            os.makedirs(self.dir + "/" + dir)
        if not os.path.exists(self.path()):
            return False
        else:
            return True

    def overwrite(self, content):
        with open(self.path(), encoding="utf-8", mode="w") as d:
            d.write(content)

    def read(self):

        if self.check():
            with open(self.path(), encoding="utf-8") as d:
                return d.read()
        else:
            raise FileNotFoundError(f"文件 {self.path()} 不存在")

    def load(self):
        if self.check():
            with open(self.path(), encoding="utf-8") as d:
                return json.load(d)
        else:
            raise FileNotFoundError(f"文件 {self.path()} 不存在")

    def write_as_json(self, data):
        with open(self.path(), encoding="utf-8", mode="w") as d:
            json.dump(data, d, ensure_ascii=False, indent=4)

    def delete(self):
        if self.check():
            os.remove(self.path())
            return f"删除 {self.path} 成功"
        else:
            raise FileNotFoundError(f"文件 {self.path()} 不存在")
