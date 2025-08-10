import json
import sys

try:
    with open("settings.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        DATA = settings["data"]
        KEY = settings["key"]
        DEVELOPMENT = settings["development"]
        LOCAL_MODE = settings["local_mode"]
        HITOKOTO_URL = settings["hitokoto_url"]
        if LOCAL_MODE == "True":
            LOCAL_MODE = True
        else:
            LOCAL_MODE = False
except FileNotFoundError:
    with open("settings.json", "w", encoding="utf-8") as f:
        settings = {
            "data": "sqlite:///data.db",
            "key": "key",
            "development": "True",
            "hitokoto_url": "https://v1.hitokoto.cn/",
            "local_mode": "False",
        }
        json.dump(settings, f, ensure_ascii=False, indent=4)
        print("settings.json 文件已创建，请重启程序。")
        sys.exit()
except KeyError as e:
    print(f"配置文件中缺少键，错误信息：{e}")
    sys.exit()
