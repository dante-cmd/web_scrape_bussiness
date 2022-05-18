from urllib.parse import urljoin, urlparse
import requests
from requests import RequestException, HTTPError, ConnectionError, ConnectTimeout
import re
import numpy as np
from lxml.html import fromstring, tostring
import time
from pathlib import Path
import json


def download(url, user_agent, num_retries=2, prox=None):
    """Download the page html in text
    """
    if not ('http' in url): # not
        print('The web pag must contain http:..')
        return None
    else:

        try:
            html = requests.get(url, headers={'User-agent': user_agent}, proxies=prox)
            if  html:
                html.raise_for_status()  # Raise error when the content can't be read
                html = html.content
            else:
                html = None

        except (RequestException, HTTPError, ConnectionError, ConnectTimeout) as e:
            print('Download error:', e.response.status_code)

            html = None
            if num_retries > 0:
                if hasattr(e, 'response') and 500 <= e.response.status_code < 600:
                        # hasattr return True if the object (e, in our case) contain the atributte 'code'
                        # recursively retry 5xx HTTP errors
                    return download(url, num_retries - 1)
        return html


def get_links(html, start_url):
    all_links = set()
    tree = fromstring(html)
    for link in tree.xpath('//a/@href'):
        # print(link )

        if link and re.match("[^#`].*", link):

            link = urljoin(start_url, link)
            #print(link)
            if re.search(r'(.+/c/esika\-\d{2}.+page\=.+)', link) or re.match(r'.+/(?:c|p)/(?:esika-\d{2}$|\d+)',link):

            #if  re.search(rf'{start_url}/.+/c/esika\-\d{2}.+page\=.+',link): # re.match(rf'^{start_url}/.*/(?:c|p)/(?:esika-\d{2}$|\d+)',link) or:
                # re.match(rf'^{start_url}.*', link) or

                link = link.rstrip('/')
                all_links.add(link)

    return all_links

def link_crawler(start_url, user_agent, prox=None, minutes=5): # link_regex
    """ Crawl from the given start URL following links matched by link_regex
    """
    crawl_queue = [start_url]
    none_type = type(None)
    time_init = time.time()
    critic_time = 30
    seen_intermediate = {start_url}
    seen_final = set()
    time_final = time.time()

    while crawl_queue and (time.time() - time_final) < minutes*60:
        index_crawl = np.random.randint(0, len(crawl_queue))
        url = crawl_queue.pop(index_crawl)
        html = download(url, user_agent, prox)
        actual_time = (time.time() - time_init)

        print(len(crawl_queue), end='\r')

        if actual_time < critic_time:

            if not isinstance(html, none_type):
                all_links = get_links(html, start_url)
                if all_links:
                    all_links_remain = all_links.difference(seen_intermediate.union(seen_final))

                    for link in list(all_links_remain):

                        if re.search(rf"({start_url}/.+/p/\d+$)", link):
                            # crawl_queue.append(link)
                            seen_final.add(link)
                            # print("Ratio Seen/Queve", len(seen_final)/len(crawl_queue), end='\r')
                            # print(link)
                        else :
                            crawl_queue.append(link)
                            seen_intermediate.add(link)
                else:
                    pass


        else:
            print('Sleeping 2 seconds', end='\r')
            time.sleep(2)
            time_init = time.time()

    return seen_final

def data_by_product(link:str, user_agent='Mozilla/5.0') -> dict:
    # link = r'https://esika.tiendabelcorp.com/pe/delineador-de-ojos-punta-plumon-eye-pro/p/200108655'
    data_dict = {}

    link_window = Path(link)
    #path_init = Path()

    #if  not (path_init / 'DataLinks').exists():
    #    (path_init / 'DataLinks').mkdir()
    #else:
    #    if not (path_init/'DataLinks'/f'{link_window.name}.json').exists():
    #        html_page = download(link,user_agent)
    #        with open(path_init/'DataLinks'/f'{link_window.name}.json', 'w') as writer:
    #            json.dump({link_window.name : html_page},writer)
    #            print("The file is old", end = '\r')
    #    else:

    #        with open(path_init / 'DataLinks' / f'{link_window.name}.json', 'r') as reader:
    #            html_page = reader.read()
    #            print("The file is new", end = '\r')

    html_page = download(link, user_agent)

    tree = fromstring(html_page.decode())

    # Precios
    # ------

    xpath_precio = "//span[@class = 'old-price' or @class = 'active-price' ]"

    for child in tree.xpath(xpath_precio):
        if (child.get('class')) and (child.text):
            data_dict[child.get('class')] = re.sub(r'([S/ ]{,3})(.*)', r'\2', child.text)

    data_dict['Code'] = link_window.name

    # Title
    xpath_title = '//textarea'
    for child in tree.xpath(xpath_title):
        data_dict['Title'] = child.attrib['data-product']

    # Imagen

    #data_img = np.NaN
    img_list = []
    if tree.xpath("//img"):

        for child in tree.xpath("//img"):
            if child.get('src'):
                if re.search(r".+(https://belc.+jpg).*", child.get('src')):
                    data_img = re.search(r".+(https://belc.+jpg).*", child.get('src')).group(1)
                    img_list.append(data_img)

    data_dict['Imagen'] = img_list

    # Colors

    xpath_color = '//*[@id="pdp-variant-list"]/li//div[contains(@style,"background")]'
    color_list = []
    if tree.xpath(xpath_color):
        for child in tree.xpath(xpath_color):
            if re.search(r'(.*\:)(.*?(?=\;))', child.attrib['style']):
                color_rbg = re.search(r'(.*\:)(.*?(?=\;))', child.attrib['style']).group(2)
                color_list.append(color_rbg)

    data_dict['Color'] = color_list

    data_category = np.NAN
    if tree.xpath('//main'):

        for child in tree.xpath('//main//div//input'):

            if child.get('name'):
                if re.search(r'([a-z]+)',child.get('name'), re.I).group(1) == 'category':
                    data_category = re.search(r'([a-z]+)', child.get('value'), re.I).group(1)
                    data_category = data_category.lower()

                # print(child.get('name'), )
    data_dict['category'] = data_category

    return data_dict

def download_data_pages(link):

    link_window = Path(link)
    path_init = Path()

    if not (path_init / 'DataPages').exists():
        (path_init / 'DataPages').mkdir()
    else:
        if not (path_init / 'DataPages' / f'{link_window.name}.json').exists():
            data_page = data_by_product(link)
            with open(path_init / 'DataPages' / f'{link_window.name}.json', 'w') as writer:
                json.dump(data_page, writer)

                print(f'{link_window.name} was downloaded...', end='\r')