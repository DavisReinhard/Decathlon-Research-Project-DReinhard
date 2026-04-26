from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Decathlon Event Alignment Dashboard",
    layout="wide",
)

st.title("Decathlon Event Alignment Dashboard")

DATA_FOLDERS = {
    "Big Ten": "Big 10 Meets",
    "SEC": "SEC Meets",
    "Big 12": "Big 12 Meets",
    "ACC": "ACC Meets",
    "D2 Nationals": "D2",
}

REQUIRED_COLS = [
    "Final Place",
    "Athlete",
    "POINTS",
    "100m",
    "LJ",
    "SP",
    "HJ",
    "400m",
    "110mH",
    "DT",
    "PV",
    "JT",
    "1500m",
]

EVENT_ORDER = ["100m", "LJ", "SP", "HJ", "400m", "110H", "DT", "PV", "JT", "1500m"]
CONFERENCE_ORDER = ["ACC", "Big 12", "Big Ten", "SEC", "D2 Nationals"]


def time_to_seconds_strict(x):
    s = str(x).strip()
    if ":" not in s:
        raise ValueError(f"1500m not in M:SS.ss format: {x}")
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)


def z_within(s):
    sd = s.std(ddof=0)
    if sd == 0:
        return s * 0.0
    return (s - s.mean()) / sd


@st.cache_data(show_spinner=False)
def load_data():
    base_dir = Path(__file__).resolve().parent
    frames = []

    for group, folder_name in DATA_FOLDERS.items():
        data_dir = base_dir / folder_name
        files = sorted(data_dir.glob("*.csv"))
        if len(files) == 0:
            raise FileNotFoundError(f"No CSV files found for {group} in: {data_dir}")

        for f in files:
            tmp = pd.read_csv(f)
            missing = set(REQUIRED_COLS) - set(tmp.columns)
            if missing:
                raise ValueError(f"{group} | {f.name} is missing columns: {sorted(missing)}")

            tmp = tmp.copy()
            tmp["conference"] = group
            group_tag = group.replace(" ", "").replace("-", "")
            tmp["meet_id"] = f"{group_tag}_{f.stem}"
            frames.append(tmp)

    df_all = pd.concat(frames, ignore_index=True)
    df = df_all.copy()
    return df


def build_analysis(df):
    df = df.copy()
    event_cols = ["100m", "LJ", "SP", "HJ", "400m", "110mH", "DT", "PV", "JT", "1500m"]
    bad_tokens = {"DNS", "DNF", "NH", "NT", "NM", "NP", "DQ", "NA", "-", "--", ""}

    for col in event_cols:
        s = df[col]
        ss = s.astype(str).str.strip()
        mask = s.isna() | ss.str.upper().isin(bad_tokens)
        if mask.any():
            raise ValueError(f"Invalid event marks found in column '{col}'.")

    df["overall_place"] = -df["Final Place"]
    df["1500m_sec"] = df["1500m"].apply(time_to_seconds_strict)

    df_rank = df.copy()
    rank_event_cols = ["100m", "LJ", "SP", "HJ", "400m", "110mH", "DT", "PV", "JT"]
    num_cols = [c + "_num" for c in rank_event_cols]

    for c in rank_event_cols:
        s = df_rank[c].astype(str).str.strip()
        extracted = s.str.extract(r"([0-9]*\.?[0-9]+)")[0]
        df_rank[c + "_num"] = pd.to_numeric(extracted, errors="coerce")

    bad_parse = df_rank[df_rank[num_cols].isna().any(axis=1)]
    if len(bad_parse) > 0:
        raise ValueError(
            f"STOP: {len(bad_parse)} rows have non-numeric event marks after parsing. "
            "Fix upstream CSV(s)."
        )

    g = df_rank.groupby("meet_id")
    df_rank["rank_100m"] = g["100m_num"].rank(ascending=True, method="min")
    df_rank["rank_400m"] = g["400m_num"].rank(ascending=True, method="min")
    df_rank["rank_110H"] = g["110mH_num"].rank(ascending=True, method="min")
    df_rank["rank_1500m"] = g["1500m_sec"].rank(ascending=True, method="min")
    df_rank["rank_LJ"] = g["LJ_num"].rank(ascending=False, method="min")
    df_rank["rank_SP"] = g["SP_num"].rank(ascending=False, method="min")
    df_rank["rank_HJ"] = g["HJ_num"].rank(ascending=False, method="min")
    df_rank["rank_DT"] = g["DT_num"].rank(ascending=False, method="min")
    df_rank["rank_PV"] = g["PV_num"].rank(ascending=False, method="min")
    df_rank["rank_JT"] = g["JT_num"].rank(ascending=False, method="min")

    rank_cols = [c for c in df_rank.columns if c.startswith("rank_")]
    spearman_rank = (
        (-df_rank[rank_cols])
        .corrwith(df_rank["overall_place"], method="spearman")
        .rename("spearman_rho")
        .reset_index()
        .rename(columns={"index": "event"})
    )
    spearman_rank["event"] = spearman_rank["event"].str.replace("^rank_", "", regex=True)
    spearman_rank = spearman_rank.sort_values("spearman_rho", ascending=False)

    df_z = df_rank.copy()
    num_col2 = [
        "100m_num",
        "400m_num",
        "110mH_num",
        "1500m_sec",
        "LJ_num",
        "SP_num",
        "HJ_num",
        "DT_num",
        "PV_num",
        "JT_num",
    ]
    missing = [c for c in num_col2 if c not in df_z.columns]
    if missing:
        raise ValueError(f"Missing required numeric columns: {missing}.")

    g = df_z.groupby("meet_id")
    df_z["z_100m"] = g["100m_num"].transform(lambda s: z_within(-s))
    df_z["z_400m"] = g["400m_num"].transform(lambda s: z_within(-s))
    df_z["z_110H"] = g["110mH_num"].transform(lambda s: z_within(-s))
    df_z["z_1500m"] = g["1500m_sec"].transform(lambda s: z_within(-s))
    df_z["z_LJ"] = g["LJ_num"].transform(z_within)
    df_z["z_SP"] = g["SP_num"].transform(z_within)
    df_z["z_HJ"] = g["HJ_num"].transform(z_within)
    df_z["z_DT"] = g["DT_num"].transform(z_within)
    df_z["z_PV"] = g["PV_num"].transform(z_within)
    df_z["z_JT"] = g["JT_num"].transform(z_within)

    z_cols = [c for c in df_z.columns if c.startswith("z_")]
    pearson_z = (
        df_z[z_cols]
        .corrwith(df_z["overall_place"], method="pearson")
        .rename("pearson_r")
        .reset_index()
        .rename(columns={"index": "event"})
    )
    pearson_z["event"] = pearson_z["event"].str.replace("^z_", "", regex=True)
    pearson_z = pearson_z.sort_values("pearson_r", ascending=False)

    corr_list = []
    for conf, d in df_rank.groupby("conference"):
        s = (-d[rank_cols]).corrwith(d["overall_place"], method="spearman")
        s.name = conf
        corr_list.append(s)
    rank_wide = pd.concat(corr_list, axis=1)
    rank_wide.index = rank_wide.index.str.replace("^rank_", "", regex=True)
    rank_wide["mean_rho"] = rank_wide.mean(axis=1)
    rank_wide["range_rho"] = rank_wide.max(axis=1) - rank_wide.min(axis=1)

    corr_list = []
    for conf, d in df_z.groupby("conference"):
        s = d[z_cols].corrwith(d["overall_place"], method="pearson")
        s.name = conf
        corr_list.append(s)
    z_wide = pd.concat(corr_list, axis=1)
    z_wide.index = z_wide.index.str.replace("^z_", "", regex=True)
    z_wide["mean_r"] = z_wide.mean(axis=1)
    z_wide["range_r"] = z_wide.max(axis=1) - z_wide.min(axis=1)

    meet_corrs = []
    for mid, d in df_z.groupby("meet_id"):
        row = {"meet_id": mid, "conference": d["conference"].iloc[0]}
        for ev in z_cols:
            row[ev.replace("z_", "")] = d[ev].corr(d["overall_place"], method="pearson")
        meet_corrs.append(row)
    meet_corrs = pd.DataFrame(meet_corrs)

    return df_rank, df_z, spearman_rank, pearson_z, rank_wide, z_wide, meet_corrs


def filter_by_conference(df, selected_conferences):
    return df[df["conference"].isin(selected_conferences)].copy()


df_raw = load_data()
conference_options = [c for c in CONFERENCE_ORDER if c in df_raw["conference"].unique().tolist()]
selected_conferences = st.multiselect(
    "Conference",
    options=conference_options,
    default=conference_options,
)

if len(selected_conferences) == 0:
    st.warning("Select at least one conference.")
    st.stop()

df_filtered = filter_by_conference(df_raw, selected_conferences)
(
    df_rank,
    df_z,
    spearman_rank,
    pearson_z,
    rank_wide,
    z_wide,
    meet_corrs,
) = build_analysis(df_filtered)

st.subheader("Summary Tables")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Spearman (Rank Method)**")
    st.dataframe(spearman_rank.reset_index(drop=True), use_container_width=True)
with col2:
    st.markdown("**Pearson (Z-Score Method)**")
    st.dataframe(pearson_z.reset_index(drop=True), use_container_width=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "Figure 1",
        "Figure 2",
        "Figure 3",
        "Figure 4",
        "Figure 5",
        "Figure 6",
        "RQ1 Scatter",
    ]
)

with tab1:
    plot_df = spearman_rank.copy().sort_values("spearman_rho", ascending=True)
    fig1 = px.bar(
        plot_df,
        x="spearman_rho",
        y="event",
        orientation="h",
        title="Figure 1: (RQ1) Event rank alignment with overall placing",
        labels={"spearman_rho": "Spearman ρ with overall_score (higher = stronger alignment)", "event": ""},
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    plot_df = pearson_z.copy().sort_values("pearson_r", ascending=True)
    fig2 = px.bar(
        plot_df,
        x="pearson_r",
        y="event",
        orientation="h",
        title="Figure 2: (RQ2) Event z-score alignment with overall placing",
        labels={"pearson_r": "Pearson r with overall_score (higher = stronger alignment)", "event": ""},
    )
    fig2.update_traces(marker_color="orange")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    plot_df = rank_wide["range_rho"].sort_values(ascending=True)
    fig3 = px.bar(
        x=plot_df.values,
        y=plot_df.index,
        orientation="h",
        title="Figure 3: (RQ3) Conference-to-conference variability by event (rank method)",
        labels={"x": "Range across conferences (bigger = more different)", "y": ""},
    )
    fig3.update_traces(marker_color="green")
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    plot_df = z_wide["range_r"].sort_values(ascending=True)
    fig4 = px.bar(
        x=plot_df.values,
        y=plot_df.index,
        orientation="h",
        title="Figure 4: (RQ3) Conference-to-conference variability by event (z-score method)",
        labels={"x": "Range across conferences (bigger = more different)", "y": ""},
    )
    fig4.update_traces(marker_color="maroon")
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    confs = [c for c in CONFERENCE_ORDER if c in z_wide.columns]
    M = z_wide[confs].copy()
    M = M.loc[M.mean(axis=1).sort_values(ascending=False).index]
    fig5 = px.imshow(
        M,
        aspect="auto",
        labels={"color": "Pearson r with overall_score", "x": "", "y": ""},
        title="Figure 5: Event importance by conference (z-score method)",
    )
    st.plotly_chart(fig5, use_container_width=True)

with tab6:
    events = [c for c in meet_corrs.columns if c not in ["meet_id", "conference"]]
    order = meet_corrs[events].mean().sort_values(ascending=False).index.tolist()
    long_df = meet_corrs.melt(
        id_vars=["meet_id", "conference"],
        value_vars=order,
        var_name="event",
        value_name="pearson_r",
    )
    fig6 = px.box(
        long_df,
        x="pearson_r",
        y="event",
        points=False,
        orientation="h",
        title="Figure 6: Meet-to-meet variability of event importance (z-score method)",
        labels={
            "pearson_r": "Meet-level Pearson r with overall placing (higher = stronger alignment)",
            "event": "",
        },
    )
    st.plotly_chart(fig6, use_container_width=True)

with tab7:
    rank_wide_plot = rank_wide.reindex(EVENT_ORDER).dropna(subset=["mean_rho", "range_rho"])
    x = rank_wide_plot["mean_rho"]
    y = rank_wide_plot["range_rho"]
    x_cut = x.mean()
    y_cut = y.mean()

    scatter_df = pd.DataFrame({"event": rank_wide_plot.index, "mean_rho": x.values, "range_rho": y.values})
    fig7 = px.scatter(
        scatter_df,
        x="mean_rho",
        y="range_rho",
        text="event",
        title="RQ1: Event strength vs stability (rank method)",
        labels={
            "mean_rho": "Mean Spearman ρ across conferences (strength)",
            "range_rho": "Range Spearman ρ across conferences (variability)",
        },
    )
    fig7.update_traces(textposition="top right")
    fig7.add_vline(x=x_cut, line_width=1)
    fig7.add_hline(y=y_cut, line_width=1)
    fig7.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.98,
        text="High variability<br>Low strength",
        showarrow=False,
        opacity=0.6,
    )
    fig7.add_annotation(
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        text="High variability<br>High strength",
        showarrow=False,
        opacity=0.6,
        xanchor="right",
    )
    fig7.add_annotation(
        xref="paper",
        yref="paper",
        x=0.02,
        y=0.02,
        text="Low variability<br>Low strength",
        showarrow=False,
        opacity=0.6,
    )
    fig7.add_annotation(
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.02,
        text="Low variability<br>High strength",
        showarrow=False,
        opacity=0.6,
        xanchor="right",
    )
    st.plotly_chart(fig7, use_container_width=True)
