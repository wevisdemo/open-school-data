import json
from random import uniform
from time import sleep
from tkinter import W
from typing import Dict
from tqdm import tqdm
from helpers.indexer import Index
from utils import ROOT_DIR, SCRAPED_FILE_DIRS, dump_json, load_json, scrape_url


if __name__ == '__main__':
  url_index = Index(ROOT_DIR + '/url_index.txt')
  gen_index = Index(ROOT_DIR + '/general_page_index.txt')
  bui_index = Index(ROOT_DIR + '/building_index.txt')
  fpath = ROOT_DIR + '/pages.json'
  pages = load_json(fpath)

  school_pages_index = {}
  si = 0

  page_iter = tqdm(pages.items())

  def scrape_pages(school_id: str, pages: Dict[str, str]):
    school_scraped = {}
    for page in pages:
      if page == 'general' or page == 'building': continue
      page_iter.desc = school_id

      url = pages[page]
      fpath = SCRAPED_FILE_DIRS[page] + '/' +school_id + '.html'
      if url_index[url] is None:
        try:
          scrape_url(url, fpath)
        except ValueError as e:
          print(e)
          continue
        sleep_for = uniform(0.3, .6)
        sleep(sleep_for)
      url_index[url] = fpath
      school_scraped[page] = fpath
    return school_scraped

  for sch_id, urls in page_iter:
    temp = scrape_pages(sch_id, urls)
    temp.update({
      'general': gen_index[sch_id],
    })
    school_pages_index[sch_id] = temp
    del temp
    si += 1

  dump_json(school_pages_index, ROOT_DIR + '/school_pages_index.json')
