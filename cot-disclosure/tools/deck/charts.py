"""Native (editable) PowerPoint bar charts for the final deck, version 3 (DECK_V3, Nov 26).

The house style of Ritik's Nov 26 deck: maroon 8C1D40 for the tool or the trained model, gold FFC627 for the user or
the baseline, near-black 191919 for the checker, a light grey for the rest; Arial; labels at least 11 pt; a 95%
interval drawn on every bar (custom error bars, absolute bounds); the count under each category label ("147/162"),
never as a data label. Values are percentages (0-100) unless a chart says otherwise.

    bars(slide, x, y, w, h, cats, series, ...)   -> the chart's graphic frame

series: [{"name", "values", "low", "high", "color", "point_colors" (optional, one per category or None)}]
"""
from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

MAROON = RGBColor(0x8C, 0x1D, 0x40)
GOLD = RGBColor(0xFF, 0xC6, 0x27)
INK = RGBColor(0x19, 0x19, 0x19)
GREY = RGBColor(0xC9, 0xC9, 0xCC)
RULE = RGBColor(0xD9, 0xD9, 0xDC)
MUTED = RGBColor(0x5C, 0x5C, 0x62)
FONT = "Arial"

C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _el(tag, **attrs):
    ns, name = tag.split(":")
    e = etree.Element("{%s}%s" % (C if ns == "c" else A, name))
    for k, v in attrs.items():
        e.set(k, str(v))
    return e


def _sub(parent, tag, **attrs):
    e = _el(tag, **attrs)
    parent.append(e)
    return e


def _numlit(parent, tag, vals):
    side = _sub(parent, tag)
    lit = _sub(side, "c:numLit")
    _sub(lit, "c:formatCode").text = "General"
    _sub(lit, "c:ptCount", val=len(vals))
    for i, v in enumerate(vals):
        if v is None:
            continue
        pt = _sub(lit, "c:pt", idx=i)
        _sub(pt, "c:v").text = f"{max(0.0, v):.4f}"


def error_bars(ser, values, low, high, color="191919", width_emu=12700):
    """Custom error bars from absolute bounds: plus = high - value, minus = value - low (schema order: before c:cat)."""
    eb = _el("c:errBars")
    _sub(eb, "c:errBarType", val="both")
    _sub(eb, "c:errValType", val="cust")
    _sub(eb, "c:noEndCap", val=0)
    _numlit(eb, "c:plus", [None if v is None or h is None else h - v for v, h in zip(values, high)])
    _numlit(eb, "c:minus", [None if v is None or lo is None else v - lo for v, lo in zip(values, low)])
    sp = _sub(eb, "c:spPr")
    ln = _sub(sp, "a:ln", w=width_emu)
    fill = _sub(ln, "a:solidFill")
    _sub(fill, "a:srgbClr", val=color)
    sx = ser._element
    cat = sx.find(qn("c:cat"))
    (cat.addprevious if cat is not None else sx.append)(eb)


def _font(tf_owner, size, color=INK, bold=False):
    f = tf_owner.font
    f.name, f.size, f.bold = FONT, Pt(size), bold
    f.color.rgb = color


def bars(slide, x, y, w, h, cats, series, *, horizontal=False, vmin=0, vmax=100, major=25, fs=11,
         number_format='0"%"', gap=60, overlap=-10, legend=True, legend_pos="top", name="chart", alt="",
         gridlines=True, value_axis=True, plot=None, cat_labels=True):
    """plot: (left, top, width, height) of the inner plot area as fractions of the frame (a manual layout, so rows
    sit where rows_y() says in PowerPoint and LibreOffice alike); cat_labels=False hides the category labels (the
    slide then draws names and counts as text beside the rows)."""
    cd = CategoryChartData(number_format=number_format)
    cd.categories = cats
    for s in series:
        cd.add_series(s["name"], [0 if v is None else v for v in s["values"]])
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    gf.name = name
    gf._element.xpath("./p:nvGraphicFramePr/p:cNvPr")[0].set("descr", alt)
    ch = gf.chart
    ch.font.name, ch.font.size = FONT, Pt(fs)
    ch.font.color.rgb = INK
    ch.has_title = False
    bp = ch.plots[0]
    bp.gap_width, bp.overlap = gap, overlap
    bp.vary_by_categories = False
    for ser, s in zip(bp.series, series):
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = s["color"]
        ser.format.line.fill.background()
        ser.invert_if_negative = False
        for i, pc in enumerate(s.get("point_colors") or []):
            if pc is not None:
                pt = ser.points[i]
                pt.format.fill.solid()
                pt.format.fill.fore_color.rgb = pc
                pt.format.line.fill.background()
        if s.get("low") is not None:
            error_bars(ser, s["values"], s["low"], s["high"])

    ca, va = ch.category_axis, ch.value_axis
    _font(ca.tick_labels, fs)
    ca.format.line.color.rgb = RULE
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.has_major_gridlines = False
    if horizontal:  # first category on top, the value axis kept at the bottom
        ca.reverse_order = True
        ch._chartSpace.xpath(".//c:valAx/c:crosses")[0].set("val", "max")
    va.minimum_scale, va.maximum_scale, va.major_unit = vmin, vmax, major
    va.has_major_gridlines = gridlines
    if gridlines:
        va.major_gridlines.format.line.color.rgb = RULE
        va.major_gridlines.format.line.width = Pt(0.5)
    va.format.line.fill.background()
    va.major_tick_mark = XL_TICK_MARK.NONE
    va.tick_labels.number_format = number_format
    va.tick_labels.number_format_is_linked = False
    _font(va.tick_labels, fs, MUTED)
    if not value_axis:
        va.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    if not cat_labels:
        ca.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    if plot is not None:
        pa = ch._chartSpace.xpath(".//c:plotArea")[0]
        old_l = pa.find(qn("c:layout"))
        if old_l is not None:
            pa.remove(old_l)
        lay = _el("c:layout")
        ml = _sub(lay, "c:manualLayout")
        _sub(ml, "c:layoutTarget", val="inner")
        _sub(ml, "c:xMode", val="edge")
        _sub(ml, "c:yMode", val="edge")
        for k, v in zip("xywh", plot):
            _sub(ml, f"c:{k}", val=f"{v:.4f}")
        pa.insert(0, lay)
    # every category label shown (LibreOffice otherwise skips some when they crowd)
    cax = ch._chartSpace.xpath(".//c:catAx")[0]
    nml = cax.find(qn("c:noMultiLvlLbl"))
    skip = _el("c:tickLblSkip", val=1)
    (nml.addprevious if nml is not None else cax.append)(skip)
    ch.has_legend = legend
    if legend:
        ch.legend.position = {"top": XL_LEGEND_POSITION.TOP, "bottom": XL_LEGEND_POSITION.BOTTOM,
                              "right": XL_LEGEND_POSITION.RIGHT}[legend_pos]
        ch.legend.include_in_layout = False
        _font(ch.legend, fs)
    return gf


def rows_y(y, h, plot, n):
    """Centre (inches) of each of n horizontal-bar rows, top to bottom, for a frame at y, h with a manual plot."""
    top, ph = y + plot[1] * h, plot[3] * h
    return [top + (i + 0.5) * ph / n for i in range(n)]


def cols_x(x, w, plot, n):
    """Centre (inches) of each of n column-chart categories, left to right, for a frame at x, w with a manual plot."""
    left, pw = x + plot[0] * w, plot[2] * w
    return [left + (i + 0.5) * pw / n for i in range(n)]
