import json
from os import makedirs, system
from typing import Dict
from utils import ROOT_DIR, SCRAPED_FILE_DIRS, SchoolDataIndex, load_soup, pages_in_general_page, get_school_soup
from tqdm import tqdm

if __name__ == '__main__':
  sdi = SchoolDataIndex()
  pages: Dict = dict()
  file_path: str = ROOT_DIR + '/general_page_index.txt'
  general_index = {}

  with open(file_path, 'r') as file_pointer:
    for line in file_pointer.readlines():
      s_id, s_fpath  = line.split('\t', maxsplit=1)
      general_index[s_id] = s_fpath.strip()

  gen_dir: str = SCRAPED_FILE_DIRS['general']
  makedirs(gen_dir + '/dump', exist_ok=True)

  for sch_id, file_path in general_index.items():
    soup = load_soup(file_path)
    if soup is None:
      print('moved', file_path)
      system('mv '+ file_path + ' ' + gen_dir + '/dump/')
    else:
      pages[sch_id] = pages_in_general_page(soup)

  with open(ROOT_DIR + '/pages.json', 'w') as file_pointer:
    json.dump(pages, file_pointer, ensure_ascii=False, indent=1)