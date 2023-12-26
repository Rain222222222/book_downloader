#!/usr/bin/env python
# -*- coding : utf-8 -*-
# @Time      : 2023/12/22 09:30
# @Author    : 我是Rain呀 --  (｡♥ᴗ♥｡) 
# @File      : us.py
# @Software  : PyCharm

from fake_user_agent import user_agent  # 用于获取随机的用户代理（User-Agent）

# 签名标志
sign_logo = """
   ██████╗  █████╗ ██╗███╗   ██╗
   ██╔══██╗██╔══██╗██║████╗  ██║
   ██████╔╝███████║██║██╔██╗ ██║
   ██╔══██╗██╔══██║██║██║╚██╗██║
   ██║  ██║██║  ██║██║██║ ╚████║
   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ 
   =============================
"""

# 请求头信息
headers = {
    'Referer': 'https://www.hetushu.com/',
    # 在随机的 User-Agent 池中随机挑选，应对反爬机制
    'User-Agent': user_agent(),
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive'
}


