import pymongo
import certifi
from config import db_uri
from logutil import logger
from pymongo.errors import DuplicateKeyError
import json
ca = certifi.where()
client = pymongo.MongoClient(db_uri, tlsCAFile=ca)


my_db = client["sadrive"]
file_map = my_db["file_map"]
sa_size_map = my_db["sa_size_map"]
star_map = my_db["star_map"]


def insert_file(
    file_id, file_name, parent_id, file_size, type, service_acc_num, shared
):
    """type should be folder/file
    shared can be true/false"""
    file_map.insert_one(
        {
            "_id": file_id,
            "file_name": file_name,
            "parent_id": parent_id,
            "file_size": int(file_size),
            "type": type,
            "service_acc_num": service_acc_num,
            "shared": shared,
        }
    )
    add_size(service_acc_num, int(file_size))


def get_file_details(file_id):
    return file_map.find_one({"_id": file_id})


# def update_file(
#     file_id, file_name, parent_id, file_size, type, service_acc_num, shared
# ):
#     data = {
#         "_id": file_id,
#         "file_name": file_name,
#         "parent_id": parent_id,
#         "file_size": int(file_size),
#         "type": type,
#         "service_acc_num": service_acc_num,
#         "shared": shared,
#     }
#     file_map.update_one({"_id": file_id}, {"$set": data})


def rename_file(file_id, new_file_name):
    old = file_map.find_one({"_id": file_id})
    old["file_name"] = new_file_name
    file_map.update_one({"_id": file_id}, {"$set": old})
    star_map.update_one({"_id": file_id}, {"$set": old})


def share_file(file_id, shared=True):
    old = file_map.find_one({"_id": file_id})
    old["shared"] = shared
    file_map.update_one({"_id": file_id}, {"$set": old})
    star_map.update_one({"_id": file_id}, {"$set": old})


def delete_file(file_id):
    details = file_map.find_one_and_delete({"_id": file_id})
    remove_size(details["service_acc_num"], details["file_size"])
    remove_star(file_id)


def insert_size_map(sa_num, size=0):
    file_path = f"accounts\\{sa_num}.json"
    with open(file_path, "r") as f:
        ce = json.load(f)['client_email']
    sa_size_map.insert_one({"_id": sa_num, "size": size,"email":ce})


def get_sa_size_taken(sa_num):
    return sa_size_map.find_one({"_id": sa_num})


def add_size(sa_num, size):
    old = sa_size_map.find_one({"_id": sa_num})
    if not old:
        insert_size_map(sa_num, size)
        return
    new_size = size + old["size"]
    sa_size_map.update_one({"_id": sa_num}, {"$set": {"_id": sa_num, "size": new_size}})


def get_size_map():
    return list(sa_size_map.find())

# 15784004812 => 14.7 gb


def get_sa_num(email):
    x = sa_size_map.find_one({"email": email})
    if x:
        return x.get('_id',None)
    return None

def find_children(parent_id):
    return list(file_map.find({"parent_id": parent_id}))


def remove_size(sa_num, size):
    old = sa_size_map.find_one({"_id": sa_num})
    if not old:
        insert_size_map(sa_num, size=0)
        return
    new_size = old["size"] - size
    sa_size_map.update_one({"_id": sa_num}, {"$set": {"_id": sa_num, "size": new_size}})


def add_star(file_id):
    details = get_file_details(file_id)
    try:
        star_map.insert_one(details)
    except DuplicateKeyError:
        logger.warning(f"Item with file_id {file_id} is already starred.")


def remove_star(file_id):
    star_map.delete_one({"_id": file_id})


def get_starred_children(parent_id):
    return list(star_map.find({"parent_id": parent_id}))


def get_starred_files():
    return list(star_map.find())


def search_for_file_contains(value):
    return list(file_map.find({ 'file_name' : { '$regex' : '.*' + value + '.*', '$options' : 'i' } }))


def space_details():
    ls = [i['size'] for i in sa_size_map.find({},{'size':1,'_id':0})]
    available =  15784004812*len(ls)
    occupied = sum(ls)
    return occupied,available


def folder_exists(name,parent_id):
    t = file_map.find_one({'parent_id':parent_id,'file_name':name,'type':'folder'},{'_id':1})
    if t:
        return t['_id']
    else:
        return None
