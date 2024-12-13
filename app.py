import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px

# Series names and their corresponding IDs
SERIES_MAPPING = {
    "Civilian Labor Force (Seasonally Adjusted)": "LNS11000000",
    "Civilian Employment (Seasonally Adjusted)": "LNS12000000",
    "Civilian Unemployment (Seasonally Adjusted)": "LNS13000000",
    "Unemployment Rate (Seasonally Adjusted)": "LNS14000000",
    "Total Nonfarm Employment (Seasonally Adjusted)": "CES0000000001",
    "Total Private Avg Weekly Hours (All Employees, Seasonally Adjusted)": "CES0500000002",
    "Total Private Avg Weekly Hours (Prod. & Nonsup. Employees, Seasonally Adjusted)": "CES0500000007",
    "Total Private Avg Hourly Earnings (All Employees, Seasonally Adjusted)": "CES0500000003",
    "Total Private Avg Hourly Earnings (Prod. & Nonsup. Employees, Seasonally Adjusted)": "CES0500000008",
}

# Function to fetch data from BLS API
def fetch_bls_data(series_ids, start_year, end_year):
    headers = {'Content-type': 'application/json'}
    data = json.dumps({
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear": end_year
    })
    response = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        st.error(f"Error fetching data: {response.text}")
        return None

# Process data into a DataFrame
def process_data(json_data):
    all_data = []
    for series in json_data['Results']['series']:
        series_id = series['seriesID']
        for item in series['data']:
            year = item['year']
            period = item['period']
            value = item['value']
            if 'M01' <= period <= 'M12':  # Only monthly data
                month = int(period.replace('M', ''))
                all_data.append({"Series Name": series_id, "Year": int(year), "Month": month, "Value": float(value)})
    return pd.DataFrame(all_data)

# Main Streamlit App
def main():
    st.title("BLS Interactive Dashboard")
    st.sidebar.header("Dashboard Settings")
    
    # User Inputs
    selected_names = st.sidebar.multiselect(
        "Select Data Series",
        list(SERIES_MAPPING.keys()),
        default=list(SERIES_MAPPING.keys())
    )
    start_year = st.sidebar.text_input("Start Year", "2023")
    end_year = st.sidebar.text_input("End Year", "2024")
    
    # Convert selected names to series IDs
    selected_ids = [SERIES_MAPPING[name] for name in selected_names]
    
    # Fetch Data
    if st.sidebar.button("Fetch Data"):
        with st.spinner("Fetching data from BLS API..."):
            json_data = fetch_bls_data(selected_ids, start_year, end_year)
            if json_data and 'Results' in json_data:
                df = process_data(json_data)
                
                # Map series IDs back to their names
                reverse_mapping = {v: k for k, v in SERIES_MAPPING.items()}
                df['Series Name'] = df['Series Name'].map(reverse_mapping)
                
                st.success("Data fetched successfully!")
                
                # Display data
                st.subheader("Raw Data")
                st.write(df)
                
                # Plot data
                st.subheader("Visualize Data")
                df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(day=1))
                fig = px.line(
                    df,
                    x="Date",
                    y="Value",
                    color="Series Name",
                    title="BLS Data Trends",
                    labels={"Value": "Value", "Date": "Date", "Series Name": "Data Series"}
                )
                st.plotly_chart(fig)
            else:
                st.error("Failed to retrieve data. Please check your inputs.")

# Run the app
if __name__ == "__main__":
    main()
