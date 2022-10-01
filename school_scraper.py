from random import shuffle, uniform
from indexer import Index
from utils import *

url_inex = Index(ROOT_DIR + '/url_index.txt')
gen_index = Index(ROOT_DIR + '/general_page_index.txt')


class SchoolScraper:
    def __init__(self) -> None:
        pass

    def __call__(self, id, data):
        fpath = (SCRAPED_FILE_DIRS['general'] + '/' + id + '.html')
        url = 'https://data.bopp-obec.info/emis/' + data['href']
        if url_inex[url] is not None:
            print('existed')
            gen_index[id] = fpath
        else:
            scrape_url(url, fpath)
            gen_index[id] = fpath
            self.sleep()
            url_inex[url] = fpath
        return fpath, url

    def sleep(self):
        sleep_for = uniform(0.3, 1)
        print('sleeping..', sleep_for)
        sleep(sleep_for)


if __name__ == '__main__':
    sdi = SchoolDataIndex()
    scraper = SchoolScraper()
    sch_ids = list(sdi.school_ids())
    slen = len(sch_ids)
    si = 0
    for prov in sdi:
        for sch_id, school in prov['schools'].items():
            print(f'[{si}/{slen}]', sch_id, end=' ')
            si += 1

            html_file_path, url = scraper(sch_id, school)
