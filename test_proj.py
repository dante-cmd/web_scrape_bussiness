import json
import utils
import time
import concurrent.futures

target_site = 'https://esika.tiendabelcorp.com/pe'
user_agent = 'Mozilla/5.0'

links_pages = utils.link_crawler(target_site, user_agent, minutes = 20)
links_pages = list(links_pages)
print(len(links_pages))

t1 = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(utils.download_data_pages, links_pages)
t2 = time.perf_counter()
print(f'Finished in {t2 - t1} seconds')

from pathlib import  Path
import pandas as pd
import numpy as np

path_json = Path().rglob('*.json')
path_json = list(path_json)

def reader_json(name_file):
    with open(name_file, 'r') as reader:
        data_json = json.load(reader)
        return data_json

kalu = [ reader_json(name_file) for name_file in path_json]
df = pd.DataFrame(kalu)
df = df.rename(columns={'active-price': 'ActivePrice', 'old-price':'OldPrice'})
df = df[['ActivePrice', 'Code', 'Title', 'category']].copy()
df['ActivePrice'] = df['ActivePrice'].astype(float).copy()
df['Quantity'] = np.random.randint(5, 500, df.shape[0])
df = df[df.category != 'l'].copy()
df.to_csv('DataScrape.csv', sep = ',', index = False)


