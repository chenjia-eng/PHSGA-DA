
# !/usr/bin/env python
# _*_coding:utf-8_*_
import sys, os, re

pPath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(pPath)
import readFasta
import saveCode

# 论文标准配置（不可改）
STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'
DEFAULT_K = 2  # 论文k=2
MIN_SEQ_LENGTH = 200  # 论文要求：≥200aa
# 论文固定的5组氨基酸分组（不可改）
AA_GROUP = {
    'alphaticr': 'GAVLMI',
    'aromatic': 'FYW',
    'postivecharger': 'KRH',
    'negativecharger': 'DE',
    'uncharger': 'STCPNQ'
}
USAGE = """
USAGE:
	python CKSAAGP.py input.fasta <k> <output>
	input.fasta:      输入筛选后的FASTA（≥200aa）
	k:                间隔值，默认2（论文固定）
	output:           输出特征TSV文件
"""


def generate_group_pairs(group_keys):
    """生成论文要求的25种组对（5×5）"""
    return [k1 + '.' + k2 for k1 in group_keys for k2 in group_keys]


def CKSAAGP(seq, k=DEFAULT_K):
    # 论文标准序列清洗
    clean_seq = re.sub('-', '', seq).upper()
    clean_seq = ''.join([aa for aa in clean_seq if aa in STANDARD_AAS])

    # 论文要求：序列≥200aa
    if len(clean_seq) < MIN_SEQ_LENGTH:
        return None

    group_keys = list(AA_GROUP.keys())
    # 构建氨基酸→分组的映射（论文固定）
    aa2group = {aa: g for g in group_keys for aa in AA_GROUP[g]}
    # 生成25种组对（论文固定顺序）
    group_pairs = generate_group_pairs(group_keys)
    code = []

    # 论文要求：遍历k=0、1、2三个间隔
    for gap in range(k + 1):
        pair_count = {gp: 0 for gp in group_pairs}
        total = 0
        # 计算当前间隔的组对数量
        for i in range(len(clean_seq)):
            j = i + gap + 1
            if j < len(clean_seq):
                aa1, aa2 = clean_seq[i], clean_seq[j]
                if aa1 in aa2group and aa2 in aa2group:
                    gp = aa2group[aa1] + '.' + aa2group[aa2]
                    pair_count[gp] += 1
                    total += 1
        # 论文要求：频率归一化
        if total == 0:
            code += [0.0] * len(group_pairs)
        else:
            code += [pair_count[gp] / total for gp in group_pairs]

    # 验证特征维度（论文要求75维）
    assert len(code) == 25 * (k + 1), f"特征维度错误，论文要求{25 * (k + 1)}维，当前{len(code)}维"
    return code


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    # 读取参数（k固定为2）
    fastas = readFasta.readFasta(sys.argv[1])
    k = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_K
    output = sys.argv[3] if len(sys.argv) >= 4 else 'CKSAAGP_encodings_paper.tsv'

    # 编码所有符合要求的序列
    encodings = []
    valid_count = 0
    for name, seq in fastas:
        seq_code = CKSAAGP(seq, k)
        if seq_code is not None:
            encodings.append([name] + seq_code)
            valid_count += 1

    # 保存特征
    if not encodings:
        print(f"错误：无有效序列（需≥{MIN_SEQ_LENGTH}aa+标准氨基酸）")
        sys.exit(1)
    saveCode.savetsv(encodings, output)
    print(f"=== CKSAAGP编码完成（论文标准）===")
    print(f"有效序列数：{valid_count}")
    print(f"特征维度：{len(encodings[0]) - 1}维（25×{k + 1}，符合论文要求）")
    print(f"输出文件：{output}")