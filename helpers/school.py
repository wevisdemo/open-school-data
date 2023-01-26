import os
from typing import Union
from helpers.indexer import Index
from helpers.utils import *
import pandas as pd
import re
from tqdm import tqdm
data_index = Index(os.path.join(ROOT_DIR, 'result_index.txt'))
mappers = load_json('header_mapper.json')

def rename(to_rename, data_dir, axis=1):
    mapper = mappers[data_dir]
    if isinstance(to_rename, pd.DataFrame):
        return to_rename.rename(mapper, axis=axis)
    raise TypeError()

def replace(to_rename, data_dir):
    mapper = mappers[data_dir]
    if isinstance(to_rename, pd.DataFrame):
        return to_rename.replace(mapper)
    if isinstance(to_rename, str):
        return mapper[to_rename]
    raise TypeError()

class SchoolData:
    def __init__(self, school_id: str, page_fpaths: Dict) -> None:
        self.school_id = school_id
        self.pages: Dict = page_fpaths
        self.save_dir = os.path.join(
            ROOT_DIR, 'school_data', 'school', school_id)

    def general(self) -> Dict:
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

                about_school_json[replace(key_name, 'general')] = value

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
            
            df = df[df.grade.apply(lambda x: 'total' not in x)]
            df = df.astype({'men': int, 'women': int, 'total': int, 'class': int})
            
            stats = df.assign(g=df.grade.apply(lambda x: x[:-1])).groupby('g').total.sum().to_dict()
            stats.update({
                'all': df.total.sum(),
                'class': df['class'].sum(),
            })
            
            df.set_index('grade').to_dict('index')
            return {
                'total': stats,
                **df.set_index('grade').to_dict('index')}

    def staff(self) -> Dict:
        staff_df: pd.DataFrame = self._find_html_table('staff', 'วิทยฐานะ')
        if staff_df is not None:
            staff_data = {}
            staff_df.columns = [
                c1 if c1 == c2 else c1 + '_' + c2
                for c1,c2 in zip(staff_df.iloc[0], staff_df.iloc[1])
            ]
            df = rename(staff_df, 'staff')
            df.drop([0,1], inplace=True)
            df = replace(df, 'staff_row_header')

            # regroup 'ลูกจ้างประจำ', 'พนักงานราชการ', 'ลูกจ้างชั่วคราว' as 'พนักงาน'
            is_edu_staff = df.position.isin(['ลูกจ้างประจำ', 'พนักงานราชการ', 'ลูกจ้างชั่วคราว'])
            df.loc[is_edu_staff, 'rank_position'] = df[is_edu_staff].position
            df.loc[is_edu_staff, 'position'] = 'พนักงาน'

            staff_stats = {}
            for position, sub_df in df.groupby('position'):
                # exclude 'รวม' row
                is_total_row = sub_df.professional_rank == 'รวม'
                sub_df = sub_df[~is_total_row].set_index('rank_position')[['men', 'women', 'total']].astype(int)

                if position == 'รวมทั้งหมด':
                    staff_stats.update(sub_df.sum().to_dict())
                else:
                    temp = sub_df.to_dict('index')
                    stats = sub_df.sum().to_dict()
                    stats.update(temp)
                    staff_stats[position] = stats

            return staff_stats

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
                if header not in rows.keys():
                    rows[header] = dict()
                row_list = row.values.tolist()
                col, cell = row_list
                cell = re.sub(r'(\d+) ?เครื่อง', r'\1', cell)
                cell = int(cell)
                if col.startswith('source'):
                    source_dict = rows[header].get('source', dict())
                    source_dict[col.replace('source_','')] = cell
                    rows[header]['source'] = source_dict
                else:
                    rows[header][col] = cell
        dict_total = rows['total']
        del rows['total']
        rows.update(dict_total)
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
        df = replace(df, 'internet')
        return dict([
            [cell if cell != '-' else None for cell in record.values()]
            for record in df[df[0] != df[1]].to_dict('records')
        ])

    def durable_goods(self) -> Dict:
        df: pd.DataFrame = self._find_html_table('durable_goods', 'จำนวนรอจำหน่าย')
        if df is not None:
            df.columns = df.iloc[0]
            df = df.iloc[1:, :]
            df = df.iloc[:-1]
            df.drop('ลำดับ', axis=1, inplace=True)
            df.fillna(0)
            df = rename(df, 'durable_goods')
            df.loc[df.code.isin(['11001', '22001', '22002']), 'type'] = 'โต๊ะเก้าอี้นักเรียน'
            def _handler(type_df,):
                type_df = type_df.astype({'working': int, 'to_be_repaired': int, 'to_be_removed': int})
                stats = type_df[['working', 'to_be_repaired', 'to_be_removed']].sum().to_dict()
                return {**stats, 'list': type_df.to_dict('records')}
            return df.groupby('type').apply(_handler).to_dict()
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
                        
                        building_details.update({replace(key.strip(), 'building'): val.strip()})
                
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
