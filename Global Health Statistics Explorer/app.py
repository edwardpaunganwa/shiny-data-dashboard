import pandas as pd
from shiny.express import input, render, ui
from shiny import reactive
from shinywidgets import render_widget
import plotly.express as px
import faicons as fa

df = pd.read_csv("Global_Health_Stats.csv")

ui.page_opts(title="GLOBAL HEALTH STATISTICS EXPLORER")

with ui.sidebar(bg="#f4f7bf"):
    ui.input_selectize(
        "country",
        label="Select Country:",
        choices=["All"] + list(df["country"].unique())
    )

    ui.input_selectize(
        "disease",
        label="Disease:",
        choices=["All"] + list(df["disease_name"].unique())
    )

    ui.input_slider(
        "year_range",
        "Select Year Range:",
        min(df["year"]),
        max(df["year"]),
        (min(df["year"]), max(df["year"]))
    )

    ui.input_radio_buttons(
        "gender",
        "Gender:",
        ["All", "Male", "Female", "Other"]
    )

@reactive.calc
def df_filt():
    df2 = df.copy()
    
    if input.country() != "All":
        df2 = df2[df2["country"] == input.country()]

    if input.disease() != "All":
        df2 = df2[df2["disease_name"] == input.disease()]
   
    if input.gender() != "All":
        df2 = df2[df2["gender"] == input.gender()]

    yr1, yr2 = input.year_range()
    df2 = df2[(df2["year"] >= yr1) & (df2["year"] <= yr2)]

    return df2

with ui.nav_panel("Overview"):

    ui.h2("Overview")

    with ui.layout_columns():

        with ui.value_box(showcase=fa.icon_svg("virus")):
            ui.h5("Total Diseases")

            @render.text
            def total_dis():
                d = df_filt()
                return d["disease_name"].nunique()

        with ui.value_box(showcase=fa.icon_svg("skull")):
            ui.h5("Average Mortality Rate")

            @render.text
            def avg_mortality():
                d = df_filt()
                return round(d["mortality_rate"].mean(), 2)

        with ui.value_box(showcase=fa.icon_svg("heart-pulse")):
            ui.h5("Average Recovery Rate")

            @render.text
            def avg_recovery():
                d = df_filt()
                return round(d["recovery_rate"].mean(), 2)

        with ui.value_box(showcase=fa.icon_svg("flag")):
            ui.h5("Top Recovery Country")

            @render.text
            def best_recovery_country():
                d = df_filt()
                if d.empty:
                    return "No data"

                temp = d.groupby("country")["recovery_rate"].mean().reset_index()
                temp = temp.sort_values("recovery_rate", ascending=False)

                return temp.iloc[0]["country"]

    with ui.layout_columns(col_widths=[6, 6]):

        with ui.card():
            ui.card_header("Most Prevalent Diseases")

            @render_widget
            def plot1():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data available")

                top = d.groupby("disease_name")["population_affected"].sum().reset_index()
                top = top.sort_values("population_affected", ascending=False)
                top = top.head(10)

                p = px.bar(
                    top,
                    x="disease_name",
                    y="population_affected",
                    title="Global Prevalence: Top 10 Diseases",
                )
                p.update_layout(template="simple_white")
                p.update_traces(marker_color="#4A90E2")

                return p

        with ui.card():
            ui.card_header("Most Deadly Diseases")

            @render_widget
            def dd_plot():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data available")

                top = d.groupby("disease_name")["mortality_rate"].mean().reset_index()
                top = top.sort_values("mortality_rate", ascending=False)
                top = top.head(10)

                p2 = px.bar(
                    top,
                    x="disease_name",
                    y="mortality_rate",
                    title="Global Mortality: Top 10 Deadliest Diseases",
                )

                p2.update_layout(template="simple_white")
                p2.update_traces(marker_color="#B0B0B0")

                return p2

    @render.text
    def check_rows():
        return f"Filtered rows: {len(df_filt())}"

with ui.nav_panel("Disease Trends"):

    ui.h2("Trends Over Time")

    ui.input_selectize(
        "trend_metric",
        label="Metric:",
        choices=["Mortality Rate", "Recovery Rate", "Incidence Rate"],
    )

    @render_widget
    def trend_plot():
        d = df_filt()
        d = d.sort_values("year")

        if d.empty:
            return px.line(title="No data available")

        if input.trend_metric() == "Mortality Rate":
            y_col = "mortality_rate"
        elif input.trend_metric() == "Recovery Rate":
            y_col = "recovery_rate"
        else:
            y_col = "incidence_rate"

        dat = d.groupby(["year", "disease_name"], as_index=False)[y_col].mean()

        p = px.line(
            dat,
            x="year",
            y=y_col,
            color="disease_name",
            title=f"{input.trend_metric()} Over Time",
        )

        p.update_layout(template="simple_white")

        return p
    
with ui.nav_panel("Treatments"):

    ui.h2("Treatment Effectiveness")

    with ui.layout_columns(col_widths=[6, 6]):

        with ui.card():
            ui.card_header("Recovery by Treatment Type")

            @render_widget
            def trt_plot():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data available")

                t1 = d.groupby("treatment_type", as_index=False)["recovery_rate"].mean()
                t1 = t1.sort_values("recovery_rate", ascending=False)

                p = px.bar(
                    t1,
                    x="recovery_rate",
                    y="treatment_type",
                    orientation="h",
                    title="Average Recovery Rate by Treatment",
                )

                p.update_layout(template="simple_white", showlegend=False)
                p.update_traces(marker_color="#5CE0BB")

                return p

        with ui.card():
            ui.card_header("Mortality by Treatment Type")

            @render_widget
            def tm_plot():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data available")

                t2 = d.groupby("treatment_type", as_index=False)["mortality_rate"].mean()
                t2 = t2.sort_values("mortality_rate", ascending=True)

                p2 = px.bar(
                    t2,
                    x="mortality_rate",
                    y="treatment_type",
                    orientation="h",
                    title="Average Mortality Rate by Treatment",
                )

                p2.update_layout(template="simple_white", showlegend=False)
                p2.update_traces(marker_color="#F0ACBA")

                return p2

with ui.nav_panel("Socio-Economics"):

    ui.h2("Healthcare & Income")

    with ui.layout_columns(col_widths=[6, 6]):

        with ui.card():
            ui.card_header("Healthcare Access vs Mortality")

            @render_widget
            def hc_plot():
                d = df_filt()
                if d.empty:
                    return px.scatter(title="No data")

                avg = d.groupby("country")[["healthcare_access", "mortality_rate"]].mean()
                avg = avg.reset_index()

                p = px.scatter(
                    avg,
                    x="healthcare_access",
                    y="mortality_rate",
                    text="country",
                    title="Healthcare Access vs Mortality",
                )

                p.update_traces(
                    textposition="top center",
                    marker=dict(size=8, color="#4682B4"),
                )
                p.update_layout(template="simple_white")

                return p

        with ui.card():
            ui.card_header("Income vs Recovery")

            @render_widget
            def inc_plot():
                d = df_filt()
                if d.empty:
                    return px.scatter(title="No data")

                avg = d.groupby("country")[["per_capita_income_usd", "recovery_rate"]].mean()
                avg = avg.reset_index()

                p2 = px.scatter(
                    avg,
                    x="per_capita_income_usd",
                    y="recovery_rate",
                    text="country",
                    title="Per Capita Income vs Recovery",
                )

                p2.update_traces(
                    textposition="top center",
                    marker=dict(size=8, color="#2E8B57"),
                )
                p2.update_layout(template="simple_white")

                return p2

with ui.nav_panel("Country Comparison"):

    ui.h2("Country Comparison")

    with ui.layout_columns(col_widths=[6, 6]):

        with ui.card():
            ui.card_header("Country Performance")

            ui.input_selectize(
                "country_metric",
                label="Select Metric:",
                choices=["Mortality Rate", "Recovery Rate", "Incidence Rate"],
            )

            @render_widget
            def c_plot():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data available")

                if input.country_metric() == "Mortality Rate":
                    y_col = "mortality_rate"
                elif input.country_metric() == "Recovery Rate":
                    y_col = "recovery_rate"
                else:
                    y_col = "incidence_rate"

                dat = d.groupby("country", as_index=False)[y_col].mean()
                dat = dat.sort_values(y_col, ascending=False)
                dat = dat.head(15)

                p = px.bar(
                    dat,
                    x=y_col,
                    y="country",
                    orientation="h",
                    title=f"Top 15 Countries by {input.country_metric()}",
                )

                p.update_layout(template="simple_white", showlegend=False)

                if "Mortality" in input.country_metric():
                    col = "#D59F0A"
                else:
                    col = "#2E8B57"

                p.update_traces(marker_color=col)

                return p

        with ui.card():
            ui.card_header("Most Improved Countries (5 Years)")

            @render_widget
            def improved_plot():
                d = df_filt()
                if d.empty:
                    return px.bar(title="No data")

                top = d.groupby("country")["improvement_in_5_years"].mean().reset_index()
                top = top.sort_values("improvement_in_5_years", ascending=False)
                top = top.head(15)

                p2 = px.bar(
                    top,
                    x="improvement_in_5_years",
                    y="country",
                    orientation="h",
                    title="Top 15 Most Improved",
                )

                p2.update_layout(template="simple_white", showlegend=False)
                p2.update_traces(marker_color="#4169E1")

                return p2

with ui.nav_panel("Age Group Analysis"):

    ui.h2("Age Group Analysis")

    ui.input_selectize(
        "age_metric",
        label="Metric:",
        choices=["mortality_rate", "recovery_rate", "incidence_rate"],
    )

    with ui.layout_columns(col_widths=[6, 6]):

        with ui.card():
            ui.card_header("Age Group")

            @render_widget
            def age_plot1():
                d = df_filt()
                if d.empty:
                    return px.box(title="No data")

                p = px.box(
                    d,
                    x="age_group",
                    y=input.age_metric(),
                    color="age_group",
                    title=f"{input.age_metric()} by Age",
                )

                p.update_layout(template="simple_white", showlegend=False)

                return p

        with ui.card():
            ui.card_header("Age and Gender")

            @render_widget
            def age_plot2():
                d = df_filt()
                if d.empty:
                    return px.box(title="No data")

                p2 = px.box(
                    d,
                    x="age_group",
                    y=input.age_metric(),
                    color="gender",
                    title=f"{input.age_metric()} by Age & Gender",
                )

                p2.update_layout(template="simple_white")

                return p2