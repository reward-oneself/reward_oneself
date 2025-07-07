# 该程序由通义灵码生成，用于获取一言（hitokoto）的数据

import requests
import os
import json
def get_hitokoto(love=""):
    url = os.environ.get('URL', 'https://v1.hitokoto.cn/')
    url = url + love
    response = requests.get(url)
    if response.status_code == 200:
        json_text = response.text
        text = json.loads(json_text)
        hitokoto_text = text["hitokoto"]
        author = text["from"]
        return f"{hitokoto_text}——{author}"
        
    else:
        return f"获取失败，错误码为{response.status_code}"

if __name__ == "__main__":
    # 调用函数并打印结果
    hitokoto_text = get_hitokoto()
    print(hitokoto_text)