# 该程序由通义灵码生成，用于获取一言（hitokoto）的数据

import json
import sys

import requests
import random

with open("hitokoto.txt", "r", encoding="utf-8") as f:
    hitokoto_text = f.read()
    hitokoto_text = hitokoto_text.split("\n")

def get_hitokoto_by_file():
    return random.choice(hitokoto_text)

def get_hitokoto(HITOKOTO_URL=None,love="",LOCAL_MODE=False):
    if LOCAL_MODE:
        return get_hitokoto_by_file()
    
    url = HITOKOTO_URL + love
    response = requests.get(url)
    if response.status_code == 200:
        json_text = response.text
        text = json.loads(json_text)
        hitokoto_text = text["hitokoto"]
        author = text["from"]
        return f"{hitokoto_text}——{author}"

    else:
        return get_hitokoto_by_file()


if __name__ == "__main__":
    # 调用函数并打印结果
    hitokoto_text = get_hitokoto(LOCAL_MODE=True)
    print(hitokoto_text)
    hitokoto_text = get_hitokoto(HITOKOTO_URL="https://v1.hitokoto.cn/")
    print(hitokoto_text)