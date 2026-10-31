# -*- coding: utf-8 -*-
"""课题06 统一提取：把 D:\\分贝项目 下 15 个原始包算成同一套指标。

产出 D:\\deepseek工作\\noise06\\build\\stats.json
"""
import os, csv, math, zipfile, json
from datetime import datetime, timezone, timedelta

ROOT = r"D:\分贝项目"
OUT_DIR = r"D:\deepseek工作\noise06\build"
tz = timezone(timedelta(hours=8))

# 点位 -> (功能区, 昼间限值, 夜间限值)
STD = {
    "图书馆":      ("1 类", 55, 45),
    "实训室走廊":  ("1 类", 55, 45),
    "食堂":        ("2 类", 60, 50),
    "运动场":      ("2 类", 60, 50),
    "主干道":      ("4a 类", 70, 55),
}
ORDER = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]
PERIOD_ORDER = ["早", "中", "晚"]


def folder_meta(folder):
    """'中午实训室' -> ('中', '实训室走廊')"""
    per = "早" if folder.startswith("早") else ("中" if folder.startswith("中午") else "晚")
    rest = folder[1:] if per == "早" else (folder[2:] if per == "中" else folder[2:])
    loc = {"路干": "主干道", "操场": "运动场", "实训走廊": "实训室走廊",
           "实训室": "实训室走廊", "图书馆": "图书馆", "食堂": "食堂"}[rest]
    return per, loc


def leq(vals):
    return 10 * math.log10(sum(10 ** (d / 10) for d in vals) / len(vals))


def pct(srt, p):
    k = (len(srt) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    return srt[f] if f == c else srt[f] * (c - k) + srt[c] * (k - f)


def peak1s(ts, vals):
    j, best = 0, -999.0
    for i, t in enumerate(ts):
        while ts[j] < t - 1.0:
            j += 1
        best = max(best, leq(vals[j:i + 1]))
    return best


# 晚上图书馆：目录里唯一的 zip 是同学用 PKG110 录的重复文件；
# 本人（PLK110）那段是未压缩的导出文件夹，此处显式指定，保证 15 组同机同管线。
SOURCE_OVERRIDE = {"晚上图书馆": "晚图书馆2026-10-25 19-11-41"}


def from_unzipped(d):
    """从未压缩的 Phyphox 导出文件夹读同结构数据。"""
    mt = {}
    for line in open(os.path.join(d, "meta", "time.csv"), encoding="utf-8-sig").read().splitlines()[1:]:
        p = next(csv.reader([line]))
        if len(p) >= 4:
            mt[p[0]] = float(p[2])
    ts, vals = [], []
    for line in open(os.path.join(d, "Amplitudes.csv"), encoding="utf-8-sig").read().splitlines()[1:]:
        p = line.split(",")
        if len(p) != 2:
            continue
        try:
            t, v = float(p[0]), float(p[1])
        except Exception:
            continue
        if math.isfinite(v) and v > -50:
            ts.append(t)
            vals.append(v)
    return dict(file=os.path.basename(d) + "/Amplitudes.csv",
                start=datetime.fromtimestamp(mt["START"], tz),
                end=datetime.fromtimestamp(mt["PAUSE"], tz),
                dur=ts[-1] - ts[0], n=len(vals), leq=leq(vals), peak=max(vals),
                peak1s=peak1s(ts, vals), lmin=min(vals),
                p10=pct(sorted(vals), .10), p50=pct(sorted(vals), .50),
                p90=pct(sorted(vals), .90))


def from_zip(d):
    name = os.path.basename(d)
    if name in SOURCE_OVERRIDE:
        return from_unzipped(os.path.join(d, SOURCE_OVERRIDE[name]))
    zp = [f for f in os.listdir(d) if f.lower().endswith(".zip")]
    if not zp:
        return None
    with zipfile.ZipFile(os.path.join(d, zp[0])) as z:
        mt = {}
        for line in z.read("meta/time.csv").decode("utf-8-sig").splitlines()[1:]:
            p = next(csv.reader([line]))
            if len(p) >= 4:
                mt[p[0]] = float(p[2])
        ts, vals = [], []
        for line in z.read("Amplitudes.csv").decode("utf-8-sig").splitlines()[1:]:
            p = line.split(",")
            if len(p) != 2:
                continue
            try:
                t, v = float(p[0]), float(p[1])
            except Exception:
                continue
            if math.isfinite(v) and v > -50:
                ts.append(t)
                vals.append(v)
    return dict(file=zp[0], start=datetime.fromtimestamp(mt["START"], tz),
                end=datetime.fromtimestamp(mt["PAUSE"], tz),
                dur=ts[-1] - ts[0], n=len(vals), leq=leq(vals), peak=max(vals),
                peak1s=peak1s(ts, vals), lmin=min(vals),
                p10=pct(sorted(vals), .10), p50=pct(sorted(vals), .50),
                p90=pct(sorted(vals), .90))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for folder in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, folder)
        if not os.path.isdir(d):
            continue
        per, loc = folder_meta(folder)
        if loc not in STD:
            continue
        cat, ld, ln = STD[loc]
        r = from_zip(d)
        if r is None:
            print("!! 无 zip:", folder)
            continue
        # 口径（2026-10-31 定）：15 组实测时刻全部落在 06:00—22:00，按 GB 3096 属昼间，
        # 判定一律用昼间限值；夜间限值只作「情景推演」另列，不参与判定。
        night = (per == "晚")
        lim = ld
        rows.append(dict(folder=folder, per=per, loc=loc, cat=cat, dayLimit=ld, nightLimit=ln,
                         limit=lim, night=night,
                         date=r["start"].strftime("%Y-%m-%d"),
                         start=r["start"].strftime("%H:%M:%S"),
                         end=r["end"].strftime("%H:%M:%S"),
                         file=r["file"],
                         dur=round(r["dur"], 1), n=r["n"],
                         leq=round(r["leq"], 2), peak=round(r["peak"], 2),
                         peak1s=round(r["peak1s"], 2), lmin=round(r["lmin"], 2),
                         p10=round(r["p10"], 2), p50=round(r["p50"], 2), p90=round(r["p90"], 2),
                         over=round(r["leq"] - lim, 2),
                         overNight=round(r["leq"] - ln, 2),
                         verdict="超标" if r["leq"] > lim else "达标",
                         verdictNight="超标" if r["leq"] > ln else "达标"))
    rows.sort(key=lambda x: (PERIOD_ORDER.index(x["per"]), ORDER.index(x["loc"])))

    print("%-3s %-7s %-5s %-11s %6s %5s %7s %7s %7s %6s %s  %s" %
          ("时段", "点位", "类别", "开始", "时长", "样本", "Leq", "峰值", "1s峰", "超出", "判定", "夜间情景"))
    for r in rows:
        print("%-3s %-7s %-5s %-11s %6.0f %5d %7.2f %7.2f %7.2f %+6.1f %s  %+6.1f %s" %
              (r["per"], r["loc"], r["cat"], r["date"][5:] + " " + r["start"],
               r["dur"], r["n"], r["leq"], r["peak"], r["peak1s"], r["over"], r["verdict"],
               r["overNight"], r["verdictNight"]))

    with open(os.path.join(OUT_DIR, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\n共 %d 组，已存 %s" % (len(rows), os.path.join(OUT_DIR, "stats.json")))


main()
