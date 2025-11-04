#测试mongodb连接
import bcrypt
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["research_papers"]
# collection = db["users"]
# user = collection.find_one({"username": "sxs"})
# print(user)
# user2 = collection.find_one({"username": "test"})
# print(user2)

# #插入另一个user，用户名为test，密码为123456
# password = "123456"
# password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
# collection.insert_one({"username": "test", "password_hash": password_hash})

#删除test用户
# collection.delete_one({"username": "test"})


# 显示所有collection
collections = db.list_collection_names()
#遍历collections
for collection in collections:
    print(collection)
    temp_collection = db[collection]
    # 打印temp_collection的每一项的键值对，并打印键值对之间的空行
    for item in temp_collection.find():
        for key, value in item.items():
            print(key, value)
        print("\n")