"""이름 바꾸기 규칙(파이프라인). 규칙은 위에서 아래로 연달아 적용된다.

각 규칙은 (stem, ext) 상태를 받아 새 상태를 돌려준다. ext는 점을 포함한다('.jpg').
규칙 옵션 오류는 validate_rules에서 RuleError로, 특정 항목에만 적용할 수 없는 경우는
apply_rules 결과의 오류 문자열로 알린다.
"""
from __future__ import annotations

import os
import re
import unicodedata

from .datetime_rules import entry_datetime, format_datetime, read_exif_datetime
from .model import RuleError, split_name
from .numbering import number_sequence

_NUMBER = re.compile(r"\d+")


def _bool(spec, key, default):
    value = spec.get(key, default)
    if not isinstance(value, bool):
        raise RuleError(f"'{key}'는 참/거짓이어야 합니다.")
    return value


def _int(spec, key, default, *, minimum=None, maximum=None):
    value = spec.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuleError(f"'{key}'는 정수여야 합니다.")
    if (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise RuleError(f"'{key}' 값의 범위를 확인해 주세요.")
    return value


def _str(spec, key, default="", *, allow_empty=True, max_len=255):
    value = spec.get(key, default)
    if not isinstance(value, str) or (not allow_empty and not value) or len(value) > max_len:
        raise RuleError(f"'{key}' 글자를 확인해 주세요.")
    return value


def _choice(spec, key, default, choices):
    value = spec.get(key, default)
    if value not in choices:
        raise RuleError(f"'{key}'는 {', '.join(choices)} 중 하나여야 합니다.")
    return value


def _ext_text(spec, key):
    value = _str(spec, key, allow_empty=False, max_len=32).strip()
    value = value if value.startswith(".") else "." + value
    if len(value) < 2 or "." in value[1:] or re.search(r'[\\/:*?"<>|\s]', value):
        raise RuleError("확장자를 확인해 주세요.")
    return value


def _place(stem, text, position, sep):
    if not text:
        return stem
    if position == "prefix":
        return text + (sep if stem else "") + stem
    if position == "suffix":
        return stem + (sep if stem else "") + text
    return text  # replace


def _scoped(state, scope, func):
    stem, ext = state
    if scope == "stem":
        return func(stem), ext
    if scope == "ext":
        return stem, func(ext)
    whole = func(stem + ext)
    return split_name(whole)


# ── 규칙 정의: (검증 함수, 적용 함수). 검증은 정규화한 옵션 dict를 돌려준다. ─────────────

def _v_replace(spec):
    find = _str(spec, "find", allow_empty=False)
    regex = _bool(spec, "regex", False)
    case = _bool(spec, "case", True)
    if regex:
        try:
            re.compile(find)
        except re.error as error:
            raise RuleError(f"정규식 오류: {error}") from None
    return dict(find=find, to=_str(spec, "to"), regex=regex, case=case,
                count=_choice(spec, "count", "all", ("all", "first")),
                scope=_choice(spec, "scope", "stem", ("stem", "ext", "name")))


def _a_replace(state, opt, ctx):
    flags = 0 if opt["case"] else re.IGNORECASE
    pattern = re.compile(opt["find"] if opt["regex"] else re.escape(opt["find"]), flags)
    count = 1 if opt["count"] == "first" else 0
    replacement = opt["to"] if opt["regex"] else opt["to"].replace("\\", "\\\\")
    return _scoped(state, opt["scope"], lambda text: pattern.sub(replacement, text, count=count))


def _v_add(spec):
    return dict(text=_str(spec, "text", allow_empty=False),
                position=_choice(spec, "position", "prefix", ("prefix", "suffix")), sep=_str(spec, "sep", max_len=8))


def _a_add(state, opt, ctx):
    entry = ctx["entry"]
    text = (opt["text"].replace("{orig}", entry.stem).replace("{folder}", os.path.basename(entry.folder))
            .replace("{date}", format_datetime(entry_datetime(entry, "mtime")[0], "YYYYMMDD")))
    return _place(state[0], text, opt["position"], opt["sep"]), state[1]


def _v_none(spec):
    return {}


def _a_clear(state, opt, ctx):
    return "", state[1]


def _v_del_pos(spec):
    start = _int(spec, "start", 1, minimum=1, maximum=1000)
    end = _int(spec, "end", start, minimum=start, maximum=1000)
    return dict(start=start, end=end, origin=_choice(spec, "origin", "start", ("start", "end")))


def _a_del_pos(state, opt, ctx):
    stem = state[0]
    if opt["origin"] == "start":
        stem = stem[:opt["start"] - 1] + stem[opt["end"]:]
    else:  # 제일 뒤에서 start번째~end번째
        length = len(stem)
        lo, hi = max(length - opt["end"], 0), max(length - opt["start"] + 1, 0)
        stem = stem[:lo] + stem[hi:]
    return stem, state[1]


def _v_del_between(spec):
    opener = _str(spec, "open", "(", allow_empty=False, max_len=4)
    closer = _str(spec, "close", ")", allow_empty=False, max_len=4)
    return dict(open=opener, close=closer, nest=_choice(spec, "nest", "outer", ("outer", "inner")),
                keep_marks=_bool(spec, "keep_marks", False))


def _a_del_between(state, opt, ctx):
    stem, opener, closer = state[0], opt["open"], opt["close"]
    spans, stack, i = [], [], 0
    while i < len(stem):
        if stem.startswith(opener, i) and (opener != closer or not stack):
            stack.append(i)
            i += len(opener)
            continue
        if stem.startswith(closer, i) and stack:
            begin = stack.pop()
            end = i + len(closer)
            depth = len(stack)
            spans.append((begin, end, depth))
            i = end
            continue
        i += 1
    if opt["nest"] == "outer":
        chosen = [(b, e) for b, e, d in spans if d == 0]
    else:  # 가장 안쪽: 다른 구간을 품지 않은 구간
        chosen = [(b, e) for b, e, d in spans if not any(b < b2 and e2 < e for b2, e2, _ in spans)]
    for begin, end in sorted(chosen, reverse=True):
        inner = (opener + closer) if opt["keep_marks"] else ""
        stem = stem[:begin] + inner + stem[end:]
    return re.sub(r" {2,}", " ", stem).strip(), state[1]


def _a_digits_keep(state, opt, ctx):
    return "".join(_NUMBER.findall(state[0])), state[1]


def _a_digits_delete(state, opt, ctx):
    return _NUMBER.sub("", state[0]), state[1]


def _v_digits_pad(spec):
    return dict(digits=_int(spec, "digits", 3, minimum=1, maximum=12),
                which=_choice(spec, "which", "last", ("first", "last")))


def _pick_number(stem, which):
    matches = list(_NUMBER.finditer(stem))
    if not matches:
        return None
    return matches[0] if which == "first" else matches[-1]


def _a_digits_pad(state, opt, ctx):
    match = _pick_number(state[0], opt["which"])
    if match is None:
        return state
    stem = state[0]
    return stem[:match.start()] + match.group().zfill(opt["digits"]) + stem[match.end():], state[1]


def _v_number(spec):
    return dict(start=_int(spec, "start", 1, minimum=0, maximum=10**9),
                step=_int(spec, "step", 1, minimum=1, maximum=10**6),
                digits=_int(spec, "digits", 3, minimum=1, maximum=12),
                position=_choice(spec, "position", "suffix", ("prefix", "suffix", "replace")),
                per_folder=_bool(spec, "per_folder", False), sep=_str(spec, "sep", "_", max_len=8))


def _a_number(state, opt, ctx):
    text = str(ctx["number"]).zfill(opt["digits"])
    return _place(state[0], text, opt["position"], opt["sep"]), state[1]


def _v_number_shift(spec):
    delta = _int(spec, "delta", 1, minimum=-10**9, maximum=10**9)
    if delta == 0:
        raise RuleError("증감 값은 0이 아니어야 합니다.")
    return dict(delta=delta, which=_choice(spec, "which", "first", ("first", "last")))


def _a_number_shift(state, opt, ctx):
    match = _pick_number(state[0], opt["which"])
    if match is None:
        return state
    value = int(match.group()) + opt["delta"]
    if value < 0:
        raise RuleError("번호가 0보다 작아집니다.")
    width = len(match.group()) if match.group().startswith("0") else 1
    stem = state[0]
    return stem[:match.start()] + str(value).zfill(width) + stem[match.end():], state[1]


def _a_ext_del(state, opt, ctx):
    return state[0], ""


def _v_ext(spec):
    return dict(ext=_ext_text(spec, "ext"))


def _a_ext_add(state, opt, ctx):
    return state[0] + state[1], opt["ext"]


def _a_ext_replace(state, opt, ctx):
    return state[0], opt["ext"]


def _v_ext_case(spec):
    return dict(mode=_choice(spec, "mode", "lower", ("lower", "upper")))


def _a_ext_case(state, opt, ctx):
    return state[0], state[1].lower() if opt["mode"] == "lower" else state[1].upper()


def _v_date(spec):
    pattern = _str(spec, "format", "YYYYMMDD", allow_empty=False, max_len=40)
    if not re.search(r"YYYY|YY|MM|DD|hh|mm|ss", pattern):
        raise RuleError("날짜 형식에 YYYY·MM·DD·hh·mm·ss 중 하나가 있어야 합니다.")
    return dict(source=_choice(spec, "source", "mtime", ("exif", "mtime", "ctime", "today")), format=pattern,
                position=_choice(spec, "position", "prefix", ("prefix", "suffix", "replace")),
                sep=_str(spec, "sep", "_", max_len=8))


def _a_date(state, opt, ctx):
    moment, fallback = entry_datetime(ctx["entry"], opt["source"], today=ctx.get("today"),
                                      exif_reader=ctx.get("exif_reader") or read_exif_datetime)
    if fallback:
        ctx["warnings"].add("exif_missing")
    return _place(state[0], format_datetime(moment, opt["format"]), opt["position"], opt["sep"]), state[1]


def _v_cleanup(spec):
    return dict(nfc=_bool(spec, "nfc", True), collapse_spaces=_bool(spec, "collapse_spaces", True),
                underscore=_choice(spec, "underscore", "keep", ("keep", "to_space", "from_space")),
                strip=_bool(spec, "strip", True))


def _a_cleanup(state, opt, ctx):
    stem = state[0]
    if opt["nfc"]:
        stem = unicodedata.normalize("NFC", stem)
    if opt["underscore"] == "to_space":
        stem = stem.replace("_", " ")
    elif opt["underscore"] == "from_space":
        stem = stem.replace(" ", "_")
    if opt["collapse_spaces"]:
        stem = re.sub(r" {2,}", " ", stem)
        stem = re.sub(r"_{2,}", "_", stem)
    if opt["strip"]:
        stem = stem.strip(" _-")
    ext = unicodedata.normalize("NFC", state[1]) if opt["nfc"] else state[1]
    return stem, ext


def _v_case(spec):
    return dict(mode=_choice(spec, "mode", "lower", ("lower", "upper", "title")))


def _a_case(state, opt, ctx):
    stem = state[0]
    return (stem.lower() if opt["mode"] == "lower" else stem.upper() if opt["mode"] == "upper" else stem.title()), state[1]


# 앱 결과 파일 접미사. 새 접미사가 생기면 여기만 고친다.
RESULT_SUFFIXES = ("(자간조정)", "(일괄적용)", "(서식통일)", "(서식적용)", "(최종검수)", "(쪽맞춤)", "(서식복사)")


def _v_strip_suffix(spec):
    return dict(to=_str(spec, "to", max_len=40))


def _a_strip_suffix(state, opt, ctx):
    stem = state[0]
    for suffix in RESULT_SUFFIXES:
        stem = stem.replace(suffix, opt["to"])
    return stem.strip(), state[1]


RULE_KINDS = {
    "replace": (_v_replace, _a_replace),
    "add": (_v_add, _a_add),
    "clear": (_v_none, _a_clear),
    "del_pos": (_v_del_pos, _a_del_pos),
    "del_between": (_v_del_between, _a_del_between),
    "digits_keep": (_v_none, _a_digits_keep),
    "digits_delete": (_v_none, _a_digits_delete),
    "digits_pad": (_v_digits_pad, _a_digits_pad),
    "number": (_v_number, _a_number),
    "number_shift": (_v_number_shift, _a_number_shift),
    "ext_del": (_v_none, _a_ext_del),
    "ext_add": (_v_ext, _a_ext_add),
    "ext_replace": (_v_ext, _a_ext_replace),
    "ext_case": (_v_ext_case, _a_ext_case),
    "date": (_v_date, _a_date),
    "cleanup": (_v_cleanup, _a_cleanup),
    "case": (_v_case, _a_case),
    "strip_result_suffix": (_v_strip_suffix, _a_strip_suffix),
}
MAX_RULES = 50


def validate_rules(rules):
    """규칙 목록을 검사해 정규화한 목록을 돌려준다. enabled=False 규칙은 빼고 돌려준다."""
    if not isinstance(rules, list) or len(rules) > MAX_RULES:
        raise RuleError(f"규칙은 {MAX_RULES}개까지 목록으로 주세요.")
    normalized = []
    for index, spec in enumerate(rules, 1):
        if not isinstance(spec, dict) or spec.get("kind") not in RULE_KINDS:
            raise RuleError(f"{index}번 규칙의 종류를 확인해 주세요.")
        if spec.get("enabled", True) is False:
            continue
        try:
            options = RULE_KINDS[spec["kind"]][0](spec)
        except RuleError as error:
            raise RuleError(f"{index}번 규칙: {error}") from None
        normalized.append(dict(kind=spec["kind"], **options))
    return normalized


def apply_rules(entries, rules, *, today=None, exif_reader=None):
    """항목마다 (새 이름 또는 None, 오류 문자열 또는 None, 경고 집합)을 목록 순서대로 돌려준다.

    번호 규칙의 순서는 주어진 entries 순서(=화면 목록 순서)를 따른다.
    """
    rules = validate_rules(rules)
    numbers = {i: number_sequence(entries, start=r["start"], step=r["step"], per_folder=r["per_folder"])
               for i, r in enumerate(rules) if r["kind"] == "number"}
    results = []
    for position, entry in enumerate(entries):
        state = (entry.stem, entry.ext)
        ctx = dict(entry=entry, today=today, exif_reader=exif_reader, warnings=set())
        try:
            for index, rule in enumerate(rules):
                if index in numbers:
                    ctx["number"] = numbers[index][position]
                state = RULE_KINDS[rule["kind"]][1](state, rule, ctx)
        except RuleError as error:
            results.append((None, str(error), ctx["warnings"]))
            continue
        results.append((state[0] + state[1], None, ctx["warnings"]))
    return results
