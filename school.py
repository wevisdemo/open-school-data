import os
from typing import Union
from indexer import Index
from utils import *
import pandas as pd
import re
from tqdm import tqdm


class SchoolData:
    def __init__(self, school_id: str, page_fpaths: Dict) -> None:
        # assert len(school_id) == 10, school_id + ' is not 10 digits'
        self.school_id = school_id
        self.pages: Dict = page_fpaths
        self.save_dir = os.path.join(
            ROOT_DIR, 'school_data', 'school', school_id)

    def general(self) -> Dict:
        about_school: List = []
        soup: BeautifulSoup = load_soup(self.pages['general'])
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

        for comment in soup.children:
            break
        url: str = re.findall('url: (.*)\n', comment)[0]

        parent_url: str = re.sub('[^/]*$', '', url)
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
                about_school.append({
                    'key': f'{dir_name}_image_path',
                    'value': image_src
                })

        js_text: str = ' '.join(
            [script.text for script in soup.find_all('script')])
        latlng: str = re.findall('LatLng\((.*)\)', js_text)
        if latlng:
            try:
                latlng_float: List[float] = [
                    float(pos) for pos in latlng[0].split(',')]
            except:
                latlng_float = None
                if ',' in latlng[0]:
                    latlng_float = latlng[0].split(',')
            about_school.append({
                'key': 'latlng',
                'value': latlng_float
            })

        return about_school

    def student(self) -> Dict:
        try:
            df: pd.DataFrame = pd.read_html(self.pages['student'])[-1]
        except:
            return None
        col_headers = df.iloc[0]
        df.columns = col_headers
        if len(df) > 2:
            df = df.iloc[1:-1]
        return df

    def staff(self) -> Dict:
        try:
            staff_df: pd.DataFrame = pd.read_html(self.pages['staff'])[-1]
        except:
            return None
        staff_header = staff_df.iloc[:2].values.tolist()
        staff_columns = [
            col1 if col1 == col2 else col1+'_'+col2
            for col1, col2 in zip(staff_header[0], staff_header[1])
        ]

        staff_df = staff_df.iloc[2:]
        staff_df.columns = staff_columns
        return staff_df

    def computer(self) -> Dict:
        file_path = self.pages['computer_internet']
        try:
            tables = pd.read_html(file_path)
        except:
            return None
        assert len(
            tables) >= 5, f'only {len(tables)} tables found, expected 5: {file_path}'
        df = tables[5]
        return df

    def internet(self) -> Dict:
        try:
            tables = pd.read_html(self.pages['computer_internet'])
            df = tables[6]
        except:
            return None
        return df

    def durable_goods(self) -> Dict:
        try:
            tables = pd.read_html(self.pages['durable_goods'])
            durable_goods_df: pd.DataFrame = tables[-2]
            durable_goods_df.columns = durable_goods_df.iloc[0]
            durable_goods_df = durable_goods_df.iloc[1:, :]
            durable_goods_df = durable_goods_df.iloc[:-1]
        except:
            return None
        return durable_goods_df

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

                for img in images:
                    img_url = parent_url + img['src']
                    building_images.append({'image_url': img_url})

                for tab_row in table.find_all('td'):
                    if tab_row.find('a') is None:
                        text = tab_row.text.strip()
                        if ':' not in text:
                            continue
                        key, val = re.sub(
                            '\s+', ' ', text).split(':', maxsplit=1)
                        building_details.update({key.strip(): val.strip()})

                building_data.append({
                    'name': heading.text,
                    'images': building_images,
                    'details': building_details
                })
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
            save_path = self.save_dir + '/' + dir + '.json'
            if dir == 'computer_internet':
                save_path = self.save_dir + '/' + 'computer' + '.json'
                data = methods['computer']()
                # dump_json(data)
                temp['computer'] = data

                save_path = self.save_dir + '/' + 'internet' + '.json'
                data = methods['internet']()
                # dump_json(data)
                temp['internet'] = data
            else:
                data = methods[dir]()
                # dump_json(data, save_path)
                temp[dir] = data
        return temp

    def _df_to_dict(self, df) -> pd.DataFrame:
        header = ''
        rows = {}
        for i, row in df.iterrows():
            if len(row.unique()) != len(row):
                header = row[0]
            else:
                row_list = row.values.tolist()
                if len(row_list) == 2:
                    if header not in rows.keys():
                        rows[header] = dict()
                    rows[header][row_list[0]] = row_list[1]
        return rows


if __name__ == '__main__':
    sdi = SchoolDataIndex()
    building_index_fpath = os.path.join(ROOT_DIR, 'building_index.txt')
    buildings = Index(building_index_fpath)

    schools_pages_fpath = os.path.join(ROOT_DIR, 'school_pages_index.json')

    schools_pages = load_json(schools_pages_fpath)

    schools_data: List = list()
    sit: int = 0
    for school_id, data in tqdm(sdi.schools()):
        sit += 1
        if school_id not in schools_pages.keys(): continue
        temp: Dict = schools_pages[school_id].copy()
        if 'building' in temp.keys():
            temp.pop('building')
        if buildings[school_id[2:]] is not None:
            temp.update({
                'building': buildings[school_id[2:]]
            })

        sd = SchoolData(school_id, temp)
        try:
            parsed = sd.save()
        except AssertionError as e:
            print(e)
            continue
        except AttributeError as e:
            print(e)
            continue
        schools_data.append(parsed)
