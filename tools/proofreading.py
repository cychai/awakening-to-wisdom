"""Conservative Chinese typography and PDF-layout proofreading helpers."""

from __future__ import annotations

import re
from typing import NamedTuple, Sequence


CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
CJK_PUNCT = "，。！？；：、）》】』」”’…"
OPEN_PUNCT = "《【『「“‘（"
MEASURE_WORDS = (
    "年|月|日|天|个|件|次|岁|元|块|万|亿|百|千|秒|分钟|小时|"
    "米|斤|页|章|节|部分|册|倍|种|条|点|期|家|人|位|辆|套"
)
NUMBERED_ITEM = re.compile(r"^\s*(?:\d+|[一二三四五六七八九十百]+)[、，,.．]\s*")
ANSWER_START = re.compile(r"^\s*答[：:]\s*")
PAGE_CONTINUATION = re.compile(
    r"([^\n。！？；：<>])\n(<!-- 原书第 \d+ 页 -->)\n\n((?![#<])\S)"
)
CONFIRMED_CORRECTIONS = (
    ("祔扯明臼", "掰扯明白"),
    ("祔扯明白", "掰扯明白"),
    ("祔开枷锁", "挣开枷锁"),
    ("被盯上行业耻辱住", "被钉上行业耻辱柱"),
    ("在自己的小世界里于什么", "在自己的小世界里干什么"),
    ("婖不知耻", "恬不知耻"),
    ("悲财的十年", "悲惨的十年"),
    ("基因的愧倡", "基因的傀儡"),
    ("基因的愧偶", "基因的傀儡"),
    ("销甲的秘密", "铠甲的秘密"),
    ("铝甲的秘密", "铠甲的秘密"),
    ("反常识心理学现象一一内非肤骗局", "反常识心理学现象——内啡肽骗局"),
    ("枢伤口处的结痴", "抠伤口处的结痂"),
    ("用舌头去婖", "用舌头去舔"),
    ("跪薛", "跪舔"),
    ("跪秤", "跪舔"),
    ("内非肤", "内啡肽"),
    ("内啡肤", "内啡肽"),
    ("恺甲", "铠甲"),
    ("铝甲", "铠甲"),
    ("婖", "舔"),
    ("很多入懂玄学", "很多不懂玄学"),
    ("不愿意的出成本", "不愿意付出成本"),
    ("别以知道", "别人知道"),
    ("更离产生美", "距离产生美"),
    ("光耀门媒", "光耀门楣"),
    ("爱渭里的刺客", "爱情里的刺客"),
    ("知沪反噬", "知识反噬"),
    ("黑暗夺林", "黑暗森林"),
    ("乌烟擢气", "乌烟瘴气"),
    ("手拿把抬", "手拿把掐"),
    ("几旬才知道", "几句才知道"),
    ("明臼", "明白"),
    ("内非肽", "内啡肽"),
    ("婖狗", "舔狗"),
    ("耍说", "要说"),
    ("谈化", "淡化"),
    ("时侯", "时候"),
    ("儿个", "几个"),
    ("増値", "增值"),
    ("我己经", "我已经"),
    ("己经", "已经"),
    ("巳经", "已经"),
    ("而己", "而已"),
    ("干万", "千万"),
    ("悲慘", "悲惨"),
    ("擔串", "撸串"),
    ("枢气的说", "赌气的说"),
    ("冃的", "目的"),
    ("羊羊得意", "洋洋得意"),
    ("人情事故", "人情世故"),
    ("做在主咖", "坐在主咖"),
    ("仪仗自己的美貌", "依仗自己的美貌"),
    ("在亲近的人", "再亲近的人"),
    ("巳不得", "恨不得"),
    ("裸采禮鞏：6頒家子气", "啰里啰嗦，一副小家子气"),
    ("面容妏好", "面容姣好"),
    ("生命峎发可危", "生命岌岌可危"),
    ("发峎可危", "岌岌可危"),
    ("在世华伦的紧急", "在世华佗的锦旗"),
    ("华伦", "华佗"),
    ("蚔蛭撼树", "蚍蜉撼树"),
    ("侁儒症", "侏儒症"),
    ("縉弱", "懦弱"),
    ("白吃冃喝", "白吃白喝"),
    ("冃手起家", "白手起家"),
    ("一张臼纸", "一张白纸"),
    ("打訰的不算", "打盹的不算"),
    ("凄厉的玸哮", "凄厉的咆哮"),
    ("吭捇吭咭", "吭哧吭哧"),
    ("像扲整扇猪肉一样", "像拎整扇猪肉一样"),
    ("救死不伤", "救死扶伤"),
    ("叠加坰缩", "叠加坍缩"),
    ("噩子纠缠", "量子纠缠"),
    ("丰满钵满", "盆满钵满"),
    ("手里擢着", "手里攥着"),
    ("财富，神华", "神话，"),
    ("才是才是", "才是"),
    ("笢法把这内容", "算法把这内容"),
    ("在网上怍开了", "在网上炸开了"),
    ("视頻", "视频"),
    ("货帀", "货币"),
    ("三大陳则", "三大原则"),
    ("鲁豫釆访", "鲁豫采访"),
    ("都是釆用了", "都是采用了"),
    ("晩上", "晚上"),
    ("越来越煩", "越来越烦"),
    ("拝击上海伪名媛", "抨击上海伪名媛"),
    ("毕竞", "毕竟"),
    ("至千", "至于"),
    ("关千", "关于"),
    ("死千", "死于"),
    ("千是", "于是"),
    ("说臼了", "说白了"),
    ("两于块", "两千块"),
    ("叱吃风云", "叱咤风云"),
    ("—个", "一个"),
    ("凄渗的哭声", "凄惨的哭声"),
    ("回亿起", "回忆起"),
    ("第一种三十万毫终身残疾被救者感恩戴德。第二种，两千块毫发未伤", "第一种，三十万，终身残疾，被救者感恩戴德。第二种，两千块，毫发未伤"),
    ("登加态", "叠加态"),
    ("坰缩", "坍缩"),
    ("自治就好", "自洽就好"),
    ("吃棣咽菜", "吃糠咽菜"),
    ("离嬡胖瘦", "高矮胖瘦"),
    ("大阳地去谈", "大胆地去谈"),
    ("想曦钱", "想赚钱"),
    ("自身日前所具备", "自身目前所具备"),
    ("僮憬", "憧憬"),
    ("一种思意", "一种恶意"),
    ("不敢反致", "不敢反驳"),
    ("苛守", "恪守"),
    ("通性福", "通幸福"),
    ("生米恩", "升米恩"),
    ("属千", "属于"),
    ("隐截", "隐藏"),
)


class LayoutLine(NamedTuple):
    text: str
    x0: float
    y0: float
    y1: float


def normalize_spacing(text: str) -> str:
    """Remove extraction-only spacing without rewriting lexical content."""
    value = text.replace("\u00a0", " ").replace("\u3000", " ")
    value = re.sub(rf"(?<=[{CJK}]) +(?=[{CJK}])", "", value)
    value = re.sub(rf" +(?=[{re.escape(CJK_PUNCT)}])", "", value)
    value = re.sub(rf"(?<=[{re.escape(OPEN_PUNCT)}]) +", "", value)
    value = re.sub(rf"(?<=[{re.escape(CJK_PUNCT)}]) +(?=[{CJK}])", "", value)
    value = re.sub(rf"(?<=\d) +(?=(?:{MEASURE_WORDS}))", "", value)
    value = re.sub(rf"(?<=[{CJK}]) +(?=\d)", "", value)
    value = re.sub(rf"(?<=[{CJK}])[?]", "？", value)
    value = re.sub(rf"(?<=[{CJK}])[!]", "！", value)
    value = re.sub(rf"(?<=[{CJK}]),", "，", value)
    value = re.sub(rf"(?<=[{CJK}\d])\)", "）", value)
    return value.strip()


def apply_confirmed_corrections(text: str) -> str:
    """Apply only corrections confirmed from original page images or context."""
    value = text
    for before, after in CONFIRMED_CORRECTIONS:
        value = value.replace(before, after)
    return value


def _starts_new_paragraph(
    current: LayoutLine,
    previous: LayoutLine,
    base_x: float,
    indent_threshold: float,
) -> bool:
    if current.x0 >= base_x + indent_threshold:
        return True
    if NUMBERED_ITEM.match(current.text) or ANSWER_START.match(current.text):
        return True
    previous_height = max(previous.y1 - previous.y0, 1.0)
    vertical_gap = current.y0 - previous.y1
    return vertical_gap > max(previous_height * 1.8, 12.0)


def group_layout_lines(
    lines: Sequence[LayoutLine], base_x: float, indent_threshold: float = 12.0
) -> list[str]:
    """Group fixed-width PDF lines into paragraphs using original geometry."""
    paragraphs: list[str] = []
    current = ""
    previous: LayoutLine | None = None
    for line in lines:
        text = normalize_spacing(line.text)
        if not text:
            continue
        if previous is not None and _starts_new_paragraph(
            line, previous, base_x, indent_threshold
        ):
            if current:
                paragraphs.append(normalize_spacing(current))
            current = text
        else:
            current += text
        previous = line
    if current:
        paragraphs.append(normalize_spacing(current))
    return paragraphs


def group_semantic_lines(lines: Sequence[LayoutLine]) -> list[str]:
    """Group OCR lines by sentence boundaries when indentation is unavailable."""
    paragraphs: list[str] = []
    current = ""
    for line in lines:
        text = normalize_spacing(line.text)
        if not text:
            continue
        explicit_start = bool(NUMBERED_ITEM.match(text) or ANSWER_START.match(text))
        if current and (explicit_start or re.search(r"[。！？；?!][”’）】》]?$", current)):
            paragraphs.append(normalize_spacing(current))
            current = text
        else:
            current += text
    if current:
        paragraphs.append(normalize_spacing(current))
    return paragraphs


def join_across_page_markers(text: str) -> str:
    """Join a sentence split only by a PDF page boundary."""
    previous = None
    value = text
    while value != previous:
        previous = value
        value = PAGE_CONTINUATION.sub(r"\1\2\3", value)
    return value
