#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from decimal import Decimal
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_COMPANIES_FILE = PROJECT_ROOT / "data" / "dcard" / "exclude_companies.txt"
EXCLUDED_TITLES_FILE = PROJECT_ROOT / "data" / "dcard" / "exclude_titles.txt"
COMPANY_CLASSIFICATION_FILE = PROJECT_ROOT / "company_industry_classification.csv"


TARGET_COLUMNS = [
    "Created_date",
    "company",
    "company_category",
    "tittle",
    "year_of_experience",
    "Seniority",
    "monthly_wage",
    "bonus",
    "total",
]

LEGACY_TARGET_COLUMNS = [
    "Created_date",
    "company",
    "tittle",
    "year_of_experience",
    "Seniority",
    "monthly_wage",
    "bonus",
    "total",
    "work_hour",
    "work_over_time",
]

LEGACY_LEVEL_TARGET_COLUMNS = [
    "Created_date",
    "company",
    "tittle",
    "level",
    "year_of_experience",
    "Seniority",
    "monthly_wage",
    "bonus",
    "total",
    "work_hour",
    "work_over_time",
]


EMPTY_MARKERS = {
    "",
    "nan",
    "none",
    "null",
    "無",
    "未知",
    "不清楚",
    "不知道",
    "保密",
    "測試",
    "x",
    "X",
    "?",
}

DEFAULT_EXCLUDED_COMPANIES: set[str] = set()

DEFAULT_EXCLUDED_TITLES: set[str] = set()


def load_exclusion_terms(file_path: Path, defaults: set[str]) -> set[str]:
    excluded = set(defaults)
    if not file_path.exists():
        return excluded

    for line in file_path.read_text(encoding="utf-8").splitlines():
        text = " ".join(line.replace("\u3000", " ").split()).strip()
        text = text.replace("（", "(").replace("）", ")")
        text = text.replace("／", "/").replace("、", " ")
        text = text.replace("/", " ")
        text = text.replace("，", " ").replace(",", " ")
        text = text.replace("+", " ").replace("&", " ")
        text = text.replace("|", " ").replace("-", " ")
        text = re.sub(r"[()\[\]{}:：]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or text.startswith("#"):
            continue
        excluded.add(re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", text).lower())
    return excluded


EXCLUDED_COMPANIES = load_exclusion_terms(EXCLUDED_COMPANIES_FILE, DEFAULT_EXCLUDED_COMPANIES)
EXCLUDED_TITLES = load_exclusion_terms(EXCLUDED_TITLES_FILE, DEFAULT_EXCLUDED_TITLES)


def load_company_classifications(file_path: Path) -> dict[str, str]:
    if not file_path.exists():
        return {}

    classifications: dict[str, str] = {}
    with file_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = row.get("company", "").strip()
            category = row.get("category", "").strip()
            if not company or not category:
                continue
            normalized = normalize_company_text(company)
            classifications[normalized.lower()] = category
    return classifications


COMPANY_ALIASES = {
    # major global company aliases
    "亞馬遜": "amazon",
    "amazon": "amazon",
    "谷歌": "google",
    "GOOGLE": "google",
    "Google": "google",
    "Google Taiwan": "google",
    "google 約聘": "google",
    "微軟": "Microsoft",
    "微軟AI RD": "Microsoft",
    "微軟AIR D": "Microsoft",
    "microsoft": "Microsoft",
    "Microsoft": "Microsoft",
    "IBM": "IBM",
    "ibm": "IBM",
    "unisys": "Unisys",
    "Unisys": "Unisys",
    "Intel": "Intel",
    "Nvidia": "Nvidia",
    "ASML": "ASML",
    "SAP": "SAP",
    "y!": "Yahoo奇摩",
    "yahoo": "Yahoo奇摩",
    "Yahoo": "Yahoo奇摩",

    # local / dataset-specific aliases
    "91App": "91APP",
    "appier": "Appier",
    "KKCOMPANY": "KKCompany",
    "TXONE": "TXOne",
    "txone network": "TXOne",
    "TxONE Networks": "TXOne",
    "NetSkope": "Netskope",
    "Trendmicro": "Trend Micro",
    "TrendMicro趨勢科技": "Trend Micro",
    "趨勢": "Trend Micro",
    "趨勢科技": "Trend Micro",
    "訊連": "CyberLink",
    "訊連科技": "CyberLink",
    "訊連Cyberlink": "CyberLink",
    "Cyberlink": "CyberLink",
    "Line Tv": "LINE TV",
    "Linetv": "LINE TV",
    "Pchome": "PChome",
    "PChome": "PChome",
    "Gogoro": "Gogoro",
    "gogoro": "Gogoro",
    "ASUS": "ASUS",
    "asus": "ASUS",
    "華碩": "ASUS",
    "華碩電腦": "ASUS",
    "Viewsonic": "ViewSonic",
    "ViewSonic": "ViewSonic",
    "Msi": "MSI",
    "群暉": "Synology",
    "Synopsys 新思": "Synopsys",
    "新思科技 Synopsys": "Synopsys",
    "Synopsys": "Synopsys",
    "QNAP": "QNAP",
    "進金生實業 國際": "進金生國際",
    "麗得": "麗得資訊顧問",
    "科萊博瑞": "科萊博瑞科技",
    "天瀚國際": "天瀚國際科技",
    "叡揚": "叡揚資訊",
    "睿揚資訊": "叡揚資訊",
    "精誠": "精誠資訊",
    "昕力": "昕力資訊",
    "偉康科技": "偉康科技股份有限公司",
    "遠傳": "遠傳電信",
    "玉山": "玉山銀行",
    "國泰": "國泰世華銀行",
    "三竹": "三竹資訊",
    "奧義智慧": "奧義智慧科技",
    "奧義智慧科技股份有限公司": "奧義智慧科技",
    "宇泰華 PalUp playsee": "宇泰華科技",
    "宇泰華科技 Palup": "宇泰華科技",
    "Palup Playsee": "宇泰華科技",
    "Palup. Playsee": "宇泰華科技",
    "Playsee Palup": "宇泰華科技",
    "沛星": "Appier",
    "佩星": "Appier",
}


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\u3000", " ").split()).strip()


def normalize_company_text(value: str) -> str:
    text = normalize_text(value)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("／", "/").replace("、", " ")
    text = text.replace("/", " ")
    text = text.replace("，", " ").replace(",", " ")
    text = text.replace("+", " ").replace("&", " ")
    text = text.replace("|", " ").replace("-", " ")
    text = re.sub(r"[()\[\]{}:：]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


COMPANY_CLASSIFICATIONS = load_company_classifications(COMPANY_CLASSIFICATION_FILE)


def should_exclude_company(value: str) -> bool:
    text = normalize_company_text(value)
    if not text:
        return True
    compact = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", text).lower()
    return compact in EXCLUDED_COMPANIES


def should_exclude_title(value: str) -> bool:
    text = normalize_title_text(value)
    if not text:
        return True
    compact = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", text).lower()
    return compact in EXCLUDED_TITLES


def normalize_title_text(value: str) -> str:
    text = normalize_text(value)
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("／", "/").replace("、", " ")
    text = text.replace("，", " ").replace(",", " ")
    text = text.replace("+", " ").replace("&", " ")
    text = text.replace("|", " ").replace("-", " ")
    text = re.sub(r"[()\[\]{}:：]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_title(value: str) -> str:
    text = normalize_title_text(value)
    if not text or text.lower() in EMPTY_MARKERS:
        return ""

    lower = text.lower()
    compact = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", lower)

    def has_zh(*parts: str) -> bool:
        return any(part in compact for part in parts)

    def has_en(*parts: str) -> bool:
        return any(re.search(rf"(?<![a-z]){re.escape(part)}(?![a-z])", lower) for part in parts)

    if has_zh("系統整合"):
        return "system engineer"

    if has_zh("專案經理") or has_en("technical program manager", "project manager"):
        return "project manager"

    if has_zh("技術處長"):
        return "engineering manager"

    if has_en("product manager", "product owner", "pm") or has_zh("產品經理", "產品規劃", "產品", "sw產品經理", "產品部研發工程師"):
        return "product manager"
    if has_zh("專案人員pm", "專案工程師"):
        return "project manager"

    if has_en("frontend", "front end", "web developer") or has_zh("前端", "angular前端", "網頁"):
        return "frontend engineer"
    if has_en("backend", "back end", "be") or has_zh("後端", "java後端", "後端程式設計", "後端軟體工程師"):
        return "backend engineer"
    if has_en("full stack", "fullstack") or has_zh("全端"):
        return "fullstack engineer"

    if has_en("ios", "android", "flutter", "mobile") or has_zh("ios", "app工程師"):
        return "mobile engineer"

    if has_en("data engineer") or has_zh("資料工程師", "數據工程師"):
        return "data engineer"
    if has_en("data scientist", "data science") or has_zh("資料科學家"):
        return "data scientist"
    if has_en("data analyst") or has_zh("資料分析師") or re.fullmatch(r"da", compact):
        return "analyst"
    if has_zh("高級研究員", "研究院", "研究員", "研究所") or has_en("senior researcher"):
        return "researcher"
    if has_en("ai engineer") or has_zh("ai工程師", "ai影像辨識", "ai演算法", "ai rd"):
        return "ai engineer"
    if re.fullmatch(r"ai", compact):
        return "ai engineer"
    if has_en("machine learning engineer", "ml engineer", "machine learning") or re.fullmatch(r"ml", compact) or has_zh("演算法工程師", "機器學習"):
        return "machine learning engineer"

    if has_en("devops", "sre"):
        return "devops engineer"
    if has_en("security", "soc") or has_zh("資安"):
        return "security engineer"

    if has_en("architect", "solutions architect") or has_zh("架構師"):
        return "architect"
    if has_en("engineering manager"):
        return "engineering manager"
    if has_en("senior account executive") or re.fullmatch(r"ae", compact):
        return "account executive"
    if has_en("account manager") or re.fullmatch(r"am", compact):
        return "account manager"
    if has_en("operations") or re.fullmatch(r"ops", compact):
        return "operations"
    if has_en("application engineer"):
        return "application engineer"
    if has_en("product engineer") or re.fullmatch(r"pe", compact):
        return "product engineer"
    if has_en("software developer") or re.fullmatch(r"sd", compact):
        return "software engineer"
    if re.fullmatch(r"senior", compact):
        return "software engineer"

    if has_en("system analyst") or has_zh("系統分析"):
        return "system analyst"
    if re.fullmatch(r"sa", compact) or has_en("sa") and not has_en("software", "system", "sales"):
        return "analyst"

    if has_en("server engineer", "cloud engineer", "cloud support engineer") or has_zh("系統工程", "資訊工程", "系統開發", "資訊系統", "hpo系統", "cim工程師"):
        return "system engineer"

    if has_en("software", "software engineer", "software developer", "swe", "sde", "pg", "ai", "tech lead", "net", "dotnet") or has_zh("軟體", "程式", "研發", "軟工", "軟功", "app工程師", "資深開發", "資深工", "工", "rd", "pg", ".net", ".NET"):
        return "software engineer"

    if has_en("qa", "automation", "test") or has_zh("測試"):
        return "qa engineer"
    if has_en("designer") or has_zh("設計師", "產品設計"):
        return "designer"
    if has_en("consultant") or has_zh("顧問"):
        return "consultant"
    if has_en("analyst") or has_zh("分析師"):
        return "analyst"
    if has_en("manager"):
        return "manager"

    if has_en("engineer", "developer", "eng", "sw") or has_zh("工程師", "工程", "高級工程師", "資深工程師", "駐點工程師", "萬能工程師", "副工程師", "網頁工程師", "前端工程", "後段工程師", "後端工程師"):
        return "software engineer"
    if has_zh("產品"):
        return "product manager"

    return text


def classify_company(value: str) -> str:
    text = normalize_company_text(value)
    if not text or text.lower() in EMPTY_MARKERS:
        return "other"

    classified = COMPANY_CLASSIFICATIONS.get(text.lower())
    if classified:
        return classified

    lower = text.lower()
    compact = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", lower)

    def has_zh(*parts: str) -> bool:
        return any(part in compact for part in parts)

    def has_en(*parts: str) -> bool:
        return any(re.search(rf"(?<![a-z]){re.escape(part)}(?![a-z])", lower) for part in parts)

    if has_zh("新創") or has_en("startup"):
        return "startup"

    if has_en("trend micro", "txone", "teamt5", "appier", "91app", "kkcompany", "shopline", "pinkoi", "gogox", "playsee", "tradebeyond", "fazz", "google", "microsoft", "ibm", "amazon", "yahoo", "17live", "cyberlink", "line tv", "biggo", "ubitus", "crescendo lab") or has_zh("微軟", "沛星", "愛酷智能", "宇泰華", "奧創物聯", "創星物聯", "亞馬遜", "奇摩"):
        if has_en("trend micro", "txone", "teamt5") or has_zh("趨勢", "資安", "奧義", "中華資安"):
            return "cybersecurity"
        if has_en("gogox"):
            return "transport_logistics"
        if has_en("shopline", "pinkoi"):
            return "ecommerce_retail"
        if has_en("17live"):
            return "gaming_entertainment"
        return "software_internet"

    if has_zh("趨勢", "資安", "奧義", "中華資安", "網安") or has_en("trend micro", "txone", "teamt5", "netskope"):
        return "cybersecurity"

    if has_en("crypto.com", "blockchain", "web3", "nft", "crypto") or has_zh("區塊鏈", "加密貨幣", "虛擬貨幣", "庫幣"):
        return "blockchain_crypto"
    if has_en("nogle"):
        return "blockchain_crypto"
    if has_zh("進金生國際", "進金生"):
        return "semiconductor_electronics"
    if has_zh("天瀚國際科技", "天瀚國際"):
        return "gaming_entertainment"

    if has_en("kkday", "fontrip") or has_zh("旅遊", "旅行社", "旅遊網", "旅遊體驗", "旅遊電商", "旅遊平台", "可樂旅行社"):
        return "travel_tourism"

    if has_en("foodpanda", "delivery hero") or has_zh("外送", "外賣", "快商務", "快送", "熊貓", "達達"):
        return "delivery_platform"

    if has_en("digitimes", "line tv", "linetv", "fubon media") or has_zh("媒體", "新聞", "電子時報", "富邦媒體"):
        return "media_publishing"

    if has_en("amazingtalker") or has_zh("線上家教", "線上英文", "語言學習", "教育平台"):
        return "edtech"

    if has_zh("銀行", "金控", "證券", "金融", "票券", "保險", "財經", "支付", "交易所") or has_en("bank", "finance", "fintech", "crypto"):
        return "financial"
    if has_zh("國泰", "中租", "悠遊卡", "裕融", "全盈", "口袋證券", "阿爾發", "普匯", "庫幣", "諦諾智金", "富邦", "玉山", "陽信", "台新", "永豐", "新光", "中信", "台中商業銀行", "商銀", "券商"):
        return "financial"

    if has_zh("電信") or has_en("telecom") or has_zh("大哥大", "種花") or compact in {"中華電信", "遠傳", "台灣大哥大"}:
        return "telecom"

    if has_zh("工研院", "國立陽明交通大學", "陽明交通大學", "國研院", "陽明"):
        return "government_research"

    if has_zh("生醫", "醫療", "醫藥", "醫院", "醫材", "診所") or has_en("biotech"):
        return "healthcare_biotech"

    if has_zh("博弈", "博奕", "菠菜", "波菜") or has_en("gambling", "casino", "betting"):
        return "gambling"

    if has_zh("遊戲", "娛樂") or has_en("game", "gaming") or compact in {"igs", "17live", "橘子子公司"}:
        return "gaming_entertainment"

    if has_zh("物流", "運輸", "外送", "車隊", "海運") or has_en("gogox"):
        return "transport_logistics"

    if has_zh("電商", "購物") or has_en("shopline", "pinkoi") or compact in {"東森購物"}:
        return "ecommerce_retail"
    if has_en("pchome", "momo", "payeasy") or has_zh("網家", "富邦媒體", "momo", "拍錢包", "購物網", "電商平台"):
        return "ecommerce_retail"

    if has_en("tsmc", "micron", "synopsys", "qnap", "synology", "viewsonic", "asus", "wiwynn", "mediatek", "lenovo", "commscope", "draytek", "gogoro", "siemens", "rivian", "msi", "inventec", "apple") or has_zh("半導體", "晶圓", "聯發科", "群暉", "華碩", "友達", "顯示器", "鴻海", "光寶", "敦泰", "研華", "科盛", "奇偶", "台塑", "電子", "電腦", "大同世界", "英業達", "富智捷", "西門子"):
        return "semiconductor_electronics"
    if has_zh("和碩", "皮卡"):
        return "semiconductor_electronics"

    if has_zh("麗得資訊顧問", "科萊博瑞科技", "透視數據", "資訊", "軟體", "系統", "科技", "數位", "電腦", "網路", "雲", "顧問", "整合") or has_en("appier", "91app", "kkcompany", "tradebeyond", "fazz", "nextlink", "systex", "systek", "microsoft", "google", "ibm", "amazon", "line tv", "biggo", "ubitus", "crescendo lab", "cyberlink", "微軟", "hcl", "unisys", "servicenow", "shoalter"):
        return "it_services"
    if has_zh("昕力", "精誠", "叡揚", "資拓", "普鴻", "鼎新", "神通", "宏益", "瑞嘉", "德義", "德魏", "使丹達", "明瑞資通", "一騰資訊", "凌群", "凌網", "嘉因", "訊力", "數揚", "商智", "長川", "北祥", "博彦", "友達數位", "台灣智慧技術研發", "騰雲", "酷必", "歐揚", "植根", "東捷", "亦思", "翰林", "柏格", "偉康", "一零四", "104 科技", "104科技", "台塑網", "資拓宏宇", "台灣實服科技", "三竹", "向上國際", "今網智慧", "台灣的軟體公司", "某新竹做系統科技公司", "GCP代理大廠", "HCL", "Unisys", "ServiceNow", "Shoalter", "Nogle", "天瀚國際科技"):
        return "it_services"

    if has_zh("傳產", "製造", "台灣塑膠工業") or has_en("manufacturing"):
        return "manufacturing_industrial"

    return "other"


def normalize_company_name(value: str) -> str:
    text = normalize_company_text(value)
    return COMPANY_ALIASES.get(text.lower(), COMPANY_ALIASES.get(text, text))


def format_number(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def add_money_values(left: str, right: str) -> str:
    return format_number(Decimal(left) + Decimal(right))


def compute_annual_total(monthly_wage: str, bonus: str) -> str:
    bonus_value = Decimal(bonus) if bonus else Decimal("0")
    return format_number(Decimal(monthly_wage) * (Decimal("12") + bonus_value))


def parse_tw_datetime(value: str) -> str:
    text = normalize_text(value)
    match = re.fullmatch(
        r"(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2}) "
        r"(?P<ampm>上午|下午) (?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})",
        text,
    )
    if not match:
        return text

    hour = int(match.group("hour"))
    ampm = match.group("ampm")
    if ampm == "下午" and hour != 12:
        hour += 12
    if ampm == "上午" and hour == 12:
        hour = 0

    return (
        f"{int(match.group('year')):04d}-"
        f"{int(match.group('month')):02d}-"
        f"{int(match.group('day')):02d} "
        f"{hour:02d}:{int(match.group('minute')):02d}:{int(match.group('second')):02d}"
    )


def strip_notes(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"[（(].*?[）)]", "", text)
    return text.strip()


def parse_single_number(value: str, *, divide_k: bool = False) -> str | None:
    text = normalize_text(value)
    if not text:
        return None

    text = strip_notes(text)
    text = text.replace("約", "").replace("大約", "").replace("大概", "")
    text = text.replace("左右", "").replace("上下", "").replace("多", "")
    text = text.replace(" ", "")

    match = re.fullmatch(r"(?P<num>\d+(?:\.\d+)?)(?P<unit>[kKwW萬]?)", text)
    if match:
        number = Decimal(match.group("num"))
        unit = match.group("unit")
        if unit in {"k", "K"} and divide_k:
            number = number / Decimal("10")
        elif unit in {"w", "W"}:
            pass
        elif unit == "萬":
            pass
        elif unit == "" and divide_k and number >= 1000:
            number = number / Decimal("10000")
        return format_number(number)

    match = re.match(r"^(?P<num>\d+(?:\.\d+)?)", text)
    if match:
        number = Decimal(match.group("num"))
        remainder = text[match.end() :]
        if divide_k and remainder[:1] in {"k", "K"}:
            number = number / Decimal("10")
        elif divide_k and number >= 1000:
            number = number / Decimal("10000")
        return format_number(number)

    return None


def parse_range(value: str, *, divide_k: bool = False) -> str | None:
    text = strip_notes(value)
    text = text.replace("約", "").replace("大約", "").replace("大概", "")
    text = text.replace("左右", "").replace("上下", "").replace("多", "")
    text = text.replace(" ", "")
    for separator in ("~", "～", "-"):
        if separator in text:
            left, right = text.split(separator, 1)
            left_number = parse_single_number(left, divide_k=divide_k)
            right_number = parse_single_number(right, divide_k=divide_k)
            if left_number is None or right_number is None:
                return None
            midpoint = (Decimal(left_number) + Decimal(right_number)) / Decimal("2")
            return format_number(midpoint)
    return None


def parse_formula(value: str, *, divide_k: bool = False) -> str | None:
    text = strip_notes(value)
    text = text.replace("約", "").replace("大約", "").replace("大概", "")
    text = text.replace(" ", "")
    match = re.fullmatch(r"(?P<left>\d+(?:\.\d+)?)(?P<unit>[kKwW萬]?)[*×](?P<right>\d+(?:\.\d+)?)", text)
    if not match:
        return None
    left = Decimal(match.group("left"))
    right = Decimal(match.group("right"))
    unit = match.group("unit")
    if unit in {"k", "K"} and divide_k:
        left = left / Decimal("10")
    elif unit == "" and divide_k and left >= 1000:
        left = left / Decimal("10000")
    return format_number(left * right)


def parse_money(value: str) -> str:
    text = normalize_text(value)
    if not text or text.lower() in EMPTY_MARKERS:
        return ""

    if text in {"無", "none", "None", "不高", "不一定"}:
        return ""

    formula = parse_formula(text, divide_k=True)
    if formula is not None:
        return formula

    ranged = parse_range(text, divide_k=True)
    if ranged is not None:
        return ranged

    parsed = parse_single_number(text, divide_k=True)
    if parsed is not None:
        return parsed

    if text.lower().endswith("k"):
        parsed = parse_single_number(text[:-1], divide_k=True)
        if parsed is not None:
            return parsed

    return ""


def parse_bonus(value: str) -> str:
    text = normalize_text(value)
    if not text or text.lower() in EMPTY_MARKERS:
        return ""

    if any(marker in text for marker in ("無", "none", "沒有", "沒", "不一定", "不發", "拿不到", "0獎金")):
        if re.search(r"\d", text) is None:
            return "0"

    if re.fullmatch(r"\d+(?:\.\d+)?\+\d+(?:\.\d+)?(?:[()（）].*)?", text):
        left, right = text.split("+", 1)
        left_number = parse_single_number(left)
        right_number = parse_single_number(right)
        if left_number is not None and right_number is not None:
            return format_number(Decimal(left_number) + Decimal(right_number))

    ranged = parse_range(text)
    if ranged is not None:
        return ranged

    parsed = parse_single_number(text)
    if parsed is not None:
        return parsed

    if "個月" in text:
        match = re.search(r"\d+(?:\.\d+)?", text)
        if match:
            return match.group(0)

    return ""


def parse_experience(value: str) -> str:
    text = normalize_text(value)
    if not text or text.lower() in EMPTY_MARKERS:
        return ""

    text = text.replace("年半", ".5年")
    text = text.replace("一年半", "1.5年")
    text = text.replace("兩年半", "2.5年")
    text = text.replace("未滿一年", "0.5年")
    text = text.replace("不滿一年", "0.5年")
    text = text.replace("不到一年", "0.5年")
    text = text.replace("<1", "0.5")
    text = text.replace("new grad", "0")
    text = text.replace("New grad", "0")
    text = text.replace("N/A", "")

    if text in {"0", "0年", "0Y", "0y"}:
        return "0"

    ranged = parse_range(text)
    if ranged is not None:
        return ranged

    text = text.replace("年", "").replace("Y", "").replace("y", "")
    text = text.replace("+", "")

    parsed = parse_single_number(text)
    if parsed is not None:
        return parsed

    return ""


def clean_row(row: list[str], *, header_kind: str) -> list[str]:
    if header_kind == "legacy_level":
        row = list(row) + [""] * (len(LEGACY_LEVEL_TARGET_COLUMNS) - len(row))
        field_indexes = {
            "created_date": 0,
            "company": 1,
            "tittle": 2,
            "year_of_experience": 4,
            "seniority": 5,
            "monthly_wage": 6,
            "bonus": 7,
            "total": 8,
        }
    elif header_kind == "legacy_work":
        row = list(row) + [""] * (len(LEGACY_TARGET_COLUMNS) - len(row))
        field_indexes = {
            "created_date": 0,
            "company": 1,
            "tittle": 2,
            "year_of_experience": 3,
            "seniority": 4,
            "monthly_wage": 5,
            "bonus": 6,
            "total": 7,
        }
    else:
        row = list(row) + [""] * (len(TARGET_COLUMNS) - len(row))
        field_indexes = {
            "created_date": 0,
            "company": 1,
            "tittle": 3,
            "year_of_experience": 4,
            "seniority": 5,
            "monthly_wage": 6,
            "bonus": 7,
            "total": 8,
        }

    created_date = parse_tw_datetime(row[field_indexes["created_date"]])
    company = normalize_company_name(row[field_indexes["company"]])
    if should_exclude_company(company):
        return []
    company_category = classify_company(company)
    if company_category == "other":
        return []
    tittle = normalize_title(row[field_indexes["tittle"]])
    if should_exclude_title(tittle):
        return []
    year_of_experience = parse_experience(row[field_indexes["year_of_experience"]])
    seniority = parse_experience(row[field_indexes["seniority"]])
    for experience_value in (year_of_experience, seniority):
        if not experience_value:
            continue
        try:
            if Decimal(experience_value) > Decimal("30"):
                return []
        except Exception:
            pass
    monthly_wage = parse_money(row[field_indexes["monthly_wage"]])
    if not monthly_wage:
        return []
    try:
        if Decimal(monthly_wage) > Decimal("100"):
            return []
    except Exception:
        pass
    bonus = parse_bonus(row[field_indexes["bonus"]])
    if bonus:
        try:
            if Decimal(bonus) > Decimal("40"):
                return []
        except Exception:
            pass
    total = compute_annual_total(monthly_wage, bonus)
    if Decimal(total) > Decimal("1000"):
        return []

    return [
        created_date,
        company,
        company_category,
        tittle,
        year_of_experience,
        seniority,
        monthly_wage,
        bonus,
        total,
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.reader(input_file)
        header = next(reader)
        if header == TARGET_COLUMNS:
            header_kind = "current"
        elif header == LEGACY_TARGET_COLUMNS:
            header_kind = "legacy_work"
        elif header == LEGACY_LEVEL_TARGET_COLUMNS:
            header_kind = "legacy_level"
        else:
            raise RuntimeError(f"Unexpected header: {header}")
        cleaned_rows = [clean_row(row, header_kind=header_kind) for row in reader]
        cleaned_rows = [row for row in cleaned_rows if row]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(TARGET_COLUMNS)
        writer.writerows(cleaned_rows)

    print(f"Wrote {len(cleaned_rows)} cleaned rows to {args.output}")


if __name__ == "__main__":
    main()
