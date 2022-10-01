from province import province_school_list
from utils import *
from tqdm import tqdm
from indexer import Index

area_index = Index(ROOT_DIR + '/area_index.txt')
obec_url_index = Index(ROOT_DIR + '/obec_url_index.txt')
building_index = Index(ROOT_DIR + '/building_index.txt')
index_page_path = 'buidling.html'
index_page_url = 'https://bobec.bopp-obec.info/build_show.php'
parent_url = re.sub('[^/]*$', '', index_page_url)

class SchoolScraper:
  def __init__(self) -> None:
    pass

  def __call__(self, id, data):
    fpath = (SCRAPED_FILE_DIRS['building'] + '/obec_' + id + '.html')
    url = parent_url + data['href']
    if obec_url_index[url] is not None:
      print('existed')
      building_index[id] = fpath
    else:
      scrape_url(url, fpath)
      building_index[id] = fpath
      self.sleep()
      obec_url_index[url] = fpath
    return fpath, url

  def sleep(self):
    sleep_for = uniform(0.3, 1)
    print('sleeping..', sleep_for)
    sleep(sleep_for)

if __name__ == '__main__':
  building_schools = list()
  scraper = SchoolScraper()

  if not is_path_existed(index_page_path):
    page = scrape_url(index_page_url, index_page_path)
  soup = load_soup(index_page_path)
  select = soup.find('select')
  if select is None: exit()

  url_pages = []
  for option in select.find_all('option'):
    if option.attrs['value'] == '0': continue
    url_pages.append(option.attrs['value'])

  area_dir = HTML_ROOT_DIR + '/' + 'area'
  makedirs(area_dir, exist_ok=True)
  for page in tqdm(url_pages, 'areas'):
    url = parent_url + page
    params = params_in_url(url)
    if not params: continue
    area_code = params[0][1]
    fpath = area_dir + '/' + area_code + '.html'
    if area_index[area_code] is None:
      scrape_url(url, fpath)
      sleep(uniform(0.3, 1))
      area_index[area_code] = fpath
  
  building_school_fpath = ROOT_DIR + '/obec_schools_index.json'

  if not is_path_existed(building_school_fpath):
    for acode, fpath in tqdm(area_index, 'school in area'):
      building_schools += province_school_list(fpath)

    with open(building_school_fpath, 'w') as fp:
      json.dump(building_schools, fp, ensure_ascii=False, indent=1)
  else:
    with open(building_school_fpath, 'r') as fp:
      building_schools = json.load(fp)
  slen = len(building_schools)
  for i, school in enumerate(building_schools):
    print(f'[{i}/{slen}]',school['ชื่อโรงเรียน'])
    scraper(school['รหัส percode'], school)
  

  