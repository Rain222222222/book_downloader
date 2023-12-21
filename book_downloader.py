#!/usr/bin/env python
# -*- coding : utf-8 -*-
# @Time      : 2023/12/20 15:07
# @Author    : 我是Rain呀 --  (｡♥ᴗ♥｡) 
# @File      : book_downloader.py
# @Software  : PyCharm


import os
import time
import requests
from lxml import etree
from retrying import retry


class NovelCrawler:
    def __init__(self, books_name):
        self.headers = {
            'Referer': 'https://www.hetushu.com/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'
        }
        self.book_name = books_name.strip()
        self.book_url = None
        self.book_chapter_url = None

    def put_url(self):
        url = f"https://www.hetushu.com/search/?keyword={self.book_name}"
        with requests.get(url, headers=self.headers, timeout=5) as response:
            response.encoding = 'zh-Hant'
            index_et = etree.HTML(response.text)
        search = index_et.xpath('//h4/a')
        for i in search:
            b_url = i.xpath('./@href')[0]
            b_name = i.xpath('./text()')[0]
            if b_name == self.book_name:
                return 'https://www.hetushu.com' + b_url

    def crawl_chapters(self):
        with requests.get(self.book_url, headers=self.headers) as result_get:
            et = etree.HTML(result_get.text)
        url_list = et.xpath('//dl[@id="dir"]/dd')
        for get_url in url_list:
            self.book_chapter_url = 'https://www.hetushu.com' + get_url.xpath('./a/@href')[0]
            self.downloader_book()

    @retry(stop_max_attempt_number=2)
    def downloader_book(self):
        with requests.get(self.book_chapter_url) as r:
            et = etree.HTML(r.text)
        book_names = et.xpath('//h3/a/text()')[0]
        book_chapter_name = et.xpath('//div[@class="title"]/text()')[0]
        text = et.xpath('//div[@id="content"]/div/text()')

        filename = f'{book_names}.txt'
        with open(filename, mode='a+', encoding='utf-8') as f1:
            rest_lines = [book_chapter_name] + [f'    {i.strip()}' for i in text]
            f1.write(''.join(line + '\n' if not line.endswith('\n') else line for line in rest_lines))
        print(f'小说 <{book_names}> 爬取下载完成： {book_chapter_name}  爬虫目标URL地址: {self.book_chapter_url}')

    def main(self):
        source_cookie_data = 'PHPSESSID=4i36lshk0bqrdqn6uh0q23jmg4; color=0; mode=night; line=2; size=16; ' \
                             'bh=%7B%22path%22%3A%22book%22%2C%22bid%22%3A%2218%22%2C%22bname%22%3A%22%E6%AD%A6%E5%8A' \
                             '%A8%E4%B9%BE%E5%9D%A4%22%2C%22sid%22%3A%2215613%22%2C%22sname%22%3A%22%E7%AC%AC%E4%B8' \
                             '%80%E5%8D%83%E4%B8%89%E7%99%BE%E9%9B%B6%E4%B8%83%E7' \
                             '%AB%A0%20%E6%88%91%E8%A6%81%E6%8A%8A%E4%BD%A0%E6%89%BE%E5%9B%9E%E6%9D%A5%22%7D'
        url = 'https://www.hetushu.com/'
        start_time = time.time()
        try:
            with requests.get(url, headers=self.headers, timeout=5) as response:
                source_cookie_data = source_cookie_data.replace(
                    '4i36lshk0bqrdqn6uh0q23jmg4',
                    response.cookies.values()[0]
                )
                self.headers.update({'Cookie': source_cookie_data})
            print('Cookie 自动更新完成')

            self.book_url = self.put_url()

            if self.book_url is None:
                error_text = """
                没有搜到到相关结果，可能原因如下：
                    1. 书库中没有这本书。
                    2. 书名存在错别字。
                    3. Cookie失效(程序自动获取)。

                处理过程：
                    1. 手动登录 https://www.hetushu.com 搜索，结果是否正常。
                    2. 书名的名字严格区分，仔细检查名称。
                    3. 手动登录网站，替换 <self.headers> 中的 Cookie 值(程序自动获取)。
                """
                exit(error_text)
        except requests.RequestException as e:
            exit(e)
        current_directory = os.getcwd()
        files_and_folders = os.listdir(current_directory)
        for file_or_folder in files_and_folders:
            if file_or_folder.startswith(self.book_name):
                file_path = os.path.join(current_directory, file_or_folder)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)  # 删除文件
                except Exception as e:
                    exit(f"删除 {file_or_folder} 时出现错误：{e}")
        self.crawl_chapters()
        end_time = time.time()

        def format_time(seconds):
            minutes, seconds = divmod(seconds, 60)
            milliseconds = (seconds - int(seconds)) * 1000
            return f'{int(minutes):02d}:{int(seconds):02d}.{int(milliseconds):03d}'

        execution_time = end_time - start_time
        print(f'\n全本小说已下载完成 共计耗时:{format_time(execution_time)}')


if __name__ == "__main__":
    print("""██████╗  █████╗ ██╗███╗   ██╗
██╔══██╗██╔══██╗██║████╗  ██║
██████╔╝███████║██║██╔██╗ ██║
██╔══██╗██╔══██║██║██║╚██╗██║
██║  ██║██║  ██║██║██║ ╚████║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ 
=============================""")
    book_name = input('⚠️书名不要有错别字⚠️\n请输入需要下载的书名：')
    crawler = NovelCrawler(book_name)
    crawler.main()
