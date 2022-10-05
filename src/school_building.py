import os
from src.province import province_school_list
from src.utils import *
from tqdm import tqdm
from indexer import Index

area_index = Index(ROOT_DIR + '/area_index.txt')
obec_url_index = Index(ROOT_DIR + '/obec_url_index.txt')
building_index = Index(ROOT_DIR + '/building_index.txt')
index_page_path =  os.path.join(HTML_ROOT_DIR, 'buidling.html')
index_page_url = 'https://bobec.bopp-obec.info/build_show.php'
parent_url = re.sub('[^/]*$', '', index_page_url)


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
  
  building_school_fpath = os.path.join(ROOT_DIR, 'obec_schools_index.json')

  if not is_path_existed(building_school_fpath):
    for acode, fpath in tqdm(area_index, 'school in area'):
      building_schools += province_school_list(fpath)

    dump_json(building_schools, building_school_fpath)
  else:
    building_schools = load_json(building_school_fpath)
  slen = len(building_schools)
  for i, school in enumerate(building_schools):
    print(f'[{i}/{slen}]',school['ชื่อโรงเรียน'])
    scraper(school['รหัส percode'], school)
  

  