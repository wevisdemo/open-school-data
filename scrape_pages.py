"""
run trough all interested pages on https://data.bopp-obec.info/emis, and save it.
"""
import os
import logging
from typing import Dict, List
from helpers.exeptions import StatusCodeException
from helpers.indexer import Index
from helpers.province import main as province_scraper
from helpers.school_scraper import SchoolScraper
from tqdm import tqdm
from helpers.utils import ROOT_DIR, SCRAPED_FILE_DIRS, SchoolDataIndex, dump_json, is_path_existed, load_json, load_soup, pages_in_general_page, url_index

sdi: SchoolDataIndex = SchoolDataIndex()

logger_fpath = os.path.join(ROOT_DIR, 'open_school_data.log')
logging.basicConfig(filename=logger_fpath)


def school_subpages(index: Index) -> Dict:
    school_url_pages_fpath: str = os.path.join(
        ROOT_DIR, 'school_url_pages.json')
    if is_path_existed(school_url_pages_fpath):
        return load_json(school_url_pages_fpath)
    pages: Dict = dict()

    gen_dir: str = SCRAPED_FILE_DIRS['general']
    os.makedirs(gen_dir + '/dump', exist_ok=True)

    for sch_id, file_path in tqdm(index):
        try:
            soup = load_soup(file_path)
        except AssertionError as e:
            logging.error(e)
            continue

        if soup is None:
            print(file_path, 'abnormal')
        else:
            pages[sch_id] = pages_in_general_page(soup)

    dump_json(pages, school_url_pages_fpath)
    return pages


def school_index_page_scraper(general_page_index: Index) -> None:
    general_page_scraper: SchoolScraper = SchoolScraper(
        SCRAPED_FILE_DIRS['general'])

    province_iter: tqdm = tqdm(sdi)
    for province in province_iter:
        for school_id, school in province['schools'].items():
            province_iter.desc = school_id
            province_iter.update()
            url = 'https://data.bopp-obec.info/emis/' + school['href']
            try:
                fpath, _ = general_page_scraper(school_id, url)
                general_page_index[school_id] = fpath
            except StatusCodeException as e:
                logging.error(e)


def subpage_scraper(school_id: str, page_urls: Dict):
    school_scraped = {}
    for page in page_urls:
        if page == 'general' or page == 'building':
            continue

        url = page_urls[page]

        scraper: SchoolScraper = SchoolScraper(SCRAPED_FILE_DIRS[page])

        if url_index[url] is None:
            try:
                page_fpath, _ = scraper(school_id, url)
            except StatusCodeException as e:
                logging.error(e)
        else:
            page_fpath = url_index[url]
            
        school_scraped[page] = page_fpath

    return school_scraped


def scrape_subpages(pages, general_page_index):
    page_file_path_index: Dict = dict()
    page_iter = tqdm(pages.items())
    for sch_id, urls in page_iter:
        temp: Dict = subpage_scraper(sch_id, urls)
        temp.update({
            'general': general_page_index[sch_id],
        })
        page_file_path_index[sch_id] = temp
    
    return page_file_path_index


def main():
    if not is_path_existed(sdi.file_path):
        province_scraper()

    general_page_index_fpath: str = os.path.join(
        ROOT_DIR, 'general_page_index.txt')
    general_page_index = Index(general_page_index_fpath)

    # scrape all school index pages
    school_index_page_scraper(general_page_index)

    # get all subpage url in school index page
    url_pages = school_subpages(general_page_index)

    # scrape all subpages
    page_file_path_index = scrape_subpages(url_pages, general_page_index)
    page_file_path_index_fpath = os.path.join(ROOT_DIR, 'school_file_path_pages.json')
    dump_json(page_file_path_index, page_file_path_index_fpath)

if __name__ == '__main__':
    main()
