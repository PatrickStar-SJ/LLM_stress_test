# stress_test.py

import argparse
import importlib
import json
import multiprocessing
import os
import random
import statistics
import time
from typing import Dict, List, Any, Optional
import csv
import requests
import tqdm

import logging
import logging.handlers




def load_test_data(data_path):
    # 1. 从JSON文件读取测试数据
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        if not test_data.get('questions', ''):
            print(f"Error: No prompts found in {data_path}")
            return 
        return test_data
    except FileNotFoundError:
        print(f"Error: Data file not found at {data_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {data_path}")
        return


def load_all_configs():
    """
    动态加载同级目录下所有 config_*.py 文件中的 info_* 变量。
    """
    configs = {}
    # 1. 获取config目录下的所有文件
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    all_files = os.listdir('./configs')
    # 2. 筛选出目标文件
    for filename in all_files:
        # 检查文件名是否符合 'config_*.py' 模式，并且不是 test.py 自身
        if filename.endswith('.py'):
            # 3. 提取模块名和变量名
            model_name = filename[:-3]
            module_name = "configs." + model_name
            try:
                # 4. 动态导入模块
                module = importlib.import_module(module_name)
                # 5. 从模块中获取变量，使用 getattr 更安全，如果变量不存在会报 AttributeError
                config_value = getattr(module, "info_model")
                # 6. 存入字典
                configs[model_name] = config_value
            except ImportError:
                print(f"警告: 无法导入模块 {module_name}")
            except AttributeError:
                print(f"警告: 在模块 {module_name} 中未找到变量 info_model")      
    return configs


def parse_response(chunk: str) -> Optional[Dict[str, Any]]:
    """
    解析服务器发送事件（SSE）的一行数据。
    假设数据格式为 `data: {JSON_OBJECT}`。
    """
    chunk = chunk.decode("utf8")
    chunk = chunk[6:] if chunk.startswith("data: ") else chunk
    # print("chunk: ", chunk)
    if chunk.strip() == "[DONE]":
        return None
    try:
        return json.loads(chunk)
    except json.JSONDecodeError:
        # 忽略无法解析的行
        return None


def send_requests(new_id: str, prompt_item: Dict[str, Any], request_config: Dict[str, Any]) -> Dict[str, Any]:
    '''
    发送请求
    '''
    result = {
        "request_id": new_id,
        "prompt": prompt_item['prompt'],
        "status": '',
        "response": '',
        "prompt_tokens": prompt_item['token'],
        "completion_tokens": -1,
        "rep_time_lst": []
    }

    url = request_config["url"]
    headers = {"Content-Type": "application/json"}
    if request_config.__contains__('appcode'):
        headers["Authorization"] = "Bearer " + request_config["appcode"]
    payload = {
        "messages": [{"role": "system","content": "You are a helpful assistant."},{"role": "user","content": prompt_item['prompt']}],
        "stream":True
    }
    for para in request_config['parameters']:
        payload[para] = request_config['parameters'][para]
    result['rep_time_lst'] = []

    try:
        start_time = time.perf_counter()
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as response:
            response.raise_for_status()  # 如果状态码不是2xx，则抛出异常
            for chunk in response.iter_lines(chunk_size=None):
                parsed_data = parse_response(chunk)
                if not parsed_data:
                    continue
                result['rep_time_lst'].append(time.perf_counter() - start_time)
                if parsed_data and "choices" in parsed_data and parsed_data["choices"]:
                    result['response'] += parsed_data["choices"][0].get("delta", {}).get("content", "")
                if 'usage' in parsed_data:
                    result['prompt_tokens'] = parsed_data["usage"]["prompt_tokens"]
                    result['completion_tokens'] = parsed_data["usage"]["completion_tokens"]
        if result['completion_tokens'] == -1:
            result['completion_tokens'] = len(result['rep_time_lst'])
        result["status"] = 'success'
    except requests.exceptions.RequestException as e:
        result["status"] = f"Request failed: {e}"
    except Exception as e:
        result["status"] = f"An unexpected error occurred: {e}"
    
    return result


def logger_init(log_queue):
    """
    配置每个工作进程的 logger。
    """
    logger = logging.getLogger(str(os.getpid()))
    logger.handlers = []
    logger.setLevel(logging.INFO)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    logger.info(f"工作进程 {str(os.getpid())} 已初始化，Logger 配置完成。")


def worker_task(task_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    每个进程执行的任务函数，循环发送请求，直到达到测试时间，其中packed_tasks包含了任务信息task_info，请求参数config
    """
    logger = logging.getLogger(str(os.getpid()))
    result_lst = []
    start_time = time.perf_counter()
    idx = 0
    while True:
        new_id = task_info['pid'] + '-' + str(idx)
        if task_info['config']['request_config']['is_static']:
            prompt_item = task_info['questions'][0]
        else:
            prompt_item = task_info['questions'][random.randint(0, len(task_info['questions'])-1)]
        result_lst.append(send_requests(new_id, prompt_item, task_info['config']['request_config']))
        logger.info(f'{new_id}  {result_lst[-1]["status"]}')
        #  若到达测试时间，则退出循环，开始统计结果
        if time.perf_counter() - start_time > task_info['config']['test_time']:
            break
        idx += 1
    #  计算首字响应时间，每秒输出token数，token间延迟等指标
    for result in result_lst:
        if result['status'] != 'success':
            logger.error(result['status'])
            logger.error('request prompt: \n' + result['prompt'])
            continue
        rep_time_lst = result.pop('rep_time_lst')
        start = rep_time_lst.pop(0)
        rep_time_lst = [x-start for x in rep_time_lst]
        result['ttft'] = start
        differences = [rep_time_lst[i+1] - rep_time_lst[i] for i in range(len(rep_time_lst)-1)]
        result['token_delay'] = sum(differences) / len(differences)
        result['total_time'] = rep_time_lst[-1]
        result['throughput'] = result['completion_tokens'] / result['total_time']
    logger.info(f"第 {task_info['pid']} 个进程所有请求发送完毕")
    return result_lst


def run_test(tasks, log_queue):

    logger = logging.getLogger('main_process')

    # 预热
    N = 5
    prompt_item = tasks[0]['questions'][0]
    logger.info("--  预热阶段  --")
    logger.info(f"共 {str(N)} 个请求")
    for i in range(N):
        tmp_result = send_requests(str(i), prompt_item, tasks[0]['config']['request_config'])
        logger.info(f"第 {str(i+1)} 个预热请求： {tmp_result['status']}")

    logger.info("\n--  开始正式压测  --\n")
    # 开始压测
    successful_results = []
    failed_results = []
    with multiprocessing.Pool(processes=len(tasks), initializer=logger_init, initargs=(log_queue, )) as pool:
        results_iterator = pool.imap_unordered(worker_task, tasks)
        for res in results_iterator:
            for item in res:
                if item["status"] != 'success':
                    failed_results.append(item)
                else:
                    successful_results.append(item)
    
    if not successful_results:
        logger.error("No successful requests to analyze.")
        return

    #  统计结果
    success_num = len(successful_results)
    prompt_tokens_lst = [0] * success_num
    completion_tokens_lst = [0] * success_num
    ttft_lst = [0] * success_num
    throughput_lst = [0] * success_num
    total_time_lst = [0] * success_num
    token_delay_lst = [0] * success_num
    for i in range(success_num):
        prompt_tokens_lst[i] = successful_results[i]['prompt_tokens']
        completion_tokens_lst[i] = successful_results[i]['completion_tokens']
        ttft_lst[i] = successful_results[i]['ttft']
        throughput_lst[i] = successful_results[i]['throughput']
        total_time_lst[i] = successful_results[i]['total_time']
        token_delay_lst[i] = successful_results[i]['token_delay']

    def cal_stats(data):
        mean_val = statistics.mean(data)  # 平均值
        max_val = max(data)  # 最大值
        min_val = min(data)  # 最小值
        p95 = statistics.quantiles(data, n=100)[94]  # P95
        p99 = statistics.quantiles(data, n=100)[98]  # P99
        return mean_val, max_val, min_val, p95, p99
    
    prompt_tokens = statistics.mean(prompt_tokens_lst)
    completion_tokens = statistics.mean(completion_tokens_lst)
    total_time = statistics.mean(total_time_lst)
    ttft, ttft_max, ttft_min, ttft_p95, ttft_p99 = cal_stats(ttft_lst)
    throughput, throughput_max, throughput_min, throughput_p95, throughput_p99 = cal_stats(throughput_lst)
    token_delay, token_delay_max, token_delay_min, token_delay_p95, token_delay_p99 = cal_stats(token_delay_lst)

    failed_num = len(failed_results)
    total_num = success_num + failed_num
    acc = success_num / total_num * 100.0
    result_info = f'''
测试线程数：{tasks[0]["cur_thread_num"]}
测试时间：{tasks[0]['config']["test_time"]}秒
请求数量：{total_num}  成功请求数量：{success_num}  失败请求数量：{failed_num}
事务成功率：{acc:.2f}%
上下文量级：{tasks[0]["cur_context"]}  prompt平均token数：{prompt_tokens}
-- 压测结果 --
首token响应时间（s）：{ttft}
token输出速度（token/s）：{throughput}
token间延迟（s）：{token_delay}
'''
    logger.info("-" * 20)
    logger.info(result_info)
    logger.info("-" * 20)

    # 保存详细结果
    ticks = time.strftime('%Y%m%d_%H%M%S',time.localtime())
    folder_path = f"result_details/{tasks[0]['config']['model_name']}/{ticks}-tn_{tasks[0]['cur_thread_num']}-tt_{tasks[0]['config']['test_time']}"  # 执行结果存放路径
    logger.info("详细结果存放路径：" + folder_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(f'{folder_path}/log', 'w', encoding='utf8') as f:
        f.write(result_info)
    with open(f'{folder_path}/successful_results.json', 'w', encoding='utf8') as f:
        json.dump(successful_results, f, ensure_ascii=False)
    with open(f'{folder_path}/failed_results.json', 'w', encoding='utf8') as f:
        json.dump(failed_results, f, ensure_ascii=False)

    # 将最终压测结果写入csv文件
    if not os.path.exists(tasks[0]['config']['result_path']):
        header = ["模型名称","测试环境","上下文长度量级","并发线程数","测试时间",
                  "prompt平均token数","回复平均token数",
                  "首token平均响应时间","token平均输出速度（token/s）","token间平均延迟","总体平均响应时间",
                  "总调用量","成功率",
                  "最小首token时间","最大首token响应时间","首token响应时间-95%line","首token时间-99%line",
                  "最小token输出速度","最大token输出速度","token输出速度-95%line","token输出速度-99%line",
                  "最小token间延迟","最大token间延迟","token间延迟-95%line","token间延迟-99%line"]
    else:
        header = []
    with open(tasks[0]['config']['result_path'], "a+", encoding="utf8") as csvfile:
        csv_writer = csv.writer(csvfile)
        if header:
            csv_writer.writerow(header)
        csv_writer.writerow([
            tasks[0]['config']['model_name'], "", tasks[0]['cur_context'], tasks[0]['cur_thread_num'], tasks[0]['config']['test_time'],
            prompt_tokens, completion_tokens,
            ttft, throughput, token_delay, total_time,
            total_num, acc,
            ttft_min, ttft_max, ttft_p95, ttft_p99,
            throughput_min, throughput_max, throughput_p95, throughput_p99,
            token_delay_min, token_delay_max, token_delay_p95, token_delay_p99
        ])
        logger.info('压测结果已保存到csv文件：' + tasks[0]['config']['result_path'])
    
    return



def main(args, log_queue):

    # 为主进程配置日志记录器
    logger = logging.getLogger('main_process') # 获取一个主进程专用的logger
    logger.setLevel(logging.INFO)
    main_queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(main_queue_handler)
    logger.propagate = False # 防止日志被重复处理
    logger.info("主进程: 日志系统初始化完成，监听器已启动。")

    # 1. 加载模型配置
    model = args.model
    configs = load_all_configs()
    # logger.info("搜索到的模型配置文件：\n"+ ", ".join(configs.keys()))
    config = configs[model]
    logger.info("-" * 20)
    logger.info(f"Starting stress test\ntest model: {config['model_name']}")
    logger.info("-" * 20)

    # 2. 使用multiprocessing.Pool进行并发压测
    context_lst = config['context_lst']
    thread_num_lst = config['thread_num_lst']

    for context in context_lst:
        for thread_num in thread_num_lst:

            data = load_test_data(f'data/{context}.json')
            tasks = [
                {
                    'pid': str(i),
                    'cur_context': context,
                    'cur_thread_num': thread_num,
                    'questions': data['questions'],
                    'config': config
                }
                for i in range(thread_num)
            ]
            run_test(tasks, log_queue)  # 执行压测
            logger.info(f"\ncontext: {context}, thread num: {thread_num} stress test finished.")


if __name__ == "__main__":
    
    log_queue = multiprocessing.Queue()
    # 配置主进程的日志格式
    formatter = logging.Formatter('%(asctime)s - %(processName)s - [%(levelname)s] - %(message)s')
    file_handler = logging.FileHandler('log.log', 'w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()  # 输出到控制台
    console_handler.setFormatter(formatter)
    listener = logging.handlers.QueueListener(log_queue, file_handler, console_handler)
    listener.start()
    print("主进程：日志监听器已启动。")

    # --- 主进程 ---
    parser = argparse.ArgumentParser(description="LLM API Streaming Stress Test Tool")
    parser.add_argument('-m', '--model', dest='model', type=str, required=True, help="It will choose config_model.py as test config")
    args = parser.parse_args()
    main(args, log_queue)

    
    # 所有任务结束后，停止监听器
    listener.stop()
    print("主进程：日志监听器已停止。所有日志已写入 log.log")
