from datetime import date
from os import makedirs
import os
from random import randrange, uniform
from time import sleep
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup
import re
import json
import requests
from os import path, makedirs
from helpers.indexer import Index
from helpers.exeptions import *

INDEX_PAGE_URL = 'https://data.bopp-obec.info/emis/index.php'

ROOT_DIR = 'out/' + '2022'#date.today().strftime('%Y')
HTML_ROOT_DIR = ROOT_DIR+'/html'
BASE_URL = 'https://data.bopp-obec.info/emis'
SCRAPING_URLS = {
    'general': BASE_URL + '/schooldata-view.php',
    'student': BASE_URL + '/schooldata-view_student.php',
    'staff': BASE_URL + '/schooldata-view_techer.php',
    'computer_internet': BASE_URL + '/schooldata-view_com-internet.php',
    'building': BASE_URL + '/schooldata-view_bobec.php',
    'durable_goods': BASE_URL + '/schooldata-view_mobec.php'
}

SCRAPED_FILE_DIRS = {}
for d in SCRAPING_URLS:
    scrape_dir = HTML_ROOT_DIR+'/school/'+d
    SCRAPED_FILE_DIRS[d] = scrape_dir
SCRAPED_FILE_DIRS['province'] = HTML_ROOT_DIR+'/province'

SCHOOL_DATA_FEILDS = list(SCRAPING_URLS)

url_index = Index(os.path.join(ROOT_DIR, 'url_index.txt'))

def load_json(fpath):
  with open(fpath, 'r') as fp:
    return json.load(fp)


def dump_json(obj, fpath):
  with open(fpath, 'w') as fp:
    json.dump(obj, fp, ensure_ascii=False, indent=1)


def prep_param_dict(soup: BeautifulSoup) -> Dict[str, str]:
    """
    prepare paramater dictionary for loading school data

    """
    interested_urls: Dict = {
        key: re.sub('^.*/', '', val)
        for key, val in SCRAPING_URLS.items()
    }
    param_dict: Dict = dict()
    for anchor in soup.find_all('a'):
        topic = [kurl for kurl, iurl in interested_urls.items()
                 if iurl in anchor.attrs['href']]
        if topic:
            param_dict[topic[0]] = re.sub('^.*\?', '', anchor.attrs['href'])
    return param_dict


def pages_in_general_page(soup):
    interested_urls: Dict = {
        key: re.sub('^.*/', '', val)
        for key, val in SCRAPING_URLS.items()
    }

    url_dict: Dict = dict()

    for anchor in soup.find_all('a'):
        topic = [
            kurl for kurl, iurl in interested_urls.items()
            if iurl in anchor.attrs['href']
        ]
        if topic:
            url_dict[topic[0]] = BASE_URL + '/' + anchor.attrs['href']
    return url_dict


def clean_text(string: str) -> str:
    """
    clean string, removing excess white space
    """
    trim_re = r'[\:\s]*$'
    string = string.strip()
    string = re.sub(trim_re, '', string)
    string = re.sub('\s+', ' ', string)
    return string


def init_directories() -> None:
    """
    initiate directories
    """
    for dir in SCRAPED_FILE_DIRS.values():
        makedirs(dir, exist_ok=True)


def params_in_url(url) -> List[Tuple]:
    """
    split url and find paramiters in it
    """
    params = url[(url.find('?')+1):]
    if not params:
        return []
    params = params.split('&')
    params = [tuple(param.split('=', maxsplit=1)) for param in params]
    return params


def download_image(image_url: str, image_file_dir: str):
    """
    download image form `image_url` to the `image_file_dir` with the same name
    as the original image
    """
    image_file_image_re = r'(.*/|\?.*)'
    image = requests.get(image_url).content
    image_file_name = re.sub(image_file_image_re, '', image_url)
    image_file_path = image_file_dir+'/'+image_file_name
    if not is_path_existed(image_file_path):
        with open(image_file_path, 'wb') as im_file:
            im_file.write(image)

    return image_file_path


def scrape_url(url, file_path) -> Dict:
    """
    scrape provided url and write it to file_path
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise StatusCodeException(
            f' {url} status code is {response.status_code}')
    scrape_date = date.today().isoformat()

    init_directories()

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


def is_path_existed(file_path) -> bool:
    """
    Check if the path is existed
    """
    return path.exists(file_path)


def load_building_data(school_id):
    url = 'https://bobec.bopp-obec.info/build_sch_view.php?Obec_code=' + school_id
    html_file_path = f'{SCRAPED_FILE_DIRS["building"]}/{school_id}.html'
    if not is_path_existed(html_file_path):
        scrape_url(url, html_file_path)
    return {"building": html_file_path}


def load_school_data(school_id: str, params_dict: Dict = {}, only=[], force=False):
    """
    load the school data by 10 digits school id. If they exis on the local
    then it will load from the local storage, or else it will scrape to
    the local storage

    params:
      - `school_id 10` digits school id
    """
    data = {}
    params = {f: '' for f in SCHOOL_DATA_FEILDS if not only or f in only}

    if params_dict:
        params.update(params_dict)

    init_directories()
    for feild in SCHOOL_DATA_FEILDS:
        if feild == 'building':
            data.update(load_building_data(school_id[4:]))
            sleep(uniform(0.4, 3))
            continue
        if only and feild not in only:
            continue
        html_file_path = f'{SCRAPED_FILE_DIRS[feild]}/{school_id}.html'
        if is_path_existed(html_file_path) and not force:
            print(html_file_path, 'already existed')
        else:
            feild_params = params[feild]
            if feild_params and feild_params[0] != '?':
                feild_params = '?'+feild_params
            if not feild_params:
                feild_params = f'?School_ID={school_id}'
            url = SCRAPING_URLS[feild] + feild_params
            scrape_url(url, html_file_path)
            sleep(uniform(0.5, 2))
        data[feild] = html_file_path
    return data


def load_soup(file_path):
    """
    Load html beautifulsoup from `file_path`
    """
    assert is_path_existed(file_path), file_path + ' not existed'

    with open(file_path, 'r') as file:
        file_html = file.read()
        soup = BeautifulSoup(file_html, 'html.parser')
        if soup.find('html') is None:
            return None
    return soup


def find_lat_lng(html_content):
    """
    find latitude and longtitude in the html page
    """
    school_lat_lng_re = f'LatLng\((\d+\.\d+,\s*\d+\.\d+)\)'
    re.findall(school_lat_lng_re, html_content)


def get_school_soup(school_id, page):
    if page not in SCRAPING_URLS.keys():
        raise ValueError(f'{page} not in ' + str(SCRAPING_URLS.keys()))
    file_path = SCRAPED_FILE_DIRS[page] + '/' + school_id + '.html'
    if is_path_existed(file_path):
        return load_soup(file_path)
    return None


class SchoolDataIndex:
    def __init__(self):
        self.data = {}
        self.dir = ROOT_DIR
        self.file_name = 'school_data_index.json'
        self.file_path = self.dir+'/'+self.file_name
        self.data = None

    def add_province(self, province_id, data):
        if self.data is None:
            self.load()
        self.data[province_id] = data
        data['schools'] = {}

    def add_school(self, province_id, school_id: str, data: Dict):
        if self.data is None:
            self.load()
        if province_id not in self.data.keys():
            self.add_province(province_id)
        self.data[province_id]['schools'][school_id] = data

    def add_schools(self, province_id, school_ids: List[str], datas: List):
        if self.data is None:
            self.load()
        assert len(school_ids) == len(datas)
        for school_id, data in zip(school_ids, datas):
            self.add_school(province_id, school_id, data)

    def load(self):
        if not is_path_existed(self.file_path):
            self.data = dict()
            return
        with open(self.file_path, 'r') as index_file:
            self.data = json.load(index_file)

    def save(self):
        dump_json(self.data, self.dir+'/'+self.file_name)

    def __getitem__(self, key):
        if self.data is None:
            self.load()
        return self.data[key]

    def get_school(self, key):
        if self.data is None:
            self.load()
        for province_id in self.data:
            if key in self.data[province_id]['schools'].keys():
                return self.data[province_id]['schools'][key]
        raise KeyError()

    def __setitem__(self, key, val):
        if self.data is None:
            self.load()
        self.data[key] = val

    def __iter__(self):
        if self.data is None:
            self.load()
        for province_id in self.data:
            yield self.data[province_id]

    def __len__(self):
        if self.data is None:
            self.load()
        return len(self.data.keys())

    def school_ids(self):
        if self.data is None:
            self.load()
        for province_id in self.data:
            schools: Dict = self.data[province_id]['schools']
            for school in schools.keys():
                yield school

    def schools(self):
        if self.data is None:
            self.load()
        for province_id in self.data:
            schools: Dict = self.data[province_id]['schools']
            for id, data in schools.items():
                yield id, data

    def school_datas(self):
        if self.data is None:
            self.load()
        for school_id in self.school_ids:
            yield load_school_data(school_id)
