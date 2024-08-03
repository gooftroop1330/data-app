import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

__HERE__ = Path(__file__).parent
UPLOAD_DIR = __HERE__ / 'uploaded_files'
UPLOAD_DIR.mkdir(exist_ok=True)

st.set_page_config(layout="wide")

st.title("MTC Income Data")
f = st.file_uploader("Upload Data", accept_multiple_files=True, type=["csv"])

def clean_data(df):
    # Drop the unnecessary 'Unnamed: 0' column if it exists
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
    
    # Convert 'Date' column to datetime, handling different formats
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    
    # Convert 'Total' column to float after removing the '$' sign and commas
    df["Total"] = df["Total"].apply(lambda x: float(x.replace('$', '').replace(',', '')))
    
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

# Initialize an empty DataFrame to combine all data
all_data = pd.DataFrame()

# Process uploaded files
if len(f) > 0:
    for file in f:
        # Save the uploaded file permanently
        file_path = UPLOAD_DIR / file.name
        with open(file_path, 'wb') as out_file:
            out_file.write(file.getbuffer())
        
        # Load and clean the uploaded file
        df = load_and_clean_data(file_path)
        # Append the data to the combined DataFrame
        all_data = pd.concat([all_data, df], ignore_index=True)

# Process previously saved files
else:
    for file_path in UPLOAD_DIR.glob('*.csv'):
        df = load_and_clean_data(file_path)
        # Append the data to the combined DataFrame
        all_data = pd.concat([all_data, df], ignore_index=True)

# Generate charts if there is data
if not all_data.empty:
    sun_chart = px.sunburst(
        all_data, names="Company", values="Total", path=["Company", "Name", "Date"]
    )
    pie_chart = px.pie(
        all_data, 
        names="Company", 
        values="Total", 
        color="Company"
    )
    
    # Removing "Name=" from the facet titles
    pie_chart.update_layout(
        annotations=[annotation.update(text=annotation.text.split("=")[-1]) for annotation in pie_chart.layout.annotations]
    )
    
    # Removing the hover data except "Total" and formatting as US currency
    pie_chart.update_traces(hovertemplate='Total: $%{value:.2f}', hoverinfo='label+value')
    
    bar_chart = px.histogram(
        all_data,
        x="Company",
        y="Total",
        color="Name",
        labels={"Total": "Total"},  # Updating the y-axis label
        barmode='group',
        color_discrete_sequence=["#07A459", "#FFFFFF", "#636466"]  # Custom color sequence
    )
    
    # Removing the hover data for "Name" and "Company" and formatting as US currency
    bar_chart.update_traces(hovertemplate='Total: $%{y:.2f}', hoverinfo='skip')
    bar_chart.update_layout(yaxis_title_text='Total', showlegend=False)
    bar_chart.update_xaxes(categoryorder='category ascending')
    
    # Formatting the hover data for Sunburst chart as US currency
    sun_chart.update_traces(hovertemplate='Total: $%{value:.2f}', hoverinfo='label+value')
    
    with st.container():
        bar, pie, sun = st.tabs(["Company Breakdown", "Pie", "Sunburst"])

        bar.plotly_chart(bar_chart, use_container_width=True)
        pie.plotly_chart(pie_chart, use_container_width=True)
        sun.plotly_chart(sun_chart, use_container_width=True)
else:
    st.write("Please upload one or more CSV files to generate the graphs.")
