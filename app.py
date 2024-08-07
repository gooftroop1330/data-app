import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from streamlit_theme import st_theme
from bcrypt import checkpw
from time import sleep
from utils import *

__HERE__ = Path(__file__).parent

DB_CONN = create_load_db()

st.set_page_config(page_title="MTC Income Data", page_icon=":bar_chart:", layout="wide")

st.title(":green[MTC] Income Data")


def check_login(un, pw):
    if "PW" in st.secrets and "UN" in st.secrets:
        check_un = st.secrets["UN"]
        if un == check_un and checkpw(
            bytes(pw, encoding="utf-8"), bytes(st.secrets["PW"], encoding="utf-8")
        ):
            st.session_state["logged_in"] = True
        else:
            st.session_state["logged_in"] = False
            st.error("Incorrect username/password combination.")

    else:
        st.error("Configuration invalid.")
    return


@st.dialog("Login")
def login():
    if not st.session_state["logged_in"]:
        un = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            check_login(un, pw)
            st.rerun()
    return


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"] == True:
    # Initialize an empty DataFrame to combine all data
    all_data = load_all_data(db_conn=DB_CONN)

    # File uploader for new data
    uploaded_files = st.sidebar.file_uploader(
        "Upload Data",
        accept_multiple_files=True,
        type=["csv"],
        label_visibility="collapsed",
    )

    # Placeholder for error messages
    upload_error_placeholder = st.empty()

    # Automatically process uploaded files
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                insert_uploaded_file_to_db(uploaded_file=uploaded_file, db_conn=DB_CONN)
            except Exception as e:
                upload_error_placeholder.error(
                    f"Error processing file {uploaded_file.name}: {e}"
                )

    all_data = load_all_data(db_conn=DB_CONN)

    # Get file to company mapping
    st.dataframe(all_data, use_container_width=True)
    # Display list of uploaded files with option to delete

    # Determine the theme
    theme = st_theme()
    if theme is not None:
        base = theme["base"]
    else:
        base = st.get_option("theme.base")

    # Set annotation color and bar colors based on theme
    if base == "dark":
        annotation_color = "#EEEEEE"
        bar_colors = ["#07A459", "#EEEEEE", "#636466"]
    else:
        annotation_color = "#333333"
        bar_colors = ["#07A459", "#333333", "#636466"]

    # Generate charts if there is data
    if not all_data.empty:
        # Calculate the total summation of the 'Total' column
        total_summation = all_data["total"].sum()

        st.subheader(f"Total Summation: ${total_summation:,.2f}")

        sun_chart = px.sunburst(
            all_data, names="company", values="total", path=["company", "name", "date"]
        )
        pie_chart = px.pie(all_data, names="company", values="total", color="company")

        # Removing "Name=" from the facet titles
        pie_chart.update_layout(
            annotations=[
                annotation.update(text=annotation.text.split("=")[-1])
                for annotation in pie_chart.layout.annotations
            ]
        )

        # Removing the hover data except "Total" and formatting as US currency
        pie_chart.update_traces(
            hovertemplate="Total: $%{value:.2f}", hoverinfo="label+value"
        )

        # Create bar chart with annotations for summation
        bar_chart = px.histogram(
            all_data,
            x="company",
            y="total",
            color="name",
            labels={"Total": "total"},  # Updating the y-axis label
            barmode="group",
            color_discrete_sequence=bar_colors,  # Custom color sequence based on theme
        )

        # Calculate summation for each Company
        company_totals = all_data.groupby("company")["total"].sum().reset_index()

        # Add annotations to the bar chart
        annotations = []
        for index, row in company_totals.iterrows():
            annotations.append(
                dict(
                    x=row["company"],
                    y=row["total"]
                    + 5000,  # Adjust the y position slightly above the bar
                    text=f"${row['total']:,.2f}",
                    showarrow=False,
                    font=dict(
                        size=12, color=annotation_color
                    ),  # Set font color based on theme
                    align="center",
                )
            )

        bar_chart.update_layout(annotations=annotations)

        # Removing the hover data for "Name" and "Company" and formatting as US currency
        bar_chart.update_traces(hovertemplate="Total: $%{y:.2f}", hoverinfo="skip")
        bar_chart.update_layout(yaxis_title_text="Total", showlegend=False)
        bar_chart.update_xaxes(categoryorder="category ascending")

        # Formatting the hover data for Sunburst chart as US currency
        sun_chart.update_traces(
            hovertemplate="Total: $%{value:.2f}", hoverinfo="label+value"
        )

        with st.container():
            bar, pie, sun = st.tabs(["Company Breakdown", "Pie", "Sunburst"])

            bar.plotly_chart(bar_chart, use_container_width=True)
            pie.plotly_chart(pie_chart, use_container_width=True)
            sun.plotly_chart(sun_chart, use_container_width=True)
    else:
        st.write("Please upload one or more CSV files to generate the graphs.")
else:
    login()
