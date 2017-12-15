from __future__ import division

import argparse

import requests
from bs4 import BeautifulSoup
import codecs
import os
import re
import sys
import time
try:
    from urlparse import urljoin
    from urllib import urlretrieve
except ImportError:
    from urllib.parse import urljoin
    from urllib.request import urlretrieve

import selenium
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import urllib.request

import json

# HOST
HOST = 'http://www.instagram.com'

# SELENIUM CSS SELECTOR
CSS_LOAD_MORE = "a._1cr2e._epyes"
CSS_RIGHT_ARROW = "a[class='_3a693 coreSpriteRightPaginationArrow']"
FIREFOX_FIRST_POST_PATH = "//div[contains(@class, '_mck9w _gvoze _f2mse')]"
TIME_TO_CAPTION_PATH = "../../../div/ul/li/span"

# FOLLOWERS/FOLLOWING RELATED
CSS_EXPLORE = "a[href='/explore/']"

# JAVASCRIPT COMMANDS
SCROLL_UP = "window.scrollTo(0, 0);"
SCROLL_DOWN = "window.scrollTo(0, document.body.scrollHeight);"


class url_change:
    def __init__(self, prev_url):
        self.prev_url = prev_url

    def __call__(self, driver):
        return self.prev_url != driver.current_url


class InstagramCrawler:

    def __init__(self, headless=True, firefox_path=None):

        firefox_binary = FirefoxBinary(firefox_path)
        options = webdriver.FirefoxOptions()

        if headless:
            options.set_headless(headless=True)
        driver = webdriver.Firefox(firefox_binary=firefox_binary, firefox_options=options)
        self._driver = driver
        driver.implicitly_wait(10)

    def browse_target_page(self, query):
        if query.startswith('#'):
            relative_url = urljoin('explore/tags/', query.strip('#'))
        else:
            relative_url = query

        target_url = urljoin(HOST, relative_url)
        self._driver.get(target_url)

    def scroll_to_num_of_posts(self, number):
        num_of_posts = int(self._driver.find_element_by_xpath("//span[@class='_fd86t']").text.replace(',', ''))
        print("posts: {}, number: {}".format(num_of_posts, number))
        number = number if number < num_of_posts else num_of_posts

        # scroll page until reached
        loadmore = WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, CSS_LOAD_MORE))
            )
        loadmore.click()

        num_to_scroll = int((number-12)/12) + 1
        for i in range(num_to_scroll):
            print("Scrolls: {}/{}".format(i, num_to_scroll))
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(0.2)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(0.2)
        return num_of_posts

    def crawl_post_urls(self):
        print("Crawl all post urls")
        posts = self._driver.find_elements_by_xpath("//div[@class='_mck9w _gvoze _f2mse']")
        urls = []
        for post in posts:
            a_tag = post.find_element_by_tag_name('a')
            urls.append(a_tag.get_attribute('href'))
        return urls

    def scrape_time_and_captions(self, urls):
        doc = requests.get(urls[0])
        soup = BeautifulSoup(doc.text, 'html.parser')
        span = soup.find('span', id='react-root')
        # print(soup.prettify())
        print(span.text)

        '''
        for url in urls:
            with urllib.request.urlopen(url) as url_open:
                print(url)
                doc = url_open.read()
                print("============================")
                print(doc)
                print("============================")
                soup = BeautifulSoup(doc, 'html.parser')
                print(soup.prettify())
                # time = soup.find('time', class_="_p29ma _6g6t5")
                # datetime = time['datetime']
                # date_title = time['title']
                # caption = soup.find_all('ul', class_='_b0tqa').text
                # print("\t{")
                # print("\t\t'datetime':"+str(datetime))
                # print("\t\t'datetime_title':"+str(date_title))
                # print("\t\t'caption:'"+caption)
                # print("\t},")
        '''

    def crawl(self, query, number):
        self.browse_target_page(query)
        num_of_posts = self.scroll_to_num_of_posts(number)
        urls = self.crawl_post_urls()
        self.scrape_time_and_captions(urls)







if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Instagram Crawler')
    parser.add_argument('-q', '--query', type=str, default='instagram',
                        help="target to crawl, add '#' for hashtags")
    parser.add_argument('-n', '--number', type=int, default=0,
                        help="Number of posts to download: integer")
    parser.add_argument('-l', '--headless', action='store_true',
                        help='If set, will driver to run script as headless')
    args = parser.parse_args()

    crawler = InstagramCrawler(headless=args.headless)
    crawler.crawl(query=args.query, number=args.number)



