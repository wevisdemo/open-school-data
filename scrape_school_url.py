from datetime import date
from os import makedirs
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import re, json, requests
from os import path, makedirs

scrape_date = date.today().isoformat()
INDEX_PAGE_URL = 'https://data.bopp-obec.info/emis/index.php'
ROOT_DIR = 'html/'+date.today().strftime('%Y-%m')
BASE_URL = 'https://data.bopp-obec.info/emis'
SCRAPING_URLS = {
  'general': BASE_URL+'/schooldata-view.php',
  'student': BASE_URL+'/schooldata-view_student.php',
  'staff': BASE_URL+'/schooldata-view.php',
  'computer_internet': BASE_URL+'/schooldata-view_com-internet.php',
  'building': BASE_URL+'/schooldata-view_bobec.php',
  'durable_goods': BASE_URL+'/schooldata-view_mobec.php?'
}

SCRAPED_FILE_DIRS = {}

for d in SCRAPING_URLS:
  scrape_dir = ROOT_DIR+'/'+d
  SCRAPED_FILE_DIRS[d] = scrape_dir

SCHOOL_DATA_FEILDS = list(SCRAPING_URLS)

def init_directorys():
  for dir in SCRAPED_FILE_DIRS.values():
    makedirs(dir, exist_ok=True)
  pass

def params_in_url(url) -> List[Tuple]:
  """
  split url and find paramiters in it
  """
  params = url[(url.find('?')+1):]
  if not params: return []
  params = params.split('&')
  params = [tuple(param.split('=', maxsplit=1)) for param in params]
  return params

def scrape_url(url, file_path):
  """
  scrape provided url and write it to file_path
  """
  response = requests.get(url)
  scrape_date = date.today().isoformat()
  
  metadata = {
    'url': url,
    'scrape_date': scrape_date
  }

  write_scraped_url(
    response.content.decode('utf-8'),
    file_path,
    metadata,)

  return {
    'file_path': file_path,
    'content': response.content.decode('utf-8')
  }

def write_scraped_url(content: str, file_path: str, metadata: Dict):
  """
  write response content to file_path and add metadata to the file
  """
  with open(file_path, 'w') as f:
    f.write(f'<!--\n')
    for key, value in metadata.items():
      f.write(f'\t{key}: {value}\n')
    f.write(f'-->\n')
    f.write(content)

def select_for_name(options: List) -> str:
  """
  if the option is selected as default then consider it as select name
  """
  for option in options:
    if 'selected' in option.attrs.keys():
      return option.get_text()
  return ''

def is_path_existed(file_path):
  return path.exists(file_path)

def load_school_data(school_id: str, params_dict: Dict={}, only=[], force=False):
  """
  load the school data by 10 digits school id. If they exis on the local
  then it will load from the local storage, or else it will scrape to
  the local storage

  params:
    - school_id 10 digits school id
  """
  data = {}
  params = {f: '' for f in SCHOOL_DATA_FEILDS}

  if params_dict:
    params.update(params_dict)
  
  init_directorys()
  for feild in SCHOOL_DATA_FEILDS:
    if only and feild not in only: continue
    html_file_path = f'{SCRAPED_FILE_DIRS[feild]}/{school_id}.html'
    if is_path_existed(html_file_path) and not force:
      pass
    else:
      feild_params = params[feild]
      if feild_params and feild_params[0] != '?':
        feild_params = '?'+feild_params
      if not feild_params:
        feild_params = f'?School_ID={school_id}'
      url = SCRAPING_URLS[feild] + feild_params
      scrape_url(url, html_file_path)
    data[feild] = html_file_path
  return data

def load_soup(file_path):
  assert is_path_existed(file_path)

  with open(file_path, 'r') as file:
    return BeautifulSoup(file.read(), 'html.parser')

def find_lat_lng(html_content):
  """
  find latitude and longtitude in the html page
  """
  school_lat_lng_re = f'LatLng\((\d+\.\d+,\s*\d+\.\d+)\)'
  re.findall(school_lat_lng_re, html_content)

class SchoolDataIndex:
  def __init__(self,):
    self.data = {}
    self.dir = '.'
    self.file_name = 'school_list_index.json'
    self.load()

  def load(self):
    with open(self.dir+'/'+self.file_name, 'r') as index_file:
      self.data = json.load(index_file)

  def save(self):
    with open(self.dir+'/'+self.file_name, 'w') as index_file:
      json.dump(self.data, index_file, ensure_ascii=False, indent=2)

  def __getitem__(self, key):
    return self.data[key]
  
  def __setitem__(self, key, val):
    self.data[key] = val
    self.save()

  def __iter__(self):
    for school_id in self.data:
      yield self.data[school_id]

  def school_ids(self):
    for province_id in self.data:
      schools = self.data[province_id]['schools']
      for school in schools:
        for param, value in params_in_url(school['href']):
          if param == 'School_ID':
            yield value

  def school_datas(self):
    for school_id in self.school_ids:
      yield load_school_data(school_id)