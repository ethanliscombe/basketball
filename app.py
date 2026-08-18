import streamlit as st
import pandas as pd

from nba_backend import (
    find_player_suggestions,
    compare_players_data,
    get_similarity_breakdown,
)


# -----------------------------
# PAGE SETUP
# -----------------------------

st.set_page_config(
    page_title="NBA Player Comparison",
    page_icon="🏀",
    layout="wide",
)

st.title("🏀 NBA Player Comparison")
st.write(
    "Compare NBA players using statistics, player roles, "
    "and similarity scores."
)


# -----------------------------
# PLAYER INPUTS
# -----------------------------

col1, col2 = st.columns(2)

with col1:
    player1 = st.text_input(
        "Player 1",
        placeholder="e.g. Jokic",
    )

with col2:
    player2 = st.text_input(
        "Player 2",
        placeholder="e.g. Luka",
    )


# -----------------------------
# COMPARISON
# -----------------------------

if st.button("Compare", type="primary"):

    if not player1 or not player2:
        st.warning("Enter both players first.")

    else:
        result = compare_players_data(player1, player2)

        if result is None:
            st.error("Could not find one or both players.")

        elif result.get("multiple_matches"):
            st.warning("Multiple players found. Please enter a more specific name.")

            if isinstance(result["player1"], list):
                st.write("Player 1 possibilities:")
                st.write(result["player1"])

            if isinstance(result["player2"], list):
                st.write("Player 2 possibilities:")
                st.write(result["player2"])

        else:
            p1 = result["player1"]
            p2 = result["player2"]

            # Overall similarity
            st.divider()

            st.subheader(
                f"{p1['player_name']} vs {p2['player_name']}"
            )

            st.metric(
                "Overall Similarity",
                f"{result['similarity']:.2f}%"
            )

            # Roles
            role_col1, role_col2 = st.columns(2)

            with role_col1:
                st.markdown(f"### {p1['player_name']}")
                st.write(
                    f"**Primary Role:** {result['role1']['primary']}"
                )
                if result["role1"]["secondary"]:
                    st.write(
                        f"**Secondary Role:** {result['role1']['secondary']}"
                    )

            with role_col2:
                st.markdown(f"### {p2['player_name']}")
                st.write(
                    f"**Primary Role:** {result['role2']['primary']}"
                )
                if result["role2"]["secondary"]:
                    st.write(
                        f"**Secondary Role:** {result['role2']['secondary']}"
                    )

            # Stats
            st.divider()
            st.subheader("📊 Statistics")

            stat_names = {
                "games": "Games",
                "ppg": "PPG",
                "rpg": "RPG",
                "apg": "APG",
                "spg": "SPG",
                "bpg": "BPG",
                "three_pct": "3P%",
                "ft_pct": "FT%",
            }

            stats = []

            for key, label in stat_names.items():
                stats.append(
                    {
                        "Stat": label,
                        p1["player_name"]: p1[key],
                        p2["player_name"]: p2[key],
                    }
                )

            stats_df = pd.DataFrame(stats)

            # Format percentages
            for column in [
                p1["player_name"],
                p2["player_name"],
            ]:
                stats_df[column] = stats_df[column].map(
                    lambda x: f"{x:.2f}"
                )

            st.dataframe(
                stats_df,
                use_container_width=True,
                hide_index=True,
            )

            # Similarity breakdown
            st.divider()
            st.subheader("📈 Similarity Breakdown")

            breakdown = get_similarity_breakdown(
                p1["player_name"],
                p2["player_name"],
            )

            if breakdown:
                breakdown_df = pd.DataFrame(
                    [
                        {
                            "Stat": stat.upper(),
                            "Similarity": f"{score:.2f}%",
                        }
                        for stat, score in breakdown.items()
                    ]
                )

                st.dataframe(
                    breakdown_df,
                    use_container_width=True,
                    hide_index=True,
                )

                chart_df = pd.DataFrame(
                    {
                        "Similarity": breakdown
                    }
                )

                st.bar_chart(chart_df)

            # Similarity explanation
            st.info(
                "The overall similarity score combines the statistical "
                "similarity and the players' role profiles."
            )
