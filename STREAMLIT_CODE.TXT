import streamlit as st
import pandas as pd

def load_data():
    try:
        # Load the CSV file
        df = pd.read_csv(r'D:\guvi\REDBUS_PROJECT\PROJECT\bus_data.csv')
        
        # Convert time columns to datetime with error handling
        try:
            df['departing_time'] = pd.to_datetime(df['departing_time'], format='%H:%M').dt.time
        except:
            st.warning("Error converting departing_time. Check the time format in your CSV.")
            
        try:
            df['reaching_time'] = pd.to_datetime(df['reaching_time'], format='%H:%M:%S').dt.time
        except:
            st.warning("Error converting reaching_time. Check the time format in your CSV.")
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def main():
    st.title("Bus Transportation Dashboard")
    
    # Load the data
    df = load_data()
    
    if df is not None:
        # Sidebar filters
        st.sidebar.header("Filters")
        
        # Bus category filter
        selected_category = st.sidebar.multiselect(
            "Select Bus Category",
            options=sorted(df['bus_category'].unique()),
            default=sorted(df['bus_category'].unique())
        )
        
        # Route filter
        selected_route = st.sidebar.multiselect(
            "Select Route",
            options=sorted(df['route_name'].unique()),
            default=sorted(df['route_name'].unique())
        )
        
        # Apply filters
        try:
            filtered_df = df[
                (df['bus_category'].isin(selected_category)) &
                (df['route_name'].isin(selected_route))
            ]
            
            # Display filtered data
            st.subheader("Filtered Bus Information")
            if not filtered_df.empty:
                # Select specific columns to display
                display_columns = ['route_name', 'bus_category', 'departing_time', 
                                 'reaching_time', 'seats_available', 'price']
                st.dataframe(filtered_df[display_columns].sort_values('departing_time'))
                
                # Summary statistics
                st.subheader("Summary Statistics")
                summary = pd.DataFrame({
                    'Average Price': [filtered_df['price'].mean()],
                    'Total Available Seats': [filtered_df['seats_available'].sum()],
                    'Number of Buses': [len(filtered_df)]
                })
                st.dataframe(summary.round(2))
                
                # Download button for filtered data
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download filtered data as CSV",
                    data=csv,
                    file_name="filtered_bus_data.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data available for the selected filters.")
                
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
    
if __name__ == '__main__':
    main()