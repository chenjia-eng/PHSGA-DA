# !/usr/bin/env python
# _*_coding:utf-8_*_
import sys, os, re

pPath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(pPath)
import readFasta
import saveCode

# 论文标准配置（不可改）
STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'  # 20种标准氨基酸
DEFAULT_K = 2  # 论文k=2
MIN_SEQ_LENGTH = 200  # 论文要求：移除＜200aa的序列
USAGE = """
USAGE:
	python CKSAAP.py input.fasta <k> <output> [aa_order]
	input.fasta:      输入筛选后的FASTA（≥200aa）
	k:                间隔值，默认2（论文固定）
	output:           输出特征TSV文件
"""


def CKSAAP(seq, k=DEFAULT_K, order=STANDARD_AAS):
    # 论文标准序列清洗
    clean_seq = re.sub('-', '', seq).upper()
    clean_seq = ''.join([aa for aa in clean_seq if aa in STANDARD_AAS])

    # 论文要求：序列≥200aa
    if len(clean_seq) < MIN_SEQ_LENGTH:
        return None

    # 生成400种氨基酸对（论文要求：20×20全组合）
    aaPairs = [aa1 + aa2 for aa1 in order for aa2 in order]
    code = []

    # 论文要求：遍历k=0、1、2三个间隔
    for gap in range(k + 1):
        pair_count = {pair: 0 for pair in aaPairs}
        total = 0
        # 计算当前间隔的氨基酸对数量
        for i in range(len(clean_seq)):
            j = i + gap + 1
            if j < len(clean_seq):
                aa1, aa2 = clean_seq[i], clean_seq[j]
                if aa1 in order and aa2 in order:
                    pair_count[aa1 + aa2] += 1
                    total += 1
        # 论文要求：频率归一化（次数/总数量）
        if total == 0:
            code += [0.0] * len(aaPairs)
        else:
            code += [pair_count[pair] / total for pair in aaPairs]

    # 验证特征维度（论文要求1200维）
    assert len(code) == 400 * (k + 1), f"特征维度错误，论文要求{400 * (k + 1)}维，当前{len(code)}维"
    return code


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    # 读取参数（k固定为2，按论文要求）
    fastas = readFasta.readFasta(sys.argv[1])
    k = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_K
    output = sys.argv[3] if len(sys.argv) >= 4 else 'CKSAAP_encodings_paper.tsv'

    # 编码所有符合要求的序列
    encodings = []
    valid_count = 0
    for name, seq in fastas:
        seq_code = CKSAAP(seq, k)
        if seq_code is not None:
            encodings.append([name] + seq_code)
            valid_count += 1

    # 保存特征
    if not encodings:
        print(f"错误：无有效序列（需≥{MIN_SEQ_LENGTH}aa+标准氨基酸）")
        sys.exit(1)
    saveCode.savetsv(encodings, output)
    print(f"=== CKSAAP编码完成（论文标准）===")
    print(f"有效序列数：{valid_count}")
    print(f"特征维度：{len(encodings[0]) - 1}维（400×{k + 1}，符合论文要求）")
    print(f"输出文件：{output}")


#!/usr/bin/env python
#_*_coding:utf-8_*_
# import sys, os, re
# pPath = os.path.split(os.path.realpath(__file__))[0]
# sys.path.append(pPath)
# import readFasta
# import saveCode
#
# # 定义20种标准氨基酸（用于序列清洗）
# STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'
# USAGE = """
# USAGE:
# 	python CKSAAP_Heat2.py input.fasta <k_space> <output> [aa_order]
# 	input.fasta:      输入FASTA格式蛋白序列文件
# 	k_space:          氨基酸间隔值，整数，默认5（论文通用）
# 	output:           输出特征编码TSV文件，默认encodings.tsv
# 	aa_order:         可选，氨基酸顺序（预设：alphabetically/polarity/sideChainVolume，或自定义20种AA串）
# """
#
# def CKSAAP(seq, gap=5, order='ACDEFGHIKLMNPQRSTVWY'):
#     """
#     CKSAAP核心编码函数
#     :param seq: 单条氨基酸序列字符串
#     :param gap: 间隔值，默认5
#     :param order: 氨基酸顺序，默认字母顺序，支持自定义
#     :return: 单条序列的CKSAAP特征向量/None（无效序列）
#     """
#     # 步骤1：严格序列清洗——移除-符号，保留仅20种标准氨基酸
#     clean_seq = re.sub('-', '', seq).upper()
#     clean_seq = ''.join([aa for aa in clean_seq if aa in STANDARD_AAS])
#     # 步骤2：短序列过滤——长度需≥gap+2，否则无有效氨基酸对
#     if len(clean_seq) < gap + 2:
#         return None
#     # 步骤3：生成400种氨基酸对（按指定顺序）
#     aaPairs = [aa1 + aa2 for aa1 in order for aa2 in order]
#     code = []
#     # 步骤4：遍历0~gap所有间隔值
#     for g in range(gap + 1):
#         myDict = {pair: 0 for pair in aaPairs}  # 初始化400个氨基酸对计数
#         sum_valid = 0  # 当前间隔的有效氨基酸对总数
#         # 遍历序列计算氨基酸对计数
#         for index1 in range(len(clean_seq)):
#             index2 = index1 + g + 1
#             if index2 < len(clean_seq):
#                 aa1, aa2 = clean_seq[index1], clean_seq[index2]
#                 if aa1 in order and aa2 in order:
#                     myDict[aa1 + aa2] += 1
#                     sum_valid += 1
#         # 步骤5：频率归一化——处理除0错误，sum=0则特征值全0
#         if sum_valid == 0:
#             code += [0.0 for _ in aaPairs]
#         else:
#             code += [myDict[pair] / sum_valid for pair in aaPairs]
#     return code
#
# if __name__ == '__main__':
#     # 定义3种预设氨基酸顺序
#     myAAorder = {
#         'alphabetically': 'ACDEFGHIKLMNPQRSTVWY',    # 字母顺序（默认）
#         'polarity': 'DENKRQHSGTAPYVMCWIFL',          # 极性顺序
#         'sideChainVolume': 'GASDPCTNEVHQILMKRFYW',   # 侧链体积顺序
#     }
#     kw = {'order': myAAorder['alphabetically']}  # 初始化默认顺序
#
#     # 无参数时打印帮助信息
#     if len(sys.argv) == 1:
#         print(USAGE)
#         sys.exit(1)
#
#     # 解析命令行参数
#     fastas = readFasta.readFasta(sys.argv[1])  # 读取FASTA序列列表
#     gap = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
#     output = sys.argv[3] if len(sys.argv) >= 4 else 'encodings.tsv'
#
#     # 处理第4个可选参数：自定义氨基酸顺序
#     if len(sys.argv) >= 5:
#         if sys.argv[4] in myAAorder:
#             kw['order'] = myAAorder[sys.argv[4]]
#         else:
#             # 过滤非法字符，仅保留20种标准氨基酸
#             tmpOrder = re.sub(f'[^{STANDARD_AAS}]', '', sys.argv[4].upper())
#             # 验证长度，确保是20种氨基酸，否则用默认
#             kw['order'] = tmpOrder if len(tmpOrder) == 20 else myAAorder['alphabetically']
#
#     # 遍历序列列表，逐个编码（修复核心bug：单序列传入）
#     encodings = []
#     valid_count = 0
#     invalid_count = 0
#     for name, seq in fastas:
#         seq_code = CKSAAP(seq, gap, **kw)
#         if seq_code is not None:
#             encodings.append([name] + seq_code)  # 首列加蛋白ID，便于后续特征整合
#             valid_count += 1
#         else:
#             invalid_count += 1
#
#     # 检查有效结果，避免保存空文件
#     if not encodings:
#         print(f"错误：无有效序列可编码（要求过滤后长度≥{gap+2}）")
#         sys.exit(1)
#
#     # 保存特征文件（你已修复saveCode.py的类型拼接bug，可直接用）
#     saveCode.savetsv(encodings, output)
#
#     # 打印运行统计信息
#     feature_dim = (gap + 1) * 400
#     print(f"=== CKSAAP编码完成 ===")
#     print(f"有效序列数：{valid_count}（已生成特征）")
#     print(f"无效序列数：{invalid_count}（短序列/杂字符过多，已过滤）")
#     print(f"氨基酸顺序：{kw['order'][:10]}...（{len(kw['order'])}种）")
#     print(f"特征维度：{feature_dim}维（gap={gap} → {gap+1}个间隔 × 400种氨基酸对）")
#     print(f"特征文件保存至：{os.path.join(pPath, output)}")