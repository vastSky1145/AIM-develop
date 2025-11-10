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

#根据json数组插入远程mongodb数据(用户名sxs)
def insert_remote_mongodb_data(json_array):
    remote_client = pymongo.MongoClient("mongodb://192.168.1.96:27017/")
    remote_db = remote_client["research_papers"]
    remote_collection = remote_db["users"]
    for user in json_array:
        password = user["password"]
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user["password_hash"] = password_hash
        
        user_to_insert = {
            "username": user["username"],
            "password_hash": password_hash
        }
        remote_collection.insert_one(user_to_insert)
        print(f"插入用户{user['username']}成功")
    print("插入所有用户成功")


if __name__ == '__main__':
#用户
# 群主
# 蒋万春
#
# 汪凯
#
# 金宇文
#
# 李昊阳
#
# 苏宪时
#
# 胡锦天
#
# 杨嘉睿
#
# 单永新
#
# 胡裕杰
#
# 韩笑
#
# 谢志贤
#
# 吴科迪
#
# 曾冠程
#
# 唐玉秀
#
# 胡宇轩
#
# 高浩天
#
# 杨子昕
    user_array = [
        {
            "username": "jwc",
            "password": "123456"
        },
        {
            "username": "wk",
            "password": "123456"
        },
        {
            "username": "jyw",
            "password": "123456"
        },
        {
            "username": "lhj",
            "password": "123456"
        },
        {
            "username": "sxs",
            "password": "123456"
        },
        {
            "username": "hjt",
            "password": "123456"
        },
        {
            "username": "yjr",
            "password": "123456"
        },
        {
            "username": "syx",
            "password": "123456"
        },
        {
            "username": "hjy",
            "password": "123456"
        },
        {
            "username": "hx",
            "password": "123456"
        },
        {
            "username": "xzx",
            "password": "123456"
        },
        {
            "username": "wkd",
            "password": "123456"
        },
        {
            "username": "zgc",
            "password": "123456"
        },
        {
            "username": "tyx",
            "password": "123456"
        },
        {
            "username": "hyx",
            "password": "123456"
        },
        {
            "username": "ght",
            "password": "123456"
        },
        {
            "username": "yzx",
            "password": "123456"
        }
    ]

    insert_remote_mongodb_data(user_array)