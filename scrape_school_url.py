from datetime import date
from os import makedirs
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import re, json, requests

scrape_date = date.today().isoformat()
INDEX_PAGE_URL = 'https://data.bopp-obec.info/emis/index.php'
ROOT_DIR = f'html/{scrape_date}'

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