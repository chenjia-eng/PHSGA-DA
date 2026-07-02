import psutil

mem = psutil.virtual_memory()
# 系统总计内存
zj = float(mem.total) / 1024 / 1024 / 1024
print(zj)