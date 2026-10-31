# -*- coding: utf-8 -*-
"""课题06 交付用 Excel：15 组声学数据表 + 雷达图 + 标准依据 + 光效参数。

输入 D:\deepseek工作\noise06\build\stats.json
输出 D:\deepseek工作\noise06\deliver\数据\课题06_十五组声学数据表与雷达图.xlsx
"""
import os, json

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import RadarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation

BUILD = r"D:\deepseek工作\noise06\build"
DELIVER = r"D:\deepseek工作\noise06\deliver"
OUT = os.path.join(DELIVER, "数据", "课题06_十五组声学数据表与雷达图.xlsx")

NAVY = "1F3864"
BLUE2 = "2E5496"
LIGHT = "EEF2F8"
ACC = "C00000"
WARN = "BF8F00"
thin = Side(style="thin", color="BFC8D6")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

ORDER = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]
PERIODS = ["早", "中", "晚"]
PER_NAME = {"早": "早（昼间 07—19 时）", "中": "中（昼间 07—19 时）", "晚": "晚（夜间 19—07 时）"}


def load():
    rows = json.load(open(os.path.join(BUILD, "stats.json"), encoding="utf-8"))
    rows.sort(key=lambda r: (PERIODS.index(r["per"]), ORDER.index(r["loc"])))
    return rows


def style_title(ws, rng, text, size=15, height=34):
    ws.merge_cells(rng)
    c = ws[rng.split(":")[0]]
    c.value = text
    c.font = Font(name="微软雅黑", size=size, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[c.row].height = height


def main():
    rows = load()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb = openpyxl.Workbook()

    # ================= 01 十五组汇总 =================
    ws = wb.active
    ws.title = "01 十五组汇总"
    ws.sheet_view.showGridLines = False

    HDR = ["编号", "时段", "标准\n归属", "监测点位", "功能区\n类别", "适用限值\n(昼间) dB(A)",
           "采样日期", "开始时刻", "时长\n(s)", "有效\n样本", "均值 Leq\ndB(A)",
           "瞬时峰值\nLmax dB(A)", "1 s 峰值\ndB(A)", "L10", "L50", "L90", "超出量\nΔdB", "判定",
           "夜间限值\n(情景) dB(A)", "情景 Δ\n(若按夜间)"]
    W = [6, 6, 15, 13, 9, 13, 12, 10, 7, 7, 11, 16, 12, 8, 8, 8, 9, 8, 13, 12]

    style_title(ws, "A1:T1", "课题 06　校园昼夜声学噪声地图测绘 —— 15 组声学数据表（早 / 中 / 晚 × 5 点位）")
    ws.merge_cells("A2:T2")
    ws["A2"].value = ("数据来源：Phyphox「声音振幅」原始包（采样率约 9.2 Hz）　｜　判定依据：GB 3096-2008《声环境质量标准》"
                      "　｜　昼间 6:00—22:00、夜间 22:00—6:00；15 组实测时刻全部落在昼间区间，故判定一律用昼间限值，夜间限值仅作情景推演（最后两列）"
                      "　｜　15 组 · 5 点位 × 3 时段"+"\n"+""+"　｜　传感器：手机麦克风（OnePlus PLK110，Phyphox 1.2.1），未接标准声级计，绝对声级存在未量化偏差")
    ws["A2"].font = Font(name="微软雅黑", size=9, color="666666")
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 40

    HR = 4
    for i, h in enumerate(HDR, 1):
        c = ws.cell(row=HR, column=i, value=h)
        c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    ws.row_dimensions[HR].height = 42

    for k, r in enumerate(rows):
        row = HR + 1 + k
        night = r["night"]
        belong = "昼间（19:00）" if night else "昼间"
        vals = [("S%02d" % (k + 1)), r["per"], belong, r["loc"], r["cat"],
                r["limit"], r["date"], r["start"], r["dur"], r["n"], r["leq"], r["peak"],
                r["peak1s"], r["p10"], r["p50"], r["p90"], r["over"], r["verdict"],
                r["nightLimit"], r["overNight"]]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=row, column=j, value=v)
            c.font = Font(name="微软雅黑", size=10, bold=(j in (11, 18)))
            c.border = BOX
            c.alignment = Alignment(horizontal="left" if j == 4 else "center", vertical="center")
            if night and j in (2, 3):
                c.fill = PatternFill("solid", fgColor="E8E8F5")
            elif (not night) and j in (2, 3):
                c.fill = PatternFill("solid", fgColor="FBF6E9")
        for j in (11, 12, 13, 14, 15, 16):
            ws.cell(row=row, column=j).number_format = "0.0"
        ws.cell(row=row, column=17).number_format = "+0.0;-0.0"
        ws.cell(row=row, column=20).number_format = "+0.0;-0.0"
        ws.row_dimensions[row].height = 21

    n_ok = sum(1 for r in rows if r["verdict"] == "达标")
    n_bad = sum(1 for r in rows if r["verdict"] == "超标")
    tr = HR + len(rows) + 2
    ws.merge_cells(start_row=tr, start_column=1, end_row=tr, end_column=20)
    n_bad_night = sum(1 for r in rows if r["verdictNight"] == "超标")
    c = ws.cell(row=tr, column=1,
                value="统计（昼间限值口径）：共 15 组　超标 %d 组 / 达标 %d 组（达标的 3 组都是主干道）；"
                      "若改按夜间限值评价，则 %d 组全部超标 —— 同一批声级，换把尺子结论就翻转"
                      % (n_bad, n_ok, n_bad_night))
    c.font = Font(name="微软雅黑", size=10, bold=True, color=ACC)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[tr].height = 24

    ws.conditional_formatting.add("Q5:Q%d" % (HR + len(rows)),
                                  ColorScaleRule(start_type="num", start_value=-13, start_color="4A90D9",
                                                 mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                 end_type="num", end_value=7, end_color="E06666"))
    ws.conditional_formatting.add("R5:R%d" % (HR + len(rows)),
                                  CellIsRule(operator="equal", formula=['"超标"'],
                                             fill=PatternFill("solid", fgColor="F8CBAD"),
                                             font=Font(name="微软雅黑", size=10, bold=True, color=ACC)))
    dv = DataValidation(type="list", formula1='"早,中,晚"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("B5:B%d" % (HR + len(rows)))

    for i, w in enumerate(W, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "E5"
    ws.auto_filter.ref = "A4:T%d" % (HR + len(rows))

    # ================= 02 点位 × 时段 =================
    ws2 = wb.create_sheet("02 点位对比")
    ws2.sheet_view.showGridLines = False
    style_title(ws2, "A1:J1", "同一测点三个时段的对比（Leq 与超出量 Δ）")

    idx = {(r["per"], r["loc"]): r for r in rows}
    hdr2 = ["监测点位", "功能区\n类别", "昼间限值", "夜间限值",
            "早 Leq", "早 Δ", "中 Leq", "中 Δ", "晚 Leq", "晚 Δ"]
    for i, h in enumerate(hdr2, 1):
        c = ws2.cell(row=3, column=i, value=h)
        c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=BLUE2)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    ws2.row_dimensions[3].height = 34

    for k, loc in enumerate(ORDER):
        row = 4 + k
        e, m, n = idx.get(("早", loc)), idx.get(("中", loc)), idx.get(("晚", loc))
        base = e or m or n
        vals = [loc, base["cat"], base["dayLimit"], base["nightLimit"],
                e["leq"] if e else None, e["over"] if e else None,
                m["leq"] if m else None, m["over"] if m else None,
                n["leq"] if n else None, n["over"] if n else None]
        for j, v in enumerate(vals, 1):
            c = ws2.cell(row=row, column=j, value=v)
            c.font = Font(name="微软雅黑", size=10, bold=(j == 1))
            c.border = BOX
            c.alignment = Alignment(horizontal="left" if j == 1 else "center", vertical="center")
            if j in (5, 7, 9) and v is not None:
                c.number_format = "0.0"
            if j in (6, 8, 10) and v is not None:
                c.number_format = "+0.0;-0.0"
        ws2.row_dimensions[row].height = 22

    ws2.conditional_formatting.add("F4:F8", ColorScaleRule(start_type="num", start_value=-13, start_color="4A90D9",
                                                            mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                            end_type="num", end_value=16, end_color="E06666"))
    ws2.conditional_formatting.add("H4:H8", ColorScaleRule(start_type="num", start_value=-13, start_color="4A90D9",
                                                            mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                            end_type="num", end_value=16, end_color="E06666"))
    ws2.conditional_formatting.add("J4:J8", ColorScaleRule(start_type="num", start_value=-13, start_color="4A90D9",
                                                            mid_type="num", mid_value=0, mid_color="FFFFFF",
                                                            end_type="num", end_value=16, end_color="E06666"))

    r0 = 10
    ws2.merge_cells(start_row=r0, start_column=1, end_row=r0, end_column=10)
    c = ws2.cell(row=r0, column=1,
                 value="读法：早 / 中 / 晚一律用昼间限值（55 / 60 / 70）。Δ > 0 即超标。"
                       "主干道是 4a 类，限值最高，三个时段全部达标（−6.5 / −12.7 / −9.7）；"
                       "若改按夜间限值 55，它会由 −9.7 翻成 +5.3。")
    c.font = Font(name="微软雅黑", size=9, color="666666")
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws2.row_dimensions[r0].height = 40

    ws2.merge_cells(start_row=r0 + 1, start_column=1, end_row=r0 + 1, end_column=10)
    c = ws2.cell(row=r0 + 1, column=1,
                 value="关键现象：三个时段的 Leq 只差 −3.1 ~ +1.6 dB，超标与否主要由「类别限值」决定；"
                       "若改按夜间限值评价，15 组会全部超标 —— 差的那 10 dB 全部来自限值换挡。")
    c.font = Font(name="微软雅黑", size=10, bold=True, color=ACC)
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws2.row_dimensions[r0 + 1].height = 40

    for i, w in enumerate([14, 10, 10, 10, 9, 9, 9, 9, 9, 9], 1):
        ws2.column_dimensions[get_column_letter(i)].width = w

    # ================= 03 雷达图 =================
    ws3 = wb.create_sheet("03 雷达图")
    ws3.sheet_view.showGridLines = False
    style_title(ws3, "A1:J1", "三分时段「超出量 Δ」雷达图（Δ = Leq − 适用限值，单位 dB）", size=14)

    ws3["A4"] = "监测点位"
    for j, p in enumerate(PERIODS, 2):
        ws3.cell(row=4, column=j, value="%s ΔdB" % p)
    for k, loc in enumerate(ORDER):
        ws3.cell(row=5 + k, column=1, value=loc)
        for j, p in enumerate(PERIODS, 2):
            r = idx.get((p, loc))
            ws3.cell(row=5 + k, column=j, value=(r["over"] if r else None))
    for rr in range(4, 10):
        for cc in range(1, 5):
            c = ws3.cell(row=rr, column=cc)
            c.border = BOX
            c.font = Font(name="微软雅黑", size=10, bold=(rr == 4))
            c.alignment = Alignment(horizontal="center", vertical="center")
            if 5 <= rr <= 9 and cc >= 2:
                c.number_format = "+0.0;-0.0"
    for col, w in zip("ABCD", [16, 12, 12, 12]):
        ws3.column_dimensions[col].width = w

    ch = RadarChart()
    ch.type = "marker"
    ch.style = 26
    ch.title = "早 / 中 / 晚 超出量 Δ（dB）"
    data = Reference(ws3, min_col=2, max_col=4, min_row=4, max_row=9)
    cats = Reference(ws3, min_col=1, min_row=5, max_row=9)
    ch.add_data(data, titles_from_data=True)
    ch.set_categories(cats)
    ch.y_axis.scaling.min = -12
    ch.y_axis.scaling.max = 8
    ch.y_axis.majorUnit = 4
    ch.height = 13.5
    ch.width = 15
    ws3.add_chart(ch, "F4")

    note_grey = [
        "为什么画 Δ 而不画绝对 dB：",
        "五个点位分属 1 类 / 2 类 / 4a 类，",
        "限值从 55 到 70 不等。画绝对声级时，",
        "主干道永远在最外圈，会被误读成最吵；",
        "换成 Δ 之后五个方向共用一把尺子：",
        "0 线 = 限值线，越往外越超标。",
    ]
    for k, s in enumerate(note_grey):
        r = 11 + k
        ws3.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        c = ws3.cell(row=r, column=1, value=s)
        c.font = Font(name="微软雅黑", size=9, color="666666")
        c.alignment = Alignment(horizontal="left", vertical="center")
        ws3.row_dimensions[r].height = 16

    note_red = [
        "三条曲线几乎贴在一起——同一批点位，早 / 中 / 晚的超出量",
        "相差不到 3 dB：傍晚并不比白天吵。若改按夜间限值重画一次，",
        "那圈会整体外扩 10 dB——外扩的是尺子，不是声音（见 01 页情景列）。",
    ]
    for k, s in enumerate(note_red):
        r = 19 + k
        ws3.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        c = ws3.cell(row=r, column=1, value=s)
        c.font = Font(name="微软雅黑", size=9, bold=True, color=ACC)
        c.alignment = Alignment(horizontal="left", vertical="center")
        ws3.row_dimensions[r].height = 16

    # ================= 04 标准依据 =================
    ws4 = wb.create_sheet("04 标准依据")
    ws4.sheet_view.showGridLines = False
    style_title(ws4, "A1:F1", "GB 3096-2008《声环境质量标准》环境噪声限值（等效声级 Leq，dB(A)）")

    h4 = ["声环境功能区类别", "适用区域（本课题对应点位）", "昼间 6:00—22:00", "夜间 22:00—6:00", "本课题点位", "取值说明"]
    for i, h in enumerate(h4, 1):
        c = ws4.cell(row=3, column=i, value=h)
        c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=BLUE2)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    ws4.row_dimensions[3].height = 36

    STD = [
        ("0 类", "康复疗养区等特别需要安静的区域", "50", "40", "—", "本课题无此类点位"),
        ("1 类", "以居民住宅、医疗卫生、文化教育、科研设计、行政办公为主要功能，需要保持安静的区域",
         "55", "45", "图书馆、实训室走廊", "文教科研办公为主，从严取值"),
        ("2 类", "以商业金融、集市贸易为主要功能，或者居住、商业、工业混杂，需要维护住宅安静的区域",
         "60", "50", "食堂、运动场", "商业与生活混杂；运动场按场地活动期间取 2 类"),
        ("3 类", "以工业生产、仓储物流为主要功能，需要防止工业噪声对周围环境产生严重影响的区域",
         "65", "55", "—", "本课题无此类点位"),
        ("4a 类", "高速公路、一级公路、二级公路、城市快速路、城市主干路、城市次干路、城市轨道交通"
                  "（地面段）、内河航道两侧区域", "70", "55", "主干道", "校园主路两侧 4a 类"),
    ]
    for k, (cat, area, day, night, pts, note) in enumerate(STD):
        row = 4 + k
        for j, v in enumerate([cat, area, day, night, pts, note], 1):
            c = ws4.cell(row=row, column=j, value=v)
            c.font = Font(name="微软雅黑", size=9, bold=(j == 1))
            c.border = BOX
            c.alignment = Alignment(horizontal="center" if j in (3, 4) else "left",
                                    vertical="center", wrap_text=(j in (2, 6)))
        ws4.row_dimensions[row].height = 46

    r = 4 + len(STD) + 1
    ws4.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    c = ws4.cell(row=r, column=1,
                 value="判定规则：Leq 实测值 > 该点位所属功能区、所属时段的限值，即判「超标」；"
                       "超出量 Δ = 实测 Leq − 限值。峰值 Lmax 与 1 s 峰值不参与达标判定，"
                       "只作为「瞬时冲击」另立通道单独告警（见第 05 页光效参数）。")
    c.font = Font(name="微软雅黑", size=9, color="333333")
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws4.row_dimensions[r].height = 46

    for i, w in enumerate([14, 46, 14, 14, 18, 34], 1):
        ws4.column_dimensions[get_column_letter(i)].width = w

    # ================= 05 光效参数 =================
    ws5 = wb.create_sheet("05 光效参数")
    ws5.sheet_view.showGridLines = False
    style_title(ws5, "A1:H1", "声学超标自动提醒 —— 光效编码与状态机参数（与《光效逻辑设计》文档一致）")

    h5 = ["状态", "触发条件（Δ = Leq − 限值）", "主色", "RGB", "亮度", "闪烁频率", "占空比", "含义"]
    for i, h in enumerate(h5, 1):
        c = ws5.cell(row=3, column=i, value=h)
        c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=BLUE2)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BOX
    ws5.row_dimensions[3].height = 34

    LIGHT = [
        ("S0 安静", "Δ ≤ −10", "青蓝", "00C2FF", "25%", "常亮", "100%", "远低于限值，无需提醒"),
        ("S1 达标", "−10 < Δ ≤ 0", "绿", "22C55E", "50%", "常亮", "100%", "符合标准，视觉上「不打扰」"),
        ("S2 轻度超标", "0 < Δ ≤ +5", "黄", "FACC15", "75%", "呼吸 0.5 Hz", "50%", "刚过线，提示注意"),
        ("S3 中度超标", "+5 < Δ ≤ +10", "橙", "FB923C", "90%", "闪烁 1.0 Hz", "50%", "明显超标，需要干预"),
        ("S4 重度超标", "Δ > +10", "红", "EF4444", "100%", "急闪 2.5 Hz", "30%", "严重超标，立即处置"),
        ("SP 瞬时冲击", "Lmax ≥ 85 dB(A)", "红白交替", "EF4444", "100%", "快闪 5.0 Hz", "50%", "脉冲式冲击，与等级判定并行"),
    ]
    for k, rowv in enumerate(LIGHT):
        row = 4 + k
        for j, v in enumerate(rowv, 1):
            c = ws5.cell(row=row, column=j, value=v)
            c.font = Font(name="微软雅黑", size=9, bold=(j == 1))
            c.border = BOX
            c.alignment = Alignment(horizontal="center" if j in (3, 4, 5, 6, 7) else "left",
                                    vertical="center", wrap_text=(j == 2))
        # 主色块填真实颜色
        sw = ws5.cell(row=row, column=3)
        sw.fill = PatternFill("solid", fgColor=rowv[3])
        sw.font = Font(name="微软雅黑", size=9, bold=True,
                       color="FFFFFF" if rowv[3] in ("00C2FF", "22C55E", "2E5496", "EF4444", "FB923C") else "333333")
        ws5.row_dimensions[row].height = 24

    r = 4 + len(LIGHT) + 1
    TIMING = [
        ("刷新周期", "1 s", "每秒采样一次，人察觉不到延迟"),
        ("上升沿", "即时切换（连续 3 s 确认）", "安全优先，宁可早报不可晚报"),
        ("下降沿", "低于下一档阈值 2 dB 且保持 5 s 才降级", "回差 + 保持，防止临界抖动"),
        ("最短保持", "任一超标状态 ≥ 10 s", "防止一次咳嗽让灯闪一下又灭"),
        ("优先级", "SP > S4 > S3 > S2 > S1 > S0", "高优先级可立即抢占，低优先级不得覆盖高优先级"),
        ("夜间模式", "22:00—6:00 亮度 ×0.4、频率上限 1 Hz", "避免「治理噪声」反而制造光污染"),
        ("冲击通道", "Lmax ≥ 85 dB(A) 立即触发，3 s 后回退", "不参与平滑、不排队去抖"),
        ("不确定度带", "±3 dB（见《创新体系》第 2 节）", "落入灰带时由 S1/S2 之间取「黄闪」并标记待复核"),
    ]
    ws5.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    c = ws5.cell(row=r, column=1, value="时序与仲裁参数")
    c.font = Font(name="微软雅黑", size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws5.row_dimensions[r].height = 24

    h6 = ["参数", "取值", "理由"]
    for i, h in enumerate(h6, 1):
        c = ws5.cell(row=r + 1, column=i if i < 3 else 3, value=h)
    # 简单三列排布：A / B / C:F
    for i, h in enumerate(h6, 1):
        col = 1 if i == 1 else (2 if i == 2 else 3)
        c = ws5.cell(row=r + 1, column=col, value=h)
        c.font = Font(name="微软雅黑", size=9, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=BLUE2)
        c.border = BOX
        c.alignment = Alignment(horizontal="center", vertical="center")
    ws5.merge_cells(start_row=r + 1, start_column=3, end_row=r + 1, end_column=8)

    for k, (name, val, why) in enumerate(TIMING):
        row = r + 2 + k
        ws5.cell(row=row, column=1, value=name).font = Font(name="微软雅黑", size=9, bold=True)
        ws5.cell(row=row, column=2, value=val).font = Font(name="微软雅黑", size=9)
        ws5.merge_cells(start_row=row, start_column=3, end_row=row, end_column=8)
        ws5.cell(row=row, column=3, value=why).font = Font(name="微软雅黑", size=9, color="555555")
        for cc in range(1, 9):
            ws5.cell(row=row, column=cc).border = BOX
        ws5.cell(row=row, column=2).alignment = Alignment(horizontal="center", vertical="center")
        ws5.cell(row=row, column=2).number_format = "@"
        ws5.row_dimensions[row].height = 22

    for i, w in enumerate([14, 30, 12, 12, 8, 14, 8, 30], 1):
        ws5.column_dimensions[get_column_letter(i)].width = w

    wb.save(OUT)
    print("saved:", OUT)
    print("15 组：超标 %d / 达标 %d" % (n_bad, n_ok))


main()
