import os
from typing import Union
from helpers.indexer import Index
from helpers.utils import *
import pandas as pd
import re
from tqdm import tqdm
data_index = Index(os.path.join(ROOT_DIR, 'result_index.txt'))

def rename(to_rename, data_dir, axis=1):
    mappers = load_json('header_mapper.json')
    mapper = mappers[data_dir]
    if isinstance(to_rename, pd.DataFrame):
        return to_rename.rename(mapper, axis=axis)
    raise TypeError()

def replace(to_rename, data_dir):
    mappers = load_json('header_mapper.json')
    mapper = mappers[data_dir]
    if isinstance(to_rename, pd.DataFrame):
        return to_rename.replace(mapper)
    raise TypeError()

class SchoolData:
    def __init__(self, school_id: str, page_fpaths: Dict) -> None:
        self.school_id = school_id
        self.pages: Dict = page_fpaths
        self.save_dir = os.path.join(
            ROOT_DIR, 'school_data', 'school', school_id)

    def general(self) -> Dict:
        about_school: Dict = dict()
        about_school_json: List = dict()
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

                if cells[1].find_all('a'):
                    links = []
                    for a_tag in cells[1].find_all('a'):
                        if not a_tag.text:
                            continue
                        links.append({
                            "text": a_tag.text,
                            "url": (parent_url
                                    if not a_tag.attrs['href'].startswith('http')
                                    else '') + a_tag.attrs['href']
                        })
                    about_school_json.update({"links": links})
                    continue

                about_school_json[key_name] = value

        image_dir: str = SCRAPED_FILE_DIRS['general']+'/image'

        if not is_path_existed(image_dir):
            makedirs(image_dir)

        for div in soup.find_all('div'):
            if not div.find('div'):
                if 'ผู้อำนวยการโรงเรียน' in div.text:
                    image = div.find('img')
                    about_school_json['principal'] = {
                        'name': div.text.strip().split('\n')[0],
                        'position_title': div.text.strip().split('\n')[1].strip()
                    }
                    image = div.find('img')
                    if image is not None:
                        image_src = image.attrs['src']
                        about_school_json['principal']['image_path'] = parent_url + image_src

                elif 'ตราสัญลักษณ์' in div.text:
                    image = div.find('img')
                    if image is not None:
                        image_src = image.attrs['src']
                        about_school_json['logo_image_path'] = parent_url + image_src

        about_school_json['latlng'] = None
        js_text: str = ' '.join(
            [script.text for script in soup.find_all('script')])
        latlng: str = re.findall('LatLng\((.*)\)', js_text)
        if latlng and ',' in latlng[0]:
            about_school_json['latlng'] = latlng[0].split(',')

        return about_school_json

    def student(self) -> Dict:
        df: pd.DataFrame = self._find_html_table('student', 'ชั้น/เพศ')
        if df is not None:
            col_headers = df.iloc[0]
            df.columns = col_headers
            if len(df) > 2:
                df = df.iloc[1:-1]
            df = rename(df, 'student')
            df = rename(df.set_index('grade'), 'student_row_header', 0).reset_index()
            return dict(zip(df.iloc[:,0].tolist(), df.iloc[:,1:].to_dict('records')))

    def staff(self) -> Dict:
        staff_df: pd.DataFrame = self._find_html_table('staff', 'วิทยฐานะ')
        if staff_df is not None:
            staff_data = {}
            staff_df = replace(staff_df, 'staff')
            for g, group_df in staff_df.iloc[2:].groupby(0):
                g = re.sub('\d\. ?','',g)
                values = [dict(zip(staff_df.iloc[1, 3:].values, row))
                    for row
                    in group_df.iloc[:, 3:].values]

                staff_data[g] = [{
                    **({staff_df.iloc[0, 1]: group_df.iloc[i, 1]} if group_df.iloc[i, 1] != '-' else {}),
                    **({staff_df.iloc[0, 2]: group_df.iloc[i, 2]} if group_df.iloc[i, 2] != '-' else {}),
                    staff_df.iloc[0, 3]: row}
                    for i, row
                    in enumerate(values) if group_df.iloc[i, 1] != 'รวม']
            return staff_data

    def computer(self) -> Dict:
        df = self._find_html_table(
            'computer_internet', 'จำนวนคอมพิวเตอร์เพื่อการเรียนการสอน')
        if df is None:
            return dict()
        header = ''
        rows = dict()
        df = replace(df, 'computer')
        for _, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                col, cell = row_list
                if col not in rows.keys():
                    rows[col] = dict()
                cell = re.sub(r'(\d+) ?เครื่อง', r'\1', cell)
                cell = int(cell)
                rows[col][header] = cell
        return rows

    def _find_html_table(self, page, keyword):
        fpath = self.pages[page]
        tables = pd.read_html(fpath)
        for table in tables:
            table_bool = (keyword == table)
            if table_bool.any().any():
                df = table
                return df

    def internet(self) -> Dict:
        df = self._find_html_table(
            'computer_internet', 'ระบบเครือข่ายอินเทอร์เน็ตที่โรงเรียนเช่าเอง')
        if df is None: dict()
        df.fillna('-', inplace=True)
        header = ''
        rows = dict()
        for i, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                col, cell = row_list
                if cell != '-':
                    if header not in rows.keys(): rows[header] = dict()
                    rows[header][col] = cell
        return rows

    def durable_goods(self) -> Dict:
        df: pd.DataFrame = self._find_html_table('durable_goods', 'จำนวนรอจำหน่าย')
        if df is not None:
            df.columns = df.iloc[0]
            df = df.iloc[1:, :]
            df = df.iloc[:-1]
            df.drop('ลำดับ', axis=1, inplace=True)
            return rename(df, 'durable_goods').to_dict('records')
        return dict()

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
                    building_images.append(img_url)
                    im_rid += 1

                for tab_row in table.find_all('td'):
                    if tab_row.find('a') is None:
                        text = tab_row.text.strip()
                        if ':' not in text:
                            continue
                        key, val = re.sub(
                            '\s+', ' ', text).split(':', maxsplit=1)
                        building_details.update({key.strip(): val.strip()})
                
                temp = {'name': heading.text,}
                temp.update(building_details)
                temp['image'] = building_images
                building_data.append(temp)
        return building_data

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
        fpath = os.path.join(self.save_dir, f'{name}.json')
        ix = self.school_id + '.' + name

        data: Dict = caller()
        if data is not None :
            dump_json(data, fpath)
            data_index[ix] = fpath
            return data
