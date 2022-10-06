import path

class Index:
  def __init__(self, fpath) -> None:
    assert fpath
    self.fpath = fpath
    self.index = dict()

    if path.Path(fpath).isfile():
      with open(fpath, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
          key, val = line.split('\t', maxsplit=1)
          self.index[key.strip()] = val.strip()

  def __getitem__(self, key):
    if key not in self.index.keys():
      return None
    return self.index[key]

  def __setitem__(self, key, val):
    same = False
    if key in self.index.keys():
      same = self.index[key] == val
      self.index[key] = val
    else:
      self.index[key] = val
    if same:
      return
    with open(self.fpath, 'a') as fp:
      fp.write(key + '\t' + val + '\n')
  
  def __iter__(self):
    return iter(self.index.items())

  def save(self):
    with open(self.fpath, 'r') as fp:
      for key, val in self.index.items():
        fp.write(key + '\t' + val + '\n')

if __name__ == '__main__':
  url_index = Index('url_index.txt')
  print(url_index.index.keys())