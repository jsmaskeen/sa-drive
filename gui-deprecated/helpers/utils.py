import time
from math import ceil



def humanbytes(size: int) -> str:
    if not size:
        return ""
    power = 2 ** 10
    number = 0
    dict_power_n = {
        0: " ",
        1: "K",
        2: "M",
        3: "G",
        4: "T",
        5: "P"
    }
    while size > power:
        size /= power
        number += 1
    return str(round(size, 3)) + " " + dict_power_n[number] + 'B'

def humantime(seconds):
    if seconds > 3600:
        return time.strftime("%Hh%Mm%Ss", time.gmtime(seconds))
    else:
        return time.strftime("%Mm%Ss", time.gmtime(seconds))
def list_into_n_parts(lst, n):
  size = ceil(len(lst) / n)
  return list(
    map(lambda x: lst[x * size:x * size + size],
    list(range(n)))
  )
