

import streamlit as st

import pandas as pd

import numpy as np

import zipfile

import io

import re

from pathlib import Path

import plotly.express as px





# ==========================================

# PAGE CONFIGURATION

# ==========================================







st.set_page_config(

    page_title="SupeRR Selector",

    layout="wide"

)



st.markdown("""

<style>

@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800&display=swap');



.stApp {

    background: linear-gradient(135deg, #E83E83 0%, #17479E 100%);

}



.stApp p,

.stApp label,

.stApp span,

.stApp li {

    color: #FFFFFF !important;

}



h1, h2, h3 {

    color: #FFFFFF !important;

}



[data-testid="stSidebar"] {

    background-color: #17479E;

}



[data-testid="stSidebar"] * {

    color: #FFFFFF !important;

}



[data-testid="stMetric"] {

    background: linear-gradient(135deg, #17479E, #C92B70);

    padding: 18px;

    border-radius: 14px;

    border: 1px solid #FFFFFF;

}



[data-testid="stMetricLabel"],

[data-testid="stMetricValue"],

[data-testid="stMetricDelta"] {

    color: #FFFFFF !important;

}



.stButton button {

    background-color: #17479E;

    color: #FFFFFF !important;

    border: 1px solid #FFFFFF;

    border-radius: 8px;

}



.stButton button:hover {

    background-color: #C92B70;

    border-color: #FFFFFF;

}



[data-testid="stExpander"] {

    background-color: #17479E;

    border: 1px solid #FFFFFF;

    border-radius: 10px;

}



[data-testid="stExpander"] * {

    color: #FFFFFF !important;

}



.stTabs [data-baseweb="tab"] {

    color: #FFFFFF !important;

}



.stTabs [aria-selected="true"] {

    border-bottom-color: #FFFFFF !important;

}



hr {

    border-color: #FFFFFF !important;

}



.royals-title {

    font-family: 'Cinzel', Georgia, serif !important;

    font-size: 48px !important;

    font-weight: 800 !important;

    letter-spacing: 4px;

    color: #FFFFFF !important;

    text-align: center;

    text-shadow: 2px 2px 5px #17479E;

}

</style>

""", unsafe_allow_html=True)



left, center, right = st.columns([1, 1, 1])



with center:

    st.image("rajasthan_royals_logo.png", width=140)



st.markdown("""

<h1 class="royals-title">

RAJASTHAN ROYALS

</h1>

""", unsafe_allow_html=True)



st.markdown(

    "<h3 style='text-align:center; color:white !important; "

    "font-family:Georgia,serif; font-size:23px;'>"

    "Identifying the Most Reliable Players Under Pressure"

    "</h3>",

    unsafe_allow_html=True

)



st.markdown("<br>", unsafe_allow_html=True)







# ==========================================

# CONFIGURATION

# ==========================================



MIN_BATTER_TOTAL_RUNS = 600



MIN_BATTER_TOTAL_RUNS = 600

MIN_BATTER_TOTAL_BALLS = 60

MIN_BATTER_PRESSURE_RUNS = 150



MIN_PRESSURE_BALLS = 120

MIN_NORMAL_BALLS = 42



MIN_BOWLER_PRESSURE_WICKETS = 25



PRESSURE_THRESHOLD = 0.60





# ==========================================

# ZIP DATA LOADING

# ==========================================



def _clean_column_name(name):
    """Convert column labels to a comparable lowercase alphanumeric form."""
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


COLUMN_ALIASES = {
    "match_id": ["matchid", "match", "gameid", "fixtureid"],
    "striker_id": ["strikerid", "batterid", "batsmanid", "playerid"],
    "striker_name": ["strikername", "battername", "batsmanname", "batter", "batsman", "striker"],
    "bowler_id": ["bowlerid", "bowlerplayerid"],
    "bowler_name": ["bowlername", "bowler"],
    "runs": ["runs", "batterruns", "batsmanruns", "runsoffbat", "runsbatter", "runsscoredbybatter"],
    "total_runs": ["totalruns", "deliveryruns", "runstotal"],
    "extras1_runs": ["extras1runs", "extraruns", "extrasruns", "totalextras", "extratotal"],
    "extras_2_runs": ["extras2runs", "byeruns", "legbyeruns", "penaltyruns"],
    "extras_type": ["extrastype", "extras", "extrakind"],
    "innings_ball_num": ["inningsballnum", "deliverynumber", "ballnumber", "ballno", "deliveryno"],
    "innings": ["innings", "inningsnum", "inning", "inningnumber"],
    "is_wicket": ["iswicket", "wicket", "wicketflag", "dismissed"],
    "dismissal_type": ["dismissaltype", "wicketkind", "dismissal", "kind"],
    "player_dismissed": ["playerdismissed", "dismissedplayer"],
    "is_four": ["isfour", "four", "boundaryfour"],
    "is_six": ["issix", "six", "boundarysix"],
    "comp_id": ["compid", "competitionid", "tournamentid", "seriesid"],
    "comp_name": ["compname", "competitionname", "tournamentname", "seriesname"],
    "match_date": ["matchdate", "date", "gamedate", "startdate"],
    "venue_country": ["venuecountry", "country", "venue"],
    "revised_target": ["revisedtarget", "target", "targetruns", "chasingtarget"],
    "first_inn_revised_overs": ["firstinnrevisedovers", "firstinningsovers", "revisedoversfirstinnings"],
    "second_inn_revised_overs": ["secondinnrevisedovers", "secondinningsovers", "revisedoverssecondinnings"],
    "match_format": ["matchformat", "format", "gametype"],
    "season": ["season", "seasonname", "year"],
}


def standardize_columns(frame):
    """Rename common cricket-data column variants to the app's standard schema."""
    frame = frame.copy()
    lookup = {_clean_column_name(col): col for col in frame.columns}
    rename = {}
    for standard_name, aliases in COLUMN_ALIASES.items():
        if standard_name in frame.columns:
            continue
        candidates = [_clean_column_name(standard_name)] + aliases
        for candidate in candidates:
            original = lookup.get(candidate)
            if original is not None and original not in rename:
                rename[original] = standard_name
                break
    return frame.rename(columns=rename)


def _classify_csv(frame):
    """Classify a CSV from its columns, not from its filename."""
    cols = set(frame.columns)
    has_match = "match_id" in cols
    has_batter = any(c in cols for c in ["striker_id", "striker_name"])
    has_bowler = any(c in cols for c in ["bowler_id", "bowler_name"])
    has_runs = "runs" in cols or "total_runs" in cols
    if has_match and has_batter and has_bowler and has_runs:
        return "ball_by_ball"
    if has_match and ("match_date" in cols or "comp_id" in cols or "revised_target" in cols):
        return "matches"
    if "comp_id" in cols and ("comp_name" in cols or "season" in cols or "match_format" in cols):
        return "competitions"
    return None


@st.cache_data(show_spinner=False)
def load_zip_file(file_bytes):
    """Read CSVs from any ZIP and identify cricket tables by their contents."""
    data = {}
    ignored = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
        csv_files = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv")
            and "__macosx" not in name.lower()
            and not name.rsplit("/", 1)[-1].startswith(".")
        ]
        if not csv_files:
            raise ValueError("The ZIP file does not contain any CSV files.")

        for filename in csv_files:
            try:
                with archive.open(filename) as file:
                    frame = pd.read_csv(file)
                frame = standardize_columns(frame)
                table_type = _classify_csv(frame)
                if table_type and table_type not in data:
                    data[table_type] = frame
                else:
                    ignored.append(filename)
            except Exception as error:
                ignored.append(f"{filename} (could not read: {error})")

    if "ball_by_ball" not in data:
        raise ValueError(
            "I couldn't identify a ball-by-ball CSV. The ZIP must contain a CSV "
            "with match ID, batter/striker, bowler and runs columns. "
            "Column names may vary, but the information must be present."
        )

    # Match and competition tables are useful but optional. Create empty tables
    # so the rest of the dashboard can still operate with ball-by-ball data alone.
    identified_tables = [key for key in ["ball_by_ball", "matches", "competitions"] if key in data]
    data.setdefault("matches", pd.DataFrame())
    data.setdefault("competitions", pd.DataFrame())
    data["_upload_info"] = {
        "identified": identified_tables,
        "ignored": ignored,
    }
    return data


# ==========================================
# DATA CLEANING AND INTEGRATION
# ==========================================


def to_number(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def to_boolean(series):
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "yes", "y", "1.0"])
    )


def prepare_data(data):
    ball = standardize_columns(data["ball_by_ball"])
    matches = standardize_columns(data.get("matches", pd.DataFrame()))
    competitions = standardize_columns(data.get("competitions", pd.DataFrame()))

    # Names can act as IDs when a dataset does not provide separate player IDs.
    if "striker_name" not in ball.columns and "striker_id" not in ball.columns:
        raise ValueError("The ball-by-ball CSV needs a batter/striker name or ID column.")
    if "bowler_name" not in ball.columns and "bowler_id" not in ball.columns:
        raise ValueError("The ball-by-ball CSV needs a bowler name or ID column.")
    if "match_id" not in ball.columns:
        raise ValueError("The ball-by-ball CSV needs a match ID column to separate matches.")

    if "striker_id" not in ball.columns:
        ball["striker_id"] = ball["striker_name"].astype(str)
    if "striker_name" not in ball.columns:
        ball["striker_name"] = ball["striker_id"].astype(str)
    if "bowler_id" not in ball.columns:
        ball["bowler_id"] = ball["bowler_name"].astype(str)
    if "bowler_name" not in ball.columns:
        ball["bowler_name"] = ball["bowler_id"].astype(str)

    # If only total delivery runs are supplied, derive batter runs by removing extras.
    if "runs" not in ball.columns:
        if "total_runs" not in ball.columns:
            raise ValueError("The ball-by-ball CSV needs batter runs or total runs.")
        extras_source = ball["extras1_runs"] if "extras1_runs" in ball.columns else pd.Series(0, index=ball.index)
        extras_second = ball["extras_2_runs"] if "extras_2_runs" in ball.columns else pd.Series(0, index=ball.index)
        ball["runs"] = to_number(ball["total_runs"]) - to_number(extras_source) - to_number(extras_second)

    if "match_id" not in ball.columns:
        raise ValueError("The ball-by-ball CSV needs a match ID column.")

    if "innings_ball_num" not in ball.columns:
        ball["innings_ball_num"] = ball.groupby(["match_id"]).cumcount() + 1

    for col in ["runs", "extras1_runs", "extras_2_runs", "innings_ball_num"]:
        if col in ball.columns:
            ball[col] = to_number(ball[col])
        else:
            ball[col] = 0

    # When a source provides total runs and batter runs but no extras column,
    # recover the extras amount rather than silently treating it as zero.
    if "total_runs" in ball.columns and "extras1_runs" not in standardize_columns(data["ball_by_ball"]).columns:
        ball["extras1_runs"] = (to_number(ball["total_runs"]) - ball["runs"]).clip(lower=0)

    ball["total_extras"] = ball["extras1_runs"] + ball["extras_2_runs"]

    if "extras_type" in ball.columns:
        ball["extras_type_clean"] = ball["extras_type"].fillna("").astype(str).str.lower().str.strip()
    else:
        ball["extras_type_clean"] = ""

    ball["is_wide"] = ball["extras_type_clean"].str.contains(r"wide|wides", regex=True)
    ball["is_noball"] = ball["extras_type_clean"].str.contains(r"no.?ball|noball|overstep", regex=True)
    ball["batter_ball"] = ~ball["is_wide"]
    ball["legal_ball"] = ~(ball["is_wide"] | ball["is_noball"])
    ball["bowler_runs"] = ball["runs"]
    charged_extras = ball["is_wide"] | ball["is_noball"]
    ball.loc[charged_extras, "bowler_runs"] += ball.loc[charged_extras, "total_extras"]

    if "is_wicket" in ball.columns:
        ball["is_wicket"] = to_boolean(ball["is_wicket"])
    elif "player_dismissed" in ball.columns:
        ball["is_wicket"] = ball["player_dismissed"].notna() & ball["player_dismissed"].astype(str).str.strip().ne("")
    elif "dismissal_type" in ball.columns:
        ball["is_wicket"] = ball["dismissal_type"].notna() & ball["dismissal_type"].astype(str).str.strip().ne("")
    else:
        ball["is_wicket"] = False

    if "dismissal_type" in ball.columns:
        ball["dismissal_type_clean"] = ball["dismissal_type"].fillna("").astype(str).str.lower().str.strip()
    else:
        ball["dismissal_type_clean"] = ""

    non_bowler_dismissals = [
        "run out", "retired hurt", "retired out", "obstructing the field",
        "handled the ball", "hit the ball twice"
    ]
    ball["bowler_wicket"] = ball["is_wicket"] & ~ball["dismissal_type_clean"].isin(non_bowler_dismissals)

    for col in ["is_four", "is_six"]:
        if col in ball.columns:
            ball[col] = to_boolean(ball[col])
        elif col == "is_four":
            ball[col] = ball["runs"].eq(4)
        else:
            ball[col] = ball["runs"].eq(6)

    # Merge match metadata only when a usable match table was detected.
    match_columns = [col for col in [
        "match_id", "comp_id", "match_date", "venue_country", "revised_target",
        "first_inn_revised_overs", "second_inn_revised_overs"
    ] if col in matches.columns]
    if "match_id" in match_columns:
        match_info = matches[match_columns].drop_duplicates(subset=["match_id"]).copy()
        ball = ball.merge(match_info, on="match_id", how="left", suffixes=("", "_match"))

    # Merge competition metadata when available.
    if "comp_id" in ball.columns and "comp_id" in competitions.columns:
        competition_columns = [
            col for col in ["comp_id", "comp_name", "match_format", "season"]
            if col in competitions.columns and (col == "comp_id" or col not in ball.columns)
        ]
        if len(competition_columns) > 1:
            competition_info = competitions[competition_columns].drop_duplicates(subset=["comp_id"])
            ball = ball.merge(competition_info, on="comp_id", how="left")

    if "season" not in ball.columns:
        if "match_date" in ball.columns:
            dates = pd.to_datetime(ball["match_date"], errors="coerce")
            ball["season"] = dates.dt.year.astype("Int64").astype(str).replace("<NA>", "Unknown")
        else:
            ball["season"] = "Unknown"
    else:
        ball["season"] = ball["season"].fillna("Unknown").astype(str)

    if "comp_name" not in ball.columns:
        if "comp_id" in ball.columns:
            ball["comp_name"] = ball["comp_id"].fillna("Unknown competition").astype(str)
        else:
            ball["comp_name"] = "Unknown competition"
    else:
        ball["comp_name"] = ball["comp_name"].fillna("Unknown competition").astype(str)

    ball["striker_name"] = ball["striker_name"].fillna(ball["striker_id"].astype(str))
    ball["bowler_name"] = ball["bowler_name"].fillna(ball["bowler_id"].astype(str))
    return ball
# ==========================================

# PRESSURE CALCULATION ENGINE

# ==========================================



def calculate_pressure(df):



    df = df.copy()



    df["innings_number"] = 1



    innings_col = None



    for col in ["innings", "innings_num", "inning"]:



        if col in df.columns:

            innings_col = col

            break



    if innings_col:

        df["innings_number"] = to_number(

            df[innings_col]

        ).astype(int)



    # Legal balls so far



    df["legal_balls_so_far"] = (

        df.groupby(["match_id", "innings_number"])["legal_ball"]

        .transform(lambda x: x.astype(int).cumsum())

    )



    # Wickets lost



    df["wickets_lost"] = (

        df.groupby(["match_id", "innings_number"])["is_wicket"]

        .transform(lambda x: x.astype(int).cumsum())

    )



    df["wickets_lost"] = df["wickets_lost"].clip(upper=10)



    # Overs limit



    df["over_limit"] = 20



    if "first_inn_revised_overs" in df.columns:



        df.loc[

            df["innings_number"] == 1,

            "over_limit"

        ] = df.loc[

            df["innings_number"] == 1,

            "first_inn_revised_overs"

        ].fillna(20)



    if "second_inn_revised_overs" in df.columns:



        df.loc[

            df["innings_number"] == 2,

            "over_limit"

        ] = df.loc[

            df["innings_number"] == 2,

            "second_inn_revised_overs"

        ].fillna(20)



    df["over_limit"] = pd.to_numeric(

        df["over_limit"],

        errors="coerce"

    ).fillna(20).clip(lower=1, upper=20)



    df["total_balls"] = df["over_limit"] * 6



    df["progress"] = (

        df["legal_balls_so_far"] /

        df["total_balls"]

    ).clip(0, 1)



    df["wicket_pressure"] = (

        df["wickets_lost"] / 10

    ).clip(0, 1)



    # First innings pressure



    first_innings_score = (

        0.50 * df["wicket_pressure"] +

        0.50 * df["progress"]

    )



    df["pressure_score"] = first_innings_score



    # Second innings pressure



    second_innings = df["innings_number"] == 2



    if "revised_target" in df.columns:



        target = pd.to_numeric(

            df["revised_target"],

            errors="coerce"

        )



        cumulative_runs = (

            df.groupby(["match_id", "innings_number"])["runs"]

            .cumsum()

        )



        runs_before_ball = (

            cumulative_runs - df["runs"]

        )



        runs_remaining = (

            target - runs_before_ball

        ).clip(lower=0)



        balls_remaining = (

            df["total_balls"] -

            df["legal_balls_so_far"] +

            df["legal_ball"].astype(int)

        ).clip(lower=1)



        required_run_rate = (

            runs_remaining / balls_remaining

        ) * 6



        rrr_pressure = (

            required_run_rate / 12

        ).clip(0, 1)



        chase_pressure = (

            0.40 * rrr_pressure +

            0.30 * df["wicket_pressure"] +

            0.30 * df["progress"]

        )



        df.loc[

            second_innings & target.notna(),

            "pressure_score"

        ] = chase_pressure[

            second_innings & target.notna()

        ]



    # Final classification



    df["pressure_score"] = (

        df["pressure_score"].fillna(0).clip(0, 1)

    )



    df["pressure_category"] = np.where(

        df["pressure_score"] >= PRESSURE_THRESHOLD,

        "Pressure",

        "Normal"

    )



    return df





# ==========================================

# SCORING FUNCTION

# ==========================================



def score_0_to_100(series, higher_is_better=True):



    values = pd.to_numeric(

        series,

        errors="coerce"

    ).fillna(0)



    low = values.min()

    high = values.max()



    if high == low:

        return pd.Series(50.0, index=series.index)



    scores = (values - low) / (high - low) * 100



    if not higher_is_better:

        scores = 100 - scores



    return scores





# ==========================================

def format_minmax_score_calculation(value, eligible_values, higher_is_better=True):
    """Return the exact 0–100 min–max calculation shown in the UI."""
    values = pd.to_numeric(eligible_values, errors="coerce").fillna(0)
    low = float(values.min())
    high = float(values.max())
    value = float(value)

    if high == low:
        return "all eligible values are equal; score = 50.00"

    scaled = (value - low) / (high - low) * 100
    if higher_is_better:
        return (
            f"({value:.3f} − {low:.3f}) ÷ ({high:.3f} − {low:.3f}) "
            f"× 100 = {scaled:.2f}"
        )
    return (
        f"100 − [({value:.3f} − {low:.3f}) ÷ ({high:.3f} − {low:.3f}) "
        f"× 100] = {100 - scaled:.2f}"
    )


# BATTER PERFORMANCE ANALYSIS

# ==========================================



def calculate_batter_ratings(df):



    bat = df.copy()



    grouped = (

        bat.groupby([

            "striker_id",

            "striker_name",

            "pressure_category"

        ])

        .agg(

            runs=("runs", "sum"),

            balls=("batter_ball", "sum"),

            fours=("is_four", "sum"),

            sixes=("is_six", "sum"),

            dismissals=("is_wicket", "sum")

        )

        .reset_index()

    )



    grouped["strike_rate"] = np.where(

        grouped["balls"] > 0,

        grouped["runs"] / grouped["balls"] * 100,

        0

    )



    grouped["boundary_percentage"] = np.where(

        grouped["runs"] > 0,

        (

            grouped["fours"] * 4 +

            grouped["sixes"] * 6

        ) / grouped["runs"] * 100,

        0

    )



    grouped["dismissal_rate"] = np.where(

        grouped["balls"] > 0,

        grouped["dismissals"] / grouped["balls"] * 100,

        0

    )



    pressure = grouped[

        grouped["pressure_category"] == "Pressure"

    ].copy()



    normal = grouped[

        grouped["pressure_category"] == "Normal"

    ].copy()



    pressure = pressure.rename(columns={

        "runs": "pressure_runs",

        "balls": "pressure_balls",

        "strike_rate": "pressure_sr",

        "boundary_percentage": "pressure_boundary",

        "dismissals": "pressure_dismissals",

        "dismissal_rate": "pressure_dismissal_rate"

    })



    normal = normal.rename(columns={

        "runs": "normal_runs",

        "balls": "normal_balls",

        "strike_rate": "normal_sr",

        "boundary_percentage": "normal_boundary",

        "dismissals": "normal_dismissals",

        "dismissal_rate": "normal_dismissal_rate"

    })



    result = pressure.merge(

        normal[[

            "striker_id",

            "normal_runs",

            "normal_balls",

            "normal_sr",

            "normal_boundary",

            "normal_dismissals",

            "normal_dismissal_rate"

        ]],

        on="striker_id",

        how="inner"

    )



    totals = (

        bat.groupby("striker_id")

        .agg(

            total_runs=("runs", "sum"),

            total_balls=("batter_ball", "sum")

        )

        .reset_index()

    )



    result = result.merge(

        totals,

        on="striker_id",

        how="left"

    )



    # Eligibility criteria



    result = result[

        (result["total_runs"] >= MIN_BATTER_TOTAL_RUNS) &

        (result["total_balls"] >= MIN_BATTER_TOTAL_BALLS) &

        (result["pressure_runs"] >= MIN_BATTER_PRESSURE_RUNS) &

        (result["pressure_balls"] >= MIN_PRESSURE_BALLS) &

        (result["normal_balls"] >= MIN_NORMAL_BALLS)

    ].copy()



    if result.empty:

        return result



    # Pressure-weighted statistics



    result["weighted_sr"] = (

        0.70 * result["pressure_sr"] +

        0.30 * result["normal_sr"]

    )



    result["weighted_boundary"] = (

        0.70 * result["pressure_boundary"] +

        0.30 * result["normal_boundary"]

    )



    result["weighted_dismissal_rate"] = (

        0.70 * result["pressure_dismissal_rate"] +

        0.30 * result["normal_dismissal_rate"]

    )



    # Convert metrics to 0-100 scores



    result["sr_score"] = score_0_to_100(

        result["weighted_sr"],

        True

    )



    result["boundary_score"] = score_0_to_100(

        result["weighted_boundary"],

        True

    )



    result["dismissal_score"] = score_0_to_100(

        result["weighted_dismissal_rate"],

        False

    )



    # Confidence = Pressure Balls / Normal Balls



    result["confidence"] = np.where(

        result["normal_balls"] > 0,

        result["pressure_balls"] / (result["pressure_balls"] + result["normal_balls"]),

        0

    )



    result["confidence_percentage"] = (

        result["confidence"] * 100

    )



    result["pressure_experience_ratio"] = (

        result["confidence_percentage"]

    )



    # Raw batter rating



    result["raw_rating"] = (

        0.45 * result["sr_score"] +

        0.25 * result["boundary_score"] +

        0.30 * result["dismissal_score"]

    )



    # Final reliability rating



    result["reliability_rating"] = (

        result["raw_rating"] * result["confidence"]

    )



    result = result.sort_values(

        "reliability_rating",

        ascending=False

    ).reset_index(drop=True)



    result["rank"] = result.index + 1



    return result





# ==========================================

# BOWLER PERFORMANCE ANALYSIS

# ==========================================



def calculate_bowler_ratings(df):



    bowl = df.copy()



    bowl["dot_ball"] = (

        (bowl["runs"] + bowl["total_extras"] == 0) &

        bowl["legal_ball"]

    )



    grouped = (

        bowl.groupby([

            "bowler_id",

            "bowler_name",

            "pressure_category"

        ])

        .agg(

            runs_conceded=("bowler_runs", "sum"),

            legal_balls=("legal_ball", "sum"),

            wickets=("bowler_wicket", "sum"),

            dot_balls=("dot_ball", "sum")

        )

        .reset_index()

    )



    grouped["economy"] = np.where(

        grouped["legal_balls"] > 0,

        grouped["runs_conceded"] /

        grouped["legal_balls"] * 6,

        0

    )



    grouped["wickets_per_100"] = np.where(

        grouped["legal_balls"] > 0,

        grouped["wickets"] /

        grouped["legal_balls"] * 100,

        0

    )



    grouped["dot_percentage"] = np.where(

        grouped["legal_balls"] > 0,

        grouped["dot_balls"] /

        grouped["legal_balls"] * 100,

        0

    )



    pressure = grouped[

        grouped["pressure_category"] == "Pressure"

    ].copy()



    normal = grouped[

        grouped["pressure_category"] == "Normal"

    ].copy()



    pressure = pressure.rename(columns={

        "runs_conceded": "pressure_runs",

        "legal_balls": "pressure_balls",

        "wickets": "pressure_wickets",

        "economy": "pressure_economy",

        "wickets_per_100": "pressure_wickets_per_100",

        "dot_percentage": "pressure_dot_percentage"

    })



    normal = normal.rename(columns={

        "runs_conceded": "normal_runs",

        "legal_balls": "normal_balls",

        "wickets": "normal_wickets",

        "economy": "normal_economy",

        "wickets_per_100": "normal_wickets_per_100",

        "dot_percentage": "normal_dot_percentage"

    })



    result = pressure.merge(

        normal[[

            "bowler_id",

            "normal_runs",

            "normal_balls",

            "normal_wickets",

            "normal_economy",

            "normal_wickets_per_100",

            "normal_dot_percentage"

        ]],

        on="bowler_id",

        how="inner"

    )



    # Eligibility criteria



    result = result[

        (result["pressure_balls"] >= MIN_PRESSURE_BALLS) &

        (result["normal_balls"] >= MIN_NORMAL_BALLS) &

        (result["pressure_wickets"] >= MIN_BOWLER_PRESSURE_WICKETS)

    ].copy()



    if result.empty:

        return result



    # Pressure-weighted statistics



    result["weighted_economy"] = (

        0.70 * result["pressure_economy"] +

        0.30 * result["normal_economy"]

    )



    result["weighted_wickets_per_100"] = (

        0.70 * result["pressure_wickets_per_100"] +

        0.30 * result["normal_wickets_per_100"]

    )



    result["weighted_dot_percentage"] = (

        0.70 * result["pressure_dot_percentage"] +

        0.30 * result["normal_dot_percentage"]

    )



    # Convert metrics to 0-100 scores



    result["economy_score"] = score_0_to_100(

        result["weighted_economy"],

        False

    )



    result["wicket_score"] = score_0_to_100(

        result["weighted_wickets_per_100"],

        True

    )



    result["dot_score"] = score_0_to_100(

        result["weighted_dot_percentage"],

        True

    )



    # Confidence = Pressure Legal Balls / Normal Legal Balls



    result["confidence"] = np.where(

        (result["pressure_balls"] + result["normal_balls"]) > 0,

        result["pressure_balls"] / (

            result["pressure_balls"] + result["normal_balls"]

        ),

        0

    )



    result["confidence_percentage"] = (

        result["confidence"] * 100

    )



    result["pressure_experience_ratio"] = (

        result["confidence_percentage"]

    )



    # Raw bowler rating



    result["raw_rating"] = (

        0.40 * result["economy_score"] +

        0.35 * result["wicket_score"] +

        0.25 * result["dot_score"]

    )



    # Final reliability rating



    result["reliability_rating"] = (

        result["raw_rating"] * result["confidence"]

    )



    result = result.sort_values(

        "reliability_rating",

        ascending=False

    ).reset_index(drop=True)



    result["rank"] = result.index + 1



    return result





# ==========================================

# STREAMLIT DASHBOARD

# ==========================================



st.sidebar.title("⚙️ Dashboard Settings")





# ==========================================

# LOAD DATASET

# ==========================================



uploaded_zip = st.sidebar.file_uploader(

    "Upload Cricket Dataset (ZIP)",

    type=["zip"],

    help=(
        "Upload a ZIP containing cricket CSV files. The app identifies "
        "ball-by-ball, match and competition data from their column headers; "
        "filenames do not need to follow a fixed naming convention."
    )

)



if uploaded_zip is None:

    st.info("Upload your cricket dataset ZIP in the sidebar to start the analysis.")

    st.stop()



try:

    with st.spinner("Loading cricket dataset..."):

        data = load_zip_file(uploaded_zip.getvalue())

        upload_info = data.get("_upload_info", {})

        df = prepare_data(data)

        df = calculate_pressure(df)

except Exception as error:

    st.error(f"Dataset loading failed: {error}")

    st.stop()





# ==========================================

# DATASET VALIDATION

# ==========================================



st.sidebar.success("Dataset loaded successfully")

if upload_info.get("identified"):
    st.sidebar.caption("Detected data: " + ", ".join(upload_info["identified"]))

if upload_info.get("ignored"):
    with st.expander("CSV files not used by the analysis"):
        st.write(upload_info["ignored"])



if not any(

    col in df.columns

    for col in ["innings", "innings_num", "inning"]

):



    st.warning(

        "No recognised innings column was found. "

        "The current pressure model may classify all deliveries "

        "as first-innings deliveries. Verify the innings column "

        "before trusting the rankings."

    )





# ==========================================

# FILTERS

# ==========================================



st.sidebar.header("Dataset Filters")



filtered_df = df.copy()



if "season" in filtered_df.columns:



    seasons = sorted(

        filtered_df["season"]

        .dropna()

        .astype(str)

        .unique()

    )



    selected_seasons = st.sidebar.multiselect(

        "Select Seasons",

        seasons,

        default=seasons

    )



    if selected_seasons:



        filtered_df = filtered_df[

            filtered_df["season"].astype(str).isin(selected_seasons)

        ]



    else:

        filtered_df = filtered_df.iloc[0:0]



if "comp_name" in filtered_df.columns:



    competitions = sorted(

        filtered_df["comp_name"]

        .dropna()

        .astype(str)

        .unique()

    )



    selected_competitions = st.sidebar.multiselect(

        "Select Competitions",

        competitions,

        default=competitions

    )



    if selected_competitions:



        filtered_df = filtered_df[

            filtered_df["comp_name"].astype(str).isin(

                selected_competitions

            )

        ]



    else:

        filtered_df = filtered_df.iloc[0:0]





# ==========================================

# CALCULATE PLAYER RATINGS

# ==========================================



batting_results = calculate_batter_ratings(filtered_df)



bowling_results = calculate_bowler_ratings(filtered_df)





# ==========================================

# OVERVIEW

# ==========================================



st.header("📊 Tournament Overview")



col1, col2, col3, col4 = st.columns(4)



col1.metric(

    "Total Deliveries",

    f"{len(filtered_df):,}"

)



col2.metric(

    "Matches",

    f"{filtered_df['match_id'].nunique():,}"

)



col3.metric(

    "Pressure Deliveries",

    f"{(filtered_df['pressure_category'] == 'Pressure').sum():,}"

)



col4.metric(

    "Normal Deliveries",

    f"{(filtered_df['pressure_category'] == 'Normal').sum():,}"

)



st.divider()





# ==========================================

# PLAYER RANKINGS

# ==========================================



st.header("🏆 Most Reliable Players Under Pressure")



tab1, tab2, tab3 = st.tabs([

    "🏏 Batters",

    "🎯 Bowlers",

    "🔍 Player Explorer"

])





# ==========================================

# BATTER RANKINGS

# ==========================================



with tab1:



    st.subheader("Top 10 Reliable Batters")



    if batting_results.empty:



        st.info(

            "No batters currently meet all eligibility criteria. "

            "Try selecting more seasons or competitions."

        )



    else:



        top_batters = batting_results.head(10)



        batter_table = top_batters[[

            "rank",

            "striker_name",

            "total_runs",

            "total_balls",

            "pressure_runs",

            "pressure_balls",

            "normal_balls",

            "confidence_percentage",

            "weighted_sr",

            "weighted_boundary",

            "weighted_dismissal_rate",

            "dismissal_score",

            "reliability_rating"

        ]].rename(columns={

            "rank": "Rank",

            "striker_name": "Batter",

            "total_runs": "Total Runs",

            "total_balls": "Total Balls",

            "pressure_runs": "Pressure Runs",

            "pressure_balls": "Pressure Balls",

            "normal_balls": "Normal Balls",

            "confidence_percentage": "Confidence %",

            "weighted_sr": "Weighted SR (70:30)",

            "weighted_boundary": "Weighted Boundary %",

            "weighted_dismissal_rate": "Weighted Dismissal Rate",

            "dismissal_score": "Dismissal Score",

            "reliability_rating": "Reliability Rating"

        })



        st.dataframe(

            batter_table,

            use_container_width=True,

            hide_index=True

        )



        st.markdown("### Individual Batter Calculations")



        for _, player in top_batters.iterrows():



            with st.expander(

                f"#{int(player['rank'])} - "

                f"{player['striker_name']} | View Calculations"

            ):



                st.markdown("**1. Eligibility checks**")



                checks = [

                    ("Total runs", player["total_runs"], MIN_BATTER_TOTAL_RUNS),

                    ("Total balls", player["total_balls"], MIN_BATTER_TOTAL_BALLS),

                    ("Pressure runs", player["pressure_runs"], MIN_BATTER_PRESSURE_RUNS),

                    ("Pressure balls", player["pressure_balls"], MIN_PRESSURE_BALLS),

                    ("Normal balls", player["normal_balls"], MIN_NORMAL_BALLS)

                ]



                for label, actual, minimum in checks:

                    st.write(

                        f"{label}: {actual:.0f} / {minimum} — PASS"

                    )



                st.markdown(

                    "**2. Pressure-weighted statistics "

                    "(70% pressure + 30% normal)**"

                )



                st.write(

                    f"Strike rate: 0.70 × {player['pressure_sr']:.3f} "

                    f"+ 0.30 × {player['normal_sr']:.3f} "

                    f"= **{player['weighted_sr']:.3f}**"

                )



                st.write(

                    f"Boundary contribution: "

                    f"0.70 × {player['pressure_boundary']:.3f} "

                    f"+ 0.30 × {player['normal_boundary']:.3f} "

                    f"= **{player['weighted_boundary']:.3f}**"

                )



                st.write(

                    f"Pressure dismissal rate: "

                    f"{player['pressure_dismissal_rate']:.3f}%"

                )



                st.write(

                    f"Normal dismissal rate: "

                    f"{player['normal_dismissal_rate']:.3f}%"

                )



                st.write(

                    f"Weighted dismissal rate: "

                    f"0.70 × {player['pressure_dismissal_rate']:.3f} "

                    f"+ 0.30 × {player['normal_dismissal_rate']:.3f} "

                    f"= **{player['weighted_dismissal_rate']:.3f}%**"

                )



                st.markdown("**3. Dismissal score calculation**")



                with st.expander("Pressure Dismissal Score Calculation"):



                    st.markdown("### 1. Pressure Dismissal Rate")



                    pressure_dismissals = player["pressure_dismissals"]

                    pressure_balls = player["pressure_balls"]



                    pressure_dismissal_rate = (

                        pressure_dismissals / pressure_balls * 100

                        if pressure_balls > 0 else 0

                    )



                    st.latex(

                        r"D_p = \frac{\text{Pressure Dismissals}}{\text{Pressure Balls}}\times100"

                    )



                    st.write(f"Pressure Dismissals = {pressure_dismissals}")

                    st.write(f"Pressure Balls = {pressure_balls}")

                    st.write(

                        f"D_p = ({pressure_dismissals} / {pressure_balls}) × 100"

                    )

                    st.write(f"Pressure Dismissal Rate = {pressure_dismissal_rate:.2f}%")



                    st.divider()



                    st.markdown("### 2. Normal Dismissal Rate")



                    normal_dismissals = player["normal_dismissals"]

                    normal_balls = player["normal_balls"]



                    normal_dismissal_rate = (

                        normal_dismissals / normal_balls * 100

                        if normal_balls > 0 else 0

                    )



                    st.latex(

                        r"D_n = \frac{\text{Normal Dismissals}}{\text{Normal Balls}}\times100"

                    )



                    st.write(f"Normal Dismissals = {normal_dismissals}")

                    st.write(f"Normal Balls = {normal_balls}")

                    st.write(

                        f"D_n = ({normal_dismissals} / {normal_balls}) × 100"

                    )

                    st.write(f"Normal Dismissal Rate = {normal_dismissal_rate:.2f}%")



                    st.divider()



                    st.markdown("### 3. Weighted Dismissal Rate")



                    weighted_dismissal_rate = (

                        0.70 * pressure_dismissal_rate

                        + 0.30 * normal_dismissal_rate

                    )



                    st.latex(

                        r"D_w = (0.70 \times D_p) + (0.30 \times D_n)"

                    )



                    st.write(

                        f"D_w = (0.70 × {pressure_dismissal_rate:.2f}) + "

                        f"(0.30 × {normal_dismissal_rate:.2f})"

                    )



                    st.write(

                        f"Weighted Dismissal Rate = {weighted_dismissal_rate:.2f}%"

                    )



                    st.divider()



                    st.markdown("### 4. Min-Max Normalisation")



                    st.write(

                        "The minimum and maximum weighted dismissal rates "

                        "are calculated across all eligible batters."

                    )



                    st.write(

                        "The final score is calculated in the ranking function "

                        "and displayed below."

                    )



                    st.divider()



                    st.markdown("### 5. Final Dismissal Score")



                    st.latex(

                        r"\text{Dismissal Score} = "

                        r"**\f**rac{D_{**\m**ax}-D_w}{D_{**\m**ax}-D_{**\m**in}}**\t**imes100"

                    )



                    st.metric(

                        "Final Dismissal Score",

                        f"{player['dismissal_score']:.2f}/100"

                    )





                st.markdown(

                    "**4. Convert each statistic to a comparable 0–100 score**"

                )



                st.write(

                    f"Strike-rate score: **{player['sr_score']:.2f}**"

                )



                st.write(

                    f"Boundary score: **{player['boundary_score']:.2f}**"

                )



                st.write(

                    f"Dismissal score: **{player['dismissal_score']:.2f}**"

                )



                st.caption(
                    "The comparison cohort is every batter passing eligibility "
                    "in the currently selected dataset filters."
                )

                st.write(
                    "Strike-rate score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_sr"],
                        batting_results["weighted_sr"],
                        higher_is_better=True,
                    )
                )
                st.write(
                    "Boundary score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_boundary"],
                        batting_results["weighted_boundary"],
                        higher_is_better=True,
                    )
                )
                st.write(
                    "Dismissal score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_dismissal_rate"],
                        batting_results["weighted_dismissal_rate"],
                        higher_is_better=False,
                    )
                )



                st.markdown("**5. Raw rating**")



                st.latex(

                    r"Raw = 0.45(SR_{score}) + "

                    r"0.25(Boundary_{score}) + "

                    r"0.30(Dismissal_{score})"

                )



                st.write(

                    f"Raw rating = **{player['raw_rating']:.3f}**"

                )



                st.markdown("**6. Confidence calculation**")



                st.write(

                    "Confidence = Pressure Balls / (Pressure Balls + Normal Balls)"

                )



                st.write(

                    f"= {player['pressure_balls']:.0f} / "

                    f"{player['normal_balls']:.0f}"

                )



                st.write(

                    f"= **{player['confidence_percentage']:.2f}%**"

                )



                st.markdown("**7. Final reliability rating**")



                st.write(

                    f"Final rating = {player['raw_rating']:.3f} × "

                    f"{player['confidence']:.4f}"

                )



                st.write(

                    f"= **{player['reliability_rating']:.3f}**"

                )



        st.subheader("Batter Reliability Comparison")



        chart = px.bar(

            top_batters,

            x="striker_name",

            y="reliability_rating",

            title="Top 10 Batter Reliability Ratings",

            labels={

                "striker_name": "Batter",

                "reliability_rating": "Rating"

            }

        )



        st.plotly_chart(

            chart,

            use_container_width=True

        )



        st.download_button(

            "⬇️ Download Batter Rankings",

            data=batting_results.to_csv(index=False),

            file_name="batter_rankings.csv",

            mime="text/csv"

        )





# ==========================================

# BOWLER RANKINGS

# ==========================================



with tab2:



    st.subheader("Top 10 Reliable Bowlers")



    if bowling_results.empty:



        st.info(

            "No bowlers currently meet all eligibility criteria. "

            "Try selecting more seasons or competitions."

        )



    else:



        top_bowlers = bowling_results.head(10)



        bowler_table = top_bowlers[[

            "rank",

            "bowler_name",

            "pressure_balls",

            "normal_balls",

            "confidence_percentage",

            "pressure_wickets",

            "weighted_economy",

            "weighted_wickets_per_100",

            "weighted_dot_percentage",

            "reliability_rating"

        ]].rename(columns={

            "rank": "Rank",

            "bowler_name": "Bowler",

            "pressure_balls": "Pressure Legal Balls",

            "normal_balls": "Normal Legal Balls",

            "confidence_percentage": "Confidence %",

            "pressure_wickets": "Pressure Wickets",

            "weighted_economy": "Weighted Economy (70:30)",

            "weighted_wickets_per_100": "Weighted Wickets/100",

            "weighted_dot_percentage": "Weighted Dot Ball %",

            "reliability_rating": "Reliability Rating"

        })



        st.dataframe(

            bowler_table,

            use_container_width=True,

            hide_index=True

        )



        st.markdown("### Individual Bowler Calculations")



        for _, player in top_bowlers.iterrows():



            with st.expander(

                f"#{int(player['rank'])} - "

                f"{player['bowler_name']} | View Calculations"

            ):



                st.markdown("**1. Eligibility checks**")



                checks = [

                    ("Pressure legal balls", player["pressure_balls"], MIN_PRESSURE_BALLS),

                    ("Normal legal balls", player["normal_balls"], MIN_NORMAL_BALLS),

                    ("Pressure wickets", player["pressure_wickets"], MIN_BOWLER_PRESSURE_WICKETS)

                ]



                for label, actual, minimum in checks:

                    st.write(

                        f"{label}: {actual:.0f} / {minimum} — PASS"

                    )



                st.markdown("**2. Base performance metrics**")

                st.write(
                    f"Pressure economy = {player['pressure_runs']:.0f} ÷ "
                    f"{player['pressure_balls']:.0f} legal balls × 6 "
                    f"= **{player['pressure_economy']:.3f}**"
                )
                st.write(
                    f"Normal economy = {player['normal_runs']:.0f} ÷ "
                    f"{player['normal_balls']:.0f} legal balls × 6 "
                    f"= **{player['normal_economy']:.3f}**"
                )
                st.write(
                    f"Pressure wickets per 100 balls = "
                    f"{player['pressure_wickets']:.0f} ÷ "
                    f"{player['pressure_balls']:.0f} × 100 "
                    f"= **{player['pressure_wickets_per_100']:.3f}**"
                )
                st.write(
                    f"Normal wickets per 100 balls = "
                    f"{player['normal_wickets']:.0f} ÷ "
                    f"{player['normal_balls']:.0f} × 100 "
                    f"= **{player['normal_wickets_per_100']:.3f}**"
                )
                st.write(
                    "Dot-ball percentage = legal dot balls ÷ legal balls × 100; "
                    f"pressure **{player['pressure_dot_percentage']:.3f}%**, "
                    f"normal **{player['normal_dot_percentage']:.3f}%**"
                )

                st.markdown(

                    "**3. Pressure-weighted statistics "

                    "(70% pressure + 30% normal)**"

                )



                st.write(

                    f"Economy: 0.70 × {player['pressure_economy']:.3f} "

                    f"+ 0.30 × {player['normal_economy']:.3f} "

                    f"= **{player['weighted_economy']:.3f}**"

                )



                st.write(

                    f"Wickets/100: "

                    f"0.70 × {player['pressure_wickets_per_100']:.3f} "

                    f"+ 0.30 × {player['normal_wickets_per_100']:.3f} "

                    f"= **{player['weighted_wickets_per_100']:.3f}**"

                )



                st.write(

                    f"Dot-ball %: "

                    f"0.70 × {player['pressure_dot_percentage']:.3f} "

                    f"+ 0.30 × {player['normal_dot_percentage']:.3f} "

                    f"= **{player['weighted_dot_percentage']:.3f}**"

                )



                st.markdown(

                    "**4. Convert each statistic to a comparable 0–100 score**"

                )



                st.write(

                    f"Economy score (lower economy is better): "

                    f"**{player['economy_score']:.2f}**"

                )



                st.write(

                    f"Wicket-rate score: **{player['wicket_score']:.2f}**"

                )



                st.write(

                    f"Dot-ball score: **{player['dot_score']:.2f}**"

                )



                st.caption(

                    "The 0–100 scaling is relative to eligible bowlers "

                    "in the currently selected dataset."

                )

                st.write(
                    "Economy score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_economy"],
                        bowling_results["weighted_economy"],
                        higher_is_better=False,
                    )
                )
                st.write(
                    "Wicket-rate score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_wickets_per_100"],
                        bowling_results["weighted_wickets_per_100"],
                        higher_is_better=True,
                    )
                )
                st.write(
                    "Dot-ball score calculation: "
                    + format_minmax_score_calculation(
                        player["weighted_dot_percentage"],
                        bowling_results["weighted_dot_percentage"],
                        higher_is_better=True,
                    )
                )



                st.markdown("**5. Raw rating**")



                st.latex(

                    r"Raw = 0.40(Economy_{score}) + "

                    r"0.35(Wicket_{score}) + "

                    r"0.25(Dot_{score})"

                )



                st.write(

                    f"Raw rating = **{player['raw_rating']:.3f}**"

                )



                st.markdown("**6. Confidence calculation**")



                st.write(

                    "Confidence = Pressure Legal Balls / (Pressure Legal Balls + Normal Legal Balls)"

                )



                st.write(

                    f"= {player['pressure_balls']:.0f} / "

                    f"({player['pressure_balls']:.0f} + {player['normal_balls']:.0f})"

                )



                st.write(

                    f"= **{player['confidence_percentage']:.2f}%**"

                )



                st.markdown("**7. Final reliability rating**")



                st.write(

                    f"Final rating = {player['raw_rating']:.3f} × "

                    f"{player['confidence']:.4f}"

                )



                st.write(

                    f"= **{player['reliability_rating']:.3f}**"

                )



        st.subheader("Bowler Reliability Comparison")



        chart = px.bar(

            top_bowlers,

            x="bowler_name",

            y="reliability_rating",

            title="Top 10 Bowler Reliability Ratings",

            labels={

                "bowler_name": "Bowler",

                "reliability_rating": "Rating"

            }

        )



        st.plotly_chart(

            chart,

            use_container_width=True

        )



        st.download_button(

            "⬇️ Download Bowler Rankings",

            data=bowling_results.to_csv(index=False),

            file_name="bowler_rankings.csv",

            mime="text/csv"

        )





# ==========================================

# PLAYER CALCULATION EXPLORER

# ==========================================



with tab3:



    st.header("🔍 Player Calculation Explorer")



    st.write(

        "Explore the weighted statistics and final reliability "

        "calculation for any eligible player."

    )



    explorer_type = st.radio(

        "Choose Player Category",

        ["Batter", "Bowler"],

        horizontal=True,

        key="explorer_type"

    )



    if explorer_type == "Batter":



        if batting_results.empty:



            st.info("No eligible batters available.")



        else:



            options = (

                batting_results

                .drop_duplicates("striker_id")

                .set_index("striker_id")["striker_name"]

                .to_dict()

            )



            selected_id = st.selectbox(

                "Select Batter",

                list(options.keys()),

                format_func=lambda x: options[x],

                key="selected_batter"

            )



            player = batting_results[

                batting_results["striker_id"] == selected_id

            ].iloc[0]



            st.subheader(f"🏏 {player['striker_name']}")



            st.markdown("**Performance statistics**")



            st.write(

                f"Pressure SR: {player['pressure_sr']:.3f} | "

                f"Normal SR: {player['normal_sr']:.3f}"

            )



            st.write(

                f"Weighted SR (70:30): **{player['weighted_sr']:.3f}**"

            )



            st.write(

                f"Weighted boundary contribution: "

                f"**{player['weighted_boundary']:.3f}**"

            )



            st.write(

                f"Pressure dismissal rate: "

                f"**{player['pressure_dismissal_rate']:.3f}%**"

            )



            st.write(

                f"Normal dismissal rate: "

                f"**{player['normal_dismissal_rate']:.3f}%**"

            )



            st.write(

                f"Weighted dismissal rate: "

                f"**{player['weighted_dismissal_rate']:.3f}%**"

            )



            st.markdown("**Dismissal score calculation**")



            st.write(

                f"Pressure dismissals: "

                f"{player['pressure_dismissals']:.0f}"

            )



            st.write(

                f"Normal dismissals: "

                f"{player['normal_dismissals']:.0f}"

            )



            st.write(

                f"Dismissal score: "

                f"**{player['dismissal_score']:.2f} / 100**"

            )



            st.caption(

                "Lower weighted dismissal rate gives a higher dismissal score."

            )



            st.markdown("**Component scores**")



            st.write(

                f"SR: {player['sr_score']:.2f}, "

                f"Boundary: {player['boundary_score']:.2f}, "

                f"Dismissal: {player['dismissal_score']:.2f}"

            )



            st.markdown("**Confidence calculation**")



            st.write(

                f"Pressure Balls / (Pressure Balls + Normal Balls) = "

                f"{player['pressure_balls']:.0f} / "

                f"{player['normal_balls']:.0f}"

            )



            st.write(

                f"Confidence: **{player['confidence_percentage']:.2f}%**"

            )



            st.write(

                f"Raw rating: **{player['raw_rating']:.3f}**"

            )



            st.metric(

                "Final Reliability Rating",

                f"{player['reliability_rating']:.3f}"

            )



    else:



        if bowling_results.empty:



            st.info("No eligible bowlers available.")



        else:



            options = (

                bowling_results

                .drop_duplicates("bowler_id")

                .set_index("bowler_id")["bowler_name"]

                .to_dict()

            )



            selected_id = st.selectbox(

                "Select Bowler",

                list(options.keys()),

                format_func=lambda x: options[x],

                key="selected_bowler"

            )



            player = bowling_results[

                bowling_results["bowler_id"] == selected_id

            ].iloc[0]



            st.subheader(f"🎯 {player['bowler_name']}")



            st.write(

                f"Pressure economy: {player['pressure_economy']:.3f} | "

                f"Normal economy: {player['normal_economy']:.3f}"

            )



            st.write(

                f"Weighted economy (70:30): "

                f"**{player['weighted_economy']:.3f}**"

            )



            st.write(

                f"Weighted wickets/100: "

                f"**{player['weighted_wickets_per_100']:.3f}**"

            )



            st.write(

                f"Weighted dot-ball %: "

                f"**{player['weighted_dot_percentage']:.3f}**"

            )



            st.write(

                f"Component scores — "

                f"Economy: {player['economy_score']:.2f}, "

                f"Wickets: {player['wicket_score']:.2f}, "

                f"Dot balls: {player['dot_score']:.2f}"

            )



            st.markdown("**Confidence calculation**")



            st.write(

                f"Pressure Legal Balls / (Pressure Legal Balls + Normal Legal Balls) = "

                f"{player['pressure_balls']:.0f} / "

                f"{player['normal_balls']:.0f}"

            )



            st.write(

                f"Confidence: **{player['confidence_percentage']:.2f}%**"

            )



            st.write(

                f"Raw rating: **{player['raw_rating']:.3f}**"

            )



            st.metric(

                "Final Reliability Rating",

                f"{player['reliability_rating']:.3f}"

            )





# ==========================================

# FOOTER

# ==========================================



st.caption(

    "SupeRR Selector 2.0 | Data-driven cricket performance analysis"

)
