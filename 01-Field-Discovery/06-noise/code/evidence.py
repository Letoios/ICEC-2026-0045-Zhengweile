# -*- coding: utf-8 -*-
"""课题06 真实性证据包：逐组指纹、设备时间、校准偏移、原始数据副本、指标输出。"""
import os, csv, json, glob, shutil, hashlib, zipfile, math
from datetime import datetime, timezone, timedelta

ROOT = r"D:\分贝项目"
SOURCE_OVERRIDE = {"晚上图书馆": "晚图书馆2026-10-25 19-11-41"}
DELIVER = r"D:\deepseek工作\noise06\deliver"
EV = os.path.join(DELIVER, "证据包")
DATA = os.path.join(DELIVER, "data")
RAWOUT = os.path.join(EV, "raw_output")
tz = timezone(timedelta(hours=8))

ORDER = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]
PERIODS = ["早", "中", "晚"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def folder_meta(folder):
    per = "早" if folder.startswith("早") else ("中" if folder.startswith("中午") else "晚")
    rest = folder[1:] if per == "早" else folder[2:]
    loc = {"路干": "主干道", "操场": "运动场", "实训走廊": "实训室走廊",
           "实训室": "实训室走廊", "图书馆": "图书馆", "食堂": "食堂"}[rest]
    return per, loc


def leq(vals):
    return 10 * math.log10(sum(10 ** (d / 10) for d in vals) / len(vals))


def main():
    for p in (EV, DATA, RAWOUT):
        os.makedirs(p, exist_ok=True)

    stats = json.load(open(os.path.join(r"D:\deepseek工作\noise06\build", "stats.json"), encoding="utf-8"))
    meta = {m["folder"]: m for m in json.load(open(os.path.join(r"D:\deepseek工作\noise06\build", "meta.json"), encoding="utf-8"))}
    by_key = {(s["per"], s["loc"]): s for s in stats}

    rows = []
    lines = []
    lines.append("课题06　15 组指标重算输出（由 noise06/extract.py 生成，本文件可逐字复核）")
    lines.append("生成时间：%s" % datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S UTC+08:00"))
    lines.append("")
    hdr = "%-4s %-3s %-7s %-6s %-9s %6s %5s %8s %8s %8s %7s %-5s %8s %s" % (
        "编号", "时段", "点位", "类别", "开始时刻", "时长s", "样本", "Leq", "Lmax", "1s峰",
        "Δ", "判定", "情景Δ", "情景判")
    lines.append(hdr)
    lines.append("-" * len(hdr.encode("gbk", "ignore")))

    seq = []
    for folder in os.listdir(ROOT):
        d = os.path.join(ROOT, folder)
        if not os.path.isdir(d):
            continue
        per, loc = folder_meta(folder)
        if (per, loc) not in by_key:
            continue
        seq.append((PERIODS.index(per), ORDER.index(loc), folder))
    seq.sort()

    if os.path.isdir(DATA):
        shutil.rmtree(DATA)
    os.makedirs(DATA, exist_ok=True)

    n = 0
    for _, _, folder in seq:
        d = os.path.join(ROOT, folder)
        per, loc = folder_meta(folder)
        n += 1
        s = by_key[(per, loc)]
        m = meta[folder]
        txt = glob.glob(os.path.join(d, "*.txt"))
        imgs = [p for p in glob.glob(os.path.join(d, "*.*"))
                if os.path.splitext(p)[1].lower() in (".png", ".jpg", ".jpeg")]

        sub_dir = SOURCE_OVERRIDE.get(folder)
        if sub_dir:
            src = os.path.join(d, sub_dir)
            zp = os.path.join(src, "Amplitudes.csv")
            zname = os.path.basename(src) + "/Amplitudes.csv"
            zsize = os.path.getsize(zp)
            zsha = sha256(zp)
            mt = {}
            for line in open(os.path.join(src, "meta", "time.csv"), encoding="utf-8-sig").read().splitlines()[1:]:
                p2 = next(csv.reader([line]))
                if len(p2) >= 4:
                    mt[p2[0]] = (float(p2[2]), p2[3])
            am = open(zp, encoding="utf-8-sig").read()
        else:
            zp = glob.glob(os.path.join(d, "*.zip"))[0]
            zname, zsize, zsha = os.path.basename(zp), os.path.getsize(zp), sha256(zp)
            with zipfile.ZipFile(zp) as z:
                mt = {}
                for line in z.read("meta/time.csv").decode("utf-8-sig").splitlines()[1:]:
                    p2 = next(csv.reader([line]))
                    if len(p2) >= 4:
                        mt[p2[0]] = (float(p2[2]), p2[3])
                am = z.read("Amplitudes.csv").decode("utf-8-sig")

        rows.append(dict(
            no="S%02d" % n, per=per, loc=loc, cat=s["cat"],
            device=m["model"], brand=m["brand"], app=m["appver"],
            start=mt["START"][1], end=mt["PAUSE"][1],
            dur=s["dur"], n=s["n"], cal=("%.2f" % m["cal"]) if m["cal"] is not None else "",
            leq=s["leq"], peak=s["peak"], peak1s=s["peak1s"],
            over=s["over"], verdict=s["verdict"],
            overn=s["overNight"], verdictn=s["verdictNight"],
            zipname=zname, zipsize=zsize, zipsha=zsha,
            txtname=os.path.basename(txt[0]) if txt else "",
            txtsha=sha256(txt[0]) if txt else "",
            imgcount=len(imgs),
            imgs="；".join("%s(%dKB)" % (os.path.basename(p), round(os.path.getsize(p) / 1024))
                          for p in sorted(imgs)),
            txt_leq=m["leq_txt"], delta=(m["delta"] if m.get("delta") is not None else "")))

        lines.append("%-4s %-3s %-7s %-6s %-9s %6.0f %5d %8.2f %8.2f %8.2f %+7.1f %-5s %+8.1f %s" % (
            "S%02d" % n, per, loc, s["cat"], mt["START"][1][11:19],
            s["dur"], s["n"], s["leq"], s["peak"], s["peak1s"], s["over"], s["verdict"],
            s["overNight"], s["verdictNight"]))

        # 原始数据副本
        sub = os.path.join(DATA, "%s_%s_%s" % ("S%02d" % n, per, loc))
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "Amplitudes.csv"), "w", encoding="utf-8-sig", newline="") as f:
            f.write(am)
        with open(os.path.join(sub, "meta.txt"), "w", encoding="utf-8") as f:
            f.write("原始文件夹：%s\n" % folder)
            f.write("设备：%s %s　Phyphox %s\n" % (m["brand"], m["model"], m["appver"]))
            f.write("开始：%s\n结束：%s\n" % (mt["START"][1], mt["PAUSE"][1]))
            f.write("自动校准偏移：%.2f dB\n" % m["cal"])
            f.write("原始文件：%s（SHA256 %s）\n" % (zname, zsha))
            f.write("指标：Leq %.2f  Lmax %.2f  1s峰 %.2f  Δ %+.2f  %s\n"
                    % (s["leq"], s["peak"], s["peak1s"], s["over"], s["verdict"]))

    lines.append("")
    over = sum(1 for r in rows if r["verdict"] == "超标")
    lines.append("合计 %d 组：超标 %d / 达标 %d" % (len(rows), over, len(rows) - over))

    with open(os.path.join(RAWOUT, "extract_15组.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # 采集证明 CSV
    cols = [("编号", "no"), ("时段", "per"), ("监测点位", "loc"), ("功能区", "cat"),
            ("设备品牌", "brand"), ("设备型号", "device"), ("App 版本", "app"),
            ("开始时刻(系统时间)", "start"), ("结束时刻(系统时间)", "end"),
            ("时长(s)", "dur"), ("有效样本", "n"), ("自动校准偏移(dB)", "cal"),
            ("Leq dB(A)", "leq"), ("Lmax dB(A)", "peak"), ("1s峰 dB(A)", "peak1s"),

            ("原始zip", "zipname"), ("zip字节", "zipsize"), ("zip SHA256", "zipsha"),
            ("另一套App文本", "txtname"), ("文本 SHA256", "txtsha"),
            ("另一套App Leq", "txt_leq"), ("双源差值", "delta"),
            ("现场照片数", "imgcount"),
            ("超出量 Δ dB（按昼间限值判定）", "over"), ("判定", "verdict"),
            ("情景 Δ dB（若按夜间限值）", "overn"), ("情景判定", "verdictn"),
            ("现场照片", "imgs")]
    with open(os.path.join(EV, "采集证明_设备时间与设备型号.csv"), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([c[0] for c in cols])
        for r in rows:
            w.writerow([r.get(c[1], "") for c in cols])

    print("rows=%d  over=%d" % (len(rows), over))
    print("证据包 ->", EV)
    print("原始数据副本 ->", DATA)


main()
