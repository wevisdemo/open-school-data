import os
from random import uniform
import re
from time import sleep
from typing import List
import requests
from indexer import Index
from utils import HTML_ROOT_DIR, ROOT_DIR, load_soup
from bs4 import BeautifulSoup
from tqdm import tqdm


def writer(file_path, bin):
  fp = open(file_path, 'wb')
  fp.write(bin)
  fp.close()


def downloader(url, file_path):
  response = requests.get(url)
  if response.status_code != 200:
    raise ValueError(f'status code not 200 [{response.status_code}] [{url}]')
  writer(file_path, response.content)

def images(soup: BeautifulSoup):
  temp = []
  ims = soup.find_all('img')
  if ims:
    temp = ims
  return temp

def make_name(imurl, prefix):
  image_name = re.sub('^.*/', '', imurl)
  image_name = re.sub('\s', '_', image_name)
  return prefix + image_name
  
if __name__ == '__main__':
  index_fpath = os.path.join(ROOT_DIR, 'obec_url_index.txt')
  image_dir = os.path.join(HTML_ROOT_DIR, 'school', 'building', 'images')
  os.makedirs(image_dir, exist_ok=True)
  index = Index(index_fpath)
  image_index_fpath = os.path.join(ROOT_DIR, '.image_url_index.txt')
  image_index = Index(image_index_fpath)

  htmls = [(u, f) for u, f in index if f.endswith('.html')]

  for url, fpath in tqdm(htmls):
    if not fpath.endswith('.html'): continue
    soup: BeautifulSoup = load_soup(fpath)
    parent_url = re.sub('[^/]*$', '', url)
    school_id = re.sub('(^.*/|\..*$)', '', fpath)
    running_id = 0
    for image in images(soup):
      image_url = (parent_url + image.attrs['src'])
      pfix = f'{school_id}_{running_id}_'
      image_fpath = os.path.join(image_dir, make_name(image_url, pfix))
      running_id += 1
      image_index[image_url] = image_fpath

  for url, fpath in tqdm(image_index):
      if index[url] is not None: continue
      try:
        downloader(url, fpath)
        sleep(uniform(0.2, .6))
      except ValueError as e:
        print(e.with_traceback(e.__traceback__))
        continue
      index[image_url] = image_fpath




