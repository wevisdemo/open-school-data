import os
from typing import Union
from helpers.indexer import Index
from helpers.utils import *
import pandas as pd
import re
from tqdm import tqdm
data_index = Index(os.path.join(ROOT_DIR, 'result_index.txt'))

class SchoolData:
    def __init__(self, school_id: str, page_fpaths: Dict) -> None:
        self.school_id = school_id
        self.pages: Dict = page_fpaths
        self.save_dir = os.path.join(
            ROOT_DIR, 'school_data', 'school', school_id)

    def general(self) -> Dict:
        about_school: Dict = dict()
        soup: BeautifulSoup = load_soup(self.pages['general'])
        table = soup.find('table').find('table', attrs={'width': '521'})
        for comment in soup.children:
            break
        url: str = re.findall('url: (.*)\n', comment)[0]

        parent_url: str = re.sub('[^/]*$', '', url)

        for table_row in table.find_all('tr'):
            cells = table_row.find_all('td')

            if len(cells) == 2:
                key_name: str = clean_text(cells[0].text)
                value: str = clean_text(cells[1].text)

                _id = 0
                if cells[1].find_all('a'):
                    for a_tag in cells[1].find_all('a'):
                        if not a_tag.text: continue
                        about_school.update(
                    {f'url_text_{_id}': a_tag.text, f'url_{_id}': parent_url + a_tag.attrs['href']})

                about_school.update({key_name: value})

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
                image = div.find('img')
                image_src = None
                if image is not None:
                    image_src = image.attrs['src']
                    about_school.update({f'{dir_name}_image_path' : parent_url + image_src})

        js_text: str = ' '.join(
            [script.text for script in soup.find_all('script')])
        latlng: str = re.findall('LatLng\((.*)\)', js_text)
        if latlng:
            about_school.update({'latlng' : latlng})
        df = pd.DataFrame(about_school)
        return df

    def student(self) -> Dict:
        df: pd.DataFrame = self._find_html_table('student', 'ชั้น/เพศ')
        if df is not None:
            col_headers = df.iloc[0]
            df.columns = col_headers
            if len(df) > 2:
                df = df.iloc[1:-1]
        return df

    def staff(self) -> Dict:
        staff_df: pd.DataFrame = self._find_html_table('staff', 'วิทยฐานะ')
        if staff_df is not None:
            staff_header = staff_df.iloc[:2].values.tolist()
            staff_columns = [
                col1 if col1 == col2 else col1+'_'+col2
                for col1, col2 in zip(staff_header[0], staff_header[1])
            ]
            staff_df = staff_df.iloc[2:]
            staff_df.columns = staff_columns
        return staff_df

    def computer(self) -> Dict:
        df = self._find_html_table('computer_internet', 'จำนวนคอมพิวเตอร์เพื่อการเรียนการสอน')
        if df is None: return
        header = ''
        rows = dict()
        for _, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                col, cell = row_list
                if col not in rows.keys():
                    rows[col] = dict()
                rows[col][header] = cell
        df = pd.DataFrame(rows)
        df.reset_index(inplace=True)
        return df

    def _find_html_table(self, page, keyword):
        fpath = self.pages[page]
        tables = pd.read_html(fpath)
        for table in tables:
            table_bool = (keyword == table)
            if table_bool.any().any():
                df = table
                return df


    def internet(self) -> Dict:
        df = self._find_html_table('computer_internet', 'ระบบเครือข่ายอินเทอร์เน็ตที่โรงเรียนเช่าเอง')
        if df is None: return
        header = ''
        rows = dict()
        for i, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                col, cell = row_list
                rows[header+'_'+col] = cell

        df = pd.DataFrame([rows.values()], columns=rows.keys())
        return df

    def durable_goods(self) -> Dict:
        df = self._find_html_table('durable_goods', 'จำนวนรอจำหน่าย')
        if df is not None:
            df.columns = df.iloc[0]
            df = df.iloc[1:, :]
            df = df.iloc[:-1]
        return df

    def building(self):
        soup = load_soup(self.pages['building'])

        for comment in soup.children:
            break
        url = re.findall('url: (.*)\n', comment)
        parent_url = re.sub('[^/]*$', '', url[0])

        building_data = []
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

                im_rid = 0
                for img in images:
                    img_url = parent_url + img['src']
                    building_images.append({'image_url': img_url})
                    im_rid += 1

                for tab_row in table.find_all('td'):
                    if tab_row.find('a') is None:
                        text = tab_row.text.strip()
                        if ':' not in text:
                            continue
                        key, val = re.sub(
                            '\s+', ' ', text).split(':', maxsplit=1)
                        building_details.update({key.strip(): val.strip()})
                temp = {'name': heading.text, }
                temp.update(building_details)
                if building_images:
                    for i, im in enumerate(building_images):
                        temp.update({f'{key}_{i}': val for key, val in im.items()})
                building_data.append(temp)
        df = pd.DataFrame(building_data)
        return df

    def save(self) -> Dict[str, Dict[str, Union[Dict, pd.DataFrame]]]:
        makedirs(self.save_dir, exist_ok=True)

        methods = {
            'building': self.building,
            'computer': self.computer,
            'durable_goods': self.durable_goods,
            'general': self.general,
            'student': self.student,
            'staff': self.staff,
            'internet': self.internet,
        }
        temp: Dict = dict()

        for dir in self.pages:
            if dir == 'computer_internet':
                for dir in ['computer', 'internet']:
                    data = self.wirte_file(methods[dir], dir)
                    temp[dir] = data
            else:
                data = self.wirte_file(methods[dir], dir)
                temp[dir] = data
        return temp

    def wirte_file(self, caller, name):
        fpath = os.path.join(self.save_dir, f'{name}.csv')
        ix = self.school_id + '.' + name
        if data_index[ix] is not None:
            fpath = data_index[ix]
            try:
                df = pd.read_csv(fpath)
                return df
            except pd.errors.EmptyDataError as e:
                print(fpath, e)

        data: pd.DataFrame = caller()
        if data is not None:
            data.to_csv(fpath, index=False)
            data_index[ix] = fpath
            return data
