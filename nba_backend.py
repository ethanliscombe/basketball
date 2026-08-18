import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# -----------------------------
# 1. LOAD LOCAL NBA DATA
# -----------------------------

DATA_PATH = Path(__file__).resolve().parent / "playerstats.parquet"

# The local dataset covers multiple NBA seasons, rather than requiring
# Basketball-Reference to be scraped every time the app starts.
if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Missing local NBA dataset: {DATA_PATH.name}. "
        "Place playerstats.parquet next to app.py and nba_backend.py."
    )


def _clean_column_name(value):
    value = str(value).strip().lower()
    value = value.replace("%", "pct")
    value = value.replace("/", "_")
    value = value.replace("-", "_")
    value = value.replace(" ", "_")
    return value


def _pick_column(df, candidates):
    """Return the first matching column from a list of normalized candidates."""
    columns = set(df.columns)
    for candidate in candidates:
        normalized = _clean_column_name(candidate)
        if normalized in columns:
            return normalized
    return None


def _to_numeric(df, column):
    if column is None:
        return pd.Series(np.nan, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def _build_season_label(value):
    """Convert common season formats to NEXUS's YYYY-YY display format."""
    if pd.isna(value):
        return None

    text = str(value).strip()

    # Already formatted: 2024-25, 2024–25, etc.
    if "-" in text or "–" in text:
        cleaned = text.replace("–", "-").replace("/", "-")
        parts = cleaned.split("-")
        if len(parts) == 2 and parts[0].isdigit():
            start = int(parts[0])
            end = parts[1][-2:]
            return f"{start}-{end}"

    # Numeric end-year convention used by the source repo:
    # 2025 means the 2024-25 season.
    try:
        year = int(float(text))
        if 1900 <= year <= 2100:
            return f"{year - 1}-{str(year)[-2:]}"
    except ValueError:
        pass

    return text


def _weighted_average(group, value_col, weight_col):
    values = pd.to_numeric(group[value_col], errors="coerce")
    weights = pd.to_numeric(group[weight_col], errors="coerce")

    valid = values.notna() & weights.notna()
    if valid.any() and weights[valid].sum() > 0:
        return float(np.average(values[valid], weights=weights[valid]))

    return float(values.mean()) if values.notna().any() else np.nan


def load_local_player_data():
    """Load and normalize the bundled multi-season player dataset."""
    raw = pd.read_parquet(DATA_PATH)
    raw.columns = [_clean_column_name(c) for c in raw.columns]

    player_col = _pick_column(
        raw,
        [
            "player_name",
            "player",
            "name",
            "display_name",
            "athlete_name",
        ],
    )
    season_col = _pick_column(
        raw,
        [
            "season",
            "season_end",
            "season_year",
            "year",
        ],
    )
    games_col = _pick_column(raw, ["games", "gp", "g"])

    if player_col is None:
        raise ValueError(
            "Could not find a player-name column in playerstats.parquet."
        )
    if season_col is None:
        raise ValueError(
            "Could not find a season column in playerstats.parquet."
        )

    df = raw.copy()
    df["player_name"] = df[player_col].astype(str).str.strip()
    df["season"] = df[season_col].map(_build_season_label)
    df["games"] = _to_numeric(df, games_col)

    # Direct per-game/percentage columns, if present.
    ppg_col = _pick_column(df, ["ppg", "pts_pg", "points_per_game"])
    rpg_col = _pick_column(df, ["rpg", "reb_pg", "rebounds_per_game"])
    apg_col = _pick_column(df, ["apg", "ast_pg", "assists_per_game"])
    spg_col = _pick_column(df, ["spg", "stl_pg", "steals_per_game"])
    bpg_col = _pick_column(df, ["bpg", "blk_pg", "blocks_per_game"])
    three_pct_col = _pick_column(
        df,
        ["three_pct", "3p_pct", "fg3_pct", "three_point_pct", "threept_pct"],
    )
    ft_pct_col = _pick_column(df, ["ft_pct", "free_throw_pct"])

    # Totals used as fallbacks when per-game fields are not present.
    pts_col = _pick_column(df, ["pts", "points"])
    reb_col = _pick_column(df, ["trb", "reb", "rebounds"])
    ast_col = _pick_column(df, ["ast", "assists"])
    stl_col = _pick_column(df, ["stl", "steals"])
    blk_col = _pick_column(df, ["blk", "blocks"])
    fg3m_col = _pick_column(df, ["fg3m", "3pm", "three_pointers_made"])
    fg3a_col = _pick_column(df, ["fg3a", "3pa", "three_pointers_attempted"])
    ftm_col = _pick_column(df, ["ftm", "free_throws_made"])
    fta_col = _pick_column(df, ["fta", "free_throws_attempted"])

    df["ppg"] = _to_numeric(df, ppg_col)
    df["rpg"] = _to_numeric(df, rpg_col)
    df["apg"] = _to_numeric(df, apg_col)
    df["spg"] = _to_numeric(df, spg_col)
    df["bpg"] = _to_numeric(df, bpg_col)
    df["three_pct"] = _to_numeric(df, three_pct_col)
    df["ft_pct"] = _to_numeric(df, ft_pct_col)

    # Compute per-game stats from season totals when needed.
    def fill_per_game(target, total_col):
        if total_col is None:
            return
        totals = _to_numeric(df, total_col)
        missing = df[target].isna() & df["games"].gt(0)
        df.loc[missing, target] = totals[missing] / df.loc[missing, "games"]

    fill_per_game("ppg", pts_col)
    fill_per_game("rpg", reb_col)
    fill_per_game("apg", ast_col)
    fill_per_game("spg", stl_col)
    fill_per_game("bpg", blk_col)

    if three_pct_col is None and fg3m_col and fg3a_col:
        made = _to_numeric(df, fg3m_col)
        attempted = _to_numeric(df, fg3a_col)
        valid = attempted.gt(0) & df["three_pct"].isna()
        df.loc[valid, "three_pct"] = (made[valid] / attempted[valid]) * 100

    if ft_pct_col is None and ftm_col and fta_col:
        made = _to_numeric(df, ftm_col)
        attempted = _to_numeric(df, fta_col)
        valid = attempted.gt(0) & df["ft_pct"].isna()
        df.loc[valid, "ft_pct"] = (made[valid] / attempted[valid]) * 100

    stat_columns = [
        "games",
        "ppg",
        "rpg",
        "apg",
        "spg",
        "bpg",
        "three_pct",
        "ft_pct",
    ]

    for stat in stat_columns:
        df[stat] = pd.to_numeric(df[stat], errors="coerce")

    # Some datasets store percentages as fractions (0.303 = 30.3%).
    # NEXUS stores/display percentages on a 0-100 scale.
    for pct_col in ["three_pct", "ft_pct"]:
        valid_pct = df[pct_col].dropna()
        if not valid_pct.empty and valid_pct.median() <= 1.0:
            df[pct_col] = df[pct_col] * 100.0

    df = df.dropna(
        subset=["player_name", "season"] + stat_columns
    ).copy()

    # If a player appeared on multiple teams in one season, combine the rows.
    # Per-game stats are weighted by games; percentages are weighted by games.
    rows = []
    for (season, player_name), group in df.groupby(
        ["season", "player_name"],
        sort=False,
        dropna=False,
    ):
        total_games = group["games"].sum()

        rows.append(
            {
                "player_name": player_name,
                "season": season,
                "games": total_games,
                "ppg": _weighted_average(group, "ppg", "games"),
                "rpg": _weighted_average(group, "rpg", "games"),
                "apg": _weighted_average(group, "apg", "games"),
                "spg": _weighted_average(group, "spg", "games"),
                "bpg": _weighted_average(group, "bpg", "games"),
                "three_pct": _weighted_average(group, "three_pct", "games"),
                "ft_pct": _weighted_average(group, "ft_pct", "games"),
            }
        )

    comparison_df = pd.DataFrame(rows)

    if comparison_df.empty:
        raise ValueError("playerstats.parquet did not contain usable player rows.")

    return comparison_df.reset_index(drop=True)


comparison_df = load_local_player_data()
AVAILABLE_SEASONS = sorted(
    comparison_df["season"].dropna().unique(),
    reverse=True,
)


def get_season_data(season=None):
    """Return one season, or the full normalized dataset."""
    if season is None:
        return comparison_df.copy()

    return comparison_df[
        comparison_df["season"] == season
    ].copy()


# -----------------------------
# 2. PLAYER SEARCH
# -----------------------------

def normalize_name(name):
    """Remove accents and normalize capitalization."""
    name = str(name).lower().strip()
    name = unicodedata.normalize("NFKD", name)
    return "".join(
        char
        for char in name
        if not unicodedata.combining(char)
    )


def find_player_suggestions(search_term, limit=10, season=None):
    """Return player names containing the search text."""
    if not isinstance(search_term, str) or not search_term.strip():
        return []

    search_term = normalize_name(search_term)
    df = get_season_data(season)

    matches = [
        player
        for player in df["player_name"].unique()
        if search_term in normalize_name(player)
    ]

    return matches[:limit]


def find_player(search_term, season=None):
    """
    Find a player by full name, last name, or partial name.

    Returns:
        dict -> one player found
        list -> multiple possible players
        None -> no player found
    """
    if not isinstance(search_term, str) or not search_term.strip():
        return None

    df = get_season_data(season)
    search_term = search_term.strip()
    normalized = df["player_name"].apply(normalize_name)
    search_name = normalize_name(search_term)

    exact = df[normalized == search_name]

    if len(exact) == 1:
        return exact.iloc[0].to_dict()

    last_name_matches = df[
        normalized.str.split().str[-1] == search_name
    ]

    if len(last_name_matches) == 1:
        return last_name_matches.iloc[0].to_dict()

    suggestions = find_player_suggestions(
        search_term,
        season=season,
    )

    if len(suggestions) == 1:
        player = df[df["player_name"] == suggestions[0]]
        if len(player) == 1:
            return player.iloc[0].to_dict()

    if len(suggestions) > 1:
        return suggestions

    return None


# -----------------------------
# 3. PLAYER ROLES
# -----------------------------

def build_roles_df(df):
    """Calculate player roles within one season."""
    roles = df.copy()

    role_stat_columns = [
        "ppg",
        "rpg",
        "apg",
        "spg",
        "bpg",
        "three_pct",
        "ft_pct",
    ]

    for stat in role_stat_columns:
        min_val = roles[stat].min()
        max_val = roles[stat].max()

        if max_val > min_val:
            roles[stat + "_norm"] = (
                (roles[stat] - min_val) / (max_val - min_val)
            )
        else:
            roles[stat + "_norm"] = 0

    roles["scoring_score"] = (
        roles["ppg_norm"] * 0.65
        + roles["ft_pct_norm"] * 0.15
        + roles["three_pct_norm"] * 0.20
    )

    roles["playmaking_score"] = (
        roles["apg_norm"] * 0.75
        + roles["rpg_norm"] * 0.10
        + roles["ppg_norm"] * 0.15
    )

    roles["rebounding_score"] = (
        roles["rpg_norm"] * 0.80
        + roles["bpg_norm"] * 0.10
        + roles["ppg_norm"] * 0.10
    )

    roles["defense_score"] = (
        roles["spg_norm"] * 0.45
        + roles["bpg_norm"] * 0.40
        + roles["rpg_norm"] * 0.15
    )

    roles["shooting_score"] = (
        roles["three_pct_norm"] * 0.70
        + roles["ft_pct_norm"] * 0.30
    )

    roles["all_around_score"] = (
        roles["ppg_norm"] * 0.25
        + roles["rpg_norm"] * 0.20
        + roles["apg_norm"] * 0.20
        + roles["spg_norm"] * 0.15
        + roles["bpg_norm"] * 0.10
        + roles["three_pct_norm"] * 0.10
    )

    role_columns = {
        "scoring_score": "Primary Scorer",
        "playmaking_score": "Playmaker",
        "rebounding_score": "Rebounder",
        "defense_score": "Defensive Specialist",
        "shooting_score": "Shooter",
        "all_around_score": "All-Around",
    }

    role_score_columns = list(role_columns.keys())

    sorted_roles = roles[role_score_columns].apply(
        lambda row: row.sort_values(ascending=False).index.tolist(),
        axis=1,
    )

    roles["primary_role"] = sorted_roles.apply(
        lambda x: role_columns[x[0]]
    )
    roles["secondary_role"] = sorted_roles.apply(
        lambda x: role_columns[x[1]]
    )

    roles["primary_role_score"] = roles.apply(
        lambda row: row[sorted_roles.loc[row.name][0]],
        axis=1,
    )
    roles["secondary_role_score"] = roles.apply(
        lambda row: row[sorted_roles.loc[row.name][1]],
        axis=1,
    )

    role_gap = (
        roles["primary_role_score"]
        - roles["secondary_role_score"]
    )

    roles.loc[role_gap > 0.20, "secondary_role"] = None

    return roles


role_frames = []

for season_value, season_group in comparison_df.groupby("season", sort=False):
    role_frame = build_roles_df(season_group.copy())
    # Keep the grouping key explicitly because newer pandas versions
    # may exclude grouping columns from DataFrameGroupBy.apply().
    role_frame["season"] = season_value
    role_frames.append(role_frame)

roles_df = pd.concat(role_frames, ignore_index=True)


# -----------------------------
# 4. SIMILARITY MODEL
# -----------------------------

STAT_WEIGHTS = {
    "ppg": 0.20,
    "rpg": 0.15,
    "apg": 0.15,
    "spg": 0.10,
    "bpg": 0.10,
    "three_pct": 0.15,
    "ft_pct": 0.15,
}


def role_aware_similarity(player1, player2, season=None):
    """Calculate NEXUS's final role-aware similarity score."""
    name1 = normalize_name(player1)
    name2 = normalize_name(player2)

    df = roles_df
    if season is not None:
        df = df[df["season"] == season]

    p1 = df[
        df["player_name"].apply(normalize_name) == name1
    ]
    p2 = df[
        df["player_name"].apply(normalize_name) == name2
    ]

    if p1.empty or p2.empty:
        return None

    p1 = p1.iloc[0]
    p2 = p2.iloc[0]

    stat_score = 0
    total_weight = 0

    for stat, weight in STAT_WEIGHTS.items():
        a = p1[stat]
        b = p2[stat]

        if pd.isna(a) or pd.isna(b):
            continue

        denominator = abs(a) + abs(b)

        if denominator == 0:
            similarity = 100
        else:
            similarity = 100 * (
                1 - abs(a - b) / denominator
            )

        stat_score += similarity * weight
        total_weight += weight

    if total_weight == 0:
        return None

    stat_score /= total_weight

    role_scores = [
        "scoring_score",
        "playmaking_score",
        "rebounding_score",
        "defense_score",
        "shooting_score",
        "all_around_score",
    ]

    role_differences = [
        abs(p1[role] - p2[role])
        for role in role_scores
    ]

    average_role_difference = np.mean(role_differences)

    role_score = 100 * (1 - average_role_difference)
    role_score = max(0, min(100, role_score))

    final_score = (
        stat_score * 0.75
        + role_score * 0.25
    )

    return round(final_score, 2)


# -----------------------------
# 5. SIMILAR PLAYERS
# -----------------------------

def get_similar_players(player_name, n=10, season=None):
    """Return the most similar players from a selected season."""
    player = find_player(player_name, season=season)

    if player is None or isinstance(player, list):
        return pd.DataFrame(
            columns=["player_name", "similarity"]
        )

    actual_name = player["player_name"]
    results = []

    season_roles = roles_df
    if season is not None:
        season_roles = roles_df[
            roles_df["season"] == season
        ]

    for other_player in season_roles["player_name"]:
        if normalize_name(other_player) == normalize_name(actual_name):
            continue

        score = role_aware_similarity(
            actual_name,
            other_player,
            season=season,
        )

        if score is not None:
            results.append((other_player, score))

    results.sort(key=lambda x: x[1], reverse=True)

    results = pd.DataFrame(
        results[:n],
        columns=["player_name", "similarity"],
    )

    if not results.empty:
        results["similarity"] = (
            results["similarity"].astype(float).round(2)
        )

    return results.reset_index(drop=True)


def get_similarity_with_roles(player_name, n=10, season=None):
    """Return similar players plus their roles."""
    results = get_similar_players(
        player_name,
        n,
        season=season,
    )

    if results.empty:
        return results

    role_info = roles_df[
        ["player_name", "season", "primary_role", "secondary_role"]
    ].copy()

    if season is not None:
        role_info = role_info[
            role_info["season"] == season
        ]

    return results.merge(
        role_info,
        on="player_name",
        how="left",
    )[
        [
            "player_name",
            "similarity",
            "primary_role",
            "secondary_role",
        ]
    ]


# -----------------------------
# 6. TWO-PLAYER COMPARISON
# -----------------------------

def compare_players_data(player1, player2, season=None):
    """Return all data needed by the Streamlit comparison interface."""
    p1 = find_player(player1, season=season)
    p2 = find_player(player2, season=season)

    if p1 is None or p2 is None:
        return None

    if isinstance(p1, list) or isinstance(p2, list):
        return {
            "multiple_matches": True,
            "player1": p1,
            "player2": p2,
        }

    score = role_aware_similarity(
        p1["player_name"],
        p2["player_name"],
        season=season,
    )

    season_roles = roles_df
    if season is not None:
        season_roles = roles_df[
            roles_df["season"] == season
        ]

    role1 = season_roles[
        season_roles["player_name"] == p1["player_name"]
    ].iloc[0]

    role2 = season_roles[
        season_roles["player_name"] == p2["player_name"]
    ].iloc[0]

    return {
        "multiple_matches": False,
        "player1": p1,
        "player2": p2,
        "similarity": score,
        "role1": {
            "primary": role1["primary_role"],
            "secondary": role1["secondary_role"],
        },
        "role2": {
            "primary": role2["primary_role"],
            "secondary": role2["secondary_role"],
        },
    }


def get_similarity_breakdown(player1, player2, season=None):
    """Calculate individual stat similarity percentages."""
    p1 = find_player(player1, season=season)
    p2 = find_player(player2, season=season)

    if (
        p1 is None
        or p2 is None
        or isinstance(p1, list)
        or isinstance(p2, list)
    ):
        return None

    stats = [
        "ppg",
        "rpg",
        "apg",
        "spg",
        "bpg",
        "three_pct",
        "ft_pct",
    ]

    breakdown = {}

    for stat in stats:
        v1 = p1[stat]
        v2 = p2[stat]

        if max(abs(v1), abs(v2)) == 0:
            similarity = 100
        else:
            similarity = (
                1 - abs(v1 - v2) / max(abs(v1), abs(v2))
            ) * 100

        breakdown[stat] = max(0, similarity)

    return breakdown


def get_overall_breakdown_similarity(player1, player2, season=None):
    """Return the average of individual stat similarities."""
    breakdown = get_similarity_breakdown(
        player1,
        player2,
        season=season,
    )

    if breakdown is None:
        return None

    return round(
        sum(breakdown.values()) / len(breakdown),
        2,
    )
