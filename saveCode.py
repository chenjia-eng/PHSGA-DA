#!/usr/bin/env python
#_*_coding:utf-8_*_

import sys

# def savetsv(encodings, file = 'encoding.tsv'):
# 	with open(file, 'w') as f:
# 		if encodings == 0:
# 			f.write('Descriptor calculation failed.')
# 		else:
# 			for i in range(len(encodings[0]) - 1):
# 				f.write(encodings[0][i] + '\t')
# 			f.write(encodings[0][-1] + '\n')
# 			for i in encodings[1:]:
# 				f.write(i[0] + '\t')
# 				for j in range(1, len(i) - 1):
# 					f.write(str(float(i[j])) + '\t')
# 				f.write(str(float(i[len(i)-1])) + '\n')
# 	return None


#!/usr/bin/env python
# _*_coding:utf-8_*_
# 通用特征保存脚本：支持字符串/数值混合类型，修复类型拼接错误
import os

def savetsv(encodings, outputfile):
    """
    将特征编码保存为TSV文件
    :param encodings: 特征列表，格式[[蛋白ID, 特征1, 特征2,...], [...]]
    :param outputfile: 输出文件路径
    """
    # 打开文件，指定UTF-8编码避免中文/特殊字符乱码
    with open(outputfile, 'w', encoding='utf-8') as f:
        # 遍历每一条序列的特征
        for row in encodings:
            # 核心修复：将所有元素统一转换为字符串，再拼接制表符
            str_row = [str(elem) for elem in row]
            # 用制表符分隔列，行尾加换行符
            f.write('\t'.join(str_row) + '\n')
    # 验证文件是否生成
    if os.path.exists(outputfile):
        return True
    else:
        print(f"错误：特征文件保存失败，未生成{outputfile}")
        return False

# # 测试用（可选，无需删除）
# if __name__ == '__main__':
#     test_encodings = [['Protein001', 0.123, 0.456, 0.789], ['Protein002', 0.987, 0.654, 0.321]]
#     savetsv(test_encodings, 'test_encodings.tsv')
#     print("测试文件保存成功！")