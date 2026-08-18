import streamlit as st
from nba_backend import (compare_players_data, get_similarity_breakdown, find_player, find_player_suggestions, get_similar_players, get_similarity_with_roles, comparison_df, AVAILABLE_SEASONS)

st.set_page_config(
    page_title="NEXUS — NBA Player Comparison",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Sidebar navigation / settings
if "page" not in st.session_state:
    st.session_state.page = "Compare Players"
if "theme" not in st.session_state:
    st.session_state.theme = "Nexus Dark"
if "accent" not in st.session_state:
    st.session_state.accent = "Indigo"

with st.sidebar:
    st.markdown("## NEXUS.")
    st.caption("NBA Player Analytics")
    st.markdown("---")

    st.markdown("**MODES**")
    if st.button("↔  Player Comparison", use_container_width=True):
        st.session_state.page = "Compare Players"
    if st.button("👤  Player Explorer", use_container_width=True):
        st.session_state.page = "Player Explorer"
    if st.button("📊  Stat Explorer", use_container_width=True):
        st.session_state.page = "Stat Explorer"

    st.markdown("**APP**")
    if st.button("⚙  Settings", use_container_width=True):
        st.session_state.page = "Settings"
    if st.button("✦  Credits", use_container_width=True):
        st.session_state.page = "Credits"

    st.markdown("---")
    st.caption("NEXUS · NBA Player Similarity")


st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 50% 0%, #18233d 0%, #0b0f17 42%, #080b11 100%);
        color: #f5f7fb;
    }
    .block-container {
        max-width: 1000px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }
    .brand {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.06em;
        margin-bottom: 0.1rem;
    }
    .brand-dot { color: #667cff; }
    .subtitle {
        color: #8e99ad;
        font-size: 0.9rem;
        margin-bottom: 2.5rem;
    }
    .input-label {
        color: #aab3c4;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }
    div[data-baseweb="input"] {
        background: #111722;
        border: 1px solid #273143;
        border-radius: 8px;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #667cff;
        box-shadow: 0 0 0 1px #667cff;
    }
    div[data-baseweb="input"] input { color: #f5f7fb; }
    .result-card {
        margin-top: 2rem;
        background: rgba(17, 23, 34, 0.88);
        border: 1px solid #293449;
        border-radius: 14px;
        padding: 2rem;
    }
    .match-title {
        text-align: center;
        color: #8994a9;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.18em;
        margin-bottom: 0.7rem;
    }
    .players {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 750;
        margin-bottom: 1.6rem;
    }
    .vs {
        color: #667085;
        font-weight: 500;
        margin: 0 0.35rem;
    }
    .score {
        text-align: center;
        font-size: 4.2rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: -0.06em;
        margin-top: 0.5rem;
        background: linear-gradient(90deg, #7c8cff, #a7b0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .score-label {
        text-align: center;
        color: #8994a9;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 0.7rem;
        margin-bottom: 2.4rem;
    }
    .section-title {
        color: #f5f7fb;
        font-size: 1rem;
        font-weight: 750;
        margin: 1.2rem 0 1rem 0;
    }
    .stat-card {
        background: #111722;
        border: 1px solid #293449;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        text-align: center;
    }
    .stat-name {
        color: #8e99ad;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .stat-value {
        color: #f5f7fb;
        font-size: 1.35rem;
        font-weight: 750;
        margin-top: 0.35rem;
    }
    .helper {
        color: #727d91;
        font-size: 0.78rem;
        text-align: center;
        margin-top: 0.8rem;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #5d7cff, #7864ef);
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 700;
        padding: 0.65rem 1.3rem;
    }
    div.stButton > button:hover {
        border: none;
        filter: brightness(1.08);
        transform: translateY(-1px);
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0a0e16;
        border-right: 1px solid #20283a;
    }
    section[data-testid="stSidebar"] h2 {
        letter-spacing: -0.05em;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent;
        border: 1px solid transparent;
        color: #aab3c4;
        text-align: left;
        font-weight: 600;
        margin: 0.15rem 0;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #151c2a;
        border-color: #293449;
        color: #f5f7fb;
        transform: none;
    }

    .settings-card, .credits-card {
        background: rgba(17, 23, 34, 0.88);
        border: 1px solid #293449;
        border-radius: 14px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #293449;
        border-radius: 12px;
        overflow: hidden;
    }

    .footer {
        text-align: center;
        color: #596478;
        font-size: 0.72rem;
        margin-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.page == "Settings":
    st.markdown('<div class="brand">SETTINGS<span class="brand-dot">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customize how NEXUS looks and feels.</div>', unsafe_allow_html=True)
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### Appearance")
    st.session_state.theme = st.selectbox("Theme", ["Nexus Dark", "Midnight", "Light"], index=["Nexus Dark", "Midnight", "Light"].index(st.session_state.theme))
    st.session_state.accent = st.selectbox("Accent color", ["Indigo", "Blue", "Purple", "Green"], index=["Indigo", "Blue", "Purple", "Green"].index(st.session_state.accent))
    st.toggle("Compact layout", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "Credits":
    st.markdown('<div class="brand">CREDITS<span class="brand-dot">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">The people, tools, and data behind NEXUS.</div>', unsafe_allow_html=True)
    st.markdown('<div class="credits-card">', unsafe_allow_html=True)
    st.markdown("### NEXUS NBA Player Analytics")
    st.write("Built as an NBA player comparison and similarity project.")
    st.markdown("**Creator**  \nYour Name")
    st.markdown("**Technology**  \nPython · Streamlit")
    st.markdown("**Data**  \nNBA statistics / project backend")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "Player Explorer":
    st.markdown('<div class="brand">PLAYER EXPLORER<span class="brand-dot">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Search any player in the NEXUS database and explore their profile.</div>', unsafe_allow_html=True)

    selected_season = st.selectbox(
        "Season",
        AVAILABLE_SEASONS,
        key="player_explorer_season",
    )

    search = st.text_input(
        "Search player",
        placeholder="e.g. Nikola Jokic",
        key="explorer_search",
    ).strip()

    if search:
        player = find_player(search, season=selected_season)

        if isinstance(player, list):
            st.markdown('<div class="section-title">Choose a player</div>', unsafe_allow_html=True)
            selected = st.selectbox("Matches", player, label_visibility="collapsed", key="explorer_match")
            player = find_player(selected, season=selected_season)

        if player is None:
            st.warning("No player found. Try a different name.")
        elif isinstance(player, dict):
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="match-title">PLAYER PROFILE</div>'
                f'<div class="players">{player["player_name"]}</div>',
                unsafe_allow_html=True,
            )

            stat_items = [
                ("PPG", player["ppg"]),
                ("RPG", player["rpg"]),
                ("APG", player["apg"]),
                ("SPG", player["spg"]),
                ("BPG", player["bpg"]),
                ("3P%", player["three_pct"]),
                ("FT%", player["ft_pct"]),
                ("GAMES", player["games"]),
            ]

            cols = st.columns(4)
            for i, (label, value) in enumerate(stat_items):
                with cols[i % 4]:
                    if label in {"3P%", "FT%"}:
                        text = f"{float(value):.1f}%"
                    elif label == "GAMES":
                        text = f"{int(value)}"
                    else:
                        text = f"{float(value):.1f}"

                    st.markdown(
                        f'<div class="stat-card">'
                        f'<div class="stat-name">{label}</div>'
                        f'<div class="stat-value">{text}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            role_row = comparison_df[
                (comparison_df["player_name"] == player["player_name"])
                & (comparison_df["season"] == selected_season)
            ]

            if not role_row.empty:
                role_row = role_row.iloc[0]
                st.markdown('<div class="section-title">Player Roles</div>', unsafe_allow_html=True)

                role_cols = st.columns(2)
                with role_cols[0]:
                    st.markdown(
                        f'<div class="stat-card"><div class="stat-name">PRIMARY ROLE</div>'
                        f'<div class="stat-value">{role_row["primary_role"]}</div></div>',
                        unsafe_allow_html=True,
                    )
                with role_cols[1]:
                    secondary = role_row["secondary_role"] or "—"
                    st.markdown(
                        f'<div class="stat-card"><div class="stat-name">SECONDARY ROLE</div>'
                        f'<div class="stat-value">{secondary}</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div class="section-title">Similar Players</div>', unsafe_allow_html=True)
            similar = get_similarity_with_roles(player["player_name"], 5, season=selected_season)

            if not similar.empty:
                display = similar.copy()
                display["similarity"] = display["similarity"].map(lambda x: f"{x:.1f}%")
                display.columns = ["Player", "Similarity", "Primary Role", "Secondary Role"]
                st.dataframe(display, use_container_width=True, hide_index=True)
            else:
                st.caption("No similar players were found.")

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="helper">Search for an NBA player to open their NEXUS profile.</div>',
            unsafe_allow_html=True,
        )

elif st.session_state.page == "Stat Explorer":
    st.markdown('<div class="brand">STAT EXPLORER<span class="brand-dot">.</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Explore and rank players across the NEXUS statistical database.</div>', unsafe_allow_html=True)

    stat_options = {
        "Points Per Game": ("ppg", 1),
        "Rebounds Per Game": ("rpg", 1),
        "Assists Per Game": ("apg", 1),
        "Steals Per Game": ("spg", 1),
        "Blocks Per Game": ("bpg", 1),
        "3-Point Percentage": ("three_pct", 1),
        "Free Throw Percentage": ("ft_pct", 1),
        "Games Played": ("games", 0),
    }

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        selected_stat = st.selectbox("Statistic", list(stat_options.keys()), key="stat_explorer_stat")
    with c2:
        selected_season = st.selectbox("Season", AVAILABLE_SEASONS, key="stat_explorer_season")
    with c3:
        top_n = st.slider("Players", 5, 50, 15, key="stat_explorer_n")

    column, _ = stat_options[selected_stat]
    table = comparison_df[
        comparison_df["season"] == selected_season
    ][["player_name", column]].copy()
    table = table.sort_values(column, ascending=False).head(top_n).reset_index(drop=True)
    table.insert(0, "Rank", range(1, len(table) + 1))

    if column in {"three_pct", "ft_pct"}:
        table[selected_stat] = table[column].map(lambda x: f"{x:.1f}%")
    elif column == "games":
        table[selected_stat] = table[column].map(lambda x: f"{int(x)}")
    else:
        table[selected_stat] = table[column].map(lambda x: f"{x:.1f}")

    table = table[["Rank", "player_name", selected_stat]]
    table.columns = ["Rank", "Player", selected_stat]

    st.markdown('<div class="section-title">Leaderboard</div>', unsafe_allow_html=True)
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.caption(f"Showing the top {len(table)} players by {selected_stat.lower()}.")

else:
    st.markdown(
    """
    <div class="brand">NEXUS<span class="brand-dot">.</span></div>
    <div class="subtitle">
        NBA player comparison powered by statistics and player similarity
    </div>
    """,
    unsafe_allow_html=True,
)

    selected_season = st.selectbox(
        "Season",
        AVAILABLE_SEASONS,
        key="comparison_season",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="input-label">Player 1</div>', unsafe_allow_html=True)
        player1 = st.text_input(
            "Player 1",
            placeholder="e.g. Tatum",
            label_visibility="collapsed",
            key="player1_input",
        )

    with col2:
        st.markdown('<div class="input-label">Player 2</div>', unsafe_allow_html=True)
        player2 = st.text_input(
            "Player 2",
            placeholder="e.g. Jokic",
            label_visibility="collapsed",
            key="player2_input",
        )

    compare_clicked = st.button("Compare Players", type="primary")

    if compare_clicked:
        player1 = player1.strip()
        player2 = player2.strip()

        if not player1 or not player2:
            st.warning("Please enter both player names.")
        elif player1.lower() == player2.lower():
            st.warning("Please enter two different players.")
        else:
            try:
                result = compare_players_data(player1, player2, season=selected_season)
            except Exception as exc:
                st.error("The player comparison could not be completed.")
                st.caption(f"Backend error: {type(exc).__name__}: {exc}")
                st.stop()

            if result is None:
                st.error("One or both players could not be found.")
                st.stop()

            if not isinstance(result, dict):
                st.error("The backend returned an unexpected result.")
                st.stop()

            if result.get("multiple_matches", False):
                st.warning(
                    "Multiple players matched. Please enter a more specific player name."
                )

                for key, label in [
                    ("player1", "Player 1 matches"),
                    ("player2", "Player 2 matches"),
                ]:
                    matches = result.get(key)

                    if isinstance(matches, list) and matches:
                        names = []
                        for match in matches:
                            if isinstance(match, dict):
                                name = match.get("player_name") or match.get("Player")
                                if name:
                                    names.append(str(name))
                            elif isinstance(match, str):
                                names.append(match)

                        if names:
                            st.markdown(f"**{label}:**")
                            st.write(", ".join(names))

                st.stop()

            try:
                breakdown = get_similarity_breakdown(player1, player2, season=selected_season)
            except Exception:
                breakdown = None

            st.markdown('<div class="result-card">', unsafe_allow_html=True)

            st.markdown(
                '<div class="match-title">PLAYER MATCH</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="players">
                    {player1}
                    <span class="vs">vs</span>
                    {player2}
                </div>
                """,
                unsafe_allow_html=True,
            )

            similarity = result.get("similarity")

            if similarity is not None:
                try:
                    similarity_value = float(similarity)
                    st.markdown(
                        f'<div class="score">{similarity_value:.1f}%</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div class="score-label">Overall Similarity</div>',
                        unsafe_allow_html=True,
                    )
                except (TypeError, ValueError):
                    st.warning("The similarity score was returned in an invalid format.")
            else:
                st.warning(
                    "The comparison completed, but no overall similarity score was returned."
                )

            if isinstance(breakdown, dict) and breakdown:
                st.markdown(
                    '<div class="section-title">Similarity Breakdown</div>',
                    unsafe_allow_html=True,
                )

                cols = st.columns(3)
                items = list(breakdown.items())

                for i, (stat, score) in enumerate(items):
                    with cols[i % 3]:
                        try:
                            score_text = f"{float(score):.1f}%"
                        except (TypeError, ValueError):
                            score_text = str(score)

                        st.markdown(
                            f"""
                            <div class="stat-card">
                                <div class="stat-name">{stat}</div>
                                <div class="stat-value">{score_text}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown(
            '<div class="helper">Enter two NBA players to see how statistically similar they are.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="footer">NEXUS · NBA Player Similarity</div>',
        unsafe_allow_html=True,
    )
