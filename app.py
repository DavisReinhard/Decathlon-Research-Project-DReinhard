from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Decathlon Event Alignment Dashboard", layout="wide")
st.title("Decathlon Event Alignment Dashboard")

BASE_DIR = Path(__file__).resolve().parent
FIG_DIR = BASE_DIR / "artifacts" / "figures"
REGEN_COMMAND = "python export_notebook_figures.py"

FIGURES = [
    ("Figure 1", "Figure 1: (RQ1) Event rank alignment with overall placing", "figure1_rq1_rank_alignment.png"),
    ("Figure 2", "Figure 2: (RQ2) Event z-score alignment with overall placing", "figure2_rq2_z_alignment.png"),
    (
        "Figure 3",
        "Figure 3: (RQ3) Conference-to-conference variability by event (rank method)",
        "figure3_conf_variability_rank.png",
    ),
    (
        "Figure 4",
        "Figure 4: (RQ3) Conference-to-conference variability by event (z-score method)",
        "figure4_conf_variability_z.png",
    ),
    ("Figure 5", "Figure 5: Event importance by conference (z-score method)", "figure5_conf_event_heatmap_z.png"),
    (
        "Figure 6",
        "Figure 6: Meet-to-meet variability of event importance (z-score method)",
        "figure6_meet_variability_boxplot_z.png",
    ),
    ("RQ1 Scatter", "RQ1: Event strength vs stability (rank method)", "rq1_strength_vs_stability.png"),
]


def show_figure(filename: str) -> None:
    image_path = FIG_DIR / filename
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
        return
    st.warning(
        f"Missing artifact: `{image_path}`\n\n"
        f"Regenerate with:\n`{REGEN_COMMAND}`"
    )


tabs = st.tabs([tab_title for tab_title, _, _ in FIGURES])
for tab, (_, figure_title, filename) in zip(tabs, FIGURES):
    with tab:
        st.subheader(figure_title)
        show_figure(filename)
