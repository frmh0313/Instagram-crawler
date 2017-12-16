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

    def __init__(self, headless=True, firefox_path=os.path.abspath('../firefox/firefox')):

        firefox_binary = FirefoxBinary(firefox_path)
        options = webdriver.FirefoxOptions()
        options.set_headless(headless=True)
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13;rv:57.0) Gecko/20100101 Firefox/57.0")
        options.add_argument("lang=ko_KR")
        options.add_argument('window-size=1920x1080')
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13;rv:57.0) Gecko/20100101 Firefox/57.0")
        driver = webdriver.Firefox(firefox_binary=firefox_binary, firefox_options=options, firefox_profile=profile)


        self._driver = driver
        self._driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: function() { return [1, 2, 3, 4, 5];},});")
        self._driver.execute_script("Object.defineProperty(navigator, 'languages', {get: function() {return['ko-KR', 'ko']}})")
        
        #user_agent = self._driver.find_element_by_css_selector('#user-agent').text
        #plugins_length = self._driver.find_element_by_css_selector('#plugins-length').text
        #languages = self._driver.find_element_by_css_selector('#languages').text
        
        #print('User-Agent: ', user_agent)
        #print('Plugin length: ', plugin_length)
        #print('languages: ', languages)

        self._driver.implicitly_wait(10)
        """
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/603.3.8 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/603.3.8")
        # chrome_options.add_argument("--headless")
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        driver = webdriver.Chrome(executable_path=os.path.abspath("chromedriver"),  chrome_options=chrome_options)
        self._driver = driver
        self._driver.implicitly_wait(10)
        """


        '''
        #if headless:
            # options.set_headless(headless=True)
            #driver = webdriver.PhantomJS(executable_path=os.path.abspath('phantomjs'))
        #else:
        '''


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
        # number = number if number < num_of_posts else num_of_posts
        number = num_of_posts

        # scroll page until reached
        load_more_exists = self._driver.find_element_by_css_selector(CSS_LOAD_MORE)
        REST_AFTER_SCROLL_DOWN = 0.3
        REST_AFTER_SCROLL_UP = 0.1
        print("load_more_exists:", load_more_exists)
        while load_more_exists is not None:
            try:
                for _ in range(5):
                    loadmore = load_more_exists
                    # loadmore = WebDriverWait(self._driver, 10).until(
                    # EC.presence_of_element_located(
                    #         (By.CSS_SELECTOR, CSS_LOAD_MORE))
                    #     )
                    time.sleep(1)
                    loadmore.click()
                    self._driver.execute_script(SCROLL_DOWN)
                    time.sleep(REST_AFTER_SCROLL_DOWN)
                    self._driver.execute_script(SCROLL_UP)
                    time.sleep(REST_AFTER_SCROLL_UP)
            except TimeoutException:
                print("TimeoutException")
                continue
            except NoSuchElementException:
                print("NoSuchElementException")
                load_more_exists = None
                break
            except StaleElementReferenceException:
                print("StaleElementReferenceException")
                self._driver.execute_script(SCROLL_DOWN)
                time.sleep(REST_AFTER_SCROLL_DOWN)
                self._driver.execute_script(SCROLL_UP)
                time.sleep(REST_AFTER_SCROLL_UP)
                break

        num_to_scroll = int((number-12)/120) + 1

        for i in range(num_to_scroll):
            print("Scrolls: {}/{}".format(i, num_to_scroll))
            self._driver.execute_script(SCROLL_DOWN)
            time.sleep(REST_AFTER_SCROLL_DOWN)
            self._driver.execute_script(SCROLL_UP)
            time.sleep(REST_AFTER_SCROLL_UP)

        num_loaded_posts = len(self._driver.find_elements_by_xpath("//div[@class='_mck9w _gvoze _f2mse']"))
        print("loaded posts: ", num_loaded_posts)
        if num_loaded_posts < number:
            load_not_finished = True
            while load_not_finished:
                num_to_scroll_more = int((number - num_loaded_posts - 12)/120) + 1
                print('num_to_scroll_more: ', num_to_scroll_more)
                for i in range(num_to_scroll_more):
                    print("Scroll more: {}/{}".format(i, num_to_scroll_more))
                    self._driver.execute_script(SCROLL_DOWN)
                    time.sleep(REST_AFTER_SCROLL_DOWN)
                    self._driver.execute_script(SCROLL_UP)
                    time.sleep(REST_AFTER_SCROLL_UP)
                num_loaded_posts = len(self._driver.find_elements_by_xpath("//div[@class='_mck9w _gvoze _f2mse']"))
                print('num_loaded_posts_after_loadmore: ', num_loaded_posts)
                if num_loaded_posts >= number:
                    load_not_finished = False
        print('page load finished')
        return num_of_posts

    def crawl_post_urls(self):
        print("Crawl all post urls")
        posts = self._driver.find_elements_by_xpath("//div[@class='_mck9w _gvoze _f2mse']")
        print("# of posts: ", len(posts))
        urls = []
        for post in posts:
            a_tag = post.find_element_by_tag_name('a')
            urls.append(a_tag.get_attribute('href'))
        print('# urls: ', len(urls))
        return urls

    def scrape_time_and_captions(self, urls):
        print('scrape time and captions')
        print("# urls: ", len(urls))
        for url in urls:
            #self._driver.get(urls[0])
            self._driver.get(url)
            trying_parse = True
            while trying_parse:
                try:
                    time_element = WebDriverWait(self._driver, 0.1).until(
                        EC.presence_of_element_located((By.TAG_NAME, "time"))
                    )
                    datetime = time_element.get_attribute('datetime')
                    date_title = time_element.get_attribute('title')
                    caption = time_element.find_element_by_xpath(
                        TIME_TO_CAPTION_PATH).text
                    print('datetime:', datetime)
                    print('datetime_title:', date_title)
                    print('caption:', caption)
                except TimeoutException:
                    print("Timeout exception in parsing stage. Trying again")
                except NoSuchElementException:
                    print("Caption not found. Pass")
                    break
                else:
                    print("else")
                    trying_parse = False

        #     except StaleElementReferenceException:
        #         print("StaleElementReferenceException. Trying again")
        #         wait_stale = 0
        #         trying_stale = True
        #         while trying_stale:
        #             try:


        '''
        doc = requests.get(urls[0])
        doc = urllib.request.urlopen(urls[0]).read()
        #soup = BeautifulSoup(doc.text, 'html.parser')
        soup = BeautifulSoup(doc, 'html.parser')
        # span = soup.find('span', id='react-root')
        print(soup.prettify())
        # print(span.text)
        '''

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
        with open('./urls.txt', 'w', encoding='utf8') as url_out:
            for url in urls:
                url_out.write(url)
                url_out.write('\n')
        # self.scrape_time_and_captions(urls)







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



