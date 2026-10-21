"""
Author: Tiago Monteiro
Date: 21-12-2025
Fixture Intelligence: pre-match analysis for fixtures with no public tracking data.
Combines recent form / H2H / standings sourced from public stats sites (FBref, Understat,
Sofascore, FotMob, Transfermarkt) with a qualitative tactical read. This is intentionally
separate from the tracking-data pages, which require SkillCorner-style positional data
that does not exist publicly for these matches.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from src import styling
from src.fixture_intel import load_fixtures, load_all_fixtures, score_predictions, match_results_table
from src.schema import FixtureIntel

HOME_COLOR = "#32FF69"
AWAY_COLOR = "#3385FF"
DRAW_COLOR = "#B0B0B0"
RESULT_COLORS = {"W": "#32FF69", "D": "#B0B0B0", "L": "#FF4B4B"}
CONFIDENCE_BADGE = {
    "high": ("#1FC96D", "High confidence"),
    "medium": ("#E8A33D", "Medium confidence"),
    "low": ("#B0B0B0", "Low confidence — sparse public data"),
}

styling.setup_page("Fixture Intelligence")


def render_form_badges(results: list) -> str:
    """Render a W/D/L streak as inline HTML badges, oldest to most recent."""
    if not results:
        return "<span style='color:#6C757D;'>No recent form data found</span>"
    spans = []
    for r in results:
        color = RESULT_COLORS.get(r.upper(), "#B0B0B0")
        spans.append(
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:24px;height:24px;border-radius:50%;background:{color};color:white;"
            f"font-weight:700;font-size:0.75rem;margin-right:4px;'>{r.upper()}</span>"
        )
    return "".join(spans)


def render_side_summary(label: str, team: str, form, color: str) -> str:
    """Render one team's form/position summary block as HTML."""
    bits = []
    if form.league_position:
        pos_txt = f"P{form.league_position}"
        if form.points is not None:
            pos_txt += f" · {form.points} pts"
        bits.append(f"<div style='color:#6C757D;font-size:0.85rem;'>{pos_txt}</div>")
    if form.goals_for is not None or form.goals_against is not None:
        gf = form.goals_for if form.goals_for is not None else "?"
        ga = form.goals_against if form.goals_against is not None else "?"
        bits.append(f"<div style='color:#6C757D;font-size:0.85rem;'>GF {gf} / GA {ga} (last 5)</div>")
    if form.note and not form.results:
        bits.append(f"<div style='color:#6C757D;font-size:0.85rem;font-style:italic;'>{form.note}</div>")
    return (
        f"<div style='background:white;border:2px solid rgba(40,167,69,0.15);border-radius:12px;"
        f"padding:1rem;'>"
        f"<div style='font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;color:{color};"
        f"font-weight:700;margin-bottom:0.35rem;'>{label}</div>"
        f"<div style='font-weight:700;font-size:1.1rem;margin-bottom:0.5rem;'>{team}</div>"
        f"<div style='margin-bottom:0.5rem;'>{render_form_badges(form.results)}</div>"
        + "".join(bits)
        + "</div>"
    )


def outcome_bar(fixture: FixtureIntel):
    """Horizontal stacked bar for the qualitative Win/Draw/Win lean."""
    estimate = fixture.analysis.outcome_estimate if fixture.analysis else []
    if not estimate or len(estimate) != 3:
        return None
    home_p, draw_p, away_p = [round(v * 100) for v in estimate]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Lean"], x=[home_p], name=fixture.home_team, orientation="h",
        marker_color=HOME_COLOR, text=f"{home_p}%", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Lean"], x=[draw_p], name="Draw", orientation="h",
        marker_color=DRAW_COLOR, text=f"{draw_p}%", textposition="inside",
    ))
    fig.add_trace(go.Bar(
        y=["Lean"], x=[away_p], name=fixture.away_team, orientation="h",
        marker_color=AWAY_COLOR, text=f"{away_p}%", textposition="inside",
    ))
    fig.update_layout(
        barmode="stack", height=110, margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True, legend=dict(orientation="h", y=-0.4),
        xaxis=dict(visible=False, range=[0, 100]), yaxis=dict(visible=False),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    return fig


def render_fixture_card(fixture: FixtureIntel):
    badge_color, badge_label = CONFIDENCE_BADGE.get(fixture.confidence, CONFIDENCE_BADGE["low"])

    st.markdown(
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"margin-bottom:0.75rem;'>"
        f"<div style='font-weight:700;font-size:1.3rem;'>{fixture.home_team} vs {fixture.away_team}</div>"
        f"<div style='background:{badge_color};color:white;padding:0.25rem 0.75rem;border-radius:999px;"
        f"font-size:0.75rem;font-weight:700;'>{badge_label}</div>"
        f"</div>"
        f"<div style='color:#6C757D;font-size:0.9rem;margin-bottom:1rem;'>"
        f"{fixture.competition} · {fixture.country} · {fixture.kickoff_date} {fixture.kickoff_time}</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(render_side_summary("Home", fixture.home_team, fixture.home_form, HOME_COLOR), unsafe_allow_html=True)
    with c2:
        st.markdown(render_side_summary("Away", fixture.away_team, fixture.away_form, AWAY_COLOR), unsafe_allow_html=True)

    if fixture.h2h_summary:
        st.markdown(f"**Head-to-head:** {fixture.h2h_summary}")

    if fixture.key_notes:
        st.markdown("**Notes**")
        for note in fixture.key_notes:
            st.markdown(f"- {note}")

    if fixture.analysis:
        st.markdown("**Tactical read**")
        st.markdown(fixture.analysis.tactical_read)
        st.markdown(f"**Lean:** {fixture.analysis.prediction_lean}")
        fig = outcome_bar(fixture)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        if fixture.analysis.confidence_note:
            st.caption(fixture.analysis.confidence_note)
    else:
        st.info("Analysis pending — research not yet compiled for this fixture.")

    if fixture.sources:
        st.caption("Sources: " + ", ".join(fixture.sources))


def main():
    styling.load_css()

    st.markdown(
        "<div class='app-header'><div>"
        "<h1 class='app-headline' style='font-size:1.6rem;'>Fixture Intelligence</h1>"
        "<p class='app-subtitle'>Pre-match analysis for fixtures without public tracking data — "
        "form, H2H and standings from public stats sources, plus a tactical read.</p>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    with st.expander("Methodology — how the tactical read is built"):
        st.markdown(
            "Tactical reads draw on a 67-factor match-determination framework, applied only where "
            "real sourced data supports it: recent win/loss streak psychology, injury and suspension "
            "burden, points-per-game trajectory and goals-conceded trend, head-to-head \"bogey team\" "
            "effects, new-manager bounce / club unrest, and xG differential where a source publishes it "
            "(mainly Europe's top-5 leagues via Understat/FBref).\n\n"
            "**Not used**, because this app has no source for them on these fixtures: set-piece conversion, "
            "pressing intensity, defensive line height (all need tracking/event data), weather, pitch "
            "condition, and referee tendencies. The outcome-lean bar is a qualitative estimate reflecting "
            "the factors above — not a calibrated statistical model.\n\n"
            "**Calibrated from a live backtest (2026-09-19/20 slate, 17 fixtures):** the first round of "
            "predictions scored 7/17 (41%) on straight Home/Draw/Away picks — tying a naive \"always "
            "pick Home\" baseline, with head-to-head and early-season attack/defense signals actually "
            "scoring *below* that baseline. Rules adopted since: (1) default to **Draw** when the top two "
            "outcome probabilities sit within ~8 points of each other and both sides have similar recent "
            "form, rather than forcing a winner; (2) discount any form/goals line built from under 5 "
            "games as noisy; (3) let a team conceding under ~0.7-1.0 goals/game pull BTTS and Over-2.5 "
            "toward No/Under even against a strong attack; (4) treat head-to-head history as a tiebreaker, "
            "not a primary signal, especially in leagues with heavy year-to-year squad turnover; (5) "
            "flag relegation six-pointers and new-manager-bounce games as high-variance rather than "
            "backing a confident contrarian pick.\n\n"
            "**Second backtest (2026-09-26/27 slate, 17 fixtures, jackpot-curated):** best strategy scored "
            "9/17 (53%) — still barely better than a coin flip. Draws hit 41% on this slate (following "
            "29% on the first). Rules added: (6) raise the default Draw prior to ~35-40% for "
            "volatility-curated slates, not the generic ~25%; (7) when one side's data is a genuine gap "
            "(\"not found\"), default to Draw rather than backing the better-known side; (8) when market "
            "odds and independent news research disagree on a leg, treat that disagreement itself as a "
            "Draw signal; (9) run odds-based and news-based predictions as parallel separate lines, not "
            "one blended narrative — on this slate they only agreed on 3 of their combined correct picks.\n\n"
            "**Update (2026-10-07): every jackpot is predicted from scratch.** The draw pattern did not "
            "hold: draws fell to 23% and 24% on the next two jackpots, and the most common result was "
            "different almost every week. Rules (1), (6), (7) and (8) are retired. Each game is now "
            "judged only on its own odds and its own dated facts, with no draw prior, no quotas and no "
            "patterns carried over from earlier jackpots. "
            "Full log: `documentation/prediction_factor_matrix.md`."
        )

    all_fixtures = load_all_fixtures()
    scoreboard = score_predictions(all_fixtures)
    if not scoreboard.empty:
        with st.expander(f"Prediction scoreboard — {scoreboard['Total'].max()} completed fixtures scored", expanded=False):
            st.markdown(
                "Every predictor (this app, plus any external site prediction recorded before "
                "kickoff) scored against actual results, across every slate on file — not just "
                "the current one. This is the same table used to calibrate the rules above."
            )
            st.dataframe(
                scoreboard.style.format({"Hit Rate": "{:.1f}%"}),
                use_container_width=True, hide_index=True,
            )
            details = match_results_table(all_fixtures)
            if not details.empty:
                st.markdown("**Per-match breakdown**")
                st.dataframe(details, use_container_width=True, hide_index=True)

    fixtures = load_fixtures()

    if not fixtures:
        st.warning(
            "No fixture intelligence data found yet. Expected a JSON file under "
            "`data/fixture_intelligence/`."
        )
        return

    st.sidebar.markdown("## Filters")
    dates = sorted({f.kickoff_date for f in fixtures})
    date_filter = st.sidebar.multiselect("Date", dates, default=dates)
    countries = sorted({f.country for f in fixtures})
    country_filter = st.sidebar.multiselect("Country", countries, default=countries)

    filtered = [f for f in fixtures if f.kickoff_date in date_filter and f.country in country_filter]
    filtered.sort(key=lambda f: (f.kickoff_date, f.kickoff_time))

    st.markdown(f"### Today & tomorrow — {len(filtered)} fixtures")

    table_rows = []
    for f in filtered:
        table_rows.append({
            "Date": f.kickoff_date,
            "Time": f.kickoff_time,
            "Country": f.country,
            "Competition": f.competition,
            "Home": f.home_team,
            "Away": f.away_team,
            "Home form": "".join(f.home_form.results) or "—",
            "Away form": "".join(f.away_form.results) or "—",
            "Lean": f.analysis.prediction_lean if f.analysis else "Pending",
            "Confidence": f.confidence,
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### Match detail")

    options = {f"{f.home_team} vs {f.away_team} — {f.kickoff_date} {f.kickoff_time}": f.match_id for f in filtered}
    if not options:
        st.info("No fixtures match the current filters.")
        return

    selected_label = st.selectbox("Select a fixture", list(options.keys()))
    selected_id = options[selected_label]
    selected = next(f for f in filtered if f.match_id == selected_id)

    with st.container(border=True):
        render_fixture_card(selected)


if __name__ == "__main__":
    main()
