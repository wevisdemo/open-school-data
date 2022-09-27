from typing import Union
from utils import *
import pandas as pd
import re
from tqdm import tqdm

class SchoolData:
    def __init__(self, school_id) -> None:
        assert len(school_id) == 10

        self.school_id = school_id
        sd = load_school_data(school_id, only=['general'])
        soup = load_soup(sd['general'])
        params_dict = prep_param_dict(soup)
        self.sd = load_school_data(school_id, params_dict)
        self.save_dir = f'{ROOT_DIR}/school_data/school/{self.school_id}'
        self.school_id_8_digit = None
    
    def general(self) -> Dict:
        about_school: List = []
        soup: BeautifulSoup = load_soup(self.sd['general'])
        table = soup.find('table').find('table', attrs={'width': '521'})
        for table_row in table.find_all('tr'):
            cells = table_row.find_all('td')

            if len(cells) == 2:
                key_name: str = clean_text(cells[0].text)
                value: str = clean_text(cells[1].text)

                if cells[1].find_all('a'):
                    value: List = [{'text': a_tag.text, 'href': a_tag.attrs['href']}
                        for a_tag in cells[1].find_all('a') if a_tag.text] 

                about_school.append({'key': key_name, 'value': value})
            else:
                about_school.append({'value': clean_text(cells[0].text)})

        for comment in soup.children: break
        url: str = re.findall('url: (.*)\n', comment)[0]

        parent_url: str  = re.sub('[^/]*$', '', url)
        image_dir: str = SCRAPED_FILE_DIRS['general']+'/image'

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
        
        js_text: str = ' '.join([script.text for script in soup.find_all('script')])
        latlng: str = re.findall('LatLng\((.*)\)', js_text)
        if latlng:
            latlng_float: List[float] = [float(pos) for pos in latlng[0].split(',')]
            about_school.append({
                'key': 'latlng',
                'value': latlng_float
            })

        return about_school

    def student(self) -> Dict:
        try:
            df: pd.DataFrame = pd.read_html(self.sd['student'])[-1]
        except:
            return None
        col_headers = df.iloc[0]
        df.columns = col_headers
        if len(df) > 2:
            df = df.iloc[1:-1]
        return df.to_dict(orient='records')

    def staff(self) -> Dict:
        try:
            staff_df: pd.DataFrame = pd.read_html(self.sd['staff'])[-1]
        except:
            return None
        staff_header = staff_df.iloc[:2].values.tolist()
        staff_columns = [
            col1 if col1 == col2 else col1+'_'+col2
            for col1, col2 in zip(staff_header[0], staff_header[1])
        ]

        staff_df = staff_df.iloc[2:]
        staff_df.columns = staff_columns
        return staff_df.to_dict(orient='records')

    def computer(self) -> Dict:
        file_path = self.sd['computer_internet']
        try:
            tables = pd.read_html(file_path)
        except:
            return None
        assert len(tables) >= 5 
        df = tables[5]
        computer = self._df_to_dict(df)
        return computer
    
    def internet(self) -> Dict:
        try:
            tables = pd.read_html(self.sd['computer_internet'])
            df = tables[6]
        except:
            return None
        return self._df_to_dict(df)

    def durable_goods(self) -> Dict:
        try:
            tables = pd.read_html(self.sd['durable_goods'])
            durable_goods_df: pd.DataFrame = tables[-2] 
            durable_goods_df.columns = durable_goods_df.iloc[0]
            durable_goods_df = durable_goods_df.iloc[1:, :]
            durable_goods_df = durable_goods_df.iloc[:-1]
        except:
            return None
        return durable_goods_df.to_dict(orient='records')

    def building(self):
        soup = load_soup(self.sd['building'])

        for comment in soup.children:
            break
        url = re.findall('url: (.*)\n', comment)
        parent_url = re.sub('[^/]*$', '', url[0])

        building_data = []
        image_id = 0
        for row in soup.find_all('div', attrs={'class': 'row'}):
            cols = row.find_all('div', attrs={'class': 'col-md-4'})
            for col in cols:
                table = col.find('table')
                if table is None:
                    continue
                heading = table.find('th')
                building_details: Dict = dict()
                images = col.find_all('img', attrs={'src': True})
                building_images = []

                image_dir = SCRAPED_FILE_DIRS['building'] + '/images'
                if not is_path_existed(image_dir):
                    makedirs(image_dir)

                for img in images:
                    img_url = parent_url + img['src']
                    image_path = image_dir + '/' + self.school_id + '_' + '{:02}'.format(image_id) + '.jpg'
                    image_id += 1

                    if not is_path_existed(image_path):
                        with open(image_path, 'wb') as im_file:
                            image = requests.get(img_url).content
                            im_file.write(image)

                    building_images.append({'image_url': img_url, 'image_path': image_path})


                for tab_row in table.find_all('td'):
                    if tab_row.find('a') is None:
                        text = tab_row.text.strip()
                        if ':' not in text: continue
                        key, val = re.sub('\s+', ' ', text).split(':', maxsplit=1)
                        building_details.update({key.strip(): val.strip()})

                building_data.append({
                    'name': heading.text,
                    'images': building_images,
                    'details': building_details
                })
        return building_data

    def save(self) -> Dict[str, Dict[str, Union[Dict, pd.DataFrame]]]:
        makedirs(self.save_dir, exist_ok=True)

        dict_temp = {
            'building' : self.building(),
            'computer' : self.computer(),
             'durable' : self.durable_goods(),
             'general' : self.general(),
             'student' : self.student(),
               'staff' : self.staff(),
            'internet' : self.internet(),
        }
        for dir, dir_dict in dict_temp.items():
            with open(self.save_dir + '/' + dir + '.json', 'w') as file:
                json.dump(dir_dict, file, ensure_ascii=False, indent=2)

        return dict_temp

    def _df_to_dict(self, df) -> pd.DataFrame:
        header = ''
        rows = {}
        for i, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                if len(row_list) == 2:
                    if header not in rows.keys(): rows[header] = dict()
                    rows[header][row_list[0]] = row_list[1]
        return rows

if __name__ == '__main__':
    sdi = SchoolDataIndex()
    school_ids = list(sdi.school_ids())

    school_data_dict: Dict = dict()
    school_iter = tqdm(school_ids[:5])
    for school_id in school_ids:
        school_iter.desc = 'School: ' + school_ids
        data: SchoolData = SchoolData(school_id)
        saved_data: Dict = data.save()
        school_data_dict[school_id] = saved_data
        school_iter.update(1)

    file_path = ROOT_DIR + '/school_data/' + 'open_school_data.json'
    with open(file_path, 'w') as file:
        json.dump(school_data_dict, file, ensure_ascii=False, indent=1)

