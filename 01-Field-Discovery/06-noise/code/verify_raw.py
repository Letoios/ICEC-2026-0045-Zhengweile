# -*- coding: utf-8 -*-
"""verify_raw.py —— 逐组核验原始文件的 SHA256 是否与 meta.txt 记录一致。

为什么要这个脚本：证据包里「数据没被改过」的论据是 SHA256，
但如果没人能自己算一遍，那句话就只是自说自话。

规则（15 组里 14 组对 zip、1 组对 CSV，原因是 S11 换过源，见 证据包/ANOMALIES.md A-07）：
  · 有 zip 的组：SHA256 算在 **zip 文件本身** 上
  · 没有 zip 的组（只有未打包的导出文件夹）：SHA256 算在 **Amplitudes.csv** 上

用法：python verify_raw.py
"""
import hashlib
import io
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest().upper()


def main():
    if not os.path.isdir(DATA):
        print("找不到 data/：%s" % DATA)
        return 2
    rows = []
    for name in sorted(os.listdir(DATA)):
        d = os.path.join(DATA, name)
        raw = os.path.join(d, "原始")
        if not os.path.isdir(raw):
            continue
        meta = io.open(os.path.join(d, "meta.txt"), encoding="utf-8").read()
        m = re.search(r"SHA256\s+([0-9A-Fa-f]{64})", meta)
        want = m.group(1).upper() if m else None

        zips = [f for f in os.listdir(raw) if f.lower().endswith(".zip")]
        if zips:
            target = zips[0]
            got = sha256_bytes(open(os.path.join(raw, target), "rb").read())
            basis = "zip"
        else:
            target, got, basis = None, None, None
            for sub in sorted(os.listdir(raw)):
                cand = os.path.join(raw, sub, "Amplitudes.csv")
                if os.path.isfile(cand):
                    target = os.path.join(sub, "Amplitudes.csv")
                    got = sha256_bytes(open(cand, "rb").read())
                    basis = "csv"
                    break
        ok = bool(want and got and want == got)
        rows.append((name, basis, target, want, got, ok))

    print("%-24s %-5s %-8s %s" % ("组", "依据", "结果", "对象"))
    print("-" * 78)
    bad = 0
    for name, basis, target, want, got, ok in rows:
        print("%-24s %-5s %-8s %s" % (name, basis or "-", "一致" if ok else "不一致", target or "-"))
        if not ok:
            bad += 1
            print("    记录 %s" % (want or "(meta.txt 里没有 SHA256)"))
            print("    实际 %s" % (got or "(找不到可算的文件)"))
    print("-" * 78)
    print("共 %d 组，核验一致 %d 组，不一致 %d 组。" % (len(rows), len(rows) - bad, bad))
    print("\n注：data/<Sxx>/Amplitudes.csv 是为了 Excel 直开而另存的 UTF-8 BOM 版本，")
    print("    与原始 zip 内的同名文件相比只多 3 字节 BOM，数据完全一致。")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
