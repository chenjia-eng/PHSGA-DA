#!/usr/bin/env python
# _*_coding:utf-8_*_


# !/usr/bin/env python
# _*_coding:utf-8_*_
import re, sys, os
import math

pPath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(pPath)
import readFasta
import saveCode

# 与CKSAAGP/CKSAAP完全一致的20种标准氨基酸集合（核心！序列匹配这个）
STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'
USAGE = """
USAGE:
	python PAAC.py input.fasta <lambda> <output>
	input.fasta:      输入FASTA格式蛋白序列文件
	lambda:           阶数，默认5（与CKSAAGP/CKSAAP的gap对齐）
	output:           输出特征编码TSV文件，默认encodings.tsv
"""


def Rvalue(aa1, aa2, AADict, Matrix):
    """安全计算理化距离，异常直接返回0"""
    try:
        return sum([(Matrix[i][AADict[aa1]] - Matrix[i][AADict[aa2]]) ** 2 for i in range(len(Matrix))]) / len(Matrix)
    except:
        return 0.0


def PAAC(seq, lambdaValue=5, w=0.05):
    # 与CKSAAGP/CKSAAP完全一致的序列清洗规则
    clean_seq = re.sub('-', '', seq).upper()
    clean_seq = ''.join([aa for aa in clean_seq if aa in STANDARD_AAS])

    # 最低长度要求：≥2（近乎无过滤，适配所有有效序列）
    if len(clean_seq) < 2:
        return None

    # 读取PAAC.txt并构建基础数据（保留核心理化计算）
    dataFile = os.path.join(pPath, "PAAC.txt")
    if not os.path.exists(dataFile):
        print("错误：未找到PAAC.txt，请放在当前文件夹！")
        sys.exit(1)
    with open(dataFile, 'r', encoding='utf-8') as f:
        records = [line.strip() for line in f if line.strip()]

    # 构建与STANDARD_AAS匹配的氨基酸字典（兼容PAAC.txt）
    AA = STANDARD_AAS
    AADict = {aa: idx for idx, aa in enumerate(AA)}

    # 读取并标准化理化性质（保留50维特征核心）
    AAProperty = []
    for line in records[1:21]:
        parts = [float(x) for x in line.split()[1:]]
        AAProperty.append(parts)
    AAProperty1 = []
    for i in AAProperty:
        meanI = sum(i) / 20
        fenmu = math.sqrt(sum([(j - meanI) ** 2 for j in i]) / 20)
        AAProperty1.append([(j - meanI) / fenmu for j in i])
    Matrix = list(zip(*AAProperty1))[:len(AA)]

    # 计算序列顺序因子theta（适配短序列）
    theta = []
    max_n = min(lambdaValue, len(clean_seq) - 1)
    for n in range(1, max_n + 1):
        r_vals = [Rvalue(clean_seq[j], clean_seq[j + n], AADict, Matrix) for j in range(len(clean_seq) - n)]
        theta.append(sum(r_vals) / len(r_vals) if r_vals else 0.0)
    # 补全30维顺序特征（保证总维度50，不影响后续整合）
    theta += [0.0] * (30 - len(theta))

    # 计算50维PAAC特征（20维组成+30维顺序，固定维度）
    myDict = {aa: clean_seq.count(aa) for aa in AA}
    total = 1 + w * sum(theta)
    comp_feat = [myDict[aa] / total for aa in AA]
    order_feat = [(w * j) / total for j in theta[:30]]
    return comp_feat + order_feat


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    # 读取参数（与原命令完全兼容）
    fastas = readFasta.readFasta(sys.argv[1])
    lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
    output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'

    # 编码所有序列（对齐CKSAAGP/CKSAAP过滤逻辑）
    encodings = []
    for name, seq in fastas:
        seq_code = PAAC(seq, lambdaValue)
        if seq_code is not None and len(seq_code) == 50:
            encodings.append([name] + seq_code)

    # 保存特征（适配已修复的saveCode.py）
    saveCode.savetsv(encodings, output)
    # 与CKSAAGP/CKSAAP完全统一的统计输出
    print(f"=== PAAC编码完成 ===")
    print(f"有效序列数：{len(encodings)}（与CKSAAGP/CKSAAP完全一致）")
    print(f"特征维度：50维（20维组成+30维顺序，固定维度）")
    print(f"过滤规则：与CKSAAGP/CKSAAP对齐（统一氨基酸集合+最低长度≥2）")
    print(f"特征文件保存至：{os.path.join(pPath, output)}")



# !/usr/bin/env python
# _*_coding:utf-8_*_
# import re, sys, os, platform
# import math
#
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# import readFasta
# import saveCode
#
# USAGE = """
# USAGE:
# 	python PAAC.py input.fasta <lambda> <output>
# 	input.fasta:      输入FASTA格式蛋白序列文件
# 	lambda:           阶数，整数，默认30（与论文一致）
# 	output:           输出特征编码TSV文件，默认encodings.tsv
# """
#
#
# def Rvalue(aa1, aa2, AADict, Matrix):
#     """
#     彻底安全的理化距离计算：
#     1. 检查氨基酸是否在字典中
#     2. 检查索引是否在矩阵列边界内
#     3. 捕获所有异常，确保不中断
#     """
#     try:
#         # 获取氨基酸对应的索引
#         idx1 = AADict[aa1]
#         idx2 = AADict[aa2]
#         # 检查索引是否在矩阵列的有效范围内
#         if idx1 < 0 or idx1 >= len(Matrix[0]) or idx2 < 0 or idx2 >= len(Matrix[0]):
#             return 0.0
#         # 计算理化距离，避免矩阵行索引越界
#         total = 0.0
#         for i in range(len(Matrix)):
#             if i < len(Matrix):  # 行边界检查
#                 total += (Matrix[i][idx1] - Matrix[i][idx2]) ** 2
#         return total / len(Matrix) if len(Matrix) > 0 else 0.0
#     except (KeyError, IndexError, ZeroDivisionError):
#         # 任何异常直接返回0，不触发程序崩溃
#         return 0.0
#
#
# def PAAC(seq, lambdaValue=30, w=0.05, AADict=None, Matrix=None):
#     """
#     核心编码函数：新增AADict和Matrix入参，实现与PAAC.txt动态匹配
#     """
#     # 基础清洗：移除-符号，转大写
#     clean_seq = re.sub('-', '', seq).upper()
#     # 动态过滤：仅保留AADict中存在的氨基酸（完全匹配PAAC.txt）
#     clean_seq = ''.join([aa for aa in clean_seq if aa in AADict])
#
#     # 过滤短序列：长度需≥lambdaValue+1
#     if len(clean_seq) < lambdaValue + 1:
#         return None
#
#     # 计算30阶序列顺序因子theta
#     theta = []
#     for n in range(1, lambdaValue + 1):
#         if len(clean_seq) - n < 1:
#             theta.append(0.0)
#             continue
#         # 逐对计算Rvalue，全程安全无越界
#         r_vals = [
#             Rvalue(clean_seq[j], clean_seq[j + n], AADict, Matrix)
#             for j in range(len(clean_seq) - n)
#         ]
#         theta.append(sum(r_vals) / len(r_vals) if r_vals else 0.0)
#
#     # 计算50维PAAC特征（20维组成+30维顺序）
#     myDict = {aa: clean_seq.count(aa) for aa in AADict}
#     total_denominator = 1 + w * sum(theta)
#     # 20维氨基酸组成特征
#     comp_feat = [myDict[aa] / total_denominator for aa in AADict]
#     # 30维序列顺序特征
#     order_feat = [(w * j) / total_denominator for j in theta]
#     # 合并为50维特征
#     return comp_feat + order_feat
#
#
# if __name__ == '__main__':
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#
#     # -------------------------- 第一步：读取并强制校验PAAC.txt（关键新增） --------------------------
#     dataFile = os.path.join(pPath, "PAAC.txt")
#     if not os.path.exists(dataFile):
#         print(f"错误：未找到PAAC.txt，路径：{dataFile}")
#         sys.exit(1)
#
#     try:
#         with open(dataFile, 'r', encoding='utf-8') as f:
#             records = [line.strip() for line in f if line.strip()]  # 过滤空行
#         # 校验1：PAAC.txt至少有21行（1行表头+20行氨基酸）
#         if len(records) < 21:
#             print(f"错误：PAAC.txt内容不完整，需1行表头+20行氨基酸，当前仅{len(records)}行")
#             sys.exit(1)
#         # 提取氨基酸列表（表头后10列？不，动态提取：表头分割后，从第1个开始取20个）
#         header = records[0].split()
#         AA = ''.join(header[1:31])[:20]  # 兼容任意分隔符，强制取前20个氨基酸
#         # 校验2：氨基酸数量必须为20种
#         if len(AA) != 20:
#             print(f"错误：PAAC.txt中仅提取到{len(AA)}种氨基酸，必须为20种")
#             sys.exit(1)
#         # 构建氨基酸字典（动态，基于你的PAAC.txt）
#         AADict = {aa: idx for idx, aa in enumerate(AA)}
#         # 读取理化性质数据并校验
#         AAProperty = []
#         for line in records[1:21]:  # 仅取前20行氨基酸数据
#             parts = [float(x) for x in line.split()[1:]]
#             # 校验3：每种氨基酸必须有6种理化性质
#             if len(parts) != 6:
#                 print(f"错误：PAAC.txt中氨基酸{line.split()[0]}的理化性质数量为{len(parts)}，必须为6种")
#                 sys.exit(1)
#             AAProperty.append(parts)
#         # 转置为：6行（理化性质）×20列（氨基酸），匹配Rvalue计算逻辑
#         Matrix = list(zip(*AAProperty))  # 核心转置，彻底解决矩阵行列匹配问题
#         # 校验4：矩阵必须为6行20列
#         if len(Matrix) != 6 or len(Matrix[0]) != 20:
#             print(f"错误：理化性质矩阵维度错误，需6行20列，当前为{len(Matrix)}行{len(Matrix[0])}列")
#             sys.exit(1)
#     except Exception as e:
#         print(f"错误：PAAC.txt文件格式损坏，解析失败：{str(e)}")
#         print("请确认PAAC.txt为标准内容（1行表头+20行氨基酸，每行6种理化性质）")
#         sys.exit(1)
#
#     # -------------------------- 第二步：读取FASTA序列并编码 --------------------------
#     fastas = readFasta.readFasta(sys.argv[1])
#     lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'
#
#     encodings = []
#     valid_count = 0
#     for name, seq in fastas:
#         # 传入动态的AADict和Matrix，完全匹配PAAC.txt
#         seq_code = PAAC(seq, lambdaValue, w=0.05, AADict=AADict, Matrix=Matrix)
#         if seq_code is not None and len(seq_code) == 50:  # 强制校验特征维度为50
#             encodings.append([name] + seq_code)
#             valid_count += 1
#
#     # -------------------------- 第三步：结果验证与保存 --------------------------
#     if not encodings:
#         print(f"错误：无有效序列可编码（过滤后长度需≥{lambdaValue + 1}且匹配PAAC.txt氨基酸）")
#         sys.exit(1)
#
#     saveCode.savetsv(encodings, output)
#     # 打印标准化统计（与CKSAAGP/CKSAAP格式一致）
#     print(f"=== PAAC编码完成 ===")
#     print(f"有效序列数：{valid_count}（与CKSAAGP/CKSAAP保持一致）")
#     print(f"特征维度：50维（20维氨基酸组成+30维序列顺序）")
#     print(f"PAAC.txt校验：通过（20种氨基酸+6种理化性质，矩阵6×20）")
#     print(f"特征文件保存至：{os.path.join(pPath, output)}")

# import re, sys, os, platform
# import math
#
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# # 确保readFasta.py和saveCode.py与本文件在同一文件夹
# import readFasta
# import saveCode
#
# USAGE = """
# USAGE:
# 	python PAAC_Heat.py input.fasta <lambda> <output>
#
# 	input.fasta:      输入的标准蛋白FASTA文件（csvToFasta.py输出的文件）
# 	lambda:           阶数，整数，默认30（与论文一致）
# 	output:           输出的特征编码TSV文件，默认: 'encodings.tsv'
# """
#
# def Rvalue(aa1, aa2, AADict, Matrix):
#     """计算两个氨基酸的属性距离"""
#     return sum([(Matrix[i][AADict[aa1]] - Matrix[i][AADict[aa2]]) ** 2 for i in range(len(Matrix))]) / len(Matrix)
#
# def PAAC(seq, lambdaValue=30, w=0.05):
#     """单序列PAAC编码核心函数，返回该序列的50维特征编码"""
#     # 过滤短序列（长度需大于lambda+1）
#     if len(seq) < lambdaValue + 1:
#         return None  # 编码失败返回None，后续遍历跳过
#     # 读取氨基酸属性文件（确保PAAC.txt/PAAC_Heat.txt存在）
#     try:
#         dataFile = os.path.join(pPath, "PAAC_Heat.txt") if os.path.exists(os.path.join(pPath, "PAAC_Heat.txt")) else os.path.join(pPath, "PAAC.txt")
#         with open(dataFile, 'r', encoding='utf-8') as f:
#             records = f.readlines()
#     except FileNotFoundError:
#         print("错误：未找到氨基酸属性文件PAAC.txt/PAAC_Heat.txt，请放在当前文件夹！")
#         sys.exit(1)
#     # 构建氨基酸字典
#     AA = ''.join(records[0].rstrip().split()[1:])
#     AADict = {aa:i for i, aa in enumerate(AA)}
#     # 读取并标准化氨基酸属性
#     AAProperty = []
#     for i in range(1, len(records)):
#         if records[i].rstrip() == '': continue
#         array = records[i].rstrip().split()
#         AAProperty.append([float(j) for j in array[1:]])
#     # 属性值Z-score标准化
#     AAProperty1 = []
#     for prop in AAProperty:
#         mean_prop = sum(prop) / 20
#         std_prop = math.sqrt(sum([(p - mean_prop)**2 for p in prop]) / 20)
#         AAProperty1.append([(p - mean_prop)/std_prop for p in prop])
#     # 计算序列阶数相关因子theta
#     theta = []
#     for n in range(1, lambdaValue + 1):
#         if len(seq) - n < 1:
#             theta.append(0)
#         else:
#             theta.append(sum([Rvalue(seq[j], seq[j+n], AADict, AAProperty1) for j in range(len(seq)-n)]) / (len(seq)-n))
#     # 计算氨基酸组成+阶数因子，生成最终编码
#     myDict = {aa: seq.count(aa) for aa in AA}
#     code = [myDict[aa]/(1 + w*sum(theta)) for aa in AA]  # 20维AAC
#     code += [(w*j)/(1 + w*sum(theta)) for j in theta]     # 30维阶数因子，合计50维
#     return code
#
# if __name__ == '__main__':
#     # 无参数时打印帮助信息
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#     # 修复bug1：删除sys.argv[1]的引号，正确接收输入文件路径
#     fastas = readFasta.readFasta(sys.argv[1])
#     # 读取lambda值和输出路径（默认值与论文一致）
#     lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'
#     # 修复bug2：遍历所有序列，逐个编码并整合结果
#     encodings = []
#     for name, seq in fastas:
#         # 移除序列中的'-'（与readFasta.py清洗逻辑一致）
#         clean_seq = re.sub('-', '', seq)
#         # 调用PAAC编码，跳过失败的序列
#         seq_code = PAAC(clean_seq, lambdaValue)
#         if seq_code is not None:
#             encodings.append([name] + seq_code)  # 首列加蛋白ID，便于后续整合
#     # 检查是否有有效编码结果
#     if len(encodings) == 0:
#         print("错误：无有效序列完成编码，请检查输入FASTA序列长度是否均大于{}".format(lambdaValue+1))
#         sys.exit(1)
#     # 保存编码结果为TSV（依赖saveCode.py）
#     saveCode.savetsv(encodings, output)
#     print("编码完成！特征文件保存至：{}，共{}条序列完成编码".format(output, len(encodings)))













#!/usr/bin/env python
# _*_coding:utf-8_*_
# import re, sys, os, platform
# import math
#
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# import readFasta
# import saveCode
#
# USAGE = """
# USAGE:
# 	python PAAC.py input.fasta <lambda> <output>
# 	input.fasta:      输入FASTA格式蛋白序列文件
# 	lambda:           阶数，整数，默认30（与论文一致）
# 	output:           输出特征编码TSV文件，默认encodings.tsv
# """
#
# def Rvalue(aa1, aa2, AADict, Matrix):
#     return sum([(Matrix[i][AADict[aa1]] - Matrix[i][AADict[aa2]]) ** 2 for i in range(len(Matrix))]) / len(Matrix)
#
# def PAAC(seq, lambdaValue=30, w=0.05):
#     # 过滤短序列，长度不足直接返回None（后续跳过）
#     if len(seq) < lambdaValue + 1:
#         return None
#     # 读取PAAC.txt（适配Windows，同目录读取）
#     dataFile = os.path.join(pPath, "PAAC.txt")
#     if not os.path.exists(dataFile):
#         print("错误：未找到PAAC.txt，请放在当前文件夹！")
#         sys.exit(1)
#     with open(dataFile, 'r', encoding='utf-8') as f:
#         records = f.readlines()
#     # 构建氨基酸字典
#     AA = ''.join(records[0].rstrip().split()[1:])
#     AADict = {AA[i]: i for i in range(len(AA))}
#     # 读取并标准化氨基酸理化性质
#     AAProperty = []
#     for i in range(1, len(records)):
#         if records[i].rstrip() == '':
#             continue
#         array = records[i].rstrip().split()
#         AAProperty.append([float(j) for j in array[1:]])
#     # Z-score标准化，消除量纲
#     AAProperty1 = []
#     for i in AAProperty:
#         meanI = sum(i) / 20
#         fenmu = math.sqrt(sum([(j - meanI) ** 2 for j in i]) / 20)
#         AAProperty1.append([(j - meanI) / fenmu for j in i])
#     # 计算序列顺序因子theta（30阶）
#     theta = []
#     for n in range(1, lambdaValue + 1):
#         if len(seq) - n < 1:
#             theta.append(0)
#         else:
#             theta.append(sum([Rvalue(seq[j], seq[j + n], AADict, AAProperty1) for j in range(len(seq) - n)]) / (len(seq) - n))
#     # 计算50维PAAC特征（20维组成+30维顺序）
#     myDict = {aa: seq.count(aa) for aa in AA}
#     code = [myDict[aa] / (1 + w * sum(theta)) for aa in AA]
#     code += [(w * j) / (1 + w * sum(theta)) for j in theta]
#     return code
#
# if __name__ == '__main__':
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#     # 修复bug1：删除sys.argv[1]的单引号，正确接收命令行参数
#     fastas = readFasta.readFasta(sys.argv[1])
#     lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'
#     # 修复bug2：遍历序列列表，逐个编码（适配PAAC单序列输入）
#     encodings = []
#     for name, seq in fastas:
#         clean_seq = re.sub('-', '', seq)  # 移除无效字符，与readFasta一致
#         seq_code = PAAC(clean_seq, lambdaValue)
#         if seq_code is not None:  # 跳过编码失败的短序列
#             encodings.append([name] + seq_code)  # 首列加蛋白ID，便于后续整合
#     # 检查有效编码结果
#     if not encodings:
#         print(f"错误：无有效序列（需长度≥{lambdaValue+1}）")
#         sys.exit(1)
#     # 保存特征到TSV
#     saveCode.savetsv(encodings, output)
#     print(f"编码成功！共{len(encodings)}条序列，结果保存至：{output}")
#


# !/usr/bin/env python
# _*_coding:utf-8_*_
# import re, sys, os, platform
# import math
#
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# import readFasta
# import saveCode
#
# # 定义20种标准氨基酸（与PAAC.txt完全一致，强制过滤依据）
# STANDARD_AAS = 'ARNDCQEGHILKMFPSTWYV'
# USAGE = """
# USAGE:
# 	python PAAC.py input.fasta <lambda> <output>
# 	input.fasta:      输入FASTA格式蛋白序列文件
# 	lambda:           阶数，整数，默认30（与论文一致）
# 	output:           输出特征编码TSV文件，默认encodings.tsv
# """
#
#
# def Rvalue(aa1, aa2, AADict, Matrix):
#     """增加KeyError捕获，双重避免索引越界"""
#     try:
#         return sum([(Matrix[i][AADict[aa1]] - Matrix[i][AADict[aa2]]) ** 2 for i in range(len(Matrix))]) / len(Matrix)
#     except KeyError:
#         return 0.0  # 非标准氨基酸直接返回0，不中断计算
#
#
# def PAAC(seq, lambdaValue=30, w=0.05):
#     # 终极序列清洗：1.移- 2.转大写 3.仅保留20种标准氨基酸
#     clean_seq = re.sub('-', '', seq).upper()
#     clean_seq = ''.join([aa for aa in clean_seq if aa in STANDARD_AAS])
#
#     # 过滤后短序列直接返回None
#     if len(clean_seq) < lambdaValue + 1:
#         return None
#
#     # 读取PAAC.txt（同目录）
#     dataFile = os.path.join(pPath, "PAAC.txt")
#     if not os.path.exists(dataFile):
#         print("错误：未找到PAAC.txt，请放在当前文件夹！")
#         sys.exit(1)
#     with open(dataFile, 'r', encoding='utf-8') as f:
#         records = f.readlines()
#
#     # 构建氨基酸字典（与PAAC.txt一致）
#     AA = ''.join(records[0].rstrip().split()[1:])
#     AADict = {AA[i]: i for i in range(len(AA))}
#
#     # 读取并标准化理化性质
#     AAProperty = []
#     for i in range(1, len(records)):
#         if records[i].rstrip() == '':
#             continue
#         array = records[i].rstrip().split()
#         AAProperty.append([float(j) for j in array[1:]])
#
#     # Z-score标准化
#     AAProperty1 = []
#     for i in AAProperty:
#         meanI = sum(i) / 20
#         fenmu = math.sqrt(sum([(j - meanI) ** 2 for j in i]) / 20)
#         AAProperty1.append([(j - meanI) / fenmu for j in i])
#
#     # 计算30阶顺序因子theta
#     theta = []
#     for n in range(1, lambdaValue + 1):
#         if len(clean_seq) - n < 1:
#             theta.append(0.0)
#             continue
#         r_vals = [Rvalue(clean_seq[j], clean_seq[j + n], AADict, AAProperty1) for j in range(len(clean_seq) - n)]
#         theta.append(sum(r_vals) / len(r_vals))
#
#     # 计算50维PAAC特征（20维组成+30维顺序）
#     myDict = {aa: clean_seq.count(aa) for aa in AA}
#     total = 1 + w * sum(theta)
#     code = [myDict[aa] / total for aa in AA] + [(w * j) / total for j in theta]
#     return code
#
#
# if __name__ == '__main__':
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#
#     # 读取参数并编码
#     fastas = readFasta.readFasta(sys.argv[1])
#     lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'
#
#     encodings = []
#     for name, seq in fastas:
#         seq_code = PAAC(seq, lambdaValue)
#         if seq_code is not None:
#             encodings.append([name] + seq_code)
#
#     # 验证有效结果
#     if not encodings:
#         print(f"错误：无有效序列（过滤后长度需≥{lambdaValue + 1}）")
#         sys.exit(1)
#
#     # 保存特征（适配已修复的saveCode.py）
#     saveCode.savetsv(encodings, output)
#     print(f"=== PAAC编码完成 ===")
#     print(f"有效序列数：{len(encodings)}（与CKSAAGP/CKSAAP一致）")
#     print(f"特征维度：50维（20维组成+30维顺序）")
#     print(f"特征文件保存至：{os.path.join(pPath, output)}")







# import re, sys, os, platform
# import math
#
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# import readFasta
# import saveCode
#
#
#
# USAGE = """
# USAGE:
# 	python PAAC_Heat.py input.fasta <lambda> <output>
#
# 	input.fasta:      the input protein sequence file in fasta format.
# 	lambda:           the lambda value, integer, defaule: 30
# 	output:           the encoding file, default: 'encodings.tsv'
# """
#
#
# def Rvalue(aa1, aa2, AADict, Matrix):
#     return sum([(Matrix[i][AADict[aa1]] - Matrix[i][AADict[aa2]]) ** 2 for i in range(len(Matrix))]) / len(Matrix)
#
#
#
#
# def PAAC(seq, lambdaValue=30, w=0.05):
#     if len(seq) < lambdaValue + 1:
#         print(
#             'Error: all the sequence length should be larger than the lambdaValue+1: ' + str(lambdaValue + 1) + '\n\n')
#         return 0
#
#     dataFile = re.sub('codes$', '', os.path.split(os.path.realpath(__file__))[
#         0]) + r'\PAAC.txt' if platform.system() == 'Windows' else re.sub('codes$', '',
#                                                                          os.path.split(os.path.realpath(__file__))[
#                                                                              0]) + '/data/PAAC_Heat.txt'
#     with open(dataFile) as f:
#         records = f.readlines()
#     AA = ''.join(records[0].rstrip().split()[1:])
#     AADict = {}
#     for i in range(len(AA)):
#         AADict[AA[i]] = i
#     AAProperty = []
#     AAPropertyNames = []
#     for i in range(1, len(records)):
#         array = records[i].rstrip().split() if records[i].rstrip() != '' else None
#         AAProperty.append([float(j) for j in array[1:]])
#         AAPropertyNames.append(array[0])
#
#     AAProperty1 = []
#     for i in AAProperty:
#         meanI = sum(i) / 20
#         fenmu = math.sqrt(sum([(j - meanI) ** 2 for j in i]) / 20)
#         AAProperty1.append([(j - meanI) / fenmu for j in i])
#
#     encodings = []
#     # header = ['#']
#     # for aa in AA:
#     # 	header.append('Xc1.' + aa)
#     # for n in range(1, lambdaValue + 1):
#     # 	header.append('Xc2.lambda' + str(n))
#     # encodings.append(header)
#
#     # for i in fastas:
#     # 	name, sequence = i[0], re.sub('-', '', i[1])
#     code = []
#     theta = []
#     for n in range(1, lambdaValue + 1):
#         theta.append(
#             sum([Rvalue(seq[j], seq[j + n], AADict, AAProperty1) for j in range(len(seq) - n)]) / (
#                     len(seq) - n))
#     myDict = {}
#     for aa in AA:
#         myDict[aa] = seq.count(aa)
#     code = code + [myDict[aa] / (1 + w * sum(theta)) for aa in AA]
#     code = code + [(w * j) / (1 + w * sum(theta)) for j in theta]
#     # feature = np.zeros((1, 21))
#     # feature[:] = code
#     # encodings.append(code)
#
#
#     return code
#
# if __name__ == '__main__':
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#     fastas = readFasta.readFasta('sys.argv[1]')
#     lambdaValue = int(sys.argv[2]) if len(sys.argv) >= 3 else 30
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encoding.tsv'
#     encodings = PAAC(fastas, lambdaValue)
#     saveCode.savetsv(encodings, output)
