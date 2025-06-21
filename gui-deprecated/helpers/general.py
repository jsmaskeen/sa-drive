class Generator:
    def __init__(self, gen):
        self.gen = gen

    def __iter__(self):
        self.value = yield from self.gen

def get_free_sa(sa_map,file_size):
    # ok_sas = []
    tmp = []
    for i in sa_map:
        if 15784004812 - int(i['size']) >=file_size:
            tmp.append([int(i['size']),int(i['_id'])])
            # ok_sas.append(int(i['_id']))
    tmp.sort(key=lambda x:x[0])
    ok_sas = [i[1] for i in tmp]
    return ok_sas

