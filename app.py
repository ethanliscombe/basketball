import streamlit as st
from nba_backend import compare_players_data, get_similarity_breakdown

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Nexus — NBA Player Comparison",
    page_icon="🏀",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background:
            radial-gradient(circle at top center, #182238 0%, #0b0f18 45%, #070a10 100%);
        color: #f5f7fa;
    }

    /* Hide Streamlit default UI */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    /* Main container */
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    /* Logo */
    .logo {
        font-size: 42px;
        font-weight: 900;
        letter-spacing: -2px;
        margin-bottom: 0;
    }

    .logo span {
        color: #6ea8ff;
    }

    .tagline {
        color: #8993a7;
        font-size: 15px;
        margin-top: -8px;
        margin-bottom: 35px;
    }

    /* Player input cards */
    .player-label {
        color: #8e99ad;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: #111722 !important;
        border: 1px solid #283246 !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 15px !important;
        font-size: 16px !important;
    }

    .stTextInput > div > div > input:focus {
        border: 1px solid #6ea8ff !important;
        box-shadow: 0 0 0 1px #6ea8ff !important;
    }

    /* Compare button */
    .stButton > button {
        width: 100%;
        height: 52px;
        border-radius: 12px;
        border: none;
        background: linear-gradient(135deg, #4d8dff, #7567ff);
        color: white;
        font-size: 16px;
        font-weight: 800;
        transition: 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(78, 141, 255, 0.25);
    }

    /* Result card */
    .result-card {
        background: rgba(17, 23, 34, 0.85);
        border: 1px solid #283246;
        border-radius: 20px;
        padding: 35px;
        margin-top: 35px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    }

    .match-title {
        text-align: center;
        color: #8993a7;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
    }

    .players {
        text-align: center;
        font-size: 27px;
        font-weight: 800;
        margin-top: 8px;
    }

    /* Similarity score */
    .score {
        text-align: center;
        font-size: 72px;
        font-weight: 900;
        letter-spacing: -4px;
        margin-top: 10px;
        background: linear-gradient(135deg, #72a7ff, #9c82ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .score-label {
        text-align: center;
        color: #8993a7;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Breakdown */
    .section-title {
        font-size: 20px;
        font-weight: 800;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    .stat-card {
        background: #111722;
        border: 1px solid #283246;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .stat-name {
        color: #9ca7ba;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stat-value {
        font-size: 24px;
        font-weight: 800;
        margin-top: 5px;
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
<div class="logo">NEXUS<span>.</span></div>
<div class="tagline">
NBA player comparison powered by statistics and player similarity
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# PLAYER INPUTS
# --------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="player-label">Player 1</div>',
                unsafe_allow_html=True)

    player1 = st.text_input(
        "Player 1",
        placeholder="e.g. Nikola Jokic",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="player-label">Player 2</div>',
                unsafe_allow_html=True)

    player2 = st.text_input(
        "Player 2",
        placeholder="e.g. Luka Doncic",
        label_visibility="collapsed"
    )


st.write("")

compare = st.button("Compare Players")


# --------------------------------------------------
# COMPARISON
# --------------------------------------------------

if compare:

    if not player1 or not player2:

        st.warning("Enter two NBA players to compare.")

    else:

        result = compare_players_data(player1, player2)
        breakdown = get_similarity_breakdown(player1, player2)

        st.markdown('<div class="result-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="match-title">PLAYER MATCH</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="players">{player1} <span style="color:#667085;">vs</span> {player2}</div>',
            unsafe_allow_html=True
        )

    if result.get("multiple_matches"):
        st.warning("Multiple players matched. Please enter a more specific player name.")
    else:
        st.markdown(
            f"""<div class="score">{result["similarity"]:.1f}%</div>""",
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="score-label">Overall Similarity</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">Similarity Breakdown</div>',
            unsafe_allow_html=True
        )

        # Create columns for breakdown
        cols = st.columns(3)

        items = list(breakdown.items())

    for i, (stat, score) in enumerate(items):
        with cols[i % 3]:
            st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-name">{stat}</div>
                <div class="stat-value">{score:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)
