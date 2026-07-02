#!/usr/bin/env python
#_*_coding:utf-8_*_

import re, os, sys

def readFasta(file):
	if os.path.exists(file) == False:
		print('Error: "' + file + '" does not exist.')
		sys.exit(1)

	with open(file) as f:
		records = f.read()

	if re.search('>', records) == None:
		print('The input file seems not in fasta format.')
		sys.exit(1)

	records = records.split('>')[1:]
	myFasta = []
	for fasta in records:
		array = fasta.split('\n')
		name, sequence = array[0].split()[0], re.sub('[^ARNDCQEGHILKMFPSTWYV-]', '-', ''.join(array[1:]).upper())
		myFasta.append([name, sequence])
	return myFasta



# 这段代码是**标准化的FASTA格式文件读取工具函数**，
# 专为蛋白质序列设计，核心实现FASTA文件的有效性校验、格式解析与序列初步清洗，
# 返回规整的序列数据供后续预处理/编码使用：
# 1. 先导入正则（re）、文件路径（os）、程序退出（sys）依赖库，
# 定义接收文件路径的`readFasta`函数；
# 2. 前置校验：先判断文件是否存在，不存在则报错退出；
# 再用正则检查文件内容是否含FASTA标志性的`>`，无则判定非FASTA格式并退出，
# 避免无效输入；
# 3. 核心解析：将文件内容按`>`分割，剔除分割后空的首元素，
# 遍历每条FASTA条目，拆分出**序列名称**（取首行第一个空格前的唯一标识）
# 和**氨基酸序列**（拼接后续所有行）；
# 4. 序列清洗：将序列统一转为大写，把非20种标准氨基酸的异常字符替换为`-`，过滤噪声；
# 5. 结果返回：将每条序列的「名称、清洗后序列」封装为列表，
# 最终返回所有序列的二维列表，方便后续直接调用处理。