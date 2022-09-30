import json
from json.encoder import py_encode_basestring_ascii
from random import uniform
from time import sleep
from typing import Dict
from tqdm import tqdm
from indexer import URLIndex
from utils import ROOT_DIR, SCRAPED_FILE_DIRS, is_path_existed, scrape_url

def load_json(fpath):
  with open(fpath, 'r') as fp:
    return json.load(fp)

def dump_json(obj, fpath):
  with open(fpath, 'w') as fp:
    json.dump(obj, fp, indent=1)

if __name__ == '__main__':
  url_index = URLIndex(ROOT_DIR + '/url_index.txt')
  fpath = ROOT_DIR+'/pages.json'
  pages = load_json(fpath)

  school_pages_index = {}
  si = 0

  page_iter = tqdm(pages.items())
  link_index_fp = open(ROOT_DIR + '/url_index.txt', 'a')

  def scrape_pages(school_id: str, pages: Dict[str, str]):
    """
    except "general" page
    """
    school_scraped = {}
    for page in pages:
      if page == 'general': continue
      page_iter.desc = school_id + ' ' + page

      url = pages[page]
      fpath = SCRAPED_FILE_DIRS[page] + '/' +school_id + '.html'
      if not is_path_existed(fpath):
        try:
          scrape_url(url, fpath)
        except ValueError as e:
          print(e)
          continue
        sleep_for = uniform(0.3, 1)
        sleep(sleep_for)
      link_index_fp.write(url + '\t' + fpath + '\n')
      school_scraped[page] = fpath
    return school_scraped

  for sch_id, urls in page_iter:
    school_pages_index[sch_id] = scrape_pages(sch_id, urls)
    si += 1

    if page_iter.n % 20 == 0:
      dump_json(school_pages_index, ROOT_DIR + '/school_pages_index.json')
    
  link_index_fp.close()
  dump_json(school_pages_index, ROOT_DIR + '/school_pages_index.json')
