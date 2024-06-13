import streamlit as st
from rediscluster import RedisCluster
import json
import rank as rk
import distributed_sort as ds

def query_data(searchword, rankword, number, begin_date=None):
    """
    查询 Redis 中包含特定关键字的数据，返回排名前二的数据列表
    """
    # 存储符合条件的数据
    filtered_data = []

    # 检索键对应的列表数据
    list_data = rc.lrange("weibo_comment:items", 0, -1)
    
    # 遍历列表中的每个字符串元素，并解析为 JSON 对象
    for json_string in list_data:
        data = json.loads(json_string)

        if searchword in data.get('content', ''):
            # 检查日期是否符合要求
            if begin_date:
                # 如果创建日期不为空且在指定日期之后，则加入筛选结果
                date = begin_date.strftime("%Y-%m-%d")
                if date in data.get('created_at', ''):
                    filtered_data.append(data)
            else:
                filtered_data.append(data)

    aim_tag = ["comments_count", "created_at",]
    if rankword in aim_tag:
        # 对符合条件的数据按照评论数进行排序，取前几名
        top_two_data = sorted(filtered_data, key=lambda x: x.get(rankword, 0), reverse=True)[:number]
    else:
        rankword = rankword[:-1]
        top_two_data = ds.distributed_rank(rankword, number, rc)

    return top_two_data

# 查询并展示数据
def query_redis_data(rankword, number, begin_date):
    searchkey = st.text_input("输入 Redis Key:")
    if st.button("查询"):
        data = query_data(searchkey, rankword, number, begin_date)

        if data:
            # 展示数据
            for i, item in enumerate(data, 1):
                st.write(f"排名 {i}:")
                st.write(f"用户: {item['user']['nick_name']}")
                st.write(f"评论数: {item['comments_count']}")
                st.write(f"发布时间: {item['created_at']}")
                st.write(f"内容: {item['content']}")
                st.write(f"发布位置: {item['ip_location']}")
                st.write(f"微博链接: {item['url']}")
                st.write("------")
        else:
            st.write("没有找到对应的数据。")

if __name__ == "__main__":
    # Streamlit应用程序的标题
    st.title('Redis 数据库微博推文查询')
    st.sidebar.title("排名参数选择")

    # 左侧下拉菜单选择发布任务的端口号
    selected_port = st.sidebar.selectbox("选择发布任务的端口号:", ["6379", "6380", "6381"])

    # 在左侧栏添加下拉菜单以选择关键键
    selected_word = st.sidebar.selectbox("选择排名关键键:", ["评论数量", "发布时间", "分布式查询"])

    # 定义关键字映射字典
    keyword_mapping = {
        "评论数量": "comments_count",
        "发布时间": "created_at",
    }

    if selected_word == "分布式查询":
        # 如果选择综合排名，则提供额外选项
        selected_tag = st.sidebar.selectbox("按照哪个标准:", ["评论数量", "发布时间"])

        vocabulary_mapping = {
            "评论数量": "comments_count1",
            "发布时间": "created_at1",
        }

        selected_key = vocabulary_mapping[selected_tag]
    else:
       # 如果选择了普通的则直接映射
        selected_key = selected_key = keyword_mapping[selected_word]

    # 是否设置日期的复选框
    set_date = st.sidebar.checkbox("设置日期")

    if set_date:
        # 如果选择了设置日期，则显示日期输入框
        begin_date = st.sidebar.date_input("选择搜索的具体日期")
    else:
        begin_date = None

    # 是否设置页面数量的复选框
    set_number = st.sidebar.checkbox("设置页面链接数量")    

    default_number = 5

    if set_number:
        # 如果选择了设置页面数量，则显示输入框
        number = int(st.sidebar.text_input("输入页面最大链接数量", value=str(default_number)))
    else:
        number = default_number

    startup_nodes = [{"host": "127.0.0.1", "port": selected_port}]

    # 创建RedisCluster实例
    rc = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

    # 在Streamlit应用程序中调用查询函数
    query_redis_data(selected_key, number, begin_date)

    # 关闭连接
    rc.close()

    # 添加作者信息
    st.text("本应用由张宇鹏设计")
