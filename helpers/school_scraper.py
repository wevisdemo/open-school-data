from random import shuffle, uniform
from helpers.indexer import Index
from helpers.utils import *
from tqdm import tqdm


class SchoolScraper:
    def __init__(self, dir) -> None:
        self.dir = dir
        pass

    def __call__(self, id, url) -> Tuple[str, str]:
        fpath = os.path.join(self.dir, id + '.html')
        if url_index[url] is None:
            scrape_url(url, fpath)
            url_index[url] = fpath
            self.sleep()
        else:
            return url_index[url], url
        return fpath, url

    def sleep(self):
        sleep_for = uniform(0.3, 1)
        sleep(sleep_for)


if __name__ == '__main__':
    sdi = SchoolDataIndex()

