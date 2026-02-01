single_test.py
单发测试用

stress_test.py
压测主脚本，使用以下命令执行：
python stress_test.py -m jiutian

-m：测试模型配置文件，对应configs下的文件名


./configs/jiutian.py
配置文件，可选择测试数据集，测试线程数，测试时间等
context_lst和thread_num_lst中的元素不是一一对应的，而是全连接式。例如
context_lst = ["256", "1k"]
thread_num_lst = [1,3,5]
实际执行时就是在256上文数据集上，分别执行1并发，3并发和5并发的测试；之后在1k上文数据集上执行同样的操作


测试时间尽量不要少于5min，减少波动影响


