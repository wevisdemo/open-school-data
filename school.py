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
  if not is_path_existed(image_file_path):
    with open(image_file_path, 'wb') as im_file:
      im_file.write(image)
  
  return image_file_path

class SchoolData:
  def __init__(self, school_id) -> None:
    assert len(school_id) == 10
    
    self.school_id = school_id
    sd = load_school_data(school_id, only=['general'])
    soup = load_soup(sd['general'])
    params_dict = prep_param_dict(soup)
    self.sd = load_school_data(school_id, params_dict)

  def general(self):
    about_school = []
    soup = load_soup(self.sd['general'])
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
        about_school.append({
          'key': f'{dir_name}_image_path',
          'value': download_image(
            parent_url+image_src, image_dir)
          })

    return about_school

  def student(self):
    return pd.read_html(self.sd['student'])[-1]

  def staff(self):
    staff_df = pd.read_html(self.sd['staff'])[-1]
    return staff_df

  def computer(self):
    tables = pd.read_html(self.sd['computer_internet'])
    df = tables[5]
    return self._merge_table(df)

  def internet(self):
    tables = pd.read_html(self.sd['computer_internet'])
    df = tables[6]
    return self._merge_table(df)

  def durable_goods(self):
    durable_goods_df = pd.read_html(self.sd['durable_goods'])[-2]
    durable_goods_df.columns = durable_goods_df.iloc[0]
    durable_goods_df  = durable_goods_df.iloc[1:, :]
    durable_goods_df.set_index('ลำดับ', inplace=True)
    return durable_goods_df.iloc[:-1]

  def building(self):
    b_soup = load_soup(self.sd['building'])
    building_url = b_soup.find('iframe').attrs['src']
    parent_url = re.sub('[^/]*$', '', building_url)
    school_building_table_file_path =\
      SCRAPED_FILE_DIRS['building']+'/'+school_id+'_building_list.html'
    scrape_url(building_url, school_building_table_file_path);
    soup = load_soup(school_building_table_file_path)

    building_data = []
    for cell in soup.find('table').find_all('td'):
      if not cell.find('img'):
        pair.update({
          'image_description': [
            x.strip()
            for x in cell.text.strip().split('\n') if x.strip()]
        })
        building_data.append(pair)
      else:
        pair = {'image_url': parent_url+cell.find('img').attrs['src']}

    image_dir = SCRAPED_FILE_DIRS['building'] + '/images'
    if not is_path_existed(image_dir):
      makedirs(image_dir)

    for i, building in enumerate(building_data):
      fex = re.findall('\.[^\.]*$', building['image_url'])
      image_path = image_dir + '/' + self.school_id + f'_{i:02}'
      if fex:
        image_path = image_path + fex[0]
      else:
        image_path = image_path + '.jpg'

      building['path'] = image_path
      
      if is_path_existed(image_path): continue
      
      with open(image_path, 'wb') as im_file:
        image = requests.get(building['image_url']).content
        im_file.write(image)
    return building_data

  def save(self):
    save_dir = f'{ROOT_DIR}/school_data'
    
    makedirs(save_dir, exist_ok=True)
    
    temp = {
      'building': self.building(),
      'general': self.general()
      }


    with open(save_dir+'/'+self.school_id+'.json', 'w') as file:
      json.dump(temp, file, ensure_ascii=False, indent=2)
    
    self.computer().to_csv(save_dir+'/'+self.school_id+'_computer.csv', index=False)
    self.internet().to_csv(save_dir+'/'+self.school_id+'_internet.csv', index=False)
    self.student().to_csv(save_dir+'/'+self.school_id+'_student.csv', index=False)
    self.staff().to_csv(save_dir+'/'+self.school_id+'_staff.csv', index=False)
    self.durable_goods().to_csv(save_dir+'/'+self.school_id+'_durable_goods.csv', index=False)

  def _merge_table(self, df):
    header = ''
    rows = []
    for i, row in df.iterrows():
      if len(row.unique()) != len(row):
        header = row[0]
      else:
        rows.append([header, *row])
    return pd.DataFrame(rows)

if __name__ == '__main__':
  student_data_df = pd.DataFrame()
  staff_data_df = pd.DataFrame()

  for school_id in school_ids[490:492]:
    school = SchoolData(school_id)
    school.save()
    # school.computer()
