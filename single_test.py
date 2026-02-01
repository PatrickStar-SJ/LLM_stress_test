# 模型性能压测
import argparse
import shutil
import requests
import json
import time
import os
import threading
import random

import queue
# 创建一个队列，用于存储压测结果
shared_queue = queue.Queue()


# 保存测试结果
class ResponseResult():
    id: str
    status: str
    question: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    rep_time_lst: list
    first_time: float
    total_time: float
    inner_time: float
    token_speed: float


def get_response(id: str, prompt_item: dict, model_config: dict):
    rep_res = ResponseResult()
    url = model_config["url"]
    headers = {"Content-Type": "application/json"}
    if model_config.__contains__('appcode'):
        headers["Authorization"] = "Bearer " + model_config["appcode"]
    body = {
        "messages": [{"role": "user","content": prompt_item['prompt']}],
        "stream":True, 
        "max_tokens": 512
    }
    for para in model_config['parameters']:
        body[para] = model_config['parameters'][para]
    rep_time_lst = []
    rep_lst = []
    
    # send request
    start_time = time.monotonic()
    rep_time_lst.append(start_time)
    with requests.post(url=url, headers=headers, json=body, stream=True) as response:
        for chunk in response.iter_lines(chunk_size=None):
            chunk = chunk.strip()
            if not chunk:
                continue
            cur_time = time.monotonic()
            print(cur_time, chunk.decode('utf-8')[5:])
            rep_time_lst.append(cur_time)
            rep_lst.append(chunk.decode('utf-8')[5:])
    
    # parse response
    text = ''
    for i,chunk in enumerate(rep_lst):
        if chunk == "":
            continue
        data = json.loads(chunk)
        print(data)
        text += data["choices"][0]["delta"]["content"]
        if data["choices"][0]["finish_reason"] != None:
            rep_res.response = text
            if 'usage' in data:
                rep_res.prompt_tokens = data["usage"]["prompt_tokens"]
                rep_res.completion_tokens = data["usage"]["completion_tokens"]
                rep_res.total_tokens = data["usage"]["total_tokens"]
            else:
                rep_res.prompt_tokens = prompt_item['token']
                rep_res.completion_tokens = len(rep_time_lst)
                rep_res.total_tokens = rep_res.prompt_tokens + rep_res.completion_tokens
            break
    
    # 生成测试结果
    rep_res.id = id
    rep_res.question = prompt_item['prompt']
    rep_res.rep_time_lst = rep_time_lst
    rep_res.status = "success"

    return rep_res


model_config = {
        'model_name': 'jiutian',
        'url': 'https://cisp.travelsky.com.cn/kunlun/ingress/api-safe/c10ca6/5e983be0668947c68f717ce93a637041/ai-9adeaa5daa024163b88c9004a14d950c/service-77e07a0f31df4994a257e86c8102313d/v1/chat/completions',
        'appcode': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI3YzVkMjkyNWE3MTM0YjJmYjVlZjRmMjQ1YjNkNWIzMSIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkyMzMzNDI1OH0.FpHquXg6asf0uH7ntNpihLqk4rDNSD50zQKHno5B0MA2YtO-geuvwJFCN0Q3bzO6qbctGCNjwjJVw2aaxUtqENRBPTyCd9d95_tswuj9FllckhUlSlFCAxCuwg_n4Srb9inHpGPhQm6y6VaHPAg18ntObc1snsC0AfPAdlTzpMim-g2Vc4yrGGcKeh07VcDqByoq5bS-Vw3Ja2d42Fd6G-vN3pwHCm04tY995DNKEDly7gKWVJNnLrnw6qsiA_FRQWV0zgRV_CVPaT11cvgyR1uqa0vJ1YB378JwNQFD4BpRsdXwpNRFYKnDn4b7533RMxczSZLs0GxXgqw3pyy9_Q',
        'parameters': {
            'model': 'qwen3',
            'max_tokens': 10,
            'stream': True,
        }
    }

prompt = '''邻区有关部门准备到锦林区学习考察，了解“智慧锦林”综合平台在社区治理方面的特点和运行情况。如果你是锦林区负责接待的工作人员，请根据以下材料，写一份情况介绍提纲。    

相关材料：
通过“智慧锦林”综合平台，锦林区打造了部门联动、街道配合、群众参与的机制，实现了以指挥中心为圆心、以网格责任体系为基础、以全方位快速响应队伍为力量的社会治理共建、共治、共享新格局。专门的APP里面，设置有水、电、气、物业等多种生活缴费功能，并提供养老金、老年证、低保申请等常用便民服务咨询与网上办理服务。在“锦林群众”栏，设有“你是我的眼”平台，提供违法、违规及扰民行为的举报渠道及奖励方式；而在“政民互动”栏，则有市民关于入学、物业、环境卫生等各方面的诉求，以及相关单位的具体答复和联系人等内容 。指挥中心王助理介绍，在平台上，大到环境整治、食品安全、治安防控、物业纠纷，小到车辆违停、占道经营等各类杂事烦事，群众都可以上来反映，通过APP实现信息源头全覆盖。 网格员童大姐每天都会巡察自己负责的网格，并上报各种情况。通常情况下，这些事由网格员自己发现并处理。

提纲：
'''
prompt_item = {
    'prompt': prompt,
    'token': 256
}

response = get_response('0-0', prompt_item, model_config)
print("回复内容", response.response)

start = response.rep_time_lst.pop(0)
response.rep_time_lst = [x-start for x in response.rep_time_lst]
print("首字响应时间： ", response.rep_time_lst[0])
print("总回复时间： ", response.rep_time_lst[-1])
print(response.rep_time_lst)

differences = [response.rep_time_lst[i+1] - response.rep_time_lst[i] for i in range(len(response.rep_time_lst)-1)]
response.inner_time = sum(differences) / len(differences)
print("token间时延： ", response.inner_time)

response.total_time = response.rep_time_lst[-1]
response.token_speed = response.completion_tokens / response.total_time
print("每秒输出token数： ", response.token_speed )