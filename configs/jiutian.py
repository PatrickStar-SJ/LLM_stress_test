info_model = dict(
    model_name = "jiutian-75B",

    # 压测参数设置
    context_lst = ["256"],  # 输入token长度，对应data中各个测试文件的名字
    thread_num_lst = [2],  # 测试线程数
    test_time = 30,  # 测试时间，单位为s
    result_path = "result/result-test.csv",  # 性能测试结果存放路径，性能测试结果会追加写到该文件里面，如果是第一次测试的话会新建该文件，所以保证前置路径存在即可，csv文件的名字可随意更改
    

    # 模型请求配置
    request_config = {
        "is_static": False,  # 是否选择静态测试。若为True，则每次发送的测试数据都是固定的；否则是从文件中随机挑选数据进行发送
        "url": "https://hl.jiutian.10086.cn/kunlun/ingress/api/hl-4a9c15/7135989ae8e84c7a8ec98ccf14552b43/ai-64eddad87966424dbd2d0770386149cc/service-528a56072f764f31a98f67948d677a0f/v1/chat/completions",
        "appcode": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIyMzU1MTU0NmEzNGY0NDBjOWUwZTliOGYyMDdiMTQ5YSIsImlzcyI6ImFwaS1hdXRoLWtleSIsImV4cCI6NDg5Mjk0NzM3NH0.HHSINNozw0elO3XK6eYzV39u82rl2Z-2UfnApAyqCvsY5EJyhD5QaiZ3GKTYRODStx3wLxgF53nKkNpaxzmq5gING8h7dNZ2ToHHqLHVakYPdN4snTxo5U8YqU2tiAhDobQYDDbyOgDFAUHJMsPRsd52KAtu_gfcZQ8CJ4dTZsFpLtbuMwaereaDpPhZzYUCEIsGxWsSsCGUDRS8M3S_Z6XhQCHrnHduVJ4IFRlv8inrQ6_htUyDQiGEMXBm78RJ5KYh5ceVbmfVK7rumT5kuuTEHarbMsASHdzN5QPfbgj3lfWMt4jFvgujq0yW96OEjiXNgeaszZ-Arrd_OmLVEg",  # 可以不传（使用本地地址，如127.0.0.1进行测试时就不用传这个）
        "parameters": {
            "model": "jiutian-cm-050",
            "max_tokens": 256,
            "stream": True,
        }
    }
)


