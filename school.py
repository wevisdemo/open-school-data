from utils import *
import pandas as pd
import re

sdi = SchoolDataIndex()
school_ids = list(sdi.school_ids())
sd = None
school_id = None

def prep_param_dict(soup):
  interested_urls = {
    key: re.sub('^.*/', '', val)
    for key, val in SCRAPING_URLS.items()
  }
  param_dict = {}
  for anchor in soup.find_all('a'):
    topic = [kurl for kurl, iurl in interested_urls.items() if iurl in anchor.attrs['href']]
    if topic:
      param_dict[topic[0]] = re.sub('^.*\?', '', anchor.attrs['href'])
  return param_dict

def _clean_text(string: str) -> str:
  trim_re = r'[\:\s]*$'
  string = string.strip()
  string = re.sub(trim_re, '', string)
  string = re.sub('\s+',' ', string)
  return string

def download_image(image_url: str, image_file_dir: str):
  image_file_image_re = r'(.*/|\?.*)'
  image = requests.get(image_url).content
  image_file_name = re.sub(image_file_image_re,'', image_url)
  image_file_path = image_file_dir+'/'+image_file_name
  if is_path_existed(image_file_path):
    return
  #   file_ext = re.findall(image_file_extention_re, image_file_path)
  #   print(file_ext)
  #   if not file_ext: return
  #   file_ext = file_ext[0]
  #   file_name = re.sub(image_file_extention_re, '', image_file_path)
  #   image_file_path = file_name+'_'+'0'+file_ext
  with open(image_file_path, 'wb') as im_file:
    im_file.write(image)
  
  return image_file_path

def general(soup):
  about_school = []
  table = soup.find('table').find('table', attrs={'width': '521'})
  for table_row in table.find_all('tr'):
    cells = table_row.find_all('td')

    if len(cells) == 2:
      key_name = _clean_text(cells[0].text)
      value = _clean_text(cells[1].text)

      if cells[1].find_all('a'):
        value = [{
          'text': a_tag.text,
          'href': a_tag.attrs['href']}
          for a_tag in cells[1].find_all('a') if a_tag.text]
      
      about_school.append({
          'key': key_name,
          'value': value
        })
    else:
      about_school.append({'value': _clean_text(cells[0].text)})
  
  for comment in soup.children: break
  url = re.findall('url: (.*)\n', comment)[0]
  parent_url = re.sub('[^/]*$', '', url)

  image_dir = SCRAPED_FILE_DIRS['general']+'/image'

  if not is_path_existed(image_dir):
    makedirs(image_dir)

  for div in soup.find_all('div'):
    if not div.find('div'):
      if 'ผู้อำนวยการโรงเรียน' in div.text:
        dir_name = 'principal'
      elif 'ตราสัญลักษณ์' in div.text:
        dir_name = 'logo'
      else:
        continue
      image_src = div.find('img').attrs['src']
      download_image(parent_url+image_src, image_dir)

  return about_school


def student():
  # soup = load_soup(sd['student'])


  # all education year student data

  # student_data_by_edu_year_urls = []
  # for option in soup.find('select').find_all('option'):
  #   if option.attrs['value']:
  #     student_data_by_edu_year_urls\
  #       .append(parent_url+option.attrs['value'])


  # def student_table(soup):
  #   col_headers = ['ชั้น/เพศ', 'ชาย', 'หญิง', 'รวม', 'ห้องเรียน']

  #   for table in soup.find_all('table'):
  #     if table.find('table'): continue
  #     tab_col_headers = [td.text for td in table.find('tr').find_all('td')]
  #     if any([col not in tab_col_headers for col in col_headers]): continue

  #     table_row = []
  #     for row in table.find_all('tr'):
  #       cells = row.find_all('td')
  #       if not table_row or (table_row and len(cells) == len(table_row[0])):
  #         table_row.append([cell.text for cell in cells])
  #     return table_row

  return pd.read_html(sd['student'])[-1]

def staff():
  staff_df = pd.read_html(sd['staff'])[-1]
  return staff_df

def computer():
  tables = pd.read_html(sd['computer_internet'])
  return tables[5]

def internet():
  tables = pd.read_html(sd['computer_internet'])
  return tables[6]

def durable_goods():
  durable_goods_df = pd.read_html(sd['durable_goods'])[-2]
  durable_goods_df.columns = durable_goods_df.iloc[0]
  durable_goods_df  = durable_goods_df.iloc[1:, :]
  durable_goods_df.set_index('ลำดับ', inplace=True)
  return durable_goods_df.iloc[:-1]

def building():
  b_soup = load_soup(sd['building'])
  building_url = b_soup.find('iframe').attrs['src']
  parent_url = re.sub('[^/]*$', '', building_url)
  school_building_table_file_path = SCRAPED_FILE_DIRS['building']+'/'+school_id+'_building_list.html'
  scrape_url(building_url, school_building_table_file_path);
  soup = load_soup(school_building_table_file_path)

  building_data = []
  for cell in soup.find('table').find_all('td'):
    if not cell.find('img'):
      pair.update({
        'image_description': [x.strip() for x in cell.text.strip().split('\n') if x.strip()]
      })
      building_data.append(pair)
    else:
      pair = {'image_url': parent_url+cell.find('img').attrs['src']}

  return building_data

if __name__ == '__main__':
  student_data_df = pd.DataFrame()
  staff_data_df = pd.DataFrame()

  for school_id in school_ids[490:492]:
    sd = load_school_data(school_id, only=['general'])
    soup = load_soup(sd['general'])
    params_dict = prep_param_dict(soup)
    sd = load_school_data(school_id, params_dict)

    general(soup)
    school_student_df = student()
    school_student_df['school_id'] = school_id
    student_data_df = pd.concat([student_data_df, school_student_df])
    school_staff_df = staff()
    school_staff_df['school_id'] = school_id
    staff_data_df = pd.concat([staff_data_df, school_staff_df])
    computer()
    internet()
    durable_goods()
    building()
  
  student_data_df.to_csv(ROOT_DIR+'/student_data.csv', index=False)
  staff_data_df.to_csv(ROOT_DIR+'/staff_data.csv', index=False)