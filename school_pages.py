import json
from os import makedirs, system
from typing import Dict
from indexer import Index
from utils import ROOT_DIR, SCRAPED_FILE_DIRS, SchoolDataIndex, load_soup, pages_in_general_page
from tqdm import tqdm

general_index = Index(ROOT_DIR + '/general_page_index.txt')

if __name__ == '__main__':
    pages: Dict = dict()

    gen_dir: str = SCRAPED_FILE_DIRS['general']
    makedirs(gen_dir + '/dump', exist_ok=True)

    for sch_id, file_path in tqdm(general_index):
        try:
            soup = load_soup(file_path)
        except AssertionError as e:
            print(e)
            continue
        if soup is None:
            print(file_path, 'abnormal')
        else:
            pages[sch_id] = pages_in_general_page(soup)

    with open(ROOT_DIR + '/pages.json', 'w') as file_pointer:
        json.dump(pages, file_pointer, ensure_ascii=False, indent=1)
