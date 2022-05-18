# -----------------------------------------------------------------------
# --------------------------- Projects ----------------------------------
# -----------------------------------------------------------------------


from urllib.parse import urljoin, urlparse
import requests
from requests import RequestException, HTTPError, ConnectionError, ConnectTimeout
import json
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from lxml.html import fromstring, tostring
from pathlib import Path
from urllib import robotparser
import time
import utils

target_site = 'https://esika.tiendabelcorp.com/pe'

# We must add /robots.txt
robots_site = target_site + '/robots.txt'
user_agent = 'Mozilla/5.0'

utils.get_robotparser(user_agent, target_site)

response = requests.get(target_site)

len(set(utils.get_links(response.text,target_site )))
len(set(utils.get_links_1(response.text)))
utils.get_links(response.text, target_site)

links_inter = 'https://esika.tiendabelcorp.com/pe/maquillaje/ojos/delineador/c/esika-010202'
links_obs = "https://esika.tiendabelcorp.com/pe/delineador-de-ojos-punta-plumon-eye-pro/p/200108655"
re.search(r"(https://esika.tiendabelcorp.com/pe/.+/p/\d+$)",links_inter ) #.group(1)

path_esika = r'https://esika.tiendabelcorp.com/pe'

response = requests.get(path_esika)
tree = fromstring(response.text)


def func_res(link: str):
    """
    :param link:
    :return: page bs4 class
    """
    response = requests.get(link)
    if response.status_code == 200:
        page = BeautifulSoup(response.content, 'html5lib')
        return page


def comp_link_func(link: str) -> list:
    """
    This function search the header and get the 3 different
    links where each one is a different cat

    :param link:
    :return: list of links
    """
    page = func_res(link)
    components_links = []
    for div in page.find('div', attrs={'class': 'yCmsComponent yComponentWrapper'}):
        if div.name == 'a':
            if div.get('href'):
                components_links.append(div.get('href'))
    return components_links


def head_link_func(link: str) -> list:
    """
    This function get the groups of product

    :param link:
    :return: list of links
    """

    head_links = []
    response = requests.get(link)
    tree = fromstring(response.text)
    path_init = '//html/body/main/div/header/div[4]/nav/div/div[2]/ul//div[@class="yCmsComponent js_nav__link"]//a'

    for child in tree.xpath(path_init):

        link_new = urljoin(link, child.attrib['href'])
        head_links.append(link_new)

    return head_links


def link_favo_func(link:str)-> list:
    """
    This function saves all links fo favourite products

    :param link:
    :return:
    """
    page = func_res(link)
    s = set()

    for element in page.find('h2').next_elements:
        if element.name == 'h2':
            print(element.text)
            break
        if element.name == 'a':
            if element.get('href') and (element.get('href') != '#'):
                mid_link = element.get('href')
                # aylis = w.get('href')
                link_com = urljoin(path_esika, mid_link)
                s.add(link_com)
    return list(s)


def link_pagination_by_head(link:str)->list:

    links_pagion = set()

    response = requests.get(link)
    tree = fromstring(response.text)
    path_init = '/html/body/main/div[4]/div/div[2]/div/div/div[4]/div/ul/li//a'
    for child in tree.xpath(path_init):

        link_ion = urljoin(link,child.attrib['href'])

        links_pagion.add(link_ion)

    return list(links_pagion)


def data_by_product(link:str, head:str) -> dict:
    # link = r'https://esika.tiendabelcorp.com/pe/delineador-de-ojos-punta-plumon-eye-pro/p/200108655'
    data_dict = {}

    # Precios

    link_window = Path(link)
    path_init = Path()

    if  not (path_init / 'DataPage').exists():
        (path_init / 'DataPage').mkdir()
    else:
        if not (path_init/'DataPage'/f'{link_window.name}.json').exists():
            response = requests.get(link)
            response_text = response.text
            with open(path_init/'DataPage'/f'{link_window.name}.json', 'w') as writer:
                json.dump({link_window.name : response_text},writer)
        else:

            with open(path_init / 'DataPage' / f'{link_window.name}.json', 'r') as reader:
                response_text = reader.read()

    tree = fromstring(response_text)

    xpath_precio = '/html/body/main/div[3]/div[1]/div/div[3]/div[2]/div[2]/ul/li/div/div/span'

    for child in tree.xpath(xpath_precio):
        if 'separator' not in child.attrib['class']:

            data_dict[child.attrib['class']] = re.sub(r'([S/ ]{,3})(.*)', r'\2', child.text)

    data_dict['Code'] = link_window.name

    # Title
    xpath_title = '/html/body/main/div[3]/div[1]/div/div[3]/div[1]/h1'

    for child in tree.xpath(xpath_title):
        data_dict['title'] = child.text.lstrip('\n')

    # Imagen

    xpath_image = r'/html/body/main/div[3]/div[1]/div/div[2]/div[1]/ul[@id="productGalleryThumbnails"]//img'
    data_img = np.NaN
    if tree.xpath(xpath_image):

        for child in tree.xpath(xpath_image):

            if re.search(r'(.*)(https://belc.*fondo[- ]{0,1}blanco.*.jpg)', child.attrib['data-src'], re.I):
                data_img = re.search(r'(.*)(https://belc.*fondo[- ]{0,1}blanco.*.jpg)', child.attrib['data-src'], re.I).group(2)

    else:
        pass
    data_dict['Imagen'] = data_img

    # Colors

    tree = fromstring(response_text)
    xpath_color = '//*[@id="pdp-variant-list"]/li//div[contains(@style,"background")]'
    color_list = []
    if tree.xpath(xpath_color):
        for child in tree.xpath(xpath_color):
            color_rbg = re.search(r'(.*\:)(.*?(?=\;))', child.attrib['style']).group(2)
            color_list.append(color_rbg)

    else:
        color_list = np.NAN

    data_dict['Color'] = color_list

    if re.search(r".*\/pe\/(.*)\/c\/.*", head):
        data_dict['Head'] = re.search(r".*\/pe\/(.*)\/c\/.*", head).group(1)
    else:
        data_dict['Head'] = np.NAN

    return data_dict


def link_products_page(link:str)->list:
    """
    This function retrieves a list of products by page

    :param link:
    :return:
    """
    response = requests.get(link)
    tree = fromstring(response.text)
    path_init = '//div[@class="product__listing product__grid"]/div//div[@class="inner-card"]//a'
    lpp = set()
    for child in tree.xpath(path_init):
        links_ptus = urljoin(link, child.attrib['href'])
        links_ptus = links_ptus.rstrip('/')
        lpp.add(links_ptus)
    return list(lpp)

import time

time_init = time.time()
path_esika = r'https://esika.tiendabelcorp.com/pe'
megalist = []

for head in head_link_func(path_esika):
    lppages = link_products_page(head)
    #print(lppages)
    for lph in link_pagination_by_head(head):
        lppages_pgion = link_products_page(lph)
        lppages.extend(lppages_pgion)

    for lp in lppages:
        data_lp = data_by_product(lp, head)
        megalist.append(data_lp)

print((time.time() - time_init)/60)


# data for mongodb
###################################################################
final_list = []

for product in megalist:
    de = product.copy()
    current_product = product.items()
    for key, value in current_product:
        #print(value, key)

        # print(value)
        try:
            if np.isnan(value):
                del de[key]
        except:
            print(key, value)
    final_list.append(de)

import json

with open('products.json','w') as writer:
    json.dump(final_list, writer)
##################################################################3

data_final = pd.DataFrame()

for k_list in megalist:
    try:
        df = pd.DataFrame.from_dict(k_list)
        data_final = pd.concat([data_final, df], ignore_index=True)
    except:
        df = pd.Series(k_list).to_frame().T
        data_final = pd.concat([data_final, df], ignore_index=True)


data_final.columns = data_final.columns.str.lower().str.replace('-', '_')
data_final = data_final.rename(columns={'code':'code_num'})
data_final.to_csv(r'data_products.csv', index=False)



#####################################
#####################################3

response = requests.get(path_esika)
tree = fromstring(response.text)
path_init = '//html/body/main/div/header/div[4]/nav/div/div[2]/ul//div[@class="yCmsComponent js_nav__link"]//a' # /div/div/ul/li*'

for child in tree.xpath(path_init):
    #print(child.tag)
    #print(child.attrib['href'])
    # print(child.find(''))
    # print(child.find_all(''))
    print(urljoin(path_esika, child.attrib['href']))
