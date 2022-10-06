import os
from typing import List
from helpers.utils import HTML_ROOT_DIR, url_index
from tqdm import tqdm


def get_url(fpath):
    comment = ''
    with open(fpath, 'r') as fp:
        c = ''
        while c != '>':
            c = fp.read(1)
            comment += c

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
