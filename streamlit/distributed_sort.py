import redis
import json
from rediscluster import RedisCluster
import rank as rk
from concurrent.futures import ThreadPoolExecutor

def enqueue_rank_task(rc, rank_key, number):
    try:
        # 发布排名任务到频道
        rc.publish('rank_channel', json.dumps({'rank_key': rank_key, '6379_number': int(number/3), '6380_number': int(number/3), '6381_number': number - 2*int(number/3)}))
        print("排名任务已发布到频道。")
    except ConnectionError as e:
        print("连接到 Redis 集群失败:", e)

# 从 Redis 集群中获取存储的数据
def get_data_from_redis_cluster(node_rc, begin, end):
    # 从每个节点获取数据
    data = []
    # 从节点中获取存储的数据
    node_data = node_rc.lrange("weibo_comment:items", begin, end)
    # 将 JSON 字符串解析为 Python 对象
    node_data = [json.loads(item) for item in node_data]
    data.extend(node_data)
    return data

def distributed_rank_worker(rc, number):
    results = []
    try:
        # 订阅排名频道
        pubsub = rc.pubsub()
        pubsub.subscribe('rank_channel')

        startup_nodes_6379 = [{"host": "127.0.0.1", "port": "6379"}]
        rc_6379 = RedisCluster(startup_nodes=startup_nodes_6379, decode_responses=True)

        startup_nodes_6380 = [{"host": "127.0.0.1", "port": "6380"}]
        rc_6380 = RedisCluster(startup_nodes=startup_nodes_6380, decode_responses=True)

        startup_nodes_6381 = [{"host": "127.0.0.1", "port": "6381"}]
        rc_6381 = RedisCluster(startup_nodes=startup_nodes_6381, decode_responses=True)

        while True:
            # message = next(pubsub.listen())
            message = pubsub.get_message()
            if message:
                if message['type'] == 'message':
                    task = json.loads(message['data'])
                    print("已接受到信息", task)
                    rank_key = task['rank_key']
                    number_6379 = task['6379_number']
                    number_6380 = task['6380_number']
                    number_6381 = task['6381_number']

                    # 在节点上执行排名任务
                    # 创建线程池
                    with ThreadPoolExecutor(max_workers=3) as executor:
                        # 提交并行任务
                        futures = [
                            executor.submit(execute_rank, rank_key, rc_6379, number_6379, '6379', number),
                            executor.submit(execute_rank, rank_key, rc_6380, number_6380, '6380', number),
                            executor.submit(execute_rank, rank_key, rc_6381, number_6381, '6381', number)
                        ]
                        
                        # 等待所有任务完成
                        for future in futures:
                            result = future.result()  
                            results.append(result)

                    # 合并结果
                    print(len(results))
                    results = merge_sorted_lists(results, rank_key)

    except ConnectionError as e:
        print("连接到 Redis 集群失败:", e)

    return results

# 在每个节点上执行排名任务
def execute_rank(rank_key, rc, number, tag, select_num):
    if tag == '6379':
        list_data = get_data_from_redis_cluster(rc, 0, number)
    elif tag == '6380':
        list_data = get_data_from_redis_cluster(rc, number+1, 2*number)
    else:
        list_data = get_data_from_redis_cluster(rc, 2*number+1, -1)

    top_data = sorted(list_data, key=lambda x: x.get(rank_key, 0), reverse=True)[:select_num]
    return top_data

def merge_sorted_lists(sorted_lists, rank_key):
    merged_list = []

    iterators = [iter(lst) for lst in sorted_lists]

    while iterators:
        iterators = [it for it in iterators if it.__length_hint__() > 0]

        if not iterators:
            break

        # 从 iterators 中选取当前值最小的迭代器
        print("iterators")
        min_iterator = min(iterators, key=lambda it: next(it).get(rank_key, 0))

        try:
            merged_list.append(next(min_iterator))
        except StopIteration:
            # 如果迭代器已经到达末尾，就不再尝试获取下一个元素
            break

    print("okokok")
    print(merged_list)
    return merged_list

def distributed_rank(rank_key, number, rc):

    list_length = rc.llen("weibo_comment:items")

    enqueue_rank_task(rc, rank_key, list_length)

    results = distributed_rank_worker(rc, number)

    return results


