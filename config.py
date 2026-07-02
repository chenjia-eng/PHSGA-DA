# import os

# SECRET_KEY = os.urandom(24)

# DEBUG = True

# HOSTNAME = '127.0.0.1'
# PORT = '3306'
# DATABASE = 'db1'
# USERNAME = 'root'
# PASSWORD = 'Gmq123456'

# DB_URI = "mysql+pymysql://{username}:{password}@{host}:{port}/{db}?charset=utf8".format(username=USERNAME,password=PASSWORD,host=HOSTNAME,port=PORT,db=DATABASE)
# SQLALCHEMY_DATABASE_URI = DB_URI
# SQLALCHEMY_TRACK_MODIFICATIONS = False

# path1 = os.path.abspath(__file__)
# PJ_PATH = os.path.dirname(path1)
# SAMPLE_PATH_OLD = PJ_PATH + "data/sample_old/"
# SAMPLE_PATH_PRE = PJ_PATH + "data/sample_pre/"
# PREDICTION_RESULT_PATH = PJ_PATH + "prediction_result/"

# ALLOWED_EXTENSIONS = set(['fasta'])

# # 在config.py中设置
# WTF_CSRF_ENABLED = False

import os

SECRET_KEY = os.urandom(24)

DEBUG = True

# ======================================
# 核心修改：彻底替换为 SQLite 数据库（无需安装MySQL）
# ======================================
SQLALCHEMY_DATABASE_URI = "sqlite:///plant.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

path1 = os.path.abspath(__file__)
PJ_PATH = os.path.dirname(path1)
SAMPLE_PATH_OLD = PJ_PATH + "/data/sample_old/"
SAMPLE_PATH_PRE = PJ_PATH + "/data/sample_pre/"
PREDICTION_RESULT_PATH = PJ_PATH + "/prediction_result/"

ALLOWED_EXTENSIONS = set(['fasta'])

# 在config.py中设置
WTF_CSRF_ENABLED = False