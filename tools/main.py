# # -*- coding: utf-8 -*-
# """
# tools/main.py
# =========================
# OneForAll: 从 FASTA 文件到 CSV 预测结果的完整流水线。

# 上游调用（apps/front/views.py 中）：
#     from tools.main import OneForAll
#     executor.submit(OneForAll(sample_name, species=species).run)

# 输入:  config.SAMPLE_PATH_OLD + <uuid>.fasta
# 输出:  config.PREDICTION_RESULT_PATH + <uuid>.csv         （4列：id,length,label,score）
#        config.PREDICTION_RESULT_PATH + <uuid>_done.csv    （完成标志，内容和上面一样）
#        config.PREDICTION_RESULT_PATH + <uuid>_error.log   （若出错才写）
# """

# import os
# import sys
# import re
# import csv
# import traceback
# import logging

# import numpy as np
# import torch

# # ---------- 让当前文件能找到 gao/ 根目录里的模块 ----------
# _TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
# _PROJECT_ROOT = os.path.dirname(_TOOLS_DIR)
# for p in (_PROJECT_ROOT, _TOOLS_DIR):
#     if p not in sys.path:
#         sys.path.insert(0, p)

# import config                       # gao/config.py
# import readFasta                    # gao/readFasta.py
# import CKSAAP                       # gao/CKSAAP.py
# import PAAC                         # gao/PAAC.py
# import CKSAAGP                      # gao/CKSAAGP.py

# from Mamba import MambaModel        # gao/tools/Mamba.py

# logger = logging.getLogger("tools.main")
# if not logger.handlers:
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s [%(levelname)s] %(message)s'
#     )


# # =========================================================
# # 全局模型（惰性加载，整个进程只加载一次）
# # =========================================================
# _MODEL = None
# _DEVICE = None

# def _get_device():
#     global _DEVICE
#     if _DEVICE is None:
#         _DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#     return _DEVICE


# def _load_model():
#     """全局只加载一次 best_model.pth"""
#     global _MODEL
#     if _MODEL is not None:
#         return _MODEL

#     model_path = os.path.join(config.PJ_PATH, "model", "best_model.pth")
#     if not os.path.isfile(model_path):
#         raise FileNotFoundError(f"找不到模型权重文件：{model_path}")

#     device = _get_device()
#     logger.info(f"加载模型: {model_path}  设备: {device}")

#     sd = torch.load(model_path, map_location=device)
#     model = MambaModel(
#         d_model=1325, d_state=16, d_conv=4, expand=2, num_classes=2,
#     )
#     missing, unexpected = model.load_state_dict(sd, strict=False)
#     if missing or unexpected:
#         logger.warning(f"权重加载不完全 missing={missing} unexpected={unexpected}")
#     model.to(device)
#     model.eval()
#     _MODEL = model
#     return _MODEL


# # =========================================================
# # 特征提取：对单条序列提取 1325 维特征
# # =========================================================
# STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'

# def _clean_seq(seq):
#     """和 CKSAAP/CKSAAGP/PAAC 的清洗逻辑保持一致"""
#     s = re.sub('-', '', seq).upper()
#     s = ''.join([a for a in s if a in STANDARD_AAS])
#     return s


# def _encode_one(seq):
#     """
#     对单条氨基酸序列提取 CKSAAP(1200) + PAAC(50) + CKSAAGP(75) = 1325 维特征。
#     不满足条件（长度 <200 或非标准氨基酸过多）返回 None。
#     """
#     clean = _clean_seq(seq)
#     if len(clean) < 200:
#         return None, f"清洗后长度 {len(clean)} < 200"

#     try:
#         f1 = CKSAAP.CKSAAP(clean, k=2)     # 1200
#         f2 = PAAC.PAAC(clean, lambdaValue=5, w=0.05)  # 50
#         f3 = CKSAAGP.CKSAAGP(clean, k=2)   # 75
#     except Exception as e:
#         return None, f"特征提取异常：{e}"

#     if f1 is None or f2 is None or f3 is None:
#         return None, "特征函数返回 None（可能长度不够或内部过滤）"

#     feat = list(f1) + list(f2) + list(f3)
#     if len(feat) != 1325:
#         return None, f"特征维度错误：{len(feat)} != 1325"

#     return feat, None


# # =========================================================
# # 主类：OneForAll
# # =========================================================
# class OneForAll:
#     """
#     接口（保持与 views.py 一致）：
#         OneForAll(sample_name, species='').run()
#     """

#     def __init__(self, sample_name, species=''):
#         self.sample_name = sample_name
#         self.species = species or ''

#         self.input_fasta = os.path.join(
#             config.SAMPLE_PATH_OLD, f"{sample_name}.fasta"
#         )
#         os.makedirs(config.PREDICTION_RESULT_PATH, exist_ok=True)
#         self.output_csv = os.path.join(
#             config.PREDICTION_RESULT_PATH, f"{sample_name}.csv"
#         )
#         self.done_flag = os.path.join(
#             config.PREDICTION_RESULT_PATH, f"{sample_name}_done.csv"
#         )
#         self.error_log = os.path.join(
#             config.PREDICTION_RESULT_PATH, f"{sample_name}_error.log"
#         )

#     # ---------- 对外入口 ----------
#     def run(self):
#         try:
#             logger.info(f"[{self.sample_name}] 开始处理 species={self.species!r}")
#             self._run_impl()
#             # 写完成标志（只要主 csv 存在即视为成功；该文件存在 → 轮询接口判定为已完成）
#             self._touch_done()
#             logger.info(f"[{self.sample_name}] 预测完成 -> {self.output_csv}")
#         except Exception as e:
#             logger.error(
#                 f"[{self.sample_name}] 预测失败: {e}\n{traceback.format_exc()}"
#             )
#             # 写错误日志
#             try:
#                 with open(self.error_log, 'w', encoding='utf-8') as f:
#                     f.write(f"{e}\n\n{traceback.format_exc()}")
#             except Exception:
#                 pass
#             # 也要写 done 文件，这样前端轮询到 done_file 才会去看 error_log
#             self._touch_done(failed=True)

#     # ---------- 核心流程 ----------
#     def _run_impl(self):
#         if not os.path.isfile(self.input_fasta):
#             raise FileNotFoundError(f"找不到输入文件：{self.input_fasta}")

#         # 1) 读 FASTA
#         fastas = readFasta.readFasta(self.input_fasta)
#         if not fastas:
#             raise ValueError("FASTA 文件为空或格式错误")
#         logger.info(f"[{self.sample_name}] 共读取 {len(fastas)} 条序列")

#         # 2) 逐条提取特征
#         records = []     # [(name, length, feat_or_None, err_or_None), ...]
#         for name, seq in fastas:
#             feat, err = _encode_one(seq)
#             records.append((name, len(_clean_seq(seq)), feat, err))

#         # 3) 准备批量 tensor
#         valid_idx = [i for i, r in enumerate(records) if r[2] is not None]
#         feats = np.asarray([records[i][2] for i in valid_idx], dtype=np.float32)

#         # 4) 推理
#         preds = [None] * len(records)   # (label_str, score_float)
#         if len(valid_idx) > 0:
#             model = _load_model()
#             device = _get_device()
#             with torch.no_grad():
#                 x = torch.from_numpy(feats).unsqueeze(1).to(device)  # [N,1,1325]
#                 # 分批，避免 OOM
#                 batch_size = 64
#                 all_logits = []
#                 for s in range(0, x.shape[0], batch_size):
#                     out = model(x[s:s + batch_size])
#                     # out = (proxcy, CE, source) —— 我们取 CE (logits)
#                     if isinstance(out, (tuple, list)):
#                         logits = out[1]
#                     else:
#                         logits = out
#                     all_logits.append(logits.cpu())
#                 logits = torch.cat(all_logits, dim=0)          # [N,2]
#                 probs = torch.softmax(logits, dim=-1).numpy()  # [N,2]
#                 labels = probs.argmax(axis=-1)                 # [N]

#             for k, i in enumerate(valid_idx):
#                 label_id = int(labels[k])
#                 score = float(probs[k, label_id])
#                 label_str = "Positive" if label_id == 1 else "Negative"
#                 preds[i] = (label_str, score)

#         # 5) 写 CSV（4 列：id, length, label, score）
#         with open(self.output_csv, 'w', encoding='utf-8', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerow(["id", "length", "label", "score"])
#             for (name, length, feat, err), pred in zip(records, preds):
#                 if pred is None:
#                     # 被过滤掉的序列也写一行，保持行数和输入对齐
#                     writer.writerow([name, length, "Filtered", "0.0000"])
#                 else:
#                     label_str, score = pred
#                     writer.writerow([name, length, label_str, f"{score:.4f}"])

#     # ---------- 写完成标志 ----------
#     def _touch_done(self, failed=False):
#         try:
#             # 把主 CSV 复制/写入一个标志文件；内容无所谓，存在即可
#             content = "failed\n" if failed else "ok\n"
#             with open(self.done_flag, 'w', encoding='utf-8') as f:
#                 f.write(content)
#         except Exception as e:
#             logger.error(f"写完成标志失败: {e}")


# # =========================================================
# # 命令行单独测试入口： python tools/main.py <uuid>
# # =========================================================
# if __name__ == '__main__':
#     if len(sys.argv) < 2:
#         print("Usage: python tools/main.py <sample_name_without_extension>")
#         print("  测试前请先把 .fasta 放到 data/sample_old/<sample_name>.fasta")
#         sys.exit(1)
#     OneForAll(sys.argv[1]).run()
#     print("✅ 预测完成")
# -*- coding: utf-8 -*-
"""
tools/main.py
=========================
OneForAll: 从 FASTA 文件到 CSV 预测结果的完整流水线。

⚠️ 本版本带【演示用延迟】：整体跑完大约 3 分钟，方便毕设/答辩展示。
   如果想恢复为真实速度，把 DEMO_DELAY = True 改成 False 即可。

上游调用（apps/front/views.py 中）：
    from tools.main import OneForAll
    executor.submit(OneForAll(sample_name, species=species).run)

输入:  config.SAMPLE_PATH_OLD + <uuid>.fasta
输出:  config.PREDICTION_RESULT_PATH + <uuid>.csv         （4列：id,length,label,score）
       config.PREDICTION_RESULT_PATH + <uuid>_done.csv    （完成标志）
       config.PREDICTION_RESULT_PATH + <uuid>_error.log   （若出错才写）
"""

import os
import sys
import re
import csv
import time
import traceback
import logging

import numpy as np
import torch

# ---------- 让当前文件能找到 gao/ 根目录里的模块 ----------
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_TOOLS_DIR)
for p in (_PROJECT_ROOT, _TOOLS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import config
import readFasta
import CKSAAP
import PAAC
import CKSAAGP

from Mamba import MambaModel

logger = logging.getLogger("tools.main")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

# =========================================================
# 🎬 演示用延迟配置（想关掉就改为 False）
# =========================================================
DEMO_DELAY = True            # 总开关：True 启用演示延迟
TARGET_SECONDS = 180         # 目标总耗时（秒），默认 3 分钟
# 各阶段耗时占比，加起来 = 1.0
STAGE_RATIO = {
    'load_fasta':    0.05,   # 读 FASTA           5%  ≈ 9s
    'encode':        0.55,   # 特征提取           55% ≈ 99s
    'load_model':    0.10,   # 加载模型           10% ≈ 18s
    'inference':     0.25,   # 模型推理           25% ≈ 45s
    'write_result':  0.05,   # 写入结果           5%  ≈ 9s
}


def _demo_sleep(stage, logger_=None):
    """根据 STAGE_RATIO 在某一阶段分配延迟时间"""
    if not DEMO_DELAY:
        return
    secs = TARGET_SECONDS * STAGE_RATIO.get(stage, 0.0)
    if logger_:
        logger_.info(f"[demo-delay] 阶段 {stage} 预计延迟 {secs:.1f} s")
    time.sleep(secs)


def _demo_sleep_split(stage, n_steps, logger_=None, msg_fmt=None):
    """
    把某一阶段的延迟平均分配到 n_steps 个小步骤里，
    用于在特征提取 / 推理等循环中打印进度日志。
    """
    if not DEMO_DELAY or n_steps <= 0:
        return 0.0
    secs = TARGET_SECONDS * STAGE_RATIO.get(stage, 0.0) / n_steps
    return secs


# =========================================================
# 全局模型（惰性加载）
# =========================================================
_MODEL = None
_DEVICE = None


def _get_device():
    global _DEVICE
    if _DEVICE is None:
        _DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return _DEVICE


def _load_model():
    global _MODEL
    if _MODEL is not None:
        # 即便模型已加载，演示模式下也"假装"又花了时间
        _demo_sleep('load_model', logger)
        return _MODEL

    model_path = os.path.join(config.PJ_PATH, "model", "best_model.pth")
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"找不到模型权重文件：{model_path}")

    device = _get_device()
    logger.info(f"加载模型: {model_path}  设备: {device}")

    # 分两步延迟：一半加载前（读盘模拟），一半加载后（初始化模拟）
    if DEMO_DELAY:
        time.sleep(TARGET_SECONDS * STAGE_RATIO['load_model'] * 0.5)

    sd = torch.load(model_path, map_location=device)
    model = MambaModel(
        d_model=1325, d_state=16, d_conv=4, expand=2, num_classes=2,
    )
    missing, unexpected = model.load_state_dict(sd, strict=False)
    if missing or unexpected:
        logger.warning(f"权重加载不完全 missing={missing} unexpected={unexpected}")
    model.to(device)
    model.eval()
    _MODEL = model

    if DEMO_DELAY:
        time.sleep(TARGET_SECONDS * STAGE_RATIO['load_model'] * 0.5)

    return _MODEL


# =========================================================
# 特征提取
# =========================================================
STANDARD_AAS = 'ACDEFGHIKLMNPQRSTVWY'


def _clean_seq(seq):
    s = re.sub('-', '', seq).upper()
    s = ''.join([a for a in s if a in STANDARD_AAS])
    return s


def _encode_one(seq):
    clean = _clean_seq(seq)
    if len(clean) < 200:
        return None, f"清洗后长度 {len(clean)} < 200"

    try:
        f1 = CKSAAP.CKSAAP(clean, k=2)
        f2 = PAAC.PAAC(clean, lambdaValue=5, w=0.05)
        f3 = CKSAAGP.CKSAAGP(clean, k=2)
    except Exception as e:
        return None, f"特征提取异常：{e}"

    if f1 is None or f2 is None or f3 is None:
        return None, "特征函数返回 None"

    feat = list(f1) + list(f2) + list(f3)
    if len(feat) != 1325:
        return None, f"特征维度错误：{len(feat)} != 1325"

    return feat, None


# =========================================================
# 主类：OneForAll
# =========================================================
class OneForAll:

    def __init__(self, sample_name, species=''):
        self.sample_name = sample_name
        self.species = species or ''
        self.input_fasta = os.path.join(
            config.SAMPLE_PATH_OLD, f"{sample_name}.fasta"
        )
        os.makedirs(config.PREDICTION_RESULT_PATH, exist_ok=True)
        self.output_csv = os.path.join(
            config.PREDICTION_RESULT_PATH, f"{sample_name}.csv"
        )
        self.done_flag = os.path.join(
            config.PREDICTION_RESULT_PATH, f"{sample_name}_done.csv"
        )
        self.error_log = os.path.join(
            config.PREDICTION_RESULT_PATH, f"{sample_name}_error.log"
        )

    def run(self):
        t0 = time.time()
        try:
            logger.info(f"[{self.sample_name}] ========== 开始预测任务 ==========")
            logger.info(f"[{self.sample_name}] species={self.species!r}")
            if DEMO_DELAY:
                logger.info(f"[{self.sample_name}] 🎬 演示模式已启用，预计 {TARGET_SECONDS}s")

            self._run_impl()
            self._touch_done()

            elapsed = time.time() - t0
            logger.info(f"[{self.sample_name}] ✅ 预测完成，总耗时 {elapsed:.1f}s -> {self.output_csv}")
        except Exception as e:
            logger.error(
                f"[{self.sample_name}] ❌ 预测失败: {e}\n{traceback.format_exc()}"
            )
            try:
                with open(self.error_log, 'w', encoding='utf-8') as f:
                    f.write(f"{e}\n\n{traceback.format_exc()}")
            except Exception:
                pass
            self._touch_done(failed=True)

    def _run_impl(self):
        # ===== 阶段 1: 读 FASTA =====
        logger.info(f"[{self.sample_name}] [1/5] 正在读取 FASTA 序列...")
        if not os.path.isfile(self.input_fasta):
            raise FileNotFoundError(f"找不到输入文件：{self.input_fasta}")

        fastas = readFasta.readFasta(self.input_fasta)
        if not fastas:
            raise ValueError("FASTA 文件为空或格式错误")
        logger.info(f"[{self.sample_name}]        共读取 {len(fastas)} 条序列")
        _demo_sleep('load_fasta', logger)

        # ===== 阶段 2: 特征提取（带进度） =====
        logger.info(f"[{self.sample_name}] [2/5] 正在提取 CKSAAP + PAAC + CKSAAGP 特征...")
        n = len(fastas)
        per_seq_sleep = _demo_sleep_split('encode', n)

        records = []
        for idx, (name, seq) in enumerate(fastas, start=1):
            feat, err = _encode_one(seq)
            records.append((name, len(_clean_seq(seq)), feat, err))

            # 每 ~10% 打印一次进度
            if n <= 10 or idx % max(1, n // 10) == 0 or idx == n:
                logger.info(f"[{self.sample_name}]        进度 {idx}/{n} "
                            f"({idx * 100 // n}%) - {name}")

            # 演示延迟
            if per_seq_sleep > 0:
                time.sleep(per_seq_sleep)

        valid_idx = [i for i, r in enumerate(records) if r[2] is not None]
        logger.info(f"[{self.sample_name}]        有效序列 {len(valid_idx)}/{n}")

        # ===== 阶段 3: 加载模型 =====
        logger.info(f"[{self.sample_name}] [3/5] 正在加载 Mamba 深度学习模型...")
        if len(valid_idx) > 0:
            model = _load_model()
            device = _get_device()
            logger.info(f"[{self.sample_name}]        模型已加载到设备 {device}")
        else:
            model = None
            device = None
            _demo_sleep('load_model', logger)

        # ===== 阶段 4: 模型推理（带进度） =====
        logger.info(f"[{self.sample_name}] [4/5] 正在执行模型推理...")
        preds = [None] * len(records)

        if len(valid_idx) > 0 and model is not None:
            feats = np.asarray([records[i][2] for i in valid_idx], dtype=np.float32)
            batch_size = 64
            n_batches = (len(feats) + batch_size - 1) // batch_size
            per_batch_sleep = _demo_sleep_split('inference', n_batches)

            all_logits = []
            with torch.no_grad():
                x = torch.from_numpy(feats).unsqueeze(1).to(device)
                for bi, s in enumerate(range(0, x.shape[0], batch_size), start=1):
                    out = model(x[s:s + batch_size])
                    logits = out[1] if isinstance(out, (tuple, list)) else out
                    all_logits.append(logits.cpu())

                    logger.info(f"[{self.sample_name}]        推理批次 {bi}/{n_batches} "
                                f"({bi * 100 // n_batches}%)")

                    if per_batch_sleep > 0:
                        time.sleep(per_batch_sleep)

                logits = torch.cat(all_logits, dim=0)
                probs = torch.softmax(logits, dim=-1).numpy()
                labels = probs.argmax(axis=-1)

            for k, i in enumerate(valid_idx):
                label_id = int(labels[k])
                score = float(probs[k, label_id])
                label_str = "Positive" if label_id == 1 else "Negative"
                preds[i] = (label_str, score)
        else:
            _demo_sleep('inference', logger)

        # ===== 阶段 5: 写 CSV =====
        logger.info(f"[{self.sample_name}] [5/5] 正在写入预测结果...")
        with open(self.output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "length", "label", "score"])
            for (name, length, feat, err), pred in zip(records, preds):
                if pred is None:
                    writer.writerow([name, length, "Filtered", "0.0000"])
                else:
                    label_str, score = pred
                    writer.writerow([name, length, label_str, f"{score:.4f}"])
        _demo_sleep('write_result', logger)
        logger.info(f"[{self.sample_name}]        结果已保存到 {self.output_csv}")

    def _touch_done(self, failed=False):
        try:
            content = "failed\n" if failed else "ok\n"
            with open(self.done_flag, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"写完成标志失败: {e}")


# =========================================================
# 命令行测试
# =========================================================
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python tools/main.py <sample_name_without_extension>")
        sys.exit(1)
    OneForAll(sys.argv[1]).run()
    print("✅ 预测完成")