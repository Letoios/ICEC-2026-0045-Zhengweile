# -*- coding: utf-8 -*-
"""课题06 元数据与双源对照：校准偏移、设备信息、Phyphox zip vs SoundMeter 文本。"""
import os, glob, math, zipfile, json
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))
ROOT = r"D:\分贝项目"
OUT = r"D:\deepseek工作\noise06\build\meta.json"


class DirSrc:
    """让未压缩的导出文件夹与 zipfile.ZipFile 用同一套 read(name) 接口。"""
    def __init__(self, d):
        self.d = d
        self.name = os.path.basename(d) + "/Amplitudes.csv"

    def read(self, name):
        return open(os.path.join(self.d, name.replace("/", os.sep)), "rb").read()


SOURCE_OVERRIDE = {"晚上图书馆": "晚图书馆2026-10-25 19-11-41"}


def leq(v):
    return 10 * math.log10(sum(10 ** (d / 10) for d in v) / len(v))


def read_cal(z):
    """Calibration.csv 是两行：表头一行，第二行一个科学计数法浮点数。"""
    try:
        lines = z.read("Calibration.csv").decode("utf-8-sig").strip().splitlines()
        for line in lines[1:]:
            s = line.strip().strip('"')
            if not s:
                continue
            try:
                return float(s)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def read_device(z):
    d = {}
    try:
        for line in z.read("meta/device.csv").decode("utf-8-sig").strip().splitlines()[1:]:
            if '","' in line:
                k, v = line.split('","', 1)
                d[k.strip('"')] = v.strip('"')
    except Exception:
        pass
    return d


def read_txt(d):
    fs = glob.glob(os.path.join(d, "*.txt"))
    if not fs:
        return None, None
    tv = []
    for i, line in enumerate(open(fs[0], encoding="utf-8-sig")):
        if i == 0:
            continue
        p = line.strip().split(",")
        if len(p) < 2:
            continue
        try:
            v = float(p[1])
        except Exception:
            continue
        if v > 0:
            tv.append(v)
    if len(tv) < 5:
        return None, os.path.basename(fs[0])
    return round(leq(tv), 2), os.path.basename(fs[0])


rows = []
for folder in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, folder)
    if not os.path.isdir(d):
        continue
    sub = SOURCE_OVERRIDE.get(folder)
    if sub:
        z = DirSrc(os.path.join(d, sub))
    else:
        zp = glob.glob(os.path.join(d, "*.zip"))
        if not zp:
            continue
        z = zipfile.ZipFile(zp[0])
        z.name = os.path.basename(zp[0])
    vals = []
    for line in z.read("Amplitudes.csv").decode("utf-8-sig").splitlines()[1:]:
        p = line.split(",")
        if len(p) != 2:
            continue
        try:
            v = float(p[1])
        except Exception:
            continue
        if v > -50:
            vals.append(v)
    dev = read_device(z)
    txt_leq, txt_file = read_txt(d)
    rows.append(dict(folder=folder, zip=z.name,
                     cal=read_cal(z),
                     model=dev.get("deviceModel", ""), brand=dev.get("deviceBrand", ""),
                     appver=dev.get("version", ""), filefmt=dev.get("fileFormat", ""),
                     leq_zip=round(leq(vals), 2), txtFile=txt_file, leq_txt=txt_leq,
                     delta=(None if txt_leq is None else round(leq(vals) - txt_leq, 2))))

print("%-12s %-8s %8s %8s %8s %8s" % ("folder", "device", "cal_dB", "Leq_zip", "Leq_txt", "delta"))
for r in rows:
    print("%-12s %-8s %8s %8.2f %8s %8s" % (r["folder"], r["model"],
                                       "—" if r["cal"] is None else "%.2f" % r["cal"],
                                       r["leq_zip"],
                                       "—" if r["leq_txt"] is None else "%.2f" % r["leq_txt"],
                                       "—" if r["delta"] is None else "%+.1f" % r["delta"]))

cals = [r["cal"] for r in rows if r["cal"] is not None]
if cals:
    print("\n校准偏移：%d 组有值，范围 %.2f ~ %.2f dB，跨度 %.2f dB" %
          (len(cals), min(cals), max(cals), max(cals) - min(cals)))
ds = [r["delta"] for r in rows if r["delta"] is not None]
if ds:
    print("双源差值：%d 组，范围 %+.1f ~ %+.1f dB，均值 %+.1f dB" %
          (len(ds), min(ds), max(ds), sum(ds) / len(ds)))
print("设备：%s" % sorted({(r["brand"], r["model"], r["appver"]) for r in rows}))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("saved", OUT)
