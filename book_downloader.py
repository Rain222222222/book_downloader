#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time      : 2023/12/20 15:07
# @Author    : 我是Rain呀 --  (｡♥ᴗ♥｡)
# @File      : book_downloader.py
# @Software  : PyCharm

import os  # 导入操作系统相关的模块，用于文件路径等操作
import random  # 导入随机数生成相关的模块，用于随机选择代理IP
import re  # 导入正则表达式模块
import time  # 导入时间相关的模块，用于记录程序运行时间
from colorama import Fore  # 导入字体颜色模块
import requests  # 导入用于发送HTTP请求的模块
from requests.adapters import HTTPAdapter  # 导入HTTP适配器，用于配置请求的重试策略
from lxml import etree  # 导入用于解析HTML的模块
import multiprocessing  # 导入多进程模块，用于并发下载章节内容
import shutil  # 导入文件操作相关的模块，用于删除临时文件夹等
from urllib3 import Retry  # 导入用于配置HTTP请求重试策略的模块
import default_information  # 导入自定义的 default_information 模块，包含必要的 headers 和 sign_logo


class NovelCrawler:
    def __init__(self, Fuzzy_name):
        # 初始化小说爬虫对象
        self.book_name = Fuzzy_name.strip()  # 初始化小说名，去除首尾空格
        self.cookies = None  # 网站的 cookies
        self.save_book_name = None  # 最后保存的书名
        self.current_directory = os.path.dirname(os.path.abspath(__file__))  # 获取当前工作目录
        self.processes = 10  # 设置多少个并发下载
        self.tmp_file_name = 'TempBookName'  # 临时文件目录名称

        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # 代理配置，不需要代理则直接配置 self.proxy_url = '' 即可
        # 代理网站 https://www.taiyanghttp.com/ 可参考，新用户注册免费可以使用

        self.proxy_url = ''
        self.proxy_ip_list = None  # 代理 IP 列表，暂时未初始化为任何值

    def put_url(self):
        search_list = {}

        def analysis_url(index_html):
            # 解析搜索结果页面，找到目标小说的链接
            search = index_html.xpath('//h4')
            for src in search:
                # 每部小说的连接
                b_url = src.xpath('./a/@href')[0]
                # 小说名称
                b_name = src.xpath('./a/text()')[0]
                # 小说作者
                z_name = src.xpath('./span/text()')[0].replace('/', '').strip()
                search_list.update({b_name: b_url})
                print(f"{len(search_list)}. 书名：{b_name} -- 作者：{z_name}")

        # 构建搜索小说的 URL
        url = f"https://www.hetushu.com/search/?keyword={self.book_name}"
        # 发送请求获取搜索结果页面

        # 发送 GET 请求，获取搜索结果页面
        with self.session.get(url, headers=default_information.headers, cookies=self.cookies,
                              proxies=self.proxy_result(), timeout=10) as response:
            response.raise_for_status()  # 如果响应状态码不是 2xx，抛出异常
            response.encoding = 'zh-Hant'  # 设置响应内容的编码为中文繁体
            index_et = etree.HTML(response.text)  # 使用 lxml 解析 HTML

        try:
            # 获取搜索结果的当前页和总页数
            page_start = index_et.xpath('//div[@class="page"]/span[@class="current"]/text()')[0]
            page_end = index_et.xpath('//input[@name="page"]/@max')[0]
            # 遍历每一页的搜索结果
            for number in range(int(page_start), int(page_end) + 1):
                url = f"https://www.hetushu.com/search/?keyword={self.book_name}&page={number}"
                # 发送 GET 请求，获取下一页的搜索结果页面
                with self.session.get(url, headers=default_information.headers, cookies=self.cookies,
                                      proxies=self.proxy_result(), timeout=10) as response:
                    response.raise_for_status()  # 如果响应状态码不是 2xx，抛出异常
                    response.encoding = 'zh-Hant'  # 设置响应内容的编码为中文繁体
                    index_et = etree.HTML(response.text)  # 使用 lxml 解析 HTML
                    analysis_url(index_et)  # 解析当前页的搜索结果
        except IndexError:
            analysis_url(index_et)  # 如果发生索引错误，说明只有一页搜索结果，直接解析当前页的搜索结果

        list_tol = len(search_list) + 1
        print(f"{list_tol}. 退出下载")
        while True:
            try:
                # 解析搜索关键字 及 共计搜索量
                print(f'\n关键词：{self.book_name}, 共搜索到{len(search_list)}本作品')
                user_search = int(input("请输入想要下载书籍的序号： "))
                if user_search == list_tol:
                    exit('已退出')  # 如果用户选择退出，则退出程序
                if 0 < user_search <= len(list(search_list.values())):
                    if list(search_list.values()):
                        # 返回用户选择的小说链接
                        self.book_name = list(search_list.keys())[int(user_search) - 1]
                        return 'https://www.hetushu.com' + list(search_list.values())[int(user_search) - 1]
                    return 0  # 如果搜索结果为空，则返回 0
                else:
                    print("输入的序号超出了范围...")
            except ValueError:
                print('错误，请输入数字...')  # 如果用户输入不是数字，捕获异常并提示错误

    def crawl_chapters(self, bk_url):
        # 发送请求获取小说章节列表页
        with self.session.get(bk_url, headers=default_information.headers,
                              proxies=self.proxy_result()) as result_get:
            et = etree.HTML(result_get.text)

        # 解析章节列表页，获取每个章节的链接并进行下载
        urls = et.xpath('//dl[@id="dir"]/dd')  # 获取章节列表
        self.save_book_name = et.xpath('//h2/text()')[0]  # 获取小说名称
        pool = multiprocessing.Pool(processes=self.processes)  # 创建进程池，控制并发下载
        for get_url in urls:
            book__url = 'https://www.hetushu.com' + get_url.xpath('./a/@href')[0]  # 构建每个章节的完整链接
            pool.apply_async(self.downloader_book, (book__url,))  # 使用进程池异步执行章节下载函数
        pool.close()  # 关闭进程池，表示不再添加新的任务
        pool.join()  # 等待所有子进程完成，确保所有章节下载完成

    def proxy_result(self):
        if self.proxy_ip_list is None:
            return None  # 如果代理 IP 列表为空，返回 None，表示不使用代理
        else:
            random_result = random.choice(self.proxy_ip_list)  # 从代理 IP 列表中随机选择一个代理
            http_dict = {
                "http": f"http://{random_result['ip']}:{random_result['port']}",
                "https": f"https://{random_result['ip']}:{random_result['port']}"
            }
            return http_dict  # 返回代理配置字典，包含 HTTP 和 HTTPS 的代理地址

    def downloader_book(self, book_chapter_url):
        # 发送请求获取小说具体章节内容页
        with self.session.get(book_chapter_url, headers=default_information.headers,
                              proxies=self.proxy_result()) as r:
            et = etree.HTML(r.text)

        # 解析章节内容页，获取小说名、章节名和内容
        book_chapter_name = et.xpath('//div[@class="title"]/text()')[0]
        text = et.xpath('//div[@id="content"]/div/text()')
        book_chapter_url_name = et.xpath('//a[@class="code"]/@href')[0]

        # 构建文件名，保存小说内容
        result = re.search(r'(\d+)\.html', book_chapter_url)
        extracted_number = result.group(1)
        temp_name = os.path.join(self.current_directory, self.tmp_file_name)
        filename = os.path.join(temp_name, extracted_number)
        with open(filename, mode='a+', encoding='utf-8') as f1:
            # 整理章节内容并写入文件
            rest_lines = [book_chapter_name] + [f'    {t.strip()}' for t in text]
            f1.write(''.join(line + '\n' if not line.endswith('\n') else line for line in rest_lines))

        # 打印下载完成信息
        print(
            f'小说 <{self.save_book_name}> 爬取下载完成： {book_chapter_name}  爬虫目标URL地址: {book_chapter_url_name}'
        )

    def save_file(self):
        # 构建临时文件夹路径
        tmp_file_path = os.path.join(self.current_directory, self.tmp_file_name)

        # 获取目录下的文件列表，并按文件名排序
        tmp_file_list = sorted(os.listdir(tmp_file_path), key=lambda x: int(x))

        # 构建输出文件的路径，使用小说名作为文件名
        output_file_path = os.path.join(self.current_directory, f"{self.save_book_name}.txt")

        # 遍历文件列表，读取每个文件的内容并写入输出文件
        for temp_file_name in tmp_file_list:
            # 构建当前输入文件的完整路径
            input_file_path = os.path.join(tmp_file_path, temp_file_name)
            # 打开当前输入文件，使用 'r' 模式，表示读取文件
            with open(input_file_path, mode='r', encoding='utf-8') as input_file:
                # 读取输入文件的内容并写入输出文件，每个文件内容之间插入换行符
                # 打开输出文件，使用 'a+' 模式，表示以追加方式打开文件
                with open(output_file_path, mode='a+', encoding='utf-8') as output_file:
                    output_file.write(input_file.read() + '\n')

        print(f"\n已下载好的小说路径： {output_file_path}")

    def proxys(self):
        try:
            result = self.session.get(self.proxy_url)  # 发送请求获取代理 IP 列表
            if result.json()["data"]:
                proxy_dict = result.json()["data"]  # 解析返回的代理 IP 列表
                # result.json()返回结果为：{"code":0,"data":[{"ip":"180.124.x.xx","port":"4331"},
                # {"ip":"115.222.xxx.xxx","port":"4375"}, ... ], "msg":"0","success":true}
                self.proxy_ip_list = proxy_dict  # 将代理 IP 列表存储到对象属性中
                print('启用代理 获取代理 IP 成功...')
            else:
                exit(result.json())  # 如果未获取到代理 IP 列表，退出程序并输出错误信息
        except requests.RequestException as e:
            exit(f"请求代理服务器异常：{e}")  # 如果请求代理服务器异常，退出程序并输出错误信息

    def main(self):
        # 初始化爬虫开始时间
        start_time = time.time()

        try:
            if not self.proxy_url.startswith('http'):
                print('未启用代理')  # 如果代理 URL 不以 'http' 开头，输出提示信息表示未启用代理
            else:
                self.proxys()  # 启用代理，调用 proxys 函数获取代理 IP 列表

            # 发送请求获取网站首页，获取 cookies
            with self.session.get('https://www.hetushu.com/', headers=default_information.headers,
                                  proxies=self.proxy_result(), timeout=5) as response:
                response.raise_for_status()
                self.cookies = response.cookies
            print('Cookie 初始化完成')

            # 获取小说详情页 URL
            book_url = self.put_url()

        except requests.RequestException as e:
            # 网络请求异常，输出错误信息
            exit(f"网络请求异常: {e}")
        temp_dir = os.path.join(self.current_directory, self.tmp_file_name)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        # 遍历当前目录下的文件和文件夹
        files_and_folders = os.listdir(self.current_directory)
        for file_or_folder in files_and_folders:
            if file_or_folder.startswith(self.book_name):
                # 构建文件路径
                file_path = os.path.join(self.current_directory, file_or_folder)
                try:
                    # 如果是文件，则删除文件
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    # 删除文件时出现错误，输出错误信息
                    exit(f"删除 {file_or_folder} 时出现错误：{e}")

        # 开始爬取章节
        self.crawl_chapters(book_url)

        # 记录结束时间，计算爬虫执行时间
        end_time = time.time()

        # 格式化执行时间
        def format_time(seconds):
            minutes, seconds = divmod(seconds, 60)
            milliseconds = (seconds - int(seconds)) * 1000
            return f'{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds):03d}'

        # 下载完成后，小说整合
        self.save_file()
        # 输出总体执行信息
        execution_time = end_time - start_time

        try:
            # 尝试递归地删除临时文件夹及其内容
            shutil.rmtree(temp_dir)
        except OSError:
            # 如果删除失败，捕获异常，并输出错误信息
            print(f'目录删除失败 {temp_dir}')

        # 输出下载完成信息和总耗时
        print(f'全本小说已下载完成 共计耗时: {format_time(execution_time)}')


if __name__ == "__main__":
    # 输出程序标志
    for i in default_information.sign_logo.split('\n'):
        print(f'{Fore.BLUE}{i.strip()}')
    # 进入一个无限循环，直到用户提供有效的书名或选择退出程序
    while True:
        # 提示用户输入书名，同时提供退出程序的选项
        print(f'当前版本号： {default_information.__version__}')
        book_name = input(f'请输入(书名｜作者名｜EXIT 退出程序)：{Fore.RESET}')

        # 判断用户输入是否为 'Q'（不区分大小写），如果是则退出程序
        if book_name.upper().strip() == 'Q':
            exit('退出程序')
        # 判断用户输入是否为非空字符串，如果是则结束循环
        elif book_name.strip():
            break

    # 创建小说爬虫对象并执行主程序
    crawler = NovelCrawler(book_name)
    crawler.main()
