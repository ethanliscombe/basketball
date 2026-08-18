import streamlit as st
from nba_backend import compare_players_data, get_similarity_breakdown

st.set_page_config(
    page_title="NEXUS — NBA Player Comparison",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

st.markdown(
    """
    <div class="brand">NEXUS<span class="brand-dot">.</span></div>
    <div class="subtitle">
        NBA player comparison powered by statistics and player similarity
    </div>
    """,
    unsafe_allow_html=True,
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
            result = compare_players_data(player1, player2)
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
            breakdown = get_similarity_breakdown(player1, player2)
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
