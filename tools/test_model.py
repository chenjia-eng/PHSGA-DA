# tools/test_model.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import config
from Mamba import MambaModel   # ← 直接用你自己的 Mamba.py

model_path = os.path.join(config.PJ_PATH, "model", "best_model.pth")
print(f"加载模型: {model_path}")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"设备: {device}")

# 加载 state_dict
sd = torch.load(model_path, map_location=device)
print(f"state_dict 类型: {type(sd)}")
if isinstance(sd, dict):
    print(f"前 5 个键: {list(sd.keys())[:5]}")

# 构造模型（参数必须和训练时完全一致）
model = MambaModel(
    d_model=1325,   # CKSAAP(1200) + PAAC(50) + CKSAAGP(75)
    d_state=16,
    d_conv=4,
    expand=2,
    num_classes=2,
)

# 加载权重
missing, unexpected = model.load_state_dict(sd, strict=False)
print(f"Missing keys:    {missing}")
print(f"Unexpected keys: {unexpected}")

model.to(device)
model.eval()

# 用假数据测试一次前向
x = torch.randn(2, 1, 1325).to(device)
with torch.no_grad():
    out = model(x)

print(f"\n输出类型: {type(out)}")
if isinstance(out, tuple):
    print(f"输出元组长度: {len(out)}")
    for i, o in enumerate(out):
        print(f"  out[{i}].shape = {o.shape}")

print("\n✅ 模型加载并推理成功！")
print("\n=== cls_fc1 的权重形状 ===")
for k, v in sd.items():
    if 'cls_fc1' in k:
        print(f"  {k}: {tuple(v.shape)}")

print("\n=== cls_fc 的权重形状 ===")
for k, v in sd.items():
    if 'cls_fc' in k and 'cls_fc1' not in k:
        print(f"  {k}: {tuple(v.shape)}")

print("\n=== 所有键名（前20个）===")
for i, k in enumerate(list(sd.keys())[:20]):
    print(f"  {k}")
