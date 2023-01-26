"""
parsing from orginal html to wanted file format
"""
import logging
from helpers.school import SchoolData
from helpers.utils import *
from tqdm import tqdm
import pandas as pd
from helpers.province import PROVINCE_HTML_DIR
from typing import Union

logger_fpath = os.path.join(ROOT_DIR, 'open_school_data.log')
logging.basicConfig(filename=logger_fpath)


def save(dataframes: Dict[str, pd.DataFrame], save_paths: Dict[str, str]):
    for kdf in dataframes:
        df = dataframes[kdf]
        fpath = save_paths[kdf]
        df.to_csv(fpath, index=False)


def remove_feilds(dictionary: Dict[str, str], feilds_to_remove: List[str]):
    for feild in feilds_to_remove:
        if feild not in dictionary.keys(): continue
        dictionary.pop(feild)


def get_affiliation_indexer():
    all_dfs = []
    for province_html in os.listdir(PROVINCE_HTML_DIR):
        if 'index.html' == province_html: continue
        file_path = os.path.join(PROVINCE_HTML_DIR, province_html)
        tables = pd.read_html(file_path, converters={'รหัสโรงเรียน': lambda x: x, 'รหัส สพท.': lambda x: x})
        all_dfs.append(tables[0].dropna().set_index('รหัสโรงเรียน'))
    return pd.concat(all_dfs)['สพท.']

def main():
    sdi = SchoolDataIndex()
    building_index_fpath = os.path.join(ROOT_DIR, 'building_index.txt')
    buildings = Index(building_index_fpath)

    schools_pages_fpath = os.path.join(ROOT_DIR, 'school_file_path_pages.json')
    schools_pages = load_json(schools_pages_fpath)
    
    school_data_dir = os.path.join(ROOT_DIR, 'school_data', 'school', )
    if not os.path.exists(school_data_dir):
        os.makedirs(school_data_dir)

    school_ids = list(sdi.school_ids())
    for school_id in tqdm(school_ids):
        if school_id not in schools_pages.keys():
            continue
        temp: Dict = schools_pages[school_id].copy()
        if 'building' in temp.keys():
            temp.pop('building')
        
        if buildings[school_id[4:]] is not None:
            temp.update({
                'building': buildings[school_id[4:]]
            })
        
        sd = SchoolData(school_id, temp)
        parsed = sd.save()

        affiliation = sdi.get_school(school_id)['สพท.']
        if isinstance(affiliation, str) and affiliation.startswith('สพป'):
            affiliation = 'สพป.'
        elif isinstance(affiliation, str) and affiliation.startswith('สพม'):
            affiliation = 'สพม.'
        else:
            print(affiliation)
        parsed['affiliation'] = affiliation
        parsed['school_size'] = get_school_size(affiliation, parsed['student']['total']['all'])
        fpath = os.path.join(ROOT_DIR, 'school_data', 'school', f'{school_id}.json')
        dump_json(parsed, fpath)

def get_school_size(school_type: str, student_number: int):
    if school_type == 'สพป.':
        if student_number <= 120:
            return 'เล็ก'
        elif student_number <= 600:
            return 'กลาง'
        elif student_number <= 1500:
            return 'ใหญ่'
        return 'ใหญ่พิเศษ'
    if school_type == 'สพม.':
        if student_number < 500:
            return 'เล็ก'
        elif student_number < 1500:
            return 'กลาง'
        elif student_number < 2500:
            return 'ใหญ่'
        return 'ใหญ่พิเศษ'
    raise ValueError('"' + school_type + '" school type not recognized')
if __name__ == '__main__':
    main()