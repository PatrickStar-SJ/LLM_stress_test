info_model = dict(
    model_name = "qwen3_4B",

    # 压测参数设置
    context_lst = ["1k","4k","16k","32k","64k"],  # 输入token长度，对应data中各个测试文件的名字
    thread_num_lst = [1,5,10,20,40],  # 测试线程数
    test_time = 300,  # 测试时间，单位为s
    result_path = "result/result-test.csv",  # 性能测试结果存放路径，性能测试结果会追加写到该文件里面，如果是第一次测试的话会新建该文件，所以保证前置路径存在即可，csv文件的名字可随意更改
    

    # 模型请求配置
    request_config = {
        "is_static": False,  # 是否选择静态测试。若为True，则每次发送的测试数据都是固定的；否则是从文件中随机挑选数据进行发送
        'url': 'https://cisp.travelsky.com.cn/kunlun/ingress/api-safe/c10ca6/5e983be0668947c68f717ce93a637041/ai-9adeaa5daa024163b88c9004a14d950c/service-77e07a0f31df4994a257e86c8102313d/v1/chat/completions',
        'appcode': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI3YzVkMjkyNWE3MTM0YjJmYjVlZjRmMjQ1YjNkNWIzMSIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDkyMzMzNDI1OH0.FpHquXg6asf0uH7ntNpihLqk4rDNSD50zQKHno5B0MA2YtO-geuvwJFCN0Q3bzO6qbctGCNjwjJVw2aaxUtqENRBPTyCd9d95_tswuj9FllckhUlSlFCAxCuwg_n4Srb9inHpGPhQm6y6VaHPAg18ntObc1snsC0AfPAdlTzpMim-g2Vc4yrGGcKeh07VcDqByoq5bS-Vw3Ja2d42Fd6G-vN3pwHCm04tY995DNKEDly7gKWVJNnLrnw6qsiA_FRQWV0zgRV_CVPaT11cvgyR1uqa0vJ1YB378JwNQFD4BpRsdXwpNRFYKnDn4b7533RMxczSZLs0GxXgqw3pyy9_Q',  # 可以不传（使用本地地址，如127.0.0.1进行测试时就不用传这个）
        "parameters": {
            "model": "qwen3",
            "max_tokens": 256,
            "stream": True,
        }
    }
)


