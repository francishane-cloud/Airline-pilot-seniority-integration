# ======================================================================
# Pilot Seniority Integration Tool  (run with:  streamlit run SeniorityIntegrator.py)
# Sections: 1 setup/constants | 2 sample data | 3 parsing & counting | 4 analysis (Create_ functions)
#           5 report helpers & charts | 6 export (CSV/PDF) | 7 report page | 8 main page
# ======================================================================
import base64  # encode/decode binary data (downloads and the embedded sample files)
import colorsys  # convert colours between RGB and HLS when shading
import hashlib  # hash the export password so it is not stored as plain text
import html  # escape text before it is placed inside HTML
import io  # in-memory file buffers (BytesIO)
import json  # build the JSON handed to the browser download script
import math  # sqrt and ceil for the dot-chart grid size
import uuid  # unique ids for report links
import zlib  # decompress the embedded sample CSV files
from datetime import datetime  # current date and time

import matplotlib  # plotting library

matplotlib.use("Agg")  # draw to image buffers only (no desktop window)
import matplotlib.pyplot as plt  # pyplot interface for figures and axes
import numpy as np  # numeric arrays (dot-chart colour grid)
import pandas as pd  # tables (DataFrames) used for every seniority list
import streamlit as st  # the web-app framework
import streamlit.components.v1 as components  # fallback HTML runner for older Streamlit versions
from matplotlib.backends.backend_pdf import PdfPages  # write multi-page PDF files
from matplotlib.patches import Patch, Rectangle  # legend swatches and row-background rectangles
from matplotlib.ticker import FuncFormatter, MaxNLocator, MultipleLocator  # axis tick formatting helpers

st.set_page_config(page_title="Pilot Seniority List Integration Tool", layout="wide")  # must be the first Streamlit call; wide page

# ----------------------------------------------------------------------
# Page-wide styling (tight spacing, prominent buttons, report tables)
# ----------------------------------------------------------------------
st.markdown(  # inject one <style> block into the page
    """
    <style>
    .block-container { padding-top: 1.6rem; padding-bottom: 1rem; }
    h1 { padding: 0 0 0.1rem 0; }
    h2, h3 { padding: 0.2rem 0 0.1rem 0; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem; }
    hr { margin: 0.4rem 0 !important; }
    [data-testid="stCaptionContainer"] { margin: 0; line-height: 1.2; }
    [data-testid="stWidgetLabel"] { min-height: 0; margin-bottom: 0.1rem; }
    div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { min-height: 2.1rem; }
    div[data-baseweb="input"] input { padding-top: 0.2rem; padding-bottom: 0.2rem; }
    [data-testid="stFileUploaderDropzone"] { padding: 0.35rem 0.6rem; }
    [data-testid="stFileUploaderDropzoneInstructions"] small { display: none; }
    div.stButton > button { padding: 0.4rem 1rem; border-width: 2px; }
    div.stButton > button p { font-size: 1.2rem; font-weight: 800; letter-spacing: 0.04em; }
    [class*="st-key-info_"] button {
        border: none !important; background: transparent !important; box-shadow: none !important;
        padding: 0 0.3rem !important; min-height: 1.6rem !important; height: 1.6rem !important;
    }
    [class*="st-key-info_"] button p { font-size: 1.25rem !important; font-weight: 700 !important; color: #1c83e1 !important; }
    [class*="st-key-info_"] button [data-testid="stIconMaterial"],
    [class*="st-key-colorpop_"] button [data-testid="stIconMaterial"] { display: none; }
    [class*="st-key-rm_sample_"] button { padding: 0 0.3rem !important; min-height: 1.5rem !important; height: 1.5rem !important; }
    [class*="st-key-rm_sample_"] button p { font-size: 0.9rem !important; font-weight: 700 !important; letter-spacing: 0 !important; }
    [class*="st-key-cat_"] [data-testid="stTextInputRootElement"], [class*="st-key-cat_"] [data-baseweb="input"],
    [class*="st-key-cat_"] [data-baseweb="base-input"], [class*="st-key-cat_"] input { min-height: 1.5rem !important; height: 1.5rem !important; }
    [class*="st-key-cat_"] input { padding: 0 0.4rem !important; font-size: 0.85rem; line-height: 1.5rem; }
    [class*="st-key-cat_"] { margin-bottom: -0.3rem; }
    .catchip { height: 1.5rem; line-height: 1.5rem; text-align: center; border-radius: 4px; font-weight: 700;
               font-size: 1.05rem; overflow: hidden; white-space: nowrap; }
    table.cnt { border-collapse: collapse; font-size: 0.9rem; margin-bottom: 0.4rem; color: #111111; }
    table.cnt th, table.cnt td { padding: 3px 10px; text-align: right; border-bottom: 1px solid rgba(0,0,0,0.18); }
    table.cnt th:first-child, table.cnt td:first-child { text-align: left; }
    table.cnt td.tot { font-weight: 700; border: 1px solid rgba(0,0,0,0.45); }
    table.cnt tr.sumrow td { font-weight: 700; border-top: 2px solid rgba(0,0,0,0.45); }
    table.cnt td.note { text-align: right; font-size: 0.75rem; font-style: italic; border-bottom: none; }
    table.cnt td.bad { color: #c2255c; }
    table.cnt td.good { color: #2b8a3e; }
    table.rpt { border-collapse: collapse; font-size: 0.85rem; color: #111111; }
    table.rpt th, table.rpt td { padding: 1px 10px; text-align: center; border: 1px solid rgba(0,0,0,0.3); line-height: 1.25; }
    table.rpt th { font-weight: 700; font-size: 0.95rem; padding: 7px 10px; }
    div.ipslwrap { max-height: 600px; overflow: auto; display: inline-block; }
    table.ipsl { border-collapse: collapse; font-size: 0.8rem; color: #111111; }
    table.ipsl th { position: sticky; top: 0; background: #dee2e6; font-weight: 700; padding: 2px 9px;
                    text-align: center; border-bottom: 1px solid #868e96; }
    table.ipsl td { padding: 0 9px; line-height: 1.25; text-align: center; white-space: nowrap; }
    </style>
    """,  # (CSS above: spacing, buttons, info symbols, category boxes, count/report/IPSL tables)
    unsafe_allow_html=True,  # allow the raw <style> tag
)  # end of the CSS injection


@st.cache_resource  # create once and share across every browser tab / rerun of this server process
def get_report_cache():  # returns the dictionary that holds finished reports
    return {}  # starts empty


REPORT_CACHE = get_report_cache()  # report_id -> report data; lets a second browser tab read the same results

EXPECTED_COLUMNS = [  # columns every uploaded seniority CSV must contain
    "SenNum",  # pilot's number on the airline's list (1 = most senior)
    "LastName",  # surname
    "FirstName",  # given name
    "Airline",  # 3-letter airline code (same on every row)
    "Rank",  # CA, FO or RP
    "Equip",  # 4-character equipment (aircraft) code
    "DOH",  # date of hire
    "DOB",  # date of birth
    "DaysInactive",  # days of furlough / inactivity
]  # end of EXPECTED_COLUMNS

RANK_COLUMNS = ["CA", "FO", "RP"]  # ranks shown as columns in the count tables

COLOR_CHOICES = {  # the 12 basic colours offered for each airline
    "Red": "#E03131",  # red
    "Orange": "#F76707",  # orange
    "Yellow": "#FCC419",  # yellow
    "Green": "#2F9E44",  # green
    "Teal": "#12B886",  # teal
    "Cyan": "#1098AD",  # cyan
    "Blue": "#4C6EF5",  # blue
    "Indigo": "#5F3DC4",  # indigo
    "Purple": "#9C36B5",  # purple
    "Pink": "#E64980",  # pink
    "Brown": "#8D5524",  # brown
    "Gray": "#868E96",  # gray
}  # end of COLOR_CHOICES

DEFAULT_AIRLINE_NAMES = {1: "Air Superior", 2: "Thunder Air"}  # names pre-filled when the program loads
DEFAULT_COLOR_NAMES = {1: "Red", 2: "Blue"}  # colours pre-selected when the program loads
DEFAULT_RETIREMENT_AGE = "65"  # pre-filled Normal Retirement Age (not used in calculations yet)

CONTACT_EMAIL = "francishane@gmail.com"  # licence / support contact address
CONTACT_SITE = "airlinepilotmerger.com"  # product website
VALID_PASSWORD_HASHES = {  # SHA-256 hashes of the accepted export passwords (plain text is not stored)
    "be13062f5fda605bfb561b37bcdf9e3b933199e63d67a1cc9a60203d3870970e",  # hash of the first password
    "f223bccd09b2dbe3f74e556d6147e964a013ea96404e3c90a9af88fcdf67ec3b",  # hash of the second password
    "fec43ea4a3ad5d2f6c401725ff13b0b0a082d80042eb2fe13be3213780888b6b",  # hash of the third password
}  # to add a password: python -c "import hashlib;print(hashlib.sha256(b'NEWPASSWORD').hexdigest())"

UPLOAD_INFO = """
**CSV format for each seniority list**

One row per pilot, **in seniority order** (the most senior pilot first). The first row must be a header with exactly these column names:

**The column header (Row 1) requires column titles EXACTLY as described. ie. SenNum, LastName, etc.**

| Column | Format | Example |
|---|---|---|
| SenNum | positive whole number (the pilot's number on the list, unique) | 1 |
| LastName | text | Smith |
| FirstName | text | Patrick |
| Airline | 3-letter code (the same for every row; different for each airline) | SUP |
| Rank | 2 letters: CA, FO or RP | CA |
| Equip | 4 characters | B737 |
| DOH | date of hire, **YYYY-MM-DD** | 2005-03-14 |
| DOB | date of birth, **YYYY-MM-DD** | 1978-06-01 |
| DaysInactive | whole number of days (0 if none) | 0 |

Example row: `1,Smith,Patrick,SUP,CA,B737,2005-03-14,1978-06-01,0`

The extra columns (NameID, DaysHired, DaysActive, RelSen) are calculated for you. Do not include them.

csv file must be in UTF-8. All cells must have appropriate values.
"""  # text shown in the (i) box beside "Upload Seniority Lists"

WEIGHT_INFO = (  # text shown in the (i) box beside the weighting slider
    "Most airline pilot mergers follow a hybrid integration formula. First a Longevity list is created based on "  # part 1
    "Date of Hire (including or excluding periods of furlough). Second a Status and Category List is created. "  # part 2
    "This list is a ratioed list based on the different categories. Typical categories are wide-body captains, "  # part 3
    "narrow-body captains, wide-body first officers, narrow-body first officers. The weighting creates a "  # part 4
    "seniority list that weights these two lists towards longevity or towards status and category."  # part 5
)  # end of WEIGHT_INFO

NOTICE_INFO = (  # text shown in the (i) box beside the Constructive Notice Date
    "The Constructive Notice Date is either the date the merger was announced, or the corporate transaction was "  # part 1
    "completed. All pilots hired after this date are placed at the bottom of the list by date of hire."  # part 2
)  # end of NOTICE_INFO

INACTIVE_INFO = (  # text shown in the (i) box beside "Exclude Inactive Periods"
    "Checking this box will create a Longevity list that is strictly date of hire and will exclude periods of "  # part 1
    "layoff, furlough, or inactivity."  # part 2
)  # end of INACTIVE_INFO

METHODOLOGY_INFO = """
### Historical Pilot Seniority List Integration Methodologies

**WestJet / Sunwing (2024)**

* Top 316 spots allotted to WestJet pilots. The #1 SWG pilot would have been #411 on the WJ list by DOH. WJA had 222 WB positions. 316 is halfway between the 222 widebody WJA positions and 411.
* Remaining pilots ratioed.
* Categories:
    1. WJA 316:0 SWG
    2. Remaining pilots
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.
* Arbitrator had full knowledge of management plans to re-size bases and potential position gains/losses. Bump & flush of most out of seniority (rank, base) positions. No position protection or reinstatement rights.

**First Air / Canadian North (2022)**

* Date of Hire, but Canadian North pilots given a 3-year bump to account for their superior category aircraft (more B737).
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.
* Ratioed captain upgrades.
* No bump/flush

**Alaska / Virgin (2016)**

* Hybrid, weighted 60% Longevity, 40% Status & Category.
* Categories:
    1. CA
    2. FO
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.
* No bump/flush All Virgin captain positions protected. Reinstatement rights for any pilot who loses position.

**American / US Airways (2013)**

* Hybrid, weighted 15% Longevity, 85% Status & Category.
* Categories:
    1. B777 / A330 CA
    2. B757 / B767 CA
    3. NB CA
    4. B777 / A330 FO
    5. B757 / B767 CA
    6. NB FO
    7. Turboprop pilots
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.
* Re-evaluation of US Air-America West merger.
* No bump/flush

**Pinnacle / Mesaba / Colgan (2011)**

* 100% Status & Category.
* Categories:
    1. CRJ900 CA
    2. DH8 & CRJ200 CA
    3. S340 CA
    4. CRJ900 / CRJ200 FO
    5. Remaining turboprop FO
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.
* No bump/flush

**United / Continental (2010)**

* Hybrid, weighted 35% Longevity, 65% Status & Category.
* Categories:
    1. WB CA
    2. B757 / B767 CA
    3. NB CA
    4. WB FO
    5. B767 / B757 FO
    6. NB FO
* No bump/flush

**Delta / Northwest (2009)**

* 100% Relative Seniority (single category; all pilots ratioed, no credit for longevity).
* No bump/flush

**Air Canada / Canadian Airlines (2000) (Keller)**

* 100% Status & Category.
* Categories:
    1. B747 CA
    2. WB CA
    3. NB CA
    4. B747 FO
    5. WB FO
    6. NB FO
    7. CRJ pilots
* No bump/flush
* Second award after original Mitchnik award overturned by the Canada Industrial Relations Board (Decision #183).

**US Airways / US Shuttle (1997)**

* 100% Status & Category.
* Categories:
    1. WB CA
    2. B727 CA
    3. FO
* Constructive Notice Pilots placed at the bottom of the list, sorted by DOH.

**FedEx / Flying Tiger (1990)**

* 100% Status & Category.
* Categories:
    1. WB CA
    2. NB CA & FOs who are projected to be captains within one year
    3. WB FO
    4. NB FO

**Pacific Western Airlines / Wardair (1989)**

* Date of Hire.
* No bump/flush. All Wardair captain positions protected.

**US Air / Piedmont (1989)**

* Date of Hire.

**Alaska / JetAmerica (1984)**

* Pre-JetAmerica Alaska pilots placed at the top of the list.
* Place the #1 JetAmerica pilot on the Alaska list and ratio the remaining pilots.

**Alaska / Hawaiian (TBD)**

* TBD.

**Allegiant / Sun Country (TBD)**

* TBD.

**Republic / Mesa (TBD)**

* TBD.
"""  # text shown in the (i) box beside "Define Integration Parameters"

PASSWORD_PROMPT = (  # text shown in the export password box
    f"Enter User license password. A user license allows export of data and individual career trajectory "  # part 1
    f"data. Contact {CONTACT_EMAIL}."  # part 2
)  # end of PASSWORD_PROMPT

PASSWORD_WRONG = f"Password incorrect. Contact {CONTACT_EMAIL} for user license."  # text shown after a wrong password

# ======================================================================
# 2. Sample data (pre-loaded when the program starts; the user can remove it and upload their own)
# ======================================================================
SAMPLE_CSV_B64_1 = "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"  # zlib-compressed, base64-encoded copy of SampleData-SUP.csv
SAMPLE_CSV_B64_2 = "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"  # zlib-compressed, base64-encoded copy of SampleData-THU.csv
SAMPLE_CSV_B64 = {1: SAMPLE_CSV_B64_1, 2: SAMPLE_CSV_B64_2}  # airline number -> embedded sample file
SAMPLE_FILE_NAMES = {1: "SampleData-SUP.csv", 2: "SampleData-THU.csv"}  # names shown for the samples


def sample_csv_buffer(n):  # returns the sample CSV for airline n as an in-memory file
    return io.BytesIO(zlib.decompress(base64.b64decode(SAMPLE_CSV_B64[n])))  # decode, decompress, wrap as a file object


# ======================================================================
# 3. Parsing and counting
# ======================================================================
def parse_seniority_list(uploaded_file):  # reads a seniority CSV and returns it with the calculated columns added
    df = pd.read_csv(uploaded_file)  # load the CSV into a table

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]  # required columns that are absent
    if missing:  # at least one column is absent
        raise ValueError(f"Missing expected column(s): {', '.join(missing)}")  # tell the user which ones

    df = df[EXPECTED_COLUMNS].copy()  # keep only the expected columns, in order

    df["SenNum"] = df["SenNum"].astype(int)  # whole numbers
    df["LastName"] = df["LastName"].astype(str)  # text
    df["FirstName"] = df["FirstName"].astype(str)  # text
    df["Airline"] = df["Airline"].astype(str).str.strip()  # text, without stray spaces
    df["Rank"] = df["Rank"].astype(str).str.strip()  # text, without stray spaces
    df["Equip"] = df["Equip"].astype(str).str.strip()  # text, without stray spaces
    df["DOH"] = pd.to_datetime(df["DOH"])  # date of hire as a real date
    df["DOB"] = pd.to_datetime(df["DOB"])  # date of birth as a real date
    df["DaysInactive"] = df["DaysInactive"].astype(int)  # whole days

    if df["Airline"].nunique() != 1:  # every row must carry the same airline code
        raise ValueError("The Airline column must contain the same code on every row.")  # reject mixed codes
    if df["SenNum"].duplicated().any():  # two pilots with the same list number
        raise ValueError("SenNum values must be unique within a seniority list.")  # reject duplicates

    today = pd.Timestamp(datetime.now().date())  # today's date (no time)

    # NameID = LastName + FirstName + SenNum + Airline. The airline code makes it unique ACROSS both airlines
    # (the same name with the same SenNum can exist at both), so every later look-up by NameID is safe.
    df["NameID"] = df["LastName"] + df["FirstName"] + df["SenNum"].astype(str) + df["Airline"]  # unique pilot key
    df["DaysHired"] = (today - df["DOH"]).dt.days.astype(int)  # days from date of hire to today
    df["DaysActive"] = (df["DaysHired"] - df["DaysInactive"]).astype(int)  # days hired minus days inactive

    total_rows = len(df)  # number of pilots on this list
    df["RelSen"] = (df["SenNum"] / total_rows).round(5)  # relative seniority as a fraction

    return df  # the enriched table


def count_categories(df, constructive_notice_date):  # Equip x Rank counts, excluding constructive-notice pilots
    notice_date = pd.Timestamp(constructive_notice_date)  # cut-off date as a timestamp
    is_notice = df["DOH"] > notice_date  # True for pilots hired after the notice date
    active = df.loc[~is_notice]  # pilots NOT subject to constructive notice

    table = pd.crosstab(active["Equip"], active["Rank"])  # count pilots per Equip (rows) and Rank (columns)
    table = table.reindex(columns=RANK_COLUMNS, fill_value=0).astype(int)  # force CA/FO/RP columns, whole numbers
    return {"table": table, "notice": int(is_notice.sum()), "total_pilots": len(df)}  # counts plus the notice total


def count_table_html(info, entered_total=None, color="#868E96", title=None):  # builds the tinted HTML count table (optional title row)
    tint = light_color(color, 0.72)  # soft, readable background in the airline's colour
    head_tint = light_color(color, 0.55)  # slightly stronger tint for the header row
    table = info["table"]  # Equip x Rank counts
    rows = []  # HTML rows, built one at a time
    for equip, r in table.iterrows():  # one row per equipment type
        vals = [int(r[c]) for c in RANK_COLUMNS]  # CA, FO, RP counts
        rows.append(  # add this equipment row
            f"<tr><td>{html.escape(str(equip))}</td>"  # equipment name
            + "".join(f"<td>{v}</td>" for v in vals)  # the three rank counts
            + f"<td class='tot'>{sum(vals)}</td></tr>"  # bold row total on the right
        )  # end of row
    col_sums = [int(table[c].sum()) for c in RANK_COLUMNS]  # column totals
    grand = sum(col_sums)  # grand total (bottom-right corner)
    rows.append(  # totals row
        "<tr class='sumrow'><td>Total</td>"  # label
        + "".join(f"<td>{v}</td>" for v in col_sums)  # CA, FO, RP totals
        + f"<td class='tot'>{grand}</td></tr>"  # grand total
    )  # end of totals row
    if entered_total is not None:  # compare with the categories the user typed in
        diff = entered_total - grand  # entered minus counted
        if diff == 0:  # they agree
            rows.append("<tr><td colspan='5' class='note good'>Categories entered match</td></tr>")  # green confirmation
        else:  # they disagree
            rows.append(f"<tr><td colspan='5' class='note bad'>Categories entered \u2212 count: {diff:+d}</td></tr>")  # red difference
    rows.append(  # constructive-notice row
        "<tr><td>Constructive Notice</td><td></td><td></td><td></td>"  # label and empty rank cells
        f"<td class='tot'>{info['notice']}</td></tr>"  # number of constructive-notice pilots
    )  # end of notice row
    header = "<tr><th>Equip</th>" + "".join(f"<th>{c}</th>" for c in RANK_COLUMNS) + "<th>Total</th></tr>"  # column headings
    title_row = f"<tr><th colspan='5' style='text-align:center'>{html.escape(title)}</th></tr>" if title else ""  # optional bold title row inside the table
    return (  # the whole table
        f"<table class='cnt' style='background:{tint}'>"  # tinted table
        f"<thead style='background:{head_tint}'>{title_row}{header}</thead>"  # tinted header (title row first, if any)
        f"<tbody>{''.join(rows)}</tbody></table>"  # body rows
    )  # end of table


def parse_count_text(text):  # reads one category entry box -> (value, is_valid)
    t = str(text if text is not None else "").strip()  # text without spaces
    if t == "":  # blank
        return 0, True  # counts as zero
    if t.isdigit():  # whole number
        return int(t), True  # valid
    return 0, False  # anything else is invalid


def entered_category_totals():  # sums the category boxes for each airline from their current values
    totals = [0, 0]  # airline 1 total, airline 2 total
    all_valid = True  # becomes False if any box is not a whole number
    for n in range(1, 7):  # categories 1-6
        for j, who in enumerate(("airline1", "airline2")):  # both airlines
            v, ok = parse_count_text(st.session_state.get(f"cat_{n}_{who}", "0"))  # read the box's current value
            totals[j] += v  # add to that airline's total
            all_valid = all_valid and ok  # remember any invalid entry
    return totals, all_valid  # totals and validity flag


# ======================================================================
# 4. Analysis: the Create_ functions (every pilot is tracked by its unique NameID)
# ======================================================================
def Create_ConstNoticeList(SenList1, SenList2, constructive_notice_date):  # pilots hired after the notice date
    notice_columns = ["NameID", "Airline", "DaysHired", "DaysActive", "DOH"]  # columns kept for these pilots
    notice_date = pd.Timestamp(constructive_notice_date)  # cut-off date as a timestamp

    ConstNotice1 = (  # airline 1's constructive-notice pilots
        SenList1.loc[SenList1["DOH"] > notice_date, notice_columns]  # hired after the cut-off
        .reset_index(drop=True)  # renumber rows from 0
    )  # end ConstNotice1
    ConstNotice2 = (  # airline 2's constructive-notice pilots
        SenList2.loc[SenList2["DOH"] > notice_date, notice_columns]  # hired after the cut-off
        .reset_index(drop=True)  # renumber rows from 0
    )  # end ConstNotice2
    ConstNoticeList = (  # both airlines combined
        pd.concat([ConstNotice1, ConstNotice2], ignore_index=True)  # stack the two lists
        .sort_values("DOH", ascending=True, kind="mergesort")  # earliest hire date first (ties keep their order)
        .reset_index(drop=True)  # renumber rows from 0
    )  # end ConstNoticeList
    return ConstNotice1, ConstNotice2, ConstNoticeList  # all three lists


def Create_LongList(SenList1, SenList2, ConstNotice1, ConstNotice2, exclude_inactive):  # the longevity list
    long_columns = ["NameID", "Airline", "DaysHired", "DaysActive"]  # columns kept

    Long1 = (  # airline 1 without constructive-notice pilots
        SenList1.loc[~SenList1["NameID"].isin(ConstNotice1["NameID"]), long_columns]  # drop notice pilots
        .reset_index(drop=True)  # renumber rows from 0
    )  # end Long1
    Long2 = (  # airline 2 without constructive-notice pilots
        SenList2.loc[~SenList2["NameID"].isin(ConstNotice2["NameID"]), long_columns]  # drop notice pilots
        .reset_index(drop=True)  # renumber rows from 0
    )  # end Long2

    LongList = pd.concat([Long1, Long2], ignore_index=True)  # both airlines together

    sort_column = "DaysHired" if exclude_inactive else "DaysActive"  # ignore inactivity only when the box is ticked
    # Larger DaysHired/DaysActive means hired longer ago -> more senior -> gets SenNum 1, so sort descending.
    LongList = LongList.sort_values(sort_column, ascending=False, kind="mergesort").reset_index(drop=True)  # stable sort

    LongList.insert(0, "SenNum", range(1, len(LongList) + 1))  # first column = row number (1 = most senior)

    return Long1, Long2, LongList  # all three lists


def Create_Category_List(SenList1, SenList2, category_counts):  # the status-and-category list
    columns = ["NameID", "Airline", "RelSen"]  # columns kept
    offset1 = 0  # next unused row in airline 1's list
    offset2 = 0  # next unused row in airline 2's list
    cat_lists = []  # one list per category

    for cat_num in range(1, 7):  # categories 1 to 6
        count1 = category_counts.get(cat_num, {}).get("airline1", 0)  # pilots airline 1 puts in this category
        count2 = category_counts.get(cat_num, {}).get("airline2", 0)  # pilots airline 2 puts in this category

        slice1 = SenList1.iloc[offset1:offset1 + count1][["NameID", "Airline"]].reset_index(drop=True)  # next block of airline 1
        if count1 > 0:  # at least one pilot in this block
            slice1["RelSen"] = [(i + 1) / count1 for i in range(len(slice1))]  # position within the category / category size
        else:  # empty category
            slice1["RelSen"] = pd.Series(dtype=float)  # empty column

        slice2 = SenList2.iloc[offset2:offset2 + count2][["NameID", "Airline"]].reset_index(drop=True)  # next block of airline 2
        if count2 > 0:  # at least one pilot in this block
            slice2["RelSen"] = [(i + 1) / count2 for i in range(len(slice2))]  # position within the category / category size
        else:  # empty category
            slice2["RelSen"] = pd.Series(dtype=float)  # empty column

        offset1 += count1  # move past the pilots just used
        offset2 += count2  # move past the pilots just used

        cat_list = (  # this category, both airlines interleaved
            pd.concat([slice1[columns], slice2[columns]], ignore_index=True)  # stack the two blocks
            .sort_values("RelSen", kind="mergesort")  # order by relative position (ties keep their order)
            .reset_index(drop=True)  # renumber rows from 0
        )  # end cat_list
        cat_lists.append(cat_list)  # keep it

    CategoryList = pd.concat(cat_lists, ignore_index=True)  # all categories one after another
    CategoryList.insert(0, "SenNum", range(1, len(CategoryList) + 1))  # first column = row number

    return cat_lists, CategoryList  # per-category lists and the combined list


def Create_HybridList(LongList, CategoryList, LongevityWeight, CategoryWeight):  # blends the two lists
    long_part = LongList[["SenNum", "NameID", "Airline"]].rename(columns={"SenNum": "SenNum_Long"})  # longevity position
    cat_part = CategoryList[["SenNum", "NameID"]].rename(columns={"SenNum": "SenNum_Category"})  # category position

    merged = pd.merge(long_part, cat_part, on="NameID", how="outer", indicator=True)  # match pilots by unique NameID

    mismatched = merged.loc[merged["_merge"] != "both", "NameID"].tolist()  # pilots missing from one of the lists
    if mismatched:  # the two lists do not contain the same pilots
        raise ValueError(  # stop with a helpful message
            "NameID mismatch between LongList and CategoryList (check that the "  # part 1
            f"category counts add up to the total pilot count): {mismatched}"  # part 2
        )  # end raise

    merged["SenScore"] = (  # weighted seniority score (lower = more senior)
        merged["SenNum_Long"] * LongevityWeight  # longevity position x its weight
        + merged["SenNum_Category"] * CategoryWeight  # category position x its weight
    )  # end SenScore

    HybridList = (  # the blended list
        merged[["NameID", "Airline", "SenScore"]]  # keep three columns
        .sort_values("SenScore", kind="mergesort")  # lowest score first (ties keep their order)
        .reset_index(drop=True)  # renumber rows from 0
    )  # end HybridList
    HybridList.insert(0, "SenNum", range(1, len(HybridList) + 1))  # first column = new row number

    return HybridList  # the blended list


def Create_StovePipedList(HybridList, SenList1, SenList2):  # interleave by airline, keeping each airline's own order
    airline1_code = SenList1["Airline"].iloc[0]  # airline 1's code
    airline2_code = SenList2["Airline"].iloc[0]  # airline 2's code

    names1 = SenList1["NameID"].tolist()  # airline 1's pilots in their original order
    names2 = SenList2["NameID"].tolist()  # airline 2's pilots in their original order
    idx1 = 0  # next unused airline 1 pilot
    idx2 = 0  # next unused airline 2 pilot

    stovepiped_names = []  # NameIDs in their final positions
    for airline in HybridList["Airline"]:  # walk down the hybrid list's airline pattern
        if airline == airline1_code:  # this slot belongs to airline 1
            if idx1 >= len(names1):  # no airline 1 pilots left
                raise ValueError(f"Ran out of {airline1_code} pilots in SenList1 while building StovepipedList.")  # stop
            stovepiped_names.append(names1[idx1])  # next airline 1 pilot in original order
            idx1 += 1  # advance
        elif airline == airline2_code:  # this slot belongs to airline 2
            if idx2 >= len(names2):  # no airline 2 pilots left
                raise ValueError(f"Ran out of {airline2_code} pilots in SenList2 while building StovepipedList.")  # stop
            stovepiped_names.append(names2[idx2])  # next airline 2 pilot in original order
            idx2 += 1  # advance
        else:  # a code that is neither airline
            raise ValueError(f"Unrecognized airline code '{airline}' in HybridList.")  # stop

    StovepipedList = HybridList.copy()  # start from the hybrid list
    StovepipedList["NameID"] = stovepiped_names  # swap in the stovepiped pilots
    return StovepipedList  # the stovepiped list


def Create_IPSL(StovepipedList, ConstNoticeList, SenList1, SenList2):  # the full Integrated Pilot Seniority List
    lookup_columns = ["NameID", "LastName", "FirstName", "Airline", "Rank", "Equip", "DOH", "DOB", "DaysInactive", "SenNum"]  # data to fetch
    lookup = pd.concat(  # one table holding every pilot from both airlines
        [SenList1[lookup_columns], SenList2[lookup_columns]],  # the two source lists
        ignore_index=True,  # renumber rows
    ).rename(columns={"SenNum": "OrigSenNum"})  # keep the pre-merger list number under a different name

    if lookup["NameID"].duplicated().any():  # two different pilots share a NameID
        dupes = lookup.loc[lookup["NameID"].duplicated(keep=False), "NameID"].unique().tolist()  # which ones
        raise ValueError(f"Duplicate NameID(s) found - SenNum must be unique within each list: {dupes[:5]}")  # stop

    order = pd.concat(  # the final order of pilots, by NameID only
        [StovepipedList[["NameID"]], ConstNoticeList[["NameID"]]],  # integrated pilots, then constructive notice at the bottom
        ignore_index=True,  # renumber rows
    )  # end order

    if order["NameID"].duplicated().any():  # a pilot appears twice in the final order
        dupes = order.loc[order["NameID"].duplicated(keep=False), "NameID"].unique().tolist()  # which ones
        raise ValueError(f"A pilot appears twice in the final list: {dupes[:5]}")  # stop

    IPSL = order.merge(lookup, on="NameID", how="left")  # fetch every other column using NameID ONLY

    missing = IPSL.loc[IPSL["LastName"].isna(), "NameID"].tolist()  # NameIDs that found no pilot
    if missing:  # at least one pilot could not be found
        raise ValueError(f"NameID(s) not found in SenList1/SenList2 while building IPSL: {missing}")  # stop

    IPSL = IPSL[["LastName", "FirstName", "NameID", "Airline", "Rank", "Equip", "DOH", "DOB", "DaysInactive", "OrigSenNum"]]  # column order
    IPSL.insert(0, "SenNum", range(1, len(IPSL) + 1))  # first column = row number in the integrated list

    total_rows = len(IPSL)  # pilots in the integrated list

    airline1_code = SenList1["Airline"].iloc[0]  # airline 1's code
    airline2_code = SenList2["Airline"].iloc[0]  # airline 2's code
    airline_totals = {airline1_code: len(SenList1), airline2_code: len(SenList2)}  # pilots per airline before the merger

    # Months between this pilot's DOH and the DOH of the nearest pilot from the other airline above him (blank if none).
    IPSL["DOHDiffMonths"] = pd.to_numeric(  # numeric column
        pd.Series(compute_doh_differential(IPSL, airline1_code, airline2_code), index=IPSL.index),  # one value per pilot
        errors="coerce",  # blanks become NaN
    ).round(1)  # one decimal place

    IPSL["PreMergeRelSen"] = IPSL.apply(  # pre-merger relative seniority as a percentile (most senior = 100, most junior = 0)
        lambda row: round((airline_totals[row["Airline"]] - row["OrigSenNum"]) / max(airline_totals[row["Airline"]] - 1, 1) * 100, 3), axis=1  # (size - number) / (size - 1)
    )  # end PreMergeRelSen
    IPSL["PostMergeRelSen"] = ((total_rows - IPSL["SenNum"]) / max(total_rows - 1, 1) * 100).round(3)  # post-merger percentile in the IPSL

    return IPSL[  # final column order
        ["SenNum", "LastName", "FirstName", "NameID", "Airline", "Rank", "Equip", "DOH", "DOB",  # identity and hire data
         "DaysInactive", "DOHDiffMonths", "PreMergeRelSen", "PostMergeRelSen"]  # inactivity and relative seniority
    ]  # end of the returned table


def Create_IPSL_Abridged(IPSL):  # short version of the IPSL for display
    name = (  # six-letter name code, e.g. SMIPAT
        IPSL["LastName"].str[:3].str.upper()  # first 3 letters of the last name
        + IPSL["FirstName"].str[:3].str.upper()  # first 3 letters of the first name
    )  # end name
    IPSL_Abridged = pd.DataFrame({  # build the abridged table
        "SenNum": IPSL["SenNum"],  # seniority number
        "Name": name,  # name code
        "Airline": IPSL["Airline"],  # airline code
        "Rank": IPSL["Rank"],  # rank
        "Equip": IPSL["Equip"],  # equipment
        "DOH": IPSL["DOH"].dt.date,  # date of hire without the time
    })  # end IPSL_Abridged
    return IPSL_Abridged  # the abridged table


# ======================================================================
# 5. Report helpers and charts (each draw_ function paints onto a given axes, so the
#    browser report and the PDF share exactly the same drawing code)
# ======================================================================
def hex_to_rgb(hex_color):  # "#RRGGBB" -> (r, g, b) with each value 0-1
    hex_color = hex_color.lstrip("#")  # drop the leading #
    return tuple(int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))  # read the three hex pairs


def rgb_to_hex(rgb):  # (r, g, b) with values 0-1 -> "#rrggbb"
    return "#" + "".join(f"{round(max(0, min(1, c)) * 255):02x}" for c in rgb)  # clamp, scale, write as hex


def light_color(hex_color, amount=0.78):  # blend a colour towards white (0 = unchanged, 1 = white)
    r, g, b = hex_to_rgb(hex_color)  # original colour
    return rgb_to_hex((r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount))  # move each channel towards 1


def shade_color(base_hex, index, total, lightness_range=(0.35, 0.75)):  # one of `total` shades of a base colour
    r, g, b = hex_to_rgb(base_hex)  # base colour
    h, l, s = colorsys.rgb_to_hls(r, g, b)  # hue, lightness, saturation
    if total <= 1:  # only one shade needed
        new_l = l  # keep the original lightness
    else:  # several shades needed
        lo, hi = lightness_range  # darkest and lightest allowed
        new_l = lo + (hi - lo) * (index / (total - 1))  # spread evenly from dark to light
    new_s = min(1.0, s * 1.1)  # slightly boost saturation so shades stay distinct
    r2, g2, b2 = colorsys.hls_to_rgb(h, new_l, new_s)  # back to RGB
    return rgb_to_hex((r2, g2, b2))  # as a hex string


def pick_grid_dimensions(total, candidates=(25, 50, 100)):  # (squares per row, rows) for the dot chart
    if total <= min(candidates):  # very short list
        return total, 1  # a single row
    target = math.sqrt(total)  # width of a square grid
    cols = min(candidates, key=lambda c: abs(c - target))  # the round row width closest to square
    rows = math.ceil(total / cols)  # rows needed to hold everyone
    return cols, rows  # grid size


def compute_doh_differential(IPSL, airline1_code, airline2_code):  # months to the nearest other-airline pilot above
    last_doh = {airline1_code: None, airline2_code: None}  # DOH of the most recent pilot seen from each airline
    ordered = IPSL.sort_values("SenNum")  # make sure we walk down the list in seniority order
    results = []  # one value per pilot
    for airline, doh in zip(ordered["Airline"], ordered["DOH"]):  # each pilot, top to bottom
        other = airline2_code if airline == airline1_code else airline1_code  # the other airline
        ref = last_doh.get(other)  # DOH of the nearest other-airline pilot above (None if none yet)
        results.append(None if ref is None else (doh - ref).days / 30.4375)  # difference in months
        last_doh[airline] = doh  # this pilot becomes the latest from his own airline
    return results  # list aligned with the list order


def build_position_groups(IPSL, airline1_code, airline2_code):  # ordered (Airline, Rank, Equip) combinations
    combos = IPSL[["Airline", "Rank", "Equip"]].drop_duplicates()  # distinct combinations present
    ranks_order = sorted(combos["Rank"].unique())  # ranks alphabetically (CA, FO, RP)
    ordered = []  # result list
    for rank in ranks_order:  # one rank at a time
        a1 = combos.loc[(combos["Airline"] == airline1_code) & (combos["Rank"] == rank), "Equip"].tolist()  # airline 1 equipment
        a2 = combos.loc[(combos["Airline"] == airline2_code) & (combos["Rank"] == rank), "Equip"].tolist()  # airline 2 equipment
        for i in range(max(len(a1), len(a2))):  # alternate between the airlines
            if i < len(a1):  # airline 1 still has one
                ordered.append((airline1_code, rank, a1[i]))  # add it
            if i < len(a2):  # airline 2 still has one
                ordered.append((airline2_code, rank, a2[i]))  # add it
    return ordered  # the ordered combinations


def position_color_map(data):  # (ordered groups, colour for each group)
    c1, c2 = data["airline1_code"], data["airline2_code"]  # airline codes
    groups = build_position_groups(data["IPSL"], c1, c2)  # ordered combinations
    colors = {}  # group -> hex colour
    for code, base in ((c1, data["airline1_color"]), (c2, data["airline2_color"])):  # each airline with its colour
        mine = [g for g in groups if g[0] == code]  # this airline's combinations
        for i, g in enumerate(mine):  # give each a different shade
            colors[g] = shade_color(base, i, len(mine))  # shade of the airline colour
    return groups, colors  # groups and colours


def airline_label(data, code):  # airline code -> airline name
    return data["airline1_name"] if code == data["airline1_code"] else data["airline2_name"]  # pick the matching name


def _style_axes(ax):  # common look for the line/box charts
    ax.spines["top"].set_visible(False)  # no top border
    ax.spines["right"].set_visible(False)  # no right border
    ax.tick_params(labelsize=7)  # small tick labels
    ax.xaxis.label.set_size(8)  # x-axis title size
    ax.yaxis.label.set_size(8)  # y-axis title size


def _draw_dot_grid(ax, grid, cols, rows, title):  # draws a colour grid with thin white lines between squares
    ax.imshow(grid, interpolation="nearest", aspect="equal")  # show the grid as square cells
    ax.set_xticks([])  # no x labels
    ax.set_yticks([])  # no y labels
    ax.set_xticks(np.arange(-0.5, cols, 1), minor=True)  # grid lines between columns
    ax.set_yticks(np.arange(-0.5, rows, 1), minor=True)  # grid lines between rows
    ax.grid(which="minor", color="white", linewidth=0.6)  # thin white borders around each square
    ax.tick_params(which="minor", size=0)  # hide the minor tick marks
    for spine in ax.spines.values():  # every border
        spine.set_visible(False)  # hide it
    ax.set_title(title, fontsize=9)  # chart title


def draw_dot_chart(ax, data):  # dot chart coloured by each pilot's airline + rank + equipment
    IPSL = data["IPSL"]  # the integrated list
    cols, rows = pick_grid_dimensions(len(IPSL))  # grid size
    groups, colors = position_color_map(data)  # colour for each airline/rank/equipment
    rgb = {g: hex_to_rgb(c) for g, c in colors.items()}  # the same colours as RGB triples

    grid = np.ones((rows, cols, 3))  # white background (unused cells stay white)
    for i, key in enumerate(zip(IPSL["Airline"], IPSL["Rank"], IPSL["Equip"])):  # each pilot in seniority order
        r, c = divmod(i, cols)  # row and column of this pilot's square
        grid[r, c] = rgb[key]  # colour by airline/rank/equipment
    _draw_dot_grid(ax, grid, cols, rows, "Dot Chart by Rank and Equipment")  # paint the grid

    def entries(code):  # legend entries for one airline
        mine = [g for g in groups if g[0] == code]  # this airline's combinations
        return [Patch(facecolor=colors[g], edgecolor="none") for g in mine], [f"{g[2]} {g[1]}" for g in mine]  # swatches, labels

    h1, l1 = entries(data["airline1_code"])  # airline 1 legend entries
    h2, l2 = entries(data["airline2_code"])  # airline 2 legend entries
    leg1 = ax.legend(h1, l1, title=data["airline1_name"], loc="upper left", bbox_to_anchor=(0.0, -0.02),  # airline 1 legend, bottom left
                     frameon=False, fontsize=7, title_fontsize=8, ncol=1, borderaxespad=0)  # no frame, one column
    leg1._legend_box.align = "left"  # left-align the legend title
    ax.add_artist(leg1)  # keep it when the second legend is added
    leg2 = ax.legend(h2, l2, title=data["airline2_name"], loc="upper right", bbox_to_anchor=(1.0, -0.02),  # airline 2 legend, bottom right
                     frameon=False, fontsize=7, title_fontsize=8, ncol=1, borderaxespad=0)  # no frame, one column
    leg2._legend_box.align = "left"  # left-align the legend title


def draw_dot_chart_airline(ax, data):  # dot chart with only two colours; constructive-notice pilots are lighter
    IPSL = data["IPSL"]  # the integrated list
    total = len(IPSL)  # number of pilots
    n_notice = data.get("n_notice", 0)  # constructive-notice pilots (they are the last rows of the list)
    cols, rows = pick_grid_dimensions(total)  # grid size
    main = {data["airline1_code"]: data["airline1_color"], data["airline2_code"]: data["airline2_color"]}  # airline -> colour
    main_rgb = {k: hex_to_rgb(v) for k, v in main.items()}  # normal squares as RGB
    light_rgb = {k: hex_to_rgb(light_color(v, 0.5)) for k, v in main.items()}  # lighter shade for constructive notice

    grid = np.ones((rows, cols, 3))  # white background
    for i, airline in enumerate(IPSL["Airline"]):  # each pilot in seniority order
        r, c = divmod(i, cols)  # row and column of this pilot's square
        grid[r, c] = light_rgb[airline] if i >= total - n_notice else main_rgb[airline]  # lighter for constructive notice
    _draw_dot_grid(ax, grid, cols, rows, "Dot Chart by Airline")  # paint the grid

    handles = [Patch(facecolor=data["airline1_color"], edgecolor="none")]  # airline 1 swatch
    labels = [data["airline1_name"]]  # airline 1 label
    if n_notice:  # there are constructive-notice pilots
        handles.append(Patch(facecolor=light_color(data["airline1_color"], 0.5), edgecolor="none"))  # airline 1 lighter swatch
        labels.append(f"{data['airline1_name']} - constructive notice")  # its label
    handles.append(Patch(facecolor=data["airline2_color"], edgecolor="none"))  # airline 2 swatch
    labels.append(data["airline2_name"])  # airline 2 label
    if n_notice:  # there are constructive-notice pilots
        handles.append(Patch(facecolor=light_color(data["airline2_color"], 0.5), edgecolor="none"))  # airline 2 lighter swatch
        labels.append(f"{data['airline2_name']} - constructive notice")  # its label
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.02), frameon=False,  # legend below the chart
              fontsize=7, ncol=2, borderaxespad=0)  # two columns, small text


def _series_by_airline(data):  # (code, name, colour) for each airline
    return [  # the two airlines
        (data["airline1_code"], data["airline1_name"], data["airline1_color"]),  # airline 1
        (data["airline2_code"], data["airline2_name"], data["airline2_color"]),  # airline 2
    ]  # end of list


def _draw_median(ax, value, color, unit=""):  # dashed horizontal line at a median, with its value beside it
    ax.axhline(value, color=color, linestyle="--", linewidth=0.9)  # the median line in the airline's colour
    ax.annotate(  # the value, written just above the right-hand end of the line
        f"Median {value:+.1f}{unit}",  # text such as "Median +24.3 mo"
        xy=(0.99, value),  # right edge of the plot (axes fraction) at the median height (data units)
        xycoords=("axes fraction", "data"),  # x is a fraction of the width, y is in data units
        xytext=(0, 2),  # lift the text 2 points above the line
        textcoords="offset points",  # offset measured in points
        ha="right", va="bottom", fontsize=7, fontweight="bold", color=color,  # right aligned, bold, airline colour
    )  # end annotate


def draw_doh_diff(ax, data):  # months between a pilot's DOH and the nearest other-airline pilot above him
    df = data["IPSL"][["SenNum", "Airline", "DOHDiffMonths"]].rename(columns={"DOHDiffMonths": "Diff"})  # needed columns
    df = df.dropna(subset=["Diff"])  # pilots with nobody from the other airline above have no value
    for code, name, color in _series_by_airline(data):  # each airline
        s = df[df["Airline"] == code]  # this airline's pilots
        ax.plot(s["SenNum"], s["Diff"], linewidth=1.2, color=color, label=name)  # line only, no points
        if len(s):  # there is data to summarise
            _draw_median(ax, float(s["Diff"].median()), color, " mo")  # median line and value
    ax.axhline(0, color="black", linewidth=0.8)  # the x-axis sits at y = 0
    ax.set_xlim(left=0)  # start the x-axis at 0
    ax.yaxis.set_major_locator(MultipleLocator(12))  # y ticks every 12 months
    ax.set_xlabel("Seniority Number")  # x-axis title
    ax.set_ylabel("DOH Difference (months)")  # y-axis title
    ax.set_title("DOH Differential", fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False, loc="upper right")  # legend
    _style_axes(ax)  # common styling


def draw_relsen_diff(ax, data):  # change in relative seniority (post-merger minus pre-merger) down the list
    df = data["IPSL"][["SenNum", "Airline", "PreMergeRelSen", "PostMergeRelSen"]].copy()  # needed columns
    df["Diff"] = df["PostMergeRelSen"] - df["PreMergeRelSen"]  # change in percentage points
    for code, name, color in _series_by_airline(data):  # each airline
        s = df[df["Airline"] == code].sort_values("SenNum")  # this airline's pilots in order
        ax.plot(s["SenNum"], s["Diff"], linewidth=1.2, color=color, label=name)  # line only, no points
        if len(s):  # there is data to summarise
            _draw_median(ax, float(s["Diff"].median()), color)  # median line and value
    ax.axhline(0, color="black", linewidth=0.8)  # the x-axis sits at y = 0
    ax.set_xlim(left=0)  # start the x-axis at 0
    ax.set_xlabel("Seniority Number")  # x-axis title
    ax.set_ylabel("Change in Relative Seniority (percentile points)")  # y-axis title
    ax.set_title("Relative Seniority Difference", fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False, loc="upper right")  # legend
    _style_axes(ax)  # common styling


def draw_relsen_variance(ax, data):  # pre-merger vs post-merger relative seniority
    IPSL = data["IPSL"]  # the integrated list
    for code, name, color in _series_by_airline(data):  # each airline
        s = IPSL[IPSL["Airline"] == code].sort_values("PreMergeRelSen")  # this airline's pilots, by pre-merger position
        ax.plot(s["PreMergeRelSen"], s["PostMergeRelSen"], linewidth=1.2, color=color, label=name)  # line only
    ax.plot([0, 100], [0, 100], color="gray", linewidth=0.8, linestyle="--")  # "no change" diagonal
    ax.set_xlim(0, 100)  # x from 0 to 100 percent
    ax.set_ylim(0, 100)  # y from 0 to 100 percent
    ax.set_xlabel("Pre-Merger Relative Seniority (percentile)")  # x-axis title
    ax.set_ylabel("Post-Merger Relative Seniority (percentile)")  # y-axis title
    ax.set_title("Relative Seniority Variance", fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False)  # legend
    _style_axes(ax)  # common styling


def draw_box_plot(ax, data):  # vertical box plot of seniority numbers by airline / rank / equipment
    IPSL = data["IPSL"]  # the integrated list
    total = len(IPSL)  # number of pilots (used to convert seniority numbers to relative seniority)
    groups, colors = position_color_map(data)  # ordered groups and their colours
    box_data = [  # the seniority numbers in each group
        IPSL[(IPSL["Airline"] == a) & (IPSL["Rank"] == r) & (IPSL["Equip"] == e)]["SenNum"].values  # one array per group
        for a, r, e in groups  # in group order
    ]  # end box_data
    positions = [0.85 * (i + 1) for i in range(len(groups))]  # boxes closer together than the default spacing of 1
    bp = ax.boxplot(  # draw the boxes
        box_data,  # data for each box
        positions=positions,  # x position of each box
        widths=0.7,  # wider boxes
        patch_artist=True,  # allow filled boxes
        medianprops={"color": "black", "linewidth": 1.6},  # centre line = median
        boxprops={"linewidth": 0.8},  # box edges = lower and upper quartiles
        whiskerprops={"linewidth": 0.8},  # whiskers
        capprops={"linewidth": 0.8},  # whisker caps
        flierprops={"marker": "o", "markersize": 3, "markerfacecolor": "none", "markeredgecolor": "black"},  # outliers as dots
        showfliers=True,  # show the outliers
    )  # end boxplot
    for patch, g in zip(bp["boxes"], groups):  # colour each box
        patch.set_facecolor(colors[g])  # shade of the airline colour
    ax.set_xticks(positions)  # one tick per box
    ax.set_xticklabels([f"{e} {r}\n({airline_label(data, a)})" for a, r, e in groups], fontsize=6)  # equipment, rank, airline
    ax.set_xlim(positions[0] - 0.55, positions[-1] + 0.55)  # trim the empty space either side of the boxes
    pad = total * 0.04  # head-room so the labels above the first box are not cut off
    ax.set_ylim(total + pad, -pad)  # inverted: number 1 at the top
    ax.set_ylabel("Seniority Number")  # left axis title

    def rel(v):  # seniority number -> relative seniority percentile (number 1 = 100%, last pilot = 0%)
        return (total - v) / max(total - 1, 1) * 100  # share of pilots who are more junior

    label_box = {"boxstyle": "round,pad=0.08", "fc": "white", "ec": "none", "alpha": 0.8}  # white backing so the text stays readable
    for pos, vals in zip(positions, box_data):  # each box
        if len(vals) == 0:  # empty group
            continue  # nothing to label
        mn = float(vals.max())  # bottom whisker end = lowest relative seniority
        q1 = float(np.percentile(vals, 75))  # bottom edge of the box
        md = float(np.median(vals))  # median
        ax.plot([pos - 0.12, pos + 0.12], [mn, mn], color="black", linewidth=1)  # short tick marking the bottom value
        ax.text(pos, mn, f"{rel(mn):.1f}%", ha="center", va="top", fontsize=5.5, bbox=label_box)  # value only, just below its tick
        ax.text(pos, q1, f"{rel(q1):.1f}%", ha="center", va="bottom", fontsize=5.5, bbox=label_box)  # value only, inside the box above its edge
        ax.text(pos, md, f"{rel(md):.1f}%", ha="center", va="bottom", fontsize=5.5, bbox=label_box)  # value only, just above the median line

    right = ax.secondary_yaxis("right", functions=(lambda y: (total - y) / max(total - 1, 1) * 100, lambda r: total - r * max(total - 1, 1) / 100))  # right axis: 0% at the bottom, 100% at the top
    right.set_ylabel("Relative Seniority (percentile)", fontsize=8)  # right axis title
    right.set_yticks(range(0, 101, 10))  # a tick every 10 percent
    right.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))  # show the ticks as percentages
    right.tick_params(labelsize=7)  # small tick labels
    ax.set_title("Box Plot of Positions", fontsize=9)  # chart title
    _style_axes(ax)  # common styling
    ax.tick_params(axis="x", labelsize=6)  # smaller x labels


def _as_of(data):  # the date the analysis was run (ages and retirements are measured from it)
    return pd.Timestamp(data["prepared_at"][:10])  # "YYYY-MM-DD HH:MM" -> just the date


def _decimal_year(dates):  # dates -> year with a fraction, e.g. 2010-07-01 -> 2010.5
    return dates.dt.year + (dates.dt.dayofyear - 1) / 365.25  # whole year plus the part of the year elapsed


def draw_age_distribution(ax, data):  # share of each airline's pilots at each age (age as of the analysis date)
    IPSL = data["IPSL"]  # the integrated list
    ages = ((_as_of(data) - IPSL["DOB"]).dt.days / 365.25).astype(int)  # age in whole years from the date of birth
    full_range = range(int(ages.min()), int(ages.max()) + 1)  # every age from youngest to oldest
    for code, name, color in _series_by_airline(data):  # each airline
        mine = ages[IPSL["Airline"] == code]  # this airline's pilot ages
        counts = mine.value_counts().reindex(full_range, fill_value=0).sort_index()  # pilots at each age
        pct = counts / max(len(mine), 1) * 100  # as a percentage of this airline's pilots (comparable between airlines)
        ax.plot(counts.index, pct.values, linewidth=1.3, color=color, label=name)  # one line per airline
    ax.set_ylim(bottom=0)  # y-axis starts at 0
    ax.set_xlabel("Age (years)")  # x-axis title
    ax.set_ylabel("% of airline's pilots")  # y-axis title
    ax.set_title("Pilot Age Distribution", fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False)  # legend
    _style_axes(ax)  # common styling


def draw_retirement(ax, data):  # number of pilots reaching Normal Retirement Age in each year
    IPSL = data["IPSL"]  # the integrated list
    nra = int(data["retirement_age"])  # Normal Retirement Age entered on the main page
    years = IPSL["DOB"].dt.year + nra  # the year each pilot reaches that age
    full_range = range(int(years.min()), int(years.max()) + 1)  # every year from first to last retirement
    for code, name, color in _series_by_airline(data):  # each airline
        mine = years[IPSL["Airline"] == code]  # this airline's retirement years
        counts = mine.value_counts().reindex(full_range, fill_value=0).sort_index()  # retirements in each year
        ax.plot(counts.index, counts.values, linewidth=1.3, color=color, label=name)  # one line per airline
    this_year = _as_of(data).year  # the year of the analysis
    ax.axvline(this_year, color="gray", linestyle=":", linewidth=0.9)  # dotted marker for the current year
    ax.annotate("analysis year", xy=(this_year, 1.0), xycoords=("data", "axes fraction"), xytext=(3, -3),  # label at the top of the marker
                textcoords="offset points", ha="left", va="top", fontsize=6, color="gray")  # small grey text
    ax.set_ylim(bottom=0)  # y-axis starts at 0
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # whole years only on the x-axis
    ax.set_xlabel("Year")  # x-axis title
    ax.set_ylabel("Pilots retiring")  # y-axis title
    ax.set_title(f"Pilot Retirements (age {nra})", fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False)  # legend
    _style_axes(ax)  # common styling


def _hire_axes(ax, data, title):  # shared look for the two relative seniority vs year of hire charts
    years = _decimal_year(data["IPSL"]["DOH"])  # every pilot's year of hire
    ax.set_ylim(years.min() - 1, years.max() + 1)  # same y range on both charts so they compare directly
    ax.set_xlim(100, 0)  # reversed x-axis: 100% (the pilots hired first) on the left
    ax.set_xlabel("Relative Seniority (percentile)")  # x-axis title
    ax.set_ylabel("Year of Hire")  # y-axis title
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))  # whole years on the y-axis
    ax.set_title(title, fontsize=9)  # chart title
    ax.legend(fontsize=7, frameon=False, markerscale=3)  # legend with larger swatches
    _style_axes(ax)  # common styling


def draw_hire_scatter_pre(ax, data):  # PRE-merger relative seniority vs year of hire, one series per airline
    IPSL = data["IPSL"]  # the integrated list
    for code, name, color in _series_by_airline(data):  # each airline
        mine = IPSL[IPSL["Airline"] == code]  # this airline's pilots
        ax.scatter(mine["PreMergeRelSen"], _decimal_year(mine["DOH"]), s=4, color=color, label=name)  # original list position
    _hire_axes(ax, data, "Pre-Merger Relative Seniority vs Year of Hire")  # axes, title, legend


def draw_hire_scatter_post(ax, data):  # POST-merger (IPSL) relative seniority vs year of hire, coloured by airline
    IPSL = data["IPSL"]  # the integrated list
    for code, name, color in _series_by_airline(data):  # each airline
        mine = IPSL[IPSL["Airline"] == code]  # this airline's pilots
        ax.scatter(mine["PostMergeRelSen"], _decimal_year(mine["DOH"]), s=4, color=color, label=name)  # integrated list position
    _hire_axes(ax, data, "Post-Merger (IPSL) Relative Seniority vs Year of Hire")  # axes, title, legend


def dot_chart_figsize(data, width=6.0):  # figure size that fits the grid plus the legend
    cols, rows = pick_grid_dimensions(len(data["IPSL"]))  # grid size
    _, colors = position_color_map(data)  # groups (for the legend length)
    per_airline = max(  # longest legend list
        sum(1 for g in colors if g[0] == data["airline1_code"]),  # airline 1 entries
        sum(1 for g in colors if g[0] == data["airline2_code"]),  # airline 2 entries
    )  # end max
    return (width, width * rows / cols + 0.7 + 0.17 * per_airline)  # width and height in inches


# ======================================================================
# 6. Export: CSV of the full IPSL and a PDF of the report
# ======================================================================
def _safe(text):  # removes characters that are not allowed in file names
    return "".join(ch for ch in str(text) if ch not in '\\/:*?"<>|').strip() or "Airline"  # keep the rest; never empty


def export_stamp():  # current date and time as YYYYMMDD-HHMM
    return datetime.now().strftime("%Y%m%d-%H%M")  # e.g. 20261018-1530


def build_ipsl_csv_bytes(data):  # the FULL IPSL (not abridged) as CSV bytes
    out = data["IPSL"].copy()  # work on a copy
    out["DOH"] = out["DOH"].dt.date  # date only (no time)
    out["DOB"] = out["DOB"].dt.date  # date only (no time)
    return out.to_csv(index=False).encode("utf-8")  # CSV text as bytes


def _count_rows(info):  # text rows for a Category Count table: equipment rows, totals, constructive notice
    table = info["table"]  # Equip x Rank counts
    rows = []  # result rows
    for equip, r in table.iterrows():  # one row per equipment type
        vals = [int(r[c]) for c in RANK_COLUMNS]  # CA, FO, RP counts
        rows.append([str(equip)] + [str(v) for v in vals] + [str(sum(vals))])  # label, counts, row total
    sums = [int(table[c].sum()) for c in RANK_COLUMNS]  # column totals
    rows.append(["Total"] + [str(v) for v in sums] + [str(sum(sums))])  # totals row
    rows.append(["Constr. Notice", "", "", "", str(info["notice"])])  # constructive-notice pilots
    return rows  # the rows


def _category_rows(data):  # rows for the category table: Cat 1-6 then Constructive Notice
    rows = [  # one row per category
        [f"Cat {c}", data["category_counts"][c]["airline1"], data["category_counts"][c]["airline2"]]  # label and both counts
        for c in range(1, 7)  # categories 1 to 6
    ]  # end rows
    rows.append(["Constructive Notice", data["n_notice1"], data["n_notice2"]])  # number of constructive-notice pilots
    return rows  # the rows


def _listing_pages(pdf, title, headers, rows, row_colors, per_page, figsize, fontsize):  # writes a tinted table as PDF pages
    cols = len(headers)  # number of columns
    header_parts = [h.split("\n") for h in headers]  # each heading split into its lines
    header_lines = max(len(h) for h in header_parts)  # tallest heading
    header_parts = [h + [""] * (header_lines - len(h)) for h in header_parts]  # pad shorter headings with blank lines
    widths = [  # character width of each column: the widest heading line or cell
        max(max(len(line) for line in header_parts[c]), max((len(r[c]) for r in rows), default=0))  # widest text in column c
        for c in range(cols)  # every column
    ]  # end widths

    def line(cells):  # one centred, fixed-width line of text
        return "  ".join(str(cell).center(w) for cell, w in zip(cells, widths))  # pad every cell to its column width

    total_chars = sum(widths) + 2 * (cols - 1)  # characters across the whole line
    axes_w_pt = figsize[0] * 0.94 * 72  # width of the table area in points
    fontsize = min(fontsize, axes_w_pt / (total_chars * 0.602))  # shrink the text if the line would be too wide
    frac = min(1.0, total_chars * 0.602 * fontsize / axes_w_pt + 0.012)  # width of the tinted band (fraction of the area)
    header_h = 0.012 + 0.019 * header_lines  # heading height (fraction of the table area)
    row_h = (1 - header_h) / per_page  # height of each row
    n_pages = max(1, math.ceil(len(rows) / per_page))  # number of pages
    mono = {"family": "DejaVu Sans Mono"}  # a fixed-width font so the columns line up
    for page in range(n_pages):  # one page at a time
        fig = plt.figure(figsize=figsize)  # new page
        fig.text(0.5, 0.968, title, ha="center", fontsize=11, weight="bold")  # page title
        fig.text(0.97, 0.015, f"Page {page + 1} of {n_pages}", ha="right", fontsize=7)  # page number
        ax = fig.add_axes([0.03, 0.035, 0.94, 0.905])  # table area
        ax.set_xlim(0, 1)  # x runs 0-1 across the table
        ax.set_ylim(0, 1)  # y runs 0-1 up the table
        ax.axis("off")  # no axes lines
        ax.add_patch(Rectangle((0.5 - frac / 2, 1 - header_h), frac, header_h, facecolor="#dee2e6", edgecolor="none"))  # heading band
        for i in range(header_lines):  # each heading line
            y = 1 - header_h * (i + 0.5) / header_lines  # vertical centre of this heading line
            ax.text(0.5, y, line([h[i] for h in header_parts]), ha="center", va="center", fontsize=fontsize, weight="bold", **mono)  # bold heading
        for k in range(per_page):  # each row on this page
            idx = page * per_page + k  # position in the full list
            if idx >= len(rows):  # no more rows
                break  # the page is not full
            y_top = 1 - header_h - k * row_h  # top edge of this row
            ax.add_patch(Rectangle((0.5 - frac / 2, y_top - row_h), frac, row_h, facecolor=row_colors[idx], edgecolor="white", linewidth=0.3))  # tinted band
            ax.text(0.5, y_top - row_h / 2, line(rows[idx]), ha="center", va="center", fontsize=fontsize, **mono)  # the row's text
        pdf.savefig(fig)  # write this page
        plt.close(fig)  # free memory


def build_pdf_bytes(data):  # the report as a multi-page PDF (bytes)
    buf = io.BytesIO()  # in-memory file
    a1, a2 = data["airline1_name"], data["airline2_name"]  # airline names
    with PdfPages(buf) as pdf:  # open the PDF for writing
        # ---- page 1: title, contact, parameters, both dot charts ----
        fig = plt.figure(figsize=(11, 8.5))  # landscape letter page
        fig.text(0.5, 0.955, f"{a1}-{a2} Integrated Pilot Seniority List", ha="center", fontsize=17, weight="bold")  # title
        fig.text(0.5, 0.925, f"{CONTACT_SITE}   |   {CONTACT_EMAIL}", ha="center", fontsize=9)  # website and e-mail
        fig.text(0.5, 0.903, f"Prepared on {data['prepared_at']}", ha="center", fontsize=9)  # date and time
        fig.text(0.05, 0.875, "Integration Parameters", fontsize=11, weight="bold", va="top")  # section heading
        fig.text(  # parameter lines
            0.05, 0.848,  # position
            f"Status and Category weight: {data['category_weight_pct']}%\n"  # category weight
            f"Longevity weight: {data['longevity_weight_pct']}%\n"  # longevity weight
            f"Exclude Inactive Periods: {'Yes' if data['exclude_inactive'] else 'No'}\n"  # checkbox
            f"Constructive Notice Date: {data['constructive_notice_date']}\n"  # notice date
            f"Normal Retirement Age: {data['retirement_age']}",  # retirement age
            fontsize=9, va="top", linespacing=1.6,  # small text with line spacing
        )  # end of the parameter text
        ax = fig.add_axes([0.28, 0.66, 0.22, 0.21])  # area for the category table
        ax.axis("off")  # no axes lines
        tbl = ax.table(  # category table
            cellText=_category_rows(data),  # body rows
            colLabels=["Category", a1, a2],  # headings
            loc="upper left", cellLoc="center", colWidths=[0.42, 0.29, 0.29],  # placement and widths
        )  # end table
        tbl.auto_set_font_size(False)  # fixed font size
        tbl.set_fontsize(7)  # small text
        tbl.scale(1, 1.05)  # slightly shorter rows
        for (row, col), cell in tbl.get_celld().items():  # every cell
            if row == 0:  # the heading row
                cell.set_text_props(weight="bold")  # bold headings
        fig.text(0.75, 0.912, "Category Count", ha="center", fontsize=10, weight="bold", va="top")  # title above the count tables
        for x0, key, name, color in ((0.52, "count_info1", a1, data["airline1_color"]), (0.76, "count_info2", a2, data["airline2_color"])):  # one table per airline
            axc = fig.add_axes([x0, 0.66, 0.22, 0.20])  # area for this count table
            axc.axis("off")  # no axes lines
            rows_c = _count_rows(data[key])  # text rows
            ctbl = axc.table(  # the count table
                cellText=rows_c, colLabels=["Equip", *RANK_COLUMNS, "Total"],  # body and headings
                cellColours=[[light_color(color, 0.72)] * 5] * len(rows_c), colColours=[light_color(color, 0.55)] * 5,  # tinted in the airline colour
                loc="upper left", cellLoc="center", colWidths=[0.34, 0.15, 0.15, 0.15, 0.2],  # placement and widths
            )  # end table
            ctbl.auto_set_font_size(False)  # fixed font size
            ctbl.set_fontsize(6.5)  # small text
            ctbl.scale(1, 1.05)  # slightly shorter rows
            axc.set_title(name, fontsize=8, weight="bold")  # airline name above its table
            for (row, col), cell in ctbl.get_celld().items():  # every cell
                if row == 0:  # the heading row
                    cell.set_text_props(weight="bold")  # bold headings
        ax1 = fig.add_axes([0.04, 0.14, 0.45, 0.46])  # left dot chart area
        draw_dot_chart(ax1, data)  # dot chart by rank and equipment
        ax2 = fig.add_axes([0.53, 0.14, 0.45, 0.46])  # right dot chart area
        draw_dot_chart_airline(ax2, data)  # dot chart by airline
        pdf.savefig(fig)  # write page 1
        plt.close(fig)  # free memory

        # ---- page 2: the four analysis charts ----
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))  # 2 x 2 grid of charts
        draw_doh_diff(axes[0, 0], data)  # top left: DOH differential
        draw_relsen_diff(axes[0, 1], data)  # top right: relative seniority difference
        draw_relsen_variance(axes[1, 0], data)  # bottom left: relative seniority variance
        draw_box_plot(axes[1, 1], data)  # bottom right: box plot
        fig.tight_layout(pad=1.5)  # stop labels overlapping
        pdf.savefig(fig)  # write page 2
        plt.close(fig)  # free memory

        # ---- page 3: age distribution, retirements, relative seniority vs year of hire ----
        fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))  # 2 x 2 grid (one cell left empty)
        draw_hire_scatter_pre(axes[0, 0], data)  # top left: pre-merger relative seniority vs year of hire
        draw_hire_scatter_post(axes[0, 1], data)  # top right: post-merger relative seniority vs year of hire
        draw_age_distribution(axes[1, 0], data)  # bottom left: age distribution
        draw_retirement(axes[1, 1], data)  # bottom right: retirements per year
        fig.tight_layout(pad=1.5)  # stop labels overlapping
        pdf.savefig(fig)  # write page 3
        plt.close(fig)  # free memory

        # ---- remaining pages: abridged IPSL, rows tinted with the airline colour ----
        ab = data["IPSL_Abridged"]  # abridged table
        tint = {  # row colour for each airline
            data["airline1_code"]: light_color(data["airline1_color"]),  # airline 1
            data["airline2_code"]: light_color(data["airline2_color"]),  # airline 2
        }  # end tint
        rows = [[str(r.SenNum), r.Name, r.Airline, r.Rank, r.Equip, str(r.DOH)] for r in ab.itertuples(index=False)]  # text rows
        _listing_pages(  # write the table pages
            pdf, f"{a1}-{a2} Abridged IPSL", ["Sen #", "Name", "Airline", "Rank", "Equip", "DOH"],  # document, title, headings
            rows, [tint[x] for x in ab["Airline"]], per_page=60, figsize=(8.5, 11), fontsize=9,  # rows, row colours, layout
        )  # end _listing_pages
    return buf.getvalue()  # the finished PDF as bytes


IPSL_PDF_HEADERS = ["Sen #", "Last Name", "First Name", "NameID", "Airline", "Rank", "Equip", "DOH", "DOB",  # column headings, part 1
                    "Days\nInactive", "DOH Diff\n(months)", "Pre-Merger\nRel Sen (%)", "Post-Merger\nRel Sen (%)"]  # part 2


def build_ipsl_pdf_bytes(data):  # the FULL IPSL as a landscape PDF, every row tinted with its airline's colour
    ipsl = data["IPSL"]  # full list
    a1, a2 = data["airline1_name"], data["airline2_name"]  # airline names
    tint = {  # row background for each airline
        data["airline1_code"]: light_color(data["airline1_color"]),  # airline 1
        data["airline2_code"]: light_color(data["airline2_color"]),  # airline 2
    }  # end tint
    text = pd.DataFrame({  # every cell converted to display text
        "SenNum": ipsl["SenNum"].astype(str),  # integrated seniority number
        "LastName": ipsl["LastName"],  # surname
        "FirstName": ipsl["FirstName"],  # given name
        "NameID": ipsl["NameID"],  # unique pilot key
        "Airline": ipsl["Airline"],  # airline code
        "Rank": ipsl["Rank"],  # rank
        "Equip": ipsl["Equip"],  # equipment
        "DOH": ipsl["DOH"].dt.strftime("%Y-%m-%d"),  # date of hire, no time
        "DOB": ipsl["DOB"].dt.strftime("%Y-%m-%d"),  # date of birth, no time
        "DaysInactive": ipsl["DaysInactive"].astype(str),  # days inactive
        "DOHDiffMonths": ipsl["DOHDiffMonths"].map(lambda v: "" if pd.isna(v) else f"{v:.1f}"),  # blank when there is no value
        "PreMergeRelSen": ipsl["PreMergeRelSen"].map(lambda v: f"{v:.3f}"),  # pre-merger relative seniority
        "PostMergeRelSen": ipsl["PostMergeRelSen"].map(lambda v: f"{v:.3f}"),  # post-merger relative seniority
    })  # end text
    buf = io.BytesIO()  # in-memory file
    with PdfPages(buf) as pdf:  # open the PDF for writing
        _listing_pages(  # write the table pages
            pdf, f"{a1}-{a2} Integrated Pilot Seniority List (IPSL)", IPSL_PDF_HEADERS,  # document, title, headings
            text.values.tolist(), [tint[x] for x in ipsl["Airline"]], per_page=46, figsize=(11, 8.5), fontsize=7,  # rows, colours, layout
        )  # end _listing_pages
    return buf.getvalue()  # the finished PDF as bytes


def build_export_files(data):  # all export files: (file name, mime type, bytes)
    stamp = export_stamp()  # date-time stamp for the file names
    base = f"{_safe(data['airline1_name'])}-{_safe(data['airline2_name'])}"  # "Airline1-Airline2"
    return [  # the three files
        (f"{base} IPSL {stamp}.csv", "text/csv", build_ipsl_csv_bytes(data)),  # full IPSL as CSV
        (f"{base} IPSL {stamp}.pdf", "application/pdf", build_ipsl_pdf_bytes(data)),  # full IPSL as PDF (same name, .pdf)
        (f"{base} integration data {stamp}.pdf", "application/pdf", build_pdf_bytes(data)),  # report as PDF
    ]  # end of list


def auto_download_html(files):  # small script that makes the browser save each file
    items = [{"name": n, "mime": m, "b64": base64.b64encode(b).decode("ascii")} for n, m, b in files]  # files as base64 text
    script = """
    <script>
    const files = __FILES__;
    function dl(f) {
      const bin = atob(f.b64);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
      const url = URL.createObjectURL(new Blob([arr], {type: f.mime}));
      const a = document.createElement('a');
      a.href = url; a.download = f.name;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 15000);
    }
    files.forEach((f, i) => setTimeout(() => dl(f), i * 900));
    </script>
    """  # JavaScript: build a download link for each file and click it, 0.9 s apart
    return script.replace("__FILES__", json.dumps(items))  # insert the file data


def run_download_script(html_text):  # runs the download script in a tiny hidden frame
    if hasattr(st, "iframe"):  # newer Streamlit
        st.iframe(html_text.strip(), height=1)  # hidden 1-pixel frame
    else:  # older Streamlit
        components.html(html_text, height=0)  # classic component


# ======================================================================
# 7. Report page (opens in a new browser tab after ANALYZE)
# ======================================================================
def _fig_for(draw_fn, data, figsize=(6, 3.8)):  # makes a new figure and draws one chart on it
    fig, ax = plt.subplots(figsize=figsize)  # empty figure with one axes
    draw_fn(ax, data)  # paint the chart
    return fig  # the finished figure


def report_category_table_html(data):  # compact table of the categories entered, plus constructive-notice pilots
    t1 = light_color(data["airline1_color"], 0.6)  # soft tint for airline 1's heading
    t2 = light_color(data["airline2_color"], 0.6)  # soft tint for airline 2's heading
    head = (  # heading row
        "<tr><th>Category</th>"  # first heading
        f"<th style='background:{t1}'>{html.escape(data['airline1_name'])}</th>"  # airline 1 heading
        f"<th style='background:{t2}'>{html.escape(data['airline2_name'])}</th></tr>"  # airline 2 heading
    )  # end head
    body = "".join(  # body rows
        f"<tr><td>{label}</td><td>{v1}</td><td>{v2}</td></tr>"  # one row
        for label, v1, v2 in _category_rows(data)  # Cat 1-6 and Constructive Notice
    )  # end body
    return f"<table class='rpt'>{head}{body}</table>"  # the finished table


def abridged_html(data):  # scrollable Abridged IPSL; each row tinted with its airline's colour
    ab = data["IPSL_Abridged"]  # abridged table
    tint = {  # row background for each airline
        data["airline1_code"]: light_color(data["airline1_color"]),  # airline 1
        data["airline2_code"]: light_color(data["airline2_color"]),  # airline 2
    }  # end tint
    parts = [  # start with the heading
        "<div class='ipslwrap'><table class='ipsl'><thead><tr>"  # wrapper, table, heading row
        "<th>Sen #</th><th>Name</th><th>Airline</th><th>Rank</th><th>Equip</th><th>DOH</th>"  # bold column headings
        "</tr></thead><tbody>"  # start of the body
    ]  # end parts
    for r in ab.itertuples(index=False):  # one row per pilot
        parts.append(  # add the row
            f"<tr style='background:{tint[r.Airline]}'>"  # tinted row
            f"<td>{r.SenNum}</td><td>{html.escape(str(r.Name))}</td><td>{r.Airline}</td>"  # number, name, airline
            f"<td>{r.Rank}</td><td>{r.Equip}</td><td>{r.DOH}</td></tr>"  # rank, equipment, date of hire
        )  # end row
    parts.append("</tbody></table></div>")  # close the table
    return "".join(parts)  # the finished HTML


def render_report_page(data):  # draws the whole report
    a1, a2 = data["airline1_name"], data["airline2_name"]  # airline names

    st.title(f"{a1}-{a2} Integrated Pilot Seniority List")  # page title
    st.markdown(  # website and e-mail links, regular size, under the title
        f"[{CONTACT_SITE}](https://{CONTACT_SITE}) &nbsp;|&nbsp; [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})"  # two hyperlinks
    )  # end markdown
    st.caption(f"Prepared on {data['prepared_at']}")  # date and time of the analysis

    st.subheader("Integration Parameters")  # section heading
    p1, p2, p3 = st.columns([2, 2, 4])  # parameters | category table | Category Count tables
    with p1:  # left block
        st.markdown(  # the parameter lines
            f"**Status and Category weight:** {data['category_weight_pct']}%  \n"  # category weight
            f"**Longevity weight:** {data['longevity_weight_pct']}%  \n"  # longevity weight
            f"**Exclude Inactive Periods:** {'Yes' if data['exclude_inactive'] else 'No'}  \n"  # checkbox
            f"**Constructive Notice Date:** {data['constructive_notice_date']}  \n"  # notice date
            f"**Normal Retirement Age:** {data['retirement_age']}"  # retirement age, under the notice date
        )  # end markdown
    with p2:  # middle block
        st.markdown(report_category_table_html(data), unsafe_allow_html=True)  # compact category table
    with p3:  # right block: the Category Count tables, beside the category table
        t1, t2 = st.columns(2)  # one table per airline, starting at the very top so they line up with the Category table
        with t1:  # airline 1
            st.markdown(count_table_html(data["count_info1"], None, data["airline1_color"], f"Category Count - {a1}"), unsafe_allow_html=True)  # tinted count table with its title inside
        with t2:  # airline 2
            st.markdown(count_table_html(data["count_info2"], None, data["airline2_color"], f"Category Count - {a2}"), unsafe_allow_html=True)  # tinted count table with its title inside

    st.divider()  # thin line

    def show(draw_fn, size=(6, 3.8)):  # draws one chart in the current column
        fig = _fig_for(draw_fn, data, size)  # build the figure
        st.pyplot(fig)  # display it
        plt.close(fig)  # free memory

    dot_size = dot_chart_figsize(data)  # figure size for the dot charts
    left, right = st.columns(2)  # row 1: two dot charts
    with left:  # left column
        show(draw_dot_chart, dot_size)  # dot chart by rank and equipment
    with right:  # right column
        show(draw_dot_chart_airline, dot_size)  # dot chart by airline

    left, right = st.columns(2)  # row 2
    with left:  # left column
        show(draw_doh_diff)  # DOH differential
    with right:  # right column
        show(draw_relsen_diff)  # relative seniority difference

    left, right = st.columns(2)  # row 3
    with left:  # left column
        show(draw_relsen_variance)  # relative seniority variance
    with right:  # right column
        show(draw_box_plot)  # box plot of positions

    left, right = st.columns(2)  # row 4
    with left:  # left column
        show(draw_hire_scatter_pre)  # pre-merger relative seniority vs year of hire
    with right:  # right column
        show(draw_hire_scatter_post)  # post-merger relative seniority vs year of hire

    left, right = st.columns(2)  # row 5, below the relative seniority vs year of hire charts
    with left:  # left column
        show(draw_age_distribution)  # pilot age distribution
    with right:  # right column
        show(draw_retirement)  # pilot retirements per year

    st.subheader("Abridged IPSL")  # section heading, below all charts
    st.markdown(abridged_html(data), unsafe_allow_html=True)  # tinted, scrollable table


_query_report_id = st.query_params.get("report_id")  # id in the web address, if this tab was opened as a report
if _query_report_id:  # this tab is a report tab
    if _query_report_id in REPORT_CACHE:  # the report is still held in memory
        render_report_page(REPORT_CACHE[_query_report_id])  # draw it
    else:  # unknown or expired id
        st.error("Report not found. It may have expired, or this tab was opened from a different app session.")  # explain
    st.stop()  # do not draw the main page in a report tab


# ======================================================================
# 8. Main page
# ======================================================================
def small_red(msg):  # small red warning text
    st.markdown(f"<span style='color:#d6336c; font-size:0.8rem;'>{msg}</span>", unsafe_allow_html=True)  # red, small


def info_popover(key, text):  # a plain (i) symbol that opens a box containing `text`
    with st.popover("\u24d8", key=f"info_{key}", type="tertiary"):  # the (i) trigger, styled by the CSS above
        st.markdown(text)  # the explanation


def password_ok(text):  # True if `text` is one of the accepted export passwords
    return hashlib.sha256(str(text).strip().encode("utf-8")).hexdigest() in VALID_PASSWORD_HASHES  # compare hashes only


@st.dialog("User license password")  # opens as a pop-up box
def export_password_dialog():  # asks for the export password
    st.markdown(PASSWORD_PROMPT)  # explanation text
    with st.form("export_pw_form", clear_on_submit=True, border=False):  # a form lets the Enter key submit
        pw = st.text_input("Password", type="password", key="export_pw")  # hidden password entry
        submitted = st.form_submit_button("Submit")  # submit button
    if submitted:  # the user pressed Submit / Enter
        if password_ok(pw):  # correct password
            st.session_state["export_authorized"] = True  # let the export run on the next pass
        else:  # wrong password
            st.session_state["show_bad_password"] = True  # show the "incorrect" box on the next pass
        st.rerun()  # close this box and rerun the page


@st.dialog("Password incorrect")  # second pop-up box
def bad_password_dialog():  # tells the user the password was wrong
    st.markdown(PASSWORD_WRONG)  # message with the contact address
    if st.button("OK", key="bad_pw_ok"):  # dismiss button
        st.rerun()  # close the box


def _set_color(state_key, color_name):  # callback: remember the colour the user clicked
    st.session_state[state_key] = color_name  # store it


def _remove_sample(n):  # callback: stop using the built-in sample list for airline n
    st.session_state[f"use_sample_{n}"] = False  # the file uploader appears instead


def _text_color_for(hex_color):  # black or white text, whichever is readable on this colour
    r, g, b = hex_to_rgb(hex_color)  # background colour
    return "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 0.6 else "#ffffff"  # light background -> dark text


def color_swatches(n):  # one colour chip; pressing it opens the 12-colour palette
    state_key = f"airline{n}_color_name"  # where this airline's colour is remembered
    if state_key not in st.session_state:  # first run
        st.session_state[state_key] = DEFAULT_COLOR_NAMES[n]  # use the default colour
    current = st.session_state[state_key]  # colour name now selected
    names = list(COLOR_CHOICES)  # the 12 colour names
    chip_hex = COLOR_CHOICES[current]  # hex code of the selected colour

    css = [  # CSS that paints the chip itself
        f".st-key-colorpop_{n} button {{ background: {chip_hex} !important; border: 1px solid rgba(0,0,0,0.4) !important;"  # chip colour
        f" min-height: 1.8rem !important; height: 1.8rem !important; padding: 0 0.6rem !important; }}"  # chip size
        f".st-key-colorpop_{n} button p {{ color: {_text_color_for(chip_hex)} !important; font-size: 1rem !important;"  # arrow colour
        f" margin: 0 !important; }}"  # no extra margin
    ]  # end css
    for name in names:  # CSS for each palette square
        hex_color = COLOR_CHOICES[name]  # this square's colour
        border = "3px solid #111111" if name == current else "1px solid rgba(0,0,0,0.25)"  # thick border marks the selection
        css.append(  # add the rules for this square
            f".st-key-sw_{n}_{name} button {{ background: {hex_color} !important; border: {border} !important;"  # colour and border
            f" min-height: 1.8rem !important; height: 1.8rem !important; padding: 0 !important; }}"  # size
            f".st-key-sw_{n}_{name} button p {{ color: {_text_color_for(hex_color)} !important;"  # tick colour
            f" font-size: 1rem !important; font-weight: 900 !important; margin: 0 !important; }}"  # tick size
        )  # end append
    st.markdown("<style>" + "".join(css) + "</style>", unsafe_allow_html=True)  # apply all the rules

    st.caption("Colour")  # small label above the chip
    with st.popover("\u00a0\u25be\u00a0", key=f"colorpop_{n}", help=f"{current} - click to change"):  # the chip that opens the palette
        per_row = 4  # squares per row in the palette
        for start in range(0, len(names), per_row):  # one row at a time
            cols = st.columns(per_row)  # a row of squares
            for col, name in zip(cols, names[start:start + per_row]):  # each square
                col.button(  # a clickable colour square
                    "\u2713" if name == current else "\u00a0",  # tick on the selected one
                    key=f"sw_{n}_{name}",  # unique key (also used by the CSS)
                    help=name,  # hover shows the colour name
                    on_click=_set_color,  # remember the click
                    args=(state_key, name),  # which airline and colour
                    width="stretch",  # fill the cell
                )  # end button
    return chip_hex  # hex code of the selected colour


def airline_inputs(n, c_name, c_file, c_color):  # the three input boxes for airline n -> (name, file source, colour)
    with c_name:  # name column
        name = st.text_input(f"Airline {n} name", key=f"airline{n}_name")  # editable airline name
    source = None  # where the CSV comes from
    with c_file:  # file column
        if st.session_state.get(f"use_sample_{n}", True):  # the built-in sample is still in use
            st.caption("Seniority list (CSV)")  # label like the uploader's
            with st.container(border=True):  # box that looks like an uploaded file
                f_text, f_x = st.columns([5, 1])  # file name | remove button
                f_text.markdown(  # file name and "sample" tag
                    f"<span style='font-size:0.75rem'>{SAMPLE_FILE_NAMES[n]} <i>(sample)</i></span>",  # small text
                    unsafe_allow_html=True,  # allow the HTML
                )  # end markdown
                f_x.button("\u2715", key=f"rm_sample_{n}", on_click=_remove_sample, args=(n,),  # remove button
                           help="Remove the sample list so you can upload your own")  # tooltip
            source = sample_csv_buffer(n)  # the embedded sample file
        else:  # the user removed the sample
            source = st.file_uploader("Seniority list (CSV)", type="csv", key=f"airline{n}_file")  # normal uploader
    with c_color:  # colour column
        hex_color = color_swatches(n)  # colour chip and palette
    return name, source, hex_color  # everything the rest of the page needs


# ---------- set the first-run defaults (names, sample lists) before any widget is drawn ----------
for _n in (1, 2):  # both airlines
    if f"airline{_n}_name" not in st.session_state:  # first run
        st.session_state[f"airline{_n}_name"] = DEFAULT_AIRLINE_NAMES[_n]  # pre-fill the airline name
    if f"use_sample_{_n}" not in st.session_state:  # first run
        st.session_state[f"use_sample_{_n}"] = True  # start with the sample list loaded

st.title("Pilot Seniority List Integration Tool")  # page title

head_col, head_info, _ = st.columns([4, 0.5, 6])  # heading | (i) symbol | spare space
with head_col:  # heading column
    st.subheader("Upload Seniority Lists")  # section heading (kept on one line)
with head_info:  # (i) column
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)  # nudge down to line up with the heading
    info_popover("upload", UPLOAD_INFO)  # CSV format help

# Airline 1 and Airline 2 side by side: name | list | colour, gap, name | list | colour
c1_name, c1_file, c1_color, _gap, c2_name, c2_file, c2_color, _rest = st.columns([1.2, 1.8, 0.7, 0.3, 1.2, 1.8, 0.7, 2.3])  # one row
airline1_name, source1, airline1_color = airline_inputs(1, c1_name, c1_file, c1_color)  # airline 1 inputs
airline2_name, source2, airline2_color = airline_inputs(2, c2_name, c2_file, c2_color)  # airline 2 inputs
a1_label = airline1_name or "Airline 1"  # name to show (fallback if blank)
a2_label = airline2_name or "Airline 2"  # name to show (fallback if blank)

SenList1 = None  # airline 1's seniority list (None until it loads)
SenList2 = None  # airline 2's seniority list (None until it loads)
status_bits = []  # short "N pilots loaded" messages

if source1 is not None:  # a list is available for airline 1
    try:  # read it
        SenList1 = parse_seniority_list(source1)  # parse and enrich
        status_bits.append(f"{a1_label}: {len(SenList1)} pilots loaded")  # success message
    except Exception as exc:  # anything wrong with the file
        st.error(f"{a1_label}: {exc}")  # show the problem

if source2 is not None:  # a list is available for airline 2
    try:  # read it
        SenList2 = parse_seniority_list(source2)  # parse and enrich
        status_bits.append(f"{a2_label}: {len(SenList2)} pilots loaded")  # success message
    except Exception as exc:  # anything wrong with the file
        st.error(f"{a2_label}: {exc}")  # show the problem

if status_bits:  # at least one list loaded
    st.caption("   |   ".join(status_bits))  # one small line of status

# ---------- constructive notice date and count ----------
date_col, date_info, _ = st.columns([1.3, 0.5, 6])  # date box | (i) symbol | spare space
with date_col:  # date column
    constructive_notice_date = st.date_input("Constructive Notice Date")  # cut-off date
with date_info:  # (i) column
    st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)  # nudge down to line up with the date box
    info_popover("notice", NOTICE_INFO)  # explanation

if st.button("COUNT CATEGORIES"):  # the user wants the Equip / Rank counts
    if SenList1 is None or SenList2 is None:  # lists missing
        st.error("Upload both seniority lists before counting categories.")  # explain
    else:  # both lists loaded
        st.session_state["count_info1"] = count_categories(SenList1, constructive_notice_date)  # airline 1 counts
        st.session_state["count_info2"] = count_categories(SenList2, constructive_notice_date)  # airline 2 counts

count_info1 = st.session_state.get("count_info1")  # saved counts for airline 1
count_info2 = st.session_state.get("count_info2")  # saved counts for airline 2
count_grand = [None, None]  # grand totals (None until counted)
if count_info1 is not None and count_info2 is not None:  # counts exist
    count_grand = [int(count_info1["table"].to_numpy().sum()), int(count_info2["table"].to_numpy().sum())]  # grand totals

# ---------- define integration parameters ----------
st.divider()  # thin line
head2_col, head2_info, _ = st.columns([4.2, 0.5, 6])  # heading | (i) symbol | spare space
with head2_col:  # heading column
    st.subheader("Define Integration Parameters")  # section heading
with head2_info:  # (i) column
    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)  # nudge down to line up with the heading
    info_popover("methods", METHODOLOGY_INFO)  # historical integration methodologies

# The slider runs Status and Category (left, 0) -> Longevity (right, 100), so its value IS the Longevity %.
longevity_pct = st.session_state.get("integration_weight", 50)  # slider's current value
category_pct = 100 - longevity_pct  # the rest goes to Status and Category

ENTRY_W = [1.3, 1, 1, 1.5]  # category table columns: label | airline 1 | airline 2 | spare

left_half, count_block = st.columns([1, 1])  # left: weighting + category entry | right: Category Count tables (starts level with Weighting)
with left_half:  # left half
    # "Weighting" and its (i) sit on one line, close together; the slider is as wide as the two airline columns of the table below
    w_label, w_slider, _w1 = st.columns([1.3, 2, 1.5])  # label + (i) | slider | spare
    with w_label:  # label column
        with st.container(horizontal=True, gap="xxsmall"):  # lay the word and the (i) out on one line with a tiny gap
            st.markdown("<div style='font-weight:600; line-height:1.6rem;'>Weighting</div>", unsafe_allow_html=True)  # label text
            info_popover("weight", WEIGHT_INFO)  # explanation, right beside the word
    with w_slider:  # slider column
        st.markdown(  # big percentages above the slider
            "<div style='display:flex; justify-content:space-between; font-size:2rem; font-weight:500;'>"  # left and right ends
            f"<span>{category_pct}%</span><span>{longevity_pct}%</span></div>",  # Status and Category % | Longevity %
            unsafe_allow_html=True,  # allow the HTML
        )  # end markdown
        st.markdown(  # captions, with a little space below them before the slider
            "<div style='display:flex; justify-content:space-between; font-size:14px; margin-bottom:0.6rem;'>"  # left and right ends
            "<span>Status and Category</span><span>Longevity</span></div>",  # the two ends of the slider
            unsafe_allow_html=True,  # allow the HTML
        )  # end markdown
        st.slider(  # the weighting slider
            "Status and Category \u2194 Longevity",  # accessibility label (hidden)
            min_value=0, max_value=100, value=50,  # 0-100, starting at 50
            label_visibility="collapsed",  # hide the label
            key="integration_weight",  # remembered under this key
        )  # end slider

    CategoryWeight = category_pct / 100  # weight on the Status and Category list (0-1)
    LongevityWeight = longevity_pct / 100  # weight on the Longevity list (0-1)

    category_counts = {n: {"airline1": 0, "airline2": 0} for n in range(1, 7)}  # numbers typed into the category boxes
    entries_valid = True  # becomes False if a box is not a whole number

    hdr = st.columns(ENTRY_W)  # heading row
    hdr[0].markdown("<div style='line-height:1.9rem; font-weight:600;'>Category</div>", unsafe_allow_html=True)  # first heading
    hdr[1].markdown(  # airline 1 name chip
        f"<div class='catchip' style='background-color:{airline1_color}; color:{_text_color_for(airline1_color)};'>"  # chip colours
        f"{html.escape(a1_label)}</div>",  # airline name
        unsafe_allow_html=True,  # allow the HTML
    )  # end markdown
    hdr[2].markdown(  # airline 2 name chip
        f"<div class='catchip' style='background-color:{airline2_color}; color:{_text_color_for(airline2_color)};'>"  # chip colours
        f"{html.escape(a2_label)}</div>",  # airline name
        unsafe_allow_html=True,  # allow the HTML
    )  # end markdown
    st.markdown("<div style='height:0.7rem'></div>", unsafe_allow_html=True)  # extra space under the heading row
    for n in range(1, 7):  # categories 1 to 6
        row = st.columns(ENTRY_W)  # one row
        row[0].markdown(f"<div style='line-height:1.5rem;'>Category {n}</div>", unsafe_allow_html=True)  # row label
        for j, who in enumerate(("airline1", "airline2")):  # both airlines
            text = row[j + 1].text_input(  # small entry box (same height as the name chip)
                f"{who} category {n}", value="0", key=f"cat_{n}_{who}",  # label (hidden), start at 0, remembered key
                label_visibility="collapsed", max_chars=6,  # hide label, at most 6 characters
            )  # end text_input
            value, ok = parse_count_text(text)  # convert the text to a number
            category_counts[n][who] = value  # store it
            entries_valid = entries_valid and ok  # remember any invalid entry

    entered, _valid = entered_category_totals()  # totals of the boxes
    tot_row = st.columns(ENTRY_W)  # totals row
    tot_row[0].markdown("<div style='line-height:1.9rem; font-weight:700;'>Total</div>", unsafe_allow_html=True)  # label
    tot_row[1].markdown(f"<div style='text-align:center; font-weight:700;'>{entered[0]}</div>", unsafe_allow_html=True)  # airline 1 total
    tot_row[2].markdown(f"<div style='text-align:center; font-weight:700;'>{entered[1]}</div>", unsafe_allow_html=True)  # airline 2 total

    if not entries_valid:  # a box holds something other than a whole number
        small_red("Category boxes must contain whole numbers.")  # explain
    for who_label, total_entered, needed in ((a1_label, entered[0], count_grand[0]), (a2_label, entered[1], count_grand[1])):  # each airline
        if needed is not None and total_entered != needed:  # counts exist and disagree with the boxes
            small_red(f"{html.escape(who_label)}: categories add up to {total_entered}, but the count is {needed}.")  # explain

    check_col, check_info, _ = st.columns([2, 0.6, 2])  # checkbox | (i) symbol | spare space
    with check_col:  # checkbox column
        exclude_inactive = st.checkbox("Exclude Inactive Periods")  # ignore inactivity in the longevity list
    with check_info:  # (i) column
        info_popover("inactive", INACTIVE_INFO)  # explanation

    ra_col, _ = st.columns([1.3, 2.7])  # narrow box for the retirement age
    with ra_col:  # box column
        retirement_age = st.text_input("Normal Retirement Age", value=DEFAULT_RETIREMENT_AGE, key="retirement_age", max_chars=3)  # not used yet
    retirement_ok = retirement_age.strip().isdigit()  # must be a whole number
    if not retirement_ok:  # not a whole number
        small_red("Normal Retirement Age must be a whole number.")  # explain

with count_block:  # right half
    if count_info1 is not None and count_info2 is not None:  # counts exist
        st.markdown("<div style='font-size:1.2rem; font-weight:700;'>Category Count</div>", unsafe_allow_html=True)  # title above the tables
        t_left, t_right = st.columns(2)  # one table per airline
        with t_left:  # airline 1 table
            st.markdown(f"**{a1_label}**")  # airline name
            st.markdown(count_table_html(count_info1, entered[0], airline1_color), unsafe_allow_html=True)  # tinted count table
        with t_right:  # airline 2 table
            st.markdown(f"**{a2_label}**")  # airline name
            st.markdown(count_table_html(count_info2, entered[1], airline2_color), unsafe_allow_html=True)  # tinted count table

# ANALYZE / EXPORT share the width of the parameters block (about half the screen)
button_block, _ = st.columns([1, 1])  # left half
with button_block:  # left half
    btn_left, btn_right = st.columns(2)  # two buttons side by side
    with btn_left:  # left button
        analyze_clicked = st.button("ANALYZE", width="stretch")  # run the integration
    with btn_right:  # right button
        export_clicked = st.button("EXPORT", width="stretch")  # export the results

# ======================================================================
# Analyze
# ======================================================================
if analyze_clicked:  # the user pressed ANALYZE
    if SenList1 is None or SenList2 is None:  # lists missing
        st.error("Upload both seniority lists before running Analyze.")  # explain
    elif not entries_valid:  # bad category entries
        st.error("Category boxes must contain whole numbers.")  # explain
    elif not retirement_ok:  # bad retirement age
        st.error("Normal Retirement Age must be a whole number.")  # explain
    elif SenList1["Airline"].iloc[0] == SenList2["Airline"].iloc[0]:  # same airline code in both files
        st.error("Both lists use the same Airline code. Each airline needs its own 3-letter code.")  # explain
    else:  # inputs look sensible
        notice_ts = pd.Timestamp(constructive_notice_date)  # cut-off date as a timestamp
        needed1 = len(SenList1) - int((SenList1["DOH"] > notice_ts).sum())  # categories must cover this many airline 1 pilots
        needed2 = len(SenList2) - int((SenList2["DOH"] > notice_ts).sum())  # categories must cover this many airline 2 pilots
        entered, _valid = entered_category_totals()  # what the user typed
        problems = []  # messages to show
        if entered[0] != needed1:  # airline 1 does not add up
            problems.append(  # explain
                f"{a1_label}: categories add up to {entered[0]}, but {needed1} are needed "  # part 1
                f"({len(SenList1)} pilots minus constructive notice pilots)."  # part 2
            )  # end append
        if entered[1] != needed2:  # airline 2 does not add up
            problems.append(  # explain
                f"{a2_label}: categories add up to {entered[1]}, but {needed2} are needed "  # part 1
                f"({len(SenList2)} pilots minus constructive notice pilots)."  # part 2
            )  # end append
        if problems:  # something does not add up
            for p in problems:  # each message
                st.error(p)  # show it
        else:  # everything adds up
            try:  # run the whole integration
                ConstNotice1, ConstNotice2, ConstNoticeList = Create_ConstNoticeList(  # constructive-notice pilots
                    SenList1, SenList2, constructive_notice_date  # inputs
                )  # end call
                Long1, Long2, LongList = Create_LongList(  # longevity list
                    SenList1, SenList2, ConstNotice1, ConstNotice2, exclude_inactive  # inputs
                )  # end call
                # Category slicing and stovepiping use each airline's list WITHOUT its constructive-notice pilots
                # (they are placed at the bottom separately), so they can never be counted twice.
                Active1 = SenList1[~SenList1["NameID"].isin(ConstNotice1["NameID"])].reset_index(drop=True)  # airline 1 minus notice pilots
                Active2 = SenList2[~SenList2["NameID"].isin(ConstNotice2["NameID"])].reset_index(drop=True)  # airline 2 minus notice pilots
                cat_lists, CategoryList = Create_Category_List(Active1, Active2, category_counts)  # status-and-category list
                HybridList = Create_HybridList(LongList, CategoryList, LongevityWeight, CategoryWeight)  # blended list
                StovepipedList = Create_StovePipedList(HybridList, Active1, Active2)  # keep each airline's own order
                IPSL = Create_IPSL(StovepipedList, ConstNoticeList, SenList1, SenList2)  # final list (all data looked up by NameID)
                IPSL_Abridged = Create_IPSL_Abridged(IPSL)  # short version

                report_data = {  # everything the report tab and the export need
                    "IPSL": IPSL,  # full list
                    "IPSL_Abridged": IPSL_Abridged,  # short list
                    "airline1_name": a1_label,  # airline 1 name
                    "airline2_name": a2_label,  # airline 2 name
                    "airline1_color": airline1_color,  # airline 1 colour
                    "airline2_color": airline2_color,  # airline 2 colour
                    "airline1_code": SenList1["Airline"].iloc[0],  # airline 1 code
                    "airline2_code": SenList2["Airline"].iloc[0],  # airline 2 code
                    "prepared_at": datetime.now().strftime("%Y-%m-%d %H:%M"),  # when the analysis ran
                    "category_counts": category_counts,  # category boxes
                    "n_notice": len(ConstNoticeList),  # all constructive-notice pilots
                    "n_notice1": len(ConstNotice1),  # airline 1's constructive-notice pilots
                    "n_notice2": len(ConstNotice2),  # airline 2's constructive-notice pilots
                    "category_weight_pct": category_pct,  # Status and Category weight (%)
                    "longevity_weight_pct": longevity_pct,  # Longevity weight (%)
                    "exclude_inactive": exclude_inactive,  # checkbox
                    "constructive_notice_date": str(constructive_notice_date),  # cut-off date
                    "retirement_age": retirement_age.strip(),  # Normal Retirement Age (not used yet)
                    "count_info1": count_categories(SenList1, constructive_notice_date),  # airline 1 Category Count table
                    "count_info2": count_categories(SenList2, constructive_notice_date),  # airline 2 Category Count table
                }  # end report_data
                report_id = str(uuid.uuid4())  # unique id for this report
                REPORT_CACHE[report_id] = report_data  # let the new tab fetch it
                st.session_state["report_id"] = report_id  # remember the link
                st.session_state["report_data"] = report_data  # remember the data for EXPORT
                st.session_state.pop("export_files", None)  # forget any earlier export
                st.success("Analysis complete.")  # tell the user
            except ValueError as exc:  # a check inside the analysis failed
                st.error(str(exc))  # show it

if st.session_state.get("report_id"):  # an analysis has been run
    st.markdown(  # link that opens the report in a new tab
        f'<a href="?report_id={st.session_state["report_id"]}" target="_blank" '  # address with the report id
        f'style="font-size:1.05rem; font-weight:600;">Open the integration report in a new tab &#8599;</a>',  # link text
        unsafe_allow_html=True,  # allow the HTML
    )  # end markdown

# ======================================================================
# Export (password protected)
# ======================================================================
if st.session_state.pop("show_bad_password", False):  # the last password was wrong
    bad_password_dialog()  # show the "Password incorrect" box

export_authorized = st.session_state.pop("export_authorized", False)  # True once for one export after a correct password

if export_clicked:  # the user pressed EXPORT
    if st.session_state.get("report_data") is None:  # nothing to export yet
        st.warning("Run ANALYZE first, then EXPORT.")  # explain
    else:  # there is something to export
        export_password_dialog()  # ask for the password

if export_authorized:  # a correct password was just entered
    with st.spinner("Preparing export files..."):  # show progress
        export_files = build_export_files(st.session_state["report_data"])  # build the CSV and PDF
    st.session_state["export_files"] = export_files  # keep them for the fallback links
    run_download_script(auto_download_html(export_files))  # make the browser save both files

if st.session_state.get("export_files"):  # files have been exported
    st.caption("Export ready. If your browser did not save the files automatically, click a file name:")  # fallback note
    for i, (fname, mime, payload) in enumerate(st.session_state["export_files"]):  # each file
        st.download_button(fname, payload, file_name=fname, mime=mime, key=f"dl_{i}", type="tertiary")  # plain text link