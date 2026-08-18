import unicodedata

import numpy as np
import pandas as pd


# -----------------------------
# 1. LOAD AND PREPARE NBA DATA
# -----------------------------

DATA_URL = "https://www.basketball-reference.com/leagues/NBA_2025_per_game.html"


def load_player_data():
    """Load and clean the NBA player data used by the notebook."""
    df = pd.read_html(DATA_URL)[0]

    # Remove repeated header rows
    df = df[df["Player"] != "Player"].copy()

    stats_to_clean = ["G", "PTS", "TRB", "AST", "STL", "BLK", "3P%", "FT%"]

    for stat in stats_to_clean:
        df[stat] = pd.to_numeric(df[stat], errors="coerce")

    df = df.dropna(subset=stats_to_clean)

    comparison_df = df[
        [
            "Player",
            "G",
            "PTS",
            "TRB",
            "AST",
            "STL",
            "BLK",
            "3P%",
            "FT%",
        ]
    ].copy()

    comparison_df = comparison_df.rename(
        columns={
            "Player": "player_name",
            "G": "games",
            "PTS": "ppg",
            "TRB": "rpg",
            "AST": "apg",
            "STL": "spg",
            "BLK": "bpg",
            "3P%": "three_pct",
            "FT%": "ft_pct",
        }
    )

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
        comparison_df[stat] = pd.to_numeric(
            comparison_df[stat], errors="coerce"
        )

    comparison_df = comparison_df.dropna(subset=stat_columns).reset_index(drop=True)

    # Combine duplicate rows for players who appeared on multiple teams.
    comparison_df = (
        comparison_df
        .groupby("player_name")
        .apply(combine_player_rows, include_groups=False)
        .reset_index(drop=True)
    )

    return comparison_df


def combine_player_rows(group):
    """Combine multiple team rows into one player row."""
    total_games = group["games"].sum()

    result = {
        "player_name": group.name,
        "games": total_games,
    }

    per_game_stats = ["ppg", "rpg", "apg", "spg", "bpg"]

    for stat in per_game_stats:
        result[stat] = (
            (group[stat] * group["games"]).sum() / total_games
        )

    result["three_pct"] = (
        (group["three_pct"] * group["games"]).sum() / total_games
    )

    result["ft_pct"] = (
        (group["ft_pct"] * group["games"]).sum() / total_games
    )

    return pd.Series(result)


comparison_df = load_player_data()


# -----------------------------
# 2. PLAYER ROLES
# -----------------------------

roles_df = comparison_df.copy()

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
    min_val = roles_df[stat].min()
    max_val = roles_df[stat].max()

    if max_val > min_val:
        roles_df[stat + "_norm"] = (
            (roles_df[stat] - min_val) / (max_val - min_val)
        )
    else:
        roles_df[stat + "_norm"] = 0


roles_df["scoring_score"] = (
    roles_df["ppg_norm"] * 0.65
    + roles_df["ft_pct_norm"] * 0.15
    + roles_df["three_pct_norm"] * 0.20
)

roles_df["playmaking_score"] = (
    roles_df["apg_norm"] * 0.75
    + roles_df["rpg_norm"] * 0.10
    + roles_df["ppg_norm"] * 0.15
)

roles_df["rebounding_score"] = (
    roles_df["rpg_norm"] * 0.80
    + roles_df["bpg_norm"] * 0.10
    + roles_df["ppg_norm"] * 0.10
)

roles_df["defense_score"] = (
    roles_df["spg_norm"] * 0.45
    + roles_df["bpg_norm"] * 0.40
    + roles_df["rpg_norm"] * 0.15
)

roles_df["shooting_score"] = (
    roles_df["three_pct_norm"] * 0.70
    + roles_df["ft_pct_norm"] * 0.30
)

roles_df["all_around_score"] = (
    roles_df["ppg_norm"] * 0.25
    + roles_df["rpg_norm"] * 0.20
    + roles_df["apg_norm"] * 0.20
    + roles_df["spg_norm"] * 0.15
    + roles_df["bpg_norm"] * 0.10
    + roles_df["three_pct_norm"] * 0.10
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

sorted_roles = roles_df[role_score_columns].apply(
    lambda row: row.sort_values(ascending=False).index.tolist(),
    axis=1,
)

roles_df["primary_role"] = sorted_roles.apply(
    lambda x: role_columns[x[0]]
)

roles_df["secondary_role"] = sorted_roles.apply(
    lambda x: role_columns[x[1]]
)

roles_df["primary_role_score"] = roles_df.apply(
    lambda row: row[sorted_roles.loc[row.name][0]],
    axis=1,
)

roles_df["secondary_role_score"] = roles_df.apply(
    lambda row: row[sorted_roles.loc[row.name][1]],
    axis=1,
)

role_gap = (
    roles_df["primary_role_score"]
    - roles_df["secondary_role_score"]
)

roles_df.loc[role_gap > 0.20, "secondary_role"] = None


# -----------------------------
# 3. NAME SEARCH
# -----------------------------

def normalize_name(name):
    """Remove accents and normalize capitalization."""
    name = str(name).lower().strip()
    name = unicodedata.normalize("NFKD", name)
    return "".join(
        char for char in name
        if not unicodedata.combining(char)
    )


def find_player_suggestions(search_term, limit=10):
    """Return player names containing the search text."""
    if not isinstance(search_term, str) or not search_term.strip():
        return []

    search_term = normalize_name(search_term)

    matches = [
        player
        for player in comparison_df["player_name"].unique()
        if search_term in normalize_name(player)
    ]

    return matches[:limit]


def find_player(search_term):
    """
    Find a player by full name, last name, or partial name.

    Returns:
        dict  -> one player found
        list  -> multiple possible players
        None  -> no player found
    """
    if not isinstance(search_term, str) or not search_term.strip():
        return None

    search_term = search_term.strip()
    normalized = comparison_df["player_name"].apply(normalize_name)
    search_name = normalize_name(search_term)

    # Exact full-name match
    exact = comparison_df[normalized == search_name]

    if len(exact) == 1:
        return exact.iloc[0].to_dict()

    # Last-name match
    last_name_matches = comparison_df[
        normalized.str.split().str[-1] == search_name
    ]

    if len(last_name_matches) == 1:
        return last_name_matches.iloc[0].to_dict()

    # Partial matches
    suggestions = find_player_suggestions(search_term)

    if len(suggestions) == 1:
        player = comparison_df[
            comparison_df["player_name"] == suggestions[0]
        ]

        if len(player) == 1:
            return player.iloc[0].to_dict()

    if len(suggestions) > 1:
        return suggestions

    return None


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


def role_aware_similarity(player1, player2):
    """Calculate the notebook's final role-aware similarity score."""
    name1 = normalize_name(player1)
    name2 = normalize_name(player2)

    p1 = roles_df[
        roles_df["player_name"].apply(normalize_name) == name1
    ]

    p2 = roles_df[
        roles_df["player_name"].apply(normalize_name) == name2
    ]

    if p1.empty or p2.empty:
        return None

    p1 = p1.iloc[0]
    p2 = p2.iloc[0]

    # 75% statistical similarity
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

    stat_score = stat_score / total_weight

    # 25% role similarity
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
# 5. SIMILAR PLAYER SEARCH
# -----------------------------

def get_similar_players(player_name, n=10):
    """Return a DataFrame of the most similar players."""
    player = find_player(player_name)

    if player is None or isinstance(player, list):
        return pd.DataFrame(
            columns=["player_name", "similarity"]
        )

    actual_name = player["player_name"]
    results = []

    for other_player in roles_df["player_name"]:
        if normalize_name(other_player) == normalize_name(actual_name):
            continue

        score = role_aware_similarity(actual_name, other_player)

        if score is not None:
            results.append((other_player, score))

    results.sort(key=lambda x: x[1], reverse=True)

    results = pd.DataFrame(
        results[:n],
        columns=["player_name", "similarity"],
    )

    if not results.empty:
        results["similarity"] = results["similarity"].astype(float).round(2)

    return results.reset_index(drop=True)


def get_similarity_with_roles(player_name, n=10):
    """Return similar players plus their primary and secondary roles."""
    results = get_similar_players(player_name, n)

    if results.empty:
        return results

    role_info = roles_df[
        ["player_name", "primary_role", "secondary_role"]
    ].copy()

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

def compare_players_data(player1, player2):
    """
    Return all data needed by the Streamlit interface
    for a two-player comparison.
    """
    p1 = find_player(player1)
    p2 = find_player(player2)

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
    )

    role1 = roles_df[
        roles_df["player_name"] == p1["player_name"]
    ].iloc[0]

    role2 = roles_df[
        roles_df["player_name"] == p2["player_name"]
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


def get_similarity_breakdown(player1, player2):
    """Calculate the individual stat similarity percentages."""
    p1 = find_player(player1)
    p2 = find_player(player2)

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


def get_overall_breakdown_similarity(player1, player2):
    """Return the average of the individual stat similarities."""
    breakdown = get_similarity_breakdown(player1, player2)

    if breakdown is None:
        return None

    return round(
        sum(breakdown.values()) / len(breakdown),
        2,
    )
