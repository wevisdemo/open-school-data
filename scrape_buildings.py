import os
from src.utils import *
from tqdm import tqdm
from src.school_scraper import SchoolScraper
from src.indexer import Index

area_index = Index(ROOT_DIR + '/area_index.txt')
building_index = Index(ROOT_DIR + '/building_index.txt')
index_page_path = os.path.join(HTML_ROOT_DIR, 'buidling.html')
index_page_url = 'https://bobec.bopp-obec.info/build_show.php'


def parse_table(table_soup):
    thead = table_soup.find('thead')
    assert thead is not None and len(thead) > 0
    headers = [head.text for head in thead.find_all('th')]

    table_data = []
    table_body = table_soup.find('tbody')
    assert table_body
    for row in table_body.find_all('tr'):
        row_tds = row.find_all('td')
        assert len(row_tds) == len(headers)
        row_data = dict()
        for col, td in zip(headers, row.find_all('td')):
            row_data[col.strip()] = td.text.strip()
            a_tag = td.find('a')
            if a_tag is not None:
                row_data['href'] = a_tag.attrs['href']
        table_data.append(row_data)
    return table_data


def school_list(file_path):
    soup: BeautifulSoup = load_soup(file_path)
    table = None
    for table in soup.find_all('table'):
        if table.find('table'):
            continue
        thead = table.find('thead')
        if thead is not None:
            break

    assert table

    table_data = parse_table(table)
    return table_data


def area_urls():
    if not is_path_existed(index_page_path):
        scrape_url(index_page_url, index_page_path)
    soup = load_soup(index_page_path)
    select = soup.find('select')
    if select is None:
        raise ValueError('school index page dose not contain select tag')

    area_page_urls = []
    for option in select.find_all('option'):
        if option.attrs['value'] == '0':
            continue
        area_page_urls.append(
            option.attrs['value'])

    return area_page_urls


def area_scraper(areas: List):
    parent_url = re.sub('[^/]*$', '', index_page_url)
    area_dir = os.path.join(HTML_ROOT_DIR, 'area')
    makedirs(area_dir, exist_ok=True)
    scraper = SchoolScraper(area_dir)

    for page in tqdm(areas, 'scraping areas'):
        url = parent_url + page
        params = params_in_url(url)
        if not params:
            continue
        area_code = params[0][1]
        fpath, _ = scraper(area_code, url)
        area_index[area_code] = fpath


def school_pages():
    building_schools: List = list()
    building_school_fpath = os.path.join(ROOT_DIR, 'b-obec_schools_index.json')

    if not is_path_existed(building_school_fpath):
        for acode, fpath in tqdm(area_index, 'getting schools in areas'):
            building_schools += school_list(fpath)

        dump_json(building_schools, building_school_fpath)
    else:
        building_schools = load_json(building_school_fpath)

    return building_schools


def school_building_scraper(school_pages):
    scraper = SchoolScraper(SCRAPED_FILE_DIRS['building'])
    parent_url = re.sub('[^/]*$', '', index_page_url)
    for school in tqdm(school_pages, 'scraping school'):
        url = parent_url + school['href']
        scraper(school['รหัส percode'], url)

def main():

    # get area page
    areas = area_urls()

    # scrape all area pages
    area_scraper(areas)

    # get all school pages
    schools = school_pages()

    # scrape all school pages
    school_building_scraper(schools)


if __name__ == '__main__':
    main()
