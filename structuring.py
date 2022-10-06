"""
parsing from orginal html to wanted file format
"""
import logging
from helpers.school import SchoolData
from helpers.utils import *
from tqdm import tqdm
import pandas as pd

logger_fpath = os.path.join(ROOT_DIR, 'open_school_data.log')
logging.basicConfig(filename=logger_fpath)


def save(dataframes: Dict[str, pd.DataFrame], save_paths: Dict[str, str]):
    for kdf in dataframes:
        df = dataframes[kdf]
        fpath = save_paths[kdf]
        df.to_csv(fpath, index=False)


def postprocess(dataframes: Dict[str, pd.DataFrame]):
    mappers = load_json('header_mapper.json')
    pp_dataframes: Dict[str, pd.DataFrame] = dict()
    primary_key = 'school_id'
    for kdf in dataframes:
        mapper = mappers[kdf]
        mapper = {old: new for old, new in mapper.items() if new}
        
        df: pd.DataFrame = pd.concat(dataframes[kdf], ignore_index=True)

        if kdf == 'durable_goods':
            df.drop('ลำดับ', axis=1, inplace=True)

        if kdf == 'staff':
            df['ตำแหน่ง'] = df['ตำแหน่ง'].apply(lambda text: re.sub('\d+\. ', '', text))

        df = df[[primary_key] + [col for col in df.columns if col != primary_key]]\
            .rename(mapper, axis=1)\
            .fillna('')
        
        pp_dataframes[kdf] = df
    return pp_dataframes


def remove_feilds(dictionary: Dict[str, str], feilds_to_remove: List[str]):
    for feild in feilds_to_remove:
        if feild not in dictionary.keys(): continue
        dictionary.pop(feild)


def main():
    sdi = SchoolDataIndex()
    building_index_fpath = os.path.join(ROOT_DIR, 'building_index.txt')
    buildings = Index(building_index_fpath)

    schools_pages_fpath = os.path.join(ROOT_DIR, 'school_file_path_pages.json')
    schools_pages = load_json(schools_pages_fpath)


    school_dfs = dict()
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

        for dir in parsed:
            if parsed[dir] is None:
                logging.warning(f'[{school_id}] {dir} is None')
                continue
            if not isinstance(parsed[dir], pd.DataFrame):
                raise TypeError(f'expected {type(pd.DataFrame)}, but {type(parsed[dir])} given')

            tdf = parsed[dir]
            tdf['school_id'] = school_id
            if dir not in school_dfs.keys():
                school_dfs[dir] = [parsed[dir]]
            else:
                school_dfs[dir].append(parsed[dir])

    save_fpaths: Dict[str, str] = dict()
    for feild in school_dfs:
        fpath = os.path.join(ROOT_DIR, 'school_data', f'{feild}.csv')
        save_fpaths[feild] = fpath

    school_dfs = postprocess(school_dfs)
    save(school_dfs, save_fpaths)


if __name__ == '__main__':
    main()