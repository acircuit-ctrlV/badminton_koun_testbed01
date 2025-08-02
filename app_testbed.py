import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

# Your existing process_table_data and dataframe_to_image functions remain unchanged

# Initialize headers and initial_data_list as before...

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(initial_data_list, columns=headers)
if 'results' not in st.session_state:
    st.session_state.results = None
if 'warning_message' not in st.session_state:
    st.session_state.warning_message = ""
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

st.title("คิดเงินค่าตีก๊วน")

# Date picker and input section as before...

# Input params as before...

st.header("ตารางก๊วน (Interactive)")

# Prepare DataFrame with index exposed
df = st.session_state.df.copy()
df.reset_index(inplace=True)  # create 'index' column for row numbers

# Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(resizable=True, editable=True)
gb.configure_column("index", header_name="Row", pinned="left", width=60)
gb.configure_column("Name", pinned="left", width=150)
# Optionally fix other columns if needed
grid_opts = gb.build()

# Render interactive grid
grid_response = AgGrid(
    df,
    gridOptions=grid_opts,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    theme="alpine",
    height=400
)

# Capture edited data back into DataFrame
edited = pd.DataFrame(grid_response["data"])
edited = edited.set_index("index")
edited = edited[df.columns.drop("index")]

if st.button("Calculate"):
    st.session_state.df = edited.copy()
    df_to_process = edited.fillna('')
    # same logic to compute dynamic_last_row_to_process & invalid_columns...
    dynamic_last_row_to_process = max(
        (idx for idx, row in df_to_process.iterrows() if str(row['Name']).strip()),
        default=-1
    ) + 1

    if dynamic_last_row_to_process <= 0:
        st.warning("No names found in the table to process. Please enter data in the 'Name' column.")
        st.session_state.results = None
    else:
        invalid_columns = []
        if len(df_to_process.columns) >= 24:
            for col_idx in range(4, 24):
                total = df_to_process.iloc[:dynamic_last_row_to_process, col_idx].astype(str).str.count('l').sum()
                if total % 4 != 0:
                    invalid_columns.append(df_to_process.columns[col_idx])
        else:
            st.session_state.warning_message = "Table column count is less than required (expected at least 24)."

        if invalid_columns:
            msg = f"Game columns with invalid total (not divisible by 4): {', '.join(invalid_columns)}"
            st.session_state.warning_message = st.session_state.warning_message or msg
            if st.session_state.warning_message:
                st.warning(st.session_state.warning_message)

        updated_df, results = process_table_data(
            df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
            last_row_to_process=dynamic_last_row_to_process
        )
        st.session_state.df = updated_df
        st.session_state.results = results
        st.experimental_rerun()

# Show warnings if any
if st.session_state.warning_message:
    st.warning(st.session_state.warning_message)

# Summary section as before...

st.header("สรุป")
if st.session_state.results:
    st.write(f"**จำนวนลูกแบดที่ใช้ทั้งหมด:** {st.session_state.results['total_slashes'] / 4} units")
    st.write(f"**คิดราคาแบบเก่า:** {st.session_state.results['old_solution_sum']}")
    st.write(f"**คิดราคาแบบใหม่:** {st.session_state.results['net_price_sum']}")
    st.write(f"**ราคาใหม่ - ราคาเก่า:** {st.session_state.results['new_solution_minus_old_solution']}")
elif st.session_state.results is None and not st.session_state.warning_message:
    st.write("No calculations performed yet or no valid data to process.")

# Download section as before...
st.markdown("---")
st.subheader("Download ตารางตีก๊วน")

if st.session_state.results:
    date_text_for_image = st.session_state.current_date.strftime("%d/%m/%Y")
    image_bytes = dataframe_to_image(st.session_state.df, date_text_for_image)
    st.download_button(
        label="Download Table as Image",
        data=image_bytes,
        file_name="badminton_table.png",
        mime="image/png"
    )
else:
    st.info("Calculate the results first to enable the download button.")
