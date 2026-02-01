info_model = dict(
    model_name = "qwen3_32B",

    # 压测参数设置
    context_lst = ["256"],  # 输入token长度，对应data中各个测试文件的名字
    thread_num_lst = [2],  # 测试线程数
    test_time = 30,  # 测试时间，单位为s
    result_path = "result/result-test.csv",  # 性能测试结果存放路径，性能测试结果会追加写到该文件里面，如果是第一次测试的话会新建该文件，所以保证前置路径存在即可，csv文件的名字可随意更改
    

    # 模型请求配置
    request_config = {
        "is_static": False,  # 是否选择静态测试。若为True，则每次发送的测试数据都是固定的；否则是从文件中随机挑选数据进行发送
        'url': 'https://cisp.travelsky.com.cn/kunlun/ingress/api-safe/c10ca6/5e983be0668947c68f717ce93a637041/ai-777425f85ac440659bc584405ccecc98/service-dcbf2c7da2454300bcf66ee55a67b89f/v1/chat/completions',
        'appcode': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI1Yzc4YzlkMmIyNTc0ZWJjOWY0ZGQwMWYzNTY0MzJmZiIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkyMzMzNDg0MX0.Y03h13YwMVnVeetNmc0VFcICAkE7uE3q7lQbEIxBFnkvnP7bsj5EXhLtsUSs163TIedNNCJpZsCXTI5jSY6zA2YlDGnYnDcHme_eHiUhqF5CGwDhaqR5BLkTyRE8giCEvP8MD-9V-vzq5OMZQhvPYyp5SZ33iWx2ZIWxgqVwp7HUoqePiZy7fd1kjgBOaE-t96K9UWWiCVDALHcq8sRQ9BDcUGqIIFuNyAX-JdQj0Kogs6O-9vD0SOii5cDY4Ajc-2hgYHkIU1gChdlNC-k6WPxTAyH7Qq6c1Hdq5MGieSkCJc5LvakfoI6wVCo7OWdL5xt-BpXGEevTIcu-fZ0c-g',  # 可以不传（使用本地地址，如127.0.0.1进行测试时就不用传这个）
        "parameters": {
            "model": "Qwen3-32B",
            "max_tokens": 256,
            "stream": True,
        }
    }
)


