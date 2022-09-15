from utils import *
import re
from tqdm import tqdm

def select_for_name(options: List) -> str:
  for option in options:
    if 'selected' in option.attrs.keys():
      return option.get_text()
  return ''

def parse_table(table_soup):
  thead = table_soup.find('thead')
  assert len(thead) > 0
  headers = [head.text for head in thead.find_all('th')]

  table_data = []

  for row in table_soup.find('tbody').find_all('tr'):
    row_tds = row.find_all('td')
    assert len(row_tds) == len(headers)
    row_data = {}
    for col, td in zip(headers, row.find_all('td')):
      row_data[col.strip()] = td.text.strip()
      a_tag = td.find('a')
      if a_tag is not None:
        row_data['href'] = a_tag.attrs['href']
    table_data.append(row_data)
  return table_data

def province_school_list(file_path):
  soup = load_soup(file_path)

  for table in soup.find_all('table'):
    if table.find('table'): continue
    thead = table.find('thead')
    if thead is not None:
      break
  
  assert table

  table_data = parse_table(table)
  return table_data

def reshape_school_data_table(list_of_school):
  new_school_data = {}
  for school in list_of_school:
    added = False
    for key, val in params_in_url(school['href']):
      if key == 'School_ID':
        if val in new_school_data.keys(): print('DUPLICATED SCHOOL ID')
        new_school_data[val] = school
        added = True
        break
    if not added:
      print(school)
  return new_school_data

if __name__ == '__main__':
  sdi = SchoolDataIndex()
  province_root_dir = f'{HTML_ROOT_DIR}/province'
  index_html_path = f'{province_root_dir}/index.html'
  index_url = 'https://data.bopp-obec.info/emis/index.php'
  parent_url = re.sub('[^/]*$', '', index_url)
  if not is_path_existed(index_html_path):
    scrape_url(index_url, index_html_path)

  soup = load_soup(index_html_path)

  province_select_name: str = 'จังหวัด/ศธจ.'
  province_url_param: str = 'province'
  provinces: List[Dict] = list()

  for select_tag_soup in soup.find_all('select'):
    options = select_tag_soup.findAll('option')
    select_tag_for = select_for_name(options=options)
    if select_tag_for != province_select_name:
      continue

    for option in options:
      if 'value' not in option.attrs.keys() or not option.attrs['value']:
        continue

      key_name = re.sub('\s*\d+\s*\.\s*', '', option.text)
      value = option.attrs['value']
      # re.findall('province=(.*)&?', value)
      province_id = re.findall(f'{province_url_param}=(.*)&?', value)
      params = re.sub('^.*\?', '', value)
      province = {'name': key_name,'url': parent_url+'school_edu_p.php'+f'?{params}', 'id': province_id[0]}
      sdi.add_province(province_id[0], province)
      # provinces.append({'name': key_name,'url': parent_url+'school_edu_p.php'+f'?{params}', 'id': province_id[0]})

  # download all province web page
  for province in tqdm(sdi):
    file_path = SCRAPED_FILE_DIRS['province']+'/'+province['id']+'.html'
    province['html_file_path'] = file_path
    if not is_path_existed(file_path):
      print(province['url'])
      scrape_url(province['url'], file_path)
    
    school_list = province_school_list(province['html_file_path'])
    school_list = reshape_school_data_table(school_list)
    sdi.add_schools(province['id'], school_list.keys(), school_list.values())

    # province['schools'] = reshape_school_data_table(school_list)
  
  sdi.save()
  
