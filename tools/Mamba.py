import torch
import torch.nn as nn
# from mamba_ssm import Mamba

import torch
import torch.nn as nn

class MambaModel(nn.Module):
    """
    
    输入：[batch, 1, d_model] -> LSTM 处理（seq_len=1）
    """
    def __init__(self, d_model=1325, d_state=16, d_conv=4, expand=2, num_classes=2):
        super(MambaModel, self).__init__()
        # 用一个单层 LSTM 替换原来的 Mamba 模块
        self.lstm = nn.LSTM(
            input_size=d_model,
            hidden_size=d_model,   # 保持输出维度不变
            num_layers=1,
            batch_first=True
        )
        # 辅助分支（同原版）
        self.cls_fc = nn.Linear(d_model, 256)
        # 主分类头
        self.cls_fc1 = nn.Sequential(
            nn.Linear(d_model, 256),
            nn.Linear(256, num_classes),
        )
        self.dropout = nn.Dropout(p=0.3)

    def forward(self, source):
        # source: [batch, 1, d_model]
        # LSTM 处理
        lstm_out, (h_n, c_n) = self.lstm(source)   # lstm_out: [batch, 1, d_model]
        # 取最后一个时间步的输出（与原 Mamba 输出形状一致）
        source_out = lstm_out[:, -1, :]   # [batch, d_model]
        # 为了保持与原代码维度一致，重新增加一个长度为1的维度（因为原代码后续会 squeeze）
        source_out = source_out.unsqueeze(1)  # [batch, 1, d_model]

        source_proxcy = self.cls_fc(source_out)
        source_proxcy = self.dropout(source_proxcy)

        source_drop = self.dropout(source_out)
        CE = self.cls_fc1(source_drop)

        # 去掉中间长度为1的维度（与原代码逻辑一致）
        source_out = torch.squeeze(source_out, dim=1)
        source_proxcy = torch.squeeze(source_proxcy, dim=1)
        CE = torch.squeeze(CE, dim=1)

        return source_proxcy, CE, source_out
# class MambaModel1(nn.Module):
#     """
#     与 best_model.pth 的权重结构严格对齐：
#       sharedNet : mamba_ssm.Mamba(d_model=1325)
#       cls_fc    : Linear(1325 -> 256)          （训练时的 proxy head，推理不使用）
#       cls_fc1   : Sequential(
#                       Linear(1325 -> 256),     # cls_fc1.0
#                       Linear(256 -> 2),        # cls_fc1.1
#                   )                            （分类头，推理用它）
#     """

#     def __init__(self, d_model=1325, d_state=16, d_conv=4, expand=2, num_classes=2):
#         super(MambaModel, self).__init__()

#         self.sharedNet = Mamba(
#             d_model=d_model,
#             d_state=d_state,
#             d_conv=d_conv,
#             expand=expand,
#         )

#         # 辅助分支（训练时用于对比/代理损失）
#         self.cls_fc = nn.Linear(d_model, 256)

#         # 主分类头：两层 Linear 串联（和 checkpoint 中的 cls_fc1.0 / cls_fc1.1 一致）
#         self.cls_fc1 = nn.Sequential(
#             nn.Linear(d_model, 256),
#             nn.Linear(256, num_classes),
#         )

#         self.dropout = nn.Dropout(p=0.3)

#     def forward(self, source):
#         # source: [batch, 1, d_model]
#         source = self.sharedNet(source)

#         source_proxcy = self.cls_fc(source)
#         source_proxcy = self.dropout(source_proxcy)

#         source = self.dropout(source)
#         CE = self.cls_fc1(source)

#         # 去掉中间那个长度为 1 的维度
#         source = torch.squeeze(source, dim=1)
#         source_proxcy = torch.squeeze(source_proxcy, dim=1)
#         CE = torch.squeeze(CE, dim=1)

#         return source_proxcy, CE, source


# # ================== 保留原来的 TransferNet（不做改动，以防你其他脚本引用）==================
# class TransferNet(nn.Module):
#     def __init__(self, d_model, d_state, d_conv, expand, num_classes):
#         super(TransferNet, self).__init__()
#         self.sharedNet = Mamba(d_model=d_model, d_state=d_state, d_conv=d_conv, expand=expand)
#         self.dropout = nn.Dropout(0.3)
#         self.fc1 = nn.Linear(d_model, 512)
#         self.relu = nn.ReLU()
#         self.cls_fc = nn.Linear(512, 256)
#         self.fc3 = nn.Linear(256, 128)
#         self.cls_fc1 = nn.Linear(128, 2)
#         self.num_class = num_classes

#     def forward(self, source):
#         source = self.sharedNet(source.unsqueeze(1))
#         features_source = source.squeeze(1)
#         features_source = self.dropout(features_source)
#         features_source = self.fc1(features_source)
#         features_source = self.relu(features_source)
#         source_proxcy = self.cls_fc(features_source)
#         features_source = self.relu(source_proxcy)
#         features_source = self.fc3(features_source)
#         features_source = self.relu(features_source)
#         source_clf = self.cls_fc1(features_source)
#         return source_proxcy, source_clf, source

#     def get_optimizer(self):
#         params = [
#             {'params': self.sharedNet.parameters()},
#             {'params': self.fc1.parameters()},
#             {'params': self.cls_fc.parameters()},
#             {'params': self.fc3.parameters()},
#         ]
#         optimizer = torch.optim.Adam(params, lr=0.0003)
#         return optimizer