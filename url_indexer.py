import os
from typing import List
from src.utils import HTML_ROOT_DIR, url_index
from tqdm import tqdm


def get_url(fpath):
    with open(fpath, 'r') as fp:
        file = fp.read()

    end = file.index('-->')
    comment = file[:end]
    for line in comment.splitlines()[1:]:
        key, val = line.split(maxsplit=1)
        if key == 'url:':
            return val


if __name__ == '__main__':
    file_paths: List = list()

    for dirpath, dirnames, filenames in os.walk(HTML_ROOT_DIR):
        for filename in filenames:
            if not filename.endswith('html'):
                continue
            fpath = os.path.join(dirpath, filename)
            file_paths.append(fpath)

    for fpath in tqdm(file_paths, 'indexing'):
        url = get_url(fpath)
        url_index[url] = fpath
