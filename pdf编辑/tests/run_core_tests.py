import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = str(ROOT / '.venv' / 'Scripts' / 'python.exe')
CLI = str(ROOT / 'PythonPDFPro.py')
REPORT = ROOT / 'tests' / 'core_test_report.txt'

# Ensure sample PDFs exist
print('生成示例 PDF...')
subprocess.run([PY, str(ROOT / 'tests' / 'create_test_pdfs.py')], check=False)

results = []

# 1. 合并
print('测试：合并 a.pdf 和 b.pdf -> merged.pdf')
rc = subprocess.run([PY, CLI, 'merge', '-i', 'a.pdf', 'b.pdf', '-o', 'merged.pdf'], cwd=str(ROOT))
ok = (rc.returncode == 0 and (ROOT / 'merged.pdf').exists())
results.append(('merge', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 2. 提取文本
print('测试：提取文本 merged.pdf -> merged.txt')
rc = subprocess.run([PY, CLI, 'extract_text', '-i', 'merged.pdf', '-o', 'merged.txt'], cwd=str(ROOT))
ok = (rc.returncode == 0 and (ROOT / 'merged.txt').exists() and (ROOT / 'merged.txt').stat().st_size > 0)
results.append(('extract_text', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 3. 提取图片
print('测试：从 merged.pdf 提取图片 -> images_out')
if (ROOT / 'images_out').exists():
    for f in (ROOT / 'images_out').glob('*'):
        try:
            f.unlink()
        except Exception:
            pass
rc = subprocess.run([PY, CLI, 'extract_images', '-i', 'merged.pdf', '-o', 'images_out'], cwd=str(ROOT))
img_dir = ROOT / 'images_out'
ok = (rc.returncode == 0 and img_dir.exists() and any(img_dir.iterdir()))
results.append(('extract_images', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 4. 加密
print('测试：加密 merged.pdf -> merged_enc.pdf')
rc = subprocess.run([PY, CLI, 'encrypt', '-i', 'merged.pdf', '-o', 'merged_enc.pdf', '-p', 'testpwd'], cwd=str(ROOT))
ok = (rc.returncode == 0 and (ROOT / 'merged_enc.pdf').exists())
results.append(('encrypt', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 5. 解密（正确密码）
print('测试：解密 merged_enc.pdf -> merged_dec.pdf (正确密码)')
rc = subprocess.run([PY, CLI, 'decrypt', '-i', 'merged_enc.pdf', '-o', 'merged_dec.pdf', '-p', 'testpwd'], cwd=str(ROOT))
ok = (rc.returncode == 0 and (ROOT / 'merged_dec.pdf').exists())
results.append(('decrypt_correct', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 6. 解密（错误密码）
print('测试：解密 merged_enc.pdf -> merged_fail.pdf (错误密码，期望失败)')
rc = subprocess.run([PY, CLI, 'decrypt', '-i', 'merged_enc.pdf', '-o', 'merged_fail.pdf', '-p', 'wrongpwd'], cwd=str(ROOT))
ok = (rc.returncode != 0 or not (ROOT / 'merged_fail.pdf').exists())
results.append(('decrypt_incorrect', ok, rc.returncode))
print('  完成' if ok else '  失败')

# 写入报告
with open(REPORT, 'w', encoding='utf-8') as f:
    for name, ok, code in results:
        f.write(f"{name}: {'PASS' if ok else 'FAIL'} (returncode={code})\n")

print('\n测试汇总：')
all_ok = True
for name, ok, code in results:
    print(f" - {name}: {'PASS' if ok else 'FAIL'} (returncode={code})")
    if not ok:
        all_ok = False

if all_ok:
    print('\n全部测试通过 ✅')
    sys.exit(0)
else:
    print('\n存在未通过的测试 ❌，详见 tests/core_test_report.txt')
    sys.exit(2)
