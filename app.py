import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

__HERE__ = Path(__file__).parent
UPLOAD_DIR = __HERE__ / "uploaded_files"
UPLOAD_DIR.mkdir(exist_ok=True)



def clean_data(df):
    # Drop the unnecessary 'Unnamed: 0' column if it exists
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Convert 'Date' column to datetime, handling different formats
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Convert 'Total' column to float after removing the '$' sign and commas
    df["Total"] = df["Total"].apply(
        lambda x: float(x.replace("$", "").replace(",", ""))
    )

    # Ensure 'Name' and 'Company' columns are of type string
    df["Name"] = df["Name"].astype(str)
    df["Company"] = df["Company"].astype(str)

    # Sort the DataFrame by 'Date'
    df = df.sort_values("Date")

    return df

def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    df = clean_data(df)
    return df

def load_all_data():
    all_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
    for file_path in UPLOAD_DIR.glob("*.csv"):
        try:
            df = load_and_clean_data(file_path)
            all_data = pd.concat([all_data, df], ignore_index=True)
        except Exception as e:
            st.error(f"Error loading file {file_path.name}: {e}")
    return all_data

def save_uploaded_file(uploaded_file):
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as out_file:
        out_file.write(uploaded_file.getbuffer())
    return file_path

def delete_file(file_name):
    file_path = UPLOAD_DIR / file_name
    if file_path.exists():
        file_path.unlink()

def get_file_company_mapping():
    file_company_mapping = {}
    for file_path in UPLOAD_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(file_path)
            if "Company" in df.columns and not df["Company"].empty:
                company_name = df["Company"].iloc[0]
                file_company_mapping[file_path.name] = company_name
            else:
                file_company_mapping[file_path.name] = "Unknown Company"
        except Exception as e:
            file_company_mapping[file_path.name] = f"Error loading {file_path.name}"
    return file_company_mapping

# Initialize an empty DataFrame to combine all data
all_data = load_all_data()

# File uploader for new data
uploaded_files = st.file_uploader("Upload Data", accept_multiple_files=True, type=["csv"])

# Automatically process uploaded files
if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            file_path = save_uploaded_file(uploaded_file)
            df = load_and_clean_data(file_path)
            all_data = pd.concat([all_data, df], ignore_index=True)
            st.success(f"File {uploaded_file.name} added successfully!")
        except Exception as e:
            st.error(f"Error processing file {uploaded_file.name}: {e}")

# Get file to company mapping
file_company_mapping = get_file_company_mapping()
unique_companies = sorted(list(set(file_company_mapping.values())))

# Display list of uploaded files with option to delete
if unique_companies:
    selected_company_to_delete = st.selectbox("Select a company to delete", unique_companies)
    file_to_delete = [file for file, company in file_company_mapping.items() if company == selected_company_to_delete]
    
    if st.button("Delete Selected Company"):
        for file_name in file_to_delete:
            delete_file(file_name)
        all_data = load_all_data()  # Reload data after deletion
        st.success(f"Files for {selected_company_to_delete} deleted successfully!")

# Clear database button
if st.button("Clear Database"):
    for file_path in UPLOAD_DIR.glob("*.csv"):
        file_path.unlink()
    all_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
    st.success("Database cleared successfully!")

# Determine the theme
theme = st_theme()
if theme is None:
    base = st.get_option("theme.base")
else:
    base = theme["base"]

# Set annotation color and bar colors based on theme
annotation_color = "#333333" if base is None or base == "light" else "#EEEEEE"
bar_colors = ["#07A459", "#333333" if base is None or base == "light" else "#EEEEEE", "#636466"]

# Generate charts if there is data
if not all_data.empty:
    # Calculate the total summation of the 'Total' column
    total_summation = all_data["Total"].sum()

    st.subheader(f"Total Summation: ${total_summation:,.2f}")

    sun_chart = px.sunburst(
        all_data, names="Company", values="Total", path=["Company", "Name", "Date"]
    )
    pie_chart = px.pie(all_data, names="Company", values="Total", color="Company")

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
        x="Company",
        y="Total",
        color="Name",
        labels={"Total": "Total"},  # Updating the y-axis label
        barmode="group",
        color_discrete_sequence=bar_colors,  # Custom color sequence based on theme
    )

    # Calculate summation for each Company
    company_totals = all_data.groupby("Company")["Total"].sum().reset_index()

    # Add annotations to the bar chart
    annotations = []
    for index, row in company_totals.iterrows():
        annotations.append(
            dict(
                x=row["Company"],
                y=row["Total"] + 5000,  # Adjust the y position slightly above the bar
                text=f"${row['Total']:,.2f}",
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
