from random import shuffle, uniform
from utils import *

class SchoolScraper:
  def __init__(self) -> None:
    pass

  def __call__(self, id, data):
    fpath = (SCRAPED_FILE_DIRS['general'] + '/' + id + '.html')
    url = 'https://data.bopp-obec.info/emis/' + data['href']
    if is_path_existed(fpath):
      print('existed')
    else:
      scrape_url(url, fpath)
      self.sleep()
    
    return fpath, url

  def sleep(self):
    sleep_for = uniform(0.3, 2.5)
    print('sleeping..', sleep_for)
    sleep(sleep_for)

if __name__ == '__main__':
  sdi = SchoolDataIndex()
  scraper = SchoolScraper()
  sch_ids = list(sdi.school_ids())
  slen = len(sch_ids)
  si = 0
  link_index_fp = open(ROOT_DIR + '/url_index.txt', 'a')
  general_index_fp = open(ROOT_DIR + '/general_page_index.txt', 'w')
  for prov in sdi:
    for sch_id, school in prov['schools'].items():
      print(f'[{si}/{slen}]',sch_id, end=' ')
      si += 1

      html_file_path, url = scraper(sch_id, school)

      link_index_fp.write(url + '\t' + html_file_path + '\n')
      general_index_fp.write(sch_id + '\t' + html_file_path + '\n')
  link_index_fp.close()
  general_index_fp.close()