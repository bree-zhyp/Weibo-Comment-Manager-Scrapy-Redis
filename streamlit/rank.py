import streamlit as st
from rediscluster import RedisCluster
import json
import jieba

def load_chinese_words(file_path):
    """
    从文件中加载中文词列表
    """
    chinese_words = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            chinese_words.append(line.strip())
    return chinese_words

def rank_motion(filtered_data, chinese_words_path, number):
    chinese_words = load_chinese_words(chinese_words_path)
    top_data = sorted(filtered_data, key=lambda x: sum(x.get('content', '').count(word) for word in chinese_words), reverse=True)[:number]
    return top_data