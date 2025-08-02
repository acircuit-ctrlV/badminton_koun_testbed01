import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import date

# --- Excel Processing Logic ---
def process_table_data(table_data_df, shuttle_val, walkin_val, court_val, real_shuttle_val, last_row_to_process):
    """
    Processes the DataFrame: counts slashes, performs calculations,
    and returns updated DataFrame and results.
    """
    # Convert DataFrame to a list of lists for easier cell-level manipulation
    processed_data_list = table_data_df.values.tolist()
    processed_data = [list(row) for row in processed_data_list]

    total_shuttlecock_grand = 0

    # Loop through rows up to dynamic_last_row_to_process
    for i in range(last_row_to_process):
        if i >= len(processed_data):
            break  # Stop if we exceed the actual number of rows

        name_cell_value = str(processed_data[i][0]).strip()
        if not name_cell_value:
            # Clear calculated fields for empty name rows
            if 2 < len(processed_data[i]):
                processed_data[i][2] = ''
            if 3 < len(processed_data[i]):
                processed_data[i][3] = ''
            continue

        # --- CHANGE: Counting 'l' instead of '/' ---
        total_row_slashes = 0
        # Iterate through game columns (indices 4 to 23)
        for col_idx in range(4, 24):
            if col_idx < len(processed_data[i]):  # Ensure column exists for the current row
                cell_value = str(processed_data[i][col_idx])
                total_row_slashes += cell_value.count('l')

        total_shuttlecock_grand += total_row_slashes

        # Update 'Total /' column (index 2)
        if 2 < len(processed_data[i]):
            processed_data[i][2] = total_row_slashes
        else:
            # Extend row if it's too short for this column
            while len(processed_data[i]) <= 2:
                processed_data[i].append('')
            processed_data[i][2] = total_row_slashes

        # Update 'Price' column (index 3)
        if 3 < len(processed_data[i]):
            processed_data[i][3] = (total_row_slashes * shuttle_val) + walkin_val
        else:
            # Extend row if it's too short for this column
            while len(processed_data[i]) <= 3:
                processed_data[i].append('')
            processed_data[i][3] = (total_row_slashes * walkin_val) + walkin_val

    # Ensure enough rows exist for calculations at row 22 and 23 (indices 21 and 22)
    while len(processed_data) < 23:
        processed_data.append([''] * len(table_data_df.columns))

    sum_d = 0  # Sum of 'Total /' column
    sum_e = 0  # Sum of 'Price' column
    for i in range(0, last_row_to_process):
        if i < len(processed_data):  # Ensure row exists
            if str(processed_data[i][0]).strip():  # Only sum if 'Name' column is not empty
                if 2 < len(processed_data[i]):  # Check if 'Total /' column exists
                    try:
                        sum_d += float(processed_data[i][2])
                    except (ValueError, TypeError):
                        pass  # Ignore if value is not a number
                if 3 < len(processed_data[i]):  # Check if 'Price' column exists
                    try:
                        sum_e += float(processed_data[i][3])
                    except (ValueError, TypeError):
                        pass  # Ignore if value is not a number

    # New calculations from the VBA code
    old_solution_sum = ((total_shuttlecock_grand / 4) * real_shuttle_val) + court_val

    results = {
        "total_slashes": total_shuttlecock_grand,
        "old_solution_sum": old_solution_sum,
        "net_price_sum": sum_e,
        "new_solution_minus_old_solution": sum_e - old_solution_sum,
        "sum_D": sum_d  # This is the sum of 'Total /' column
    }

    # Convert the processed list of lists back to a DataFrame
    updated_table_df = pd.DataFrame(processed_data, columns=table_data_df.columns)
    return updated_table_df, results


def dataframe_to_image(df, date_text=""):
    """
    Converts a pandas DataFrame to a Pillow Image object with aligned columns,
    and adds a title and a date.
    """
    try:
        font_path = "THSarabunNew.ttf"
        font = ImageFont.truetype(font_path, 20)
        title_font = ImageFont.truetype(font_path, 28)
    except IOError:
        st.warning(f"Font file '{font_path}' not found. Using default font.")
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Calculate column widths based on the maximum width of text in each column
    column_widths = {}
    for col in df.columns:
        # Get the width of the column header
        header_width = font.getbbox(str(col))[2]
        # Get the max width of all cell values in the column
        max_value_width = max([font.getbbox(str(item))[2] for item in df[col]]) if not df[col].empty else 0
        column_widths[col] = max(header_width, max_value_width)

    # Add some padding to each column
    column_padding = 10
    total_width = sum(column_widths.values()) + (len(column_widths) + 1) * column_padding
    
    # Calculate image dimensions
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
    header_height = line_height + column_padding
    row_height = line_height + 5  # Add a little extra space for rows
    
    title_text = "ตารางก๊วน"
    title_height = title_font.getbbox(title_text)[3] - title_font.getbbox(title_text)[1]
    
    img_width = total_width + 40
    img_height = title_height + line_height + 20 + header_height + (len(df) * row_height) + 40
    
    # Create the image
    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)
    
    x_offset = 20
    y_offset = 20
    
    # Draw title
    draw.text((x_offset, y_offset), title_text, font=title_font, fill='black')
    
    # Draw the date
    date_x = x_offset + title_font.getbbox(title_text)[2] + 20
    date_y = y_offset + (title_height - (font.getbbox(date_text)[3] - font.getbbox(date_text)[1])) / 2
    draw.text((date_x, date_y), date_text, font=font, fill='black')
    
    # Draw the red box around the date
    box_padding = 5
    box_coords = [
        date_x - box_padding,
        date_y - box_padding,
        date_x + font.getbbox(date_text)[2] + box_padding,
        date_y + (font.getbbox(date_text)[3] - font.getbbox(date_text)[1]) + box_padding
    ]
    draw.rectangle(box_coords, outline="red", width=2)
    
    y_offset_start = y_offset + title_height + 10
    y_offset = y_offset_start
    
    # Draw headers
    current_x = x_offset
    for col in df.columns:
        draw.text((current_x, y_offset), str(col), font=font, fill='black')
        current_x += column_widths[col] + column_padding
        
    y_offset += header_height
    
    # Draw data rows
    for _, row in df.iterrows():
        current_x = x_offset
        for col in df.columns:
            draw.text((current_x, y_offset), str(row[col]), font=font, fill='black')
            current_x += column_widths[col] + column_padding
        y_offset += row_height
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return buf

# --- Streamlit Session State Management ---
headers = ["Name", "Time", "Total /", "Price", "game1", "game2", "game3", "game4", "game5",
           "game6", "game7", "game8", "game9", "game10", "game11", "game12", "game13",
           "game14", "game15", "game16", "game17", "game18", "game19", "game20"]

initial_data_list = [
    ["is", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["ploy", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["mart", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["voy", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["jump", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["tong", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["k", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["song", "18:00", "", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nice", "18:00", "", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["nut", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["temp", "18:00", "", "", "l", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    ["pin", "18:00", "", "", "l", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
]
for row in initial_data_list:
    while len(row) < len(headers):
        row.append("")

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(initial_data_list, columns=headers)
if 'results' not in st.session_state:
    st.session_state.results = None
if 'warning_message' not in st.session_state:
    st.session_state.warning_message = ""
if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today()

st.title("คิดเงินค่าตีก๊วน")

# --- Date input and display ---
st.header("ใส่ข้อมูล")
col_date_picker, col_date_display = st.columns([1, 4])
with col_date_picker:
    selected_date = st.date_input("เลือกวันที่", st.session_state.current_date)
with col_date_display:
    st.session_state.current_date = selected_date
    date_to_display = st.session_state.current_date.strftime("%d/%m/%Y")
    st.markdown(f'<div style="border:2px solid red; padding:5px; margin-top:20px; width: fit-content;">{date_to_display}</div>', unsafe_allow_html=True)

# --- Input Parameters ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    shuttle_val = st.number_input("ค่าลูก:", value=20, step=1)
with col2:
    walkin_val = st.number_input("ค่าคอร์ดต่อคน:", value=60, step=1)
with col3:
    court_val = st.number_input("ค่าเช่าคอร์ด:", value=0, step=1)
with col4:
    real_shuttle_val = st.number_input("ค่าลูกตามจริง:", value=0, step=1)

st.header("ตารางก๊วน")

# Define the column configuration to freeze the "Name" column
#column_configuration = {
#    "Name": st.column_config.TextColumn(
#        "Name",
#        help="The name of the player",
#        fixed="left"
#    )
#}
#
## Pass the column configuration to st.data_editor
#edited_df = st.data_editor(
#    st.session_state.df,
#    num_rows="dynamic",
#    use_container_width=True,
#    key="main_data_editor",
#    column_config=column_configuration
#)
edited_df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    key="main_data_editor"
)


if st.button("Calculate"):
    st.session_state.df = edited_df

    st.session_state.warning_message = ""

    df_to_process = st.session_state.df.fillna('')

    dynamic_last_row_to_process = 0
    for idx, row in df_to_process.iterrows():
        if str(row['Name']).strip():
            dynamic_last_row_to_process = idx + 1

    if dynamic_last_row_to_process == 0:
        st.warning("No names found in the table to process. Please enter data in the 'Name' column.")
        st.session_state.results = None
    else:
        invalid_columns = []
        if len(df_to_process.columns) >= 24:
            for col_idx in range(4, 24):
                if col_idx < len(df_to_process.columns):
                    total_slashes_in_column = df_to_process.iloc[:dynamic_last_row_to_process, col_idx].astype(str).str.count('l').sum()
                    if total_slashes_in_column % 4 != 0:
                        invalid_columns.append(df_to_process.columns[col_idx])
        else:
            st.session_state.warning_message = "The table does not have enough columns for full game data validation (expected at least 24 columns for 'game1' to 'game20')."

        if invalid_columns:
            if st.session_state.warning_message:
                st.session_state.warning_message += f"\n\nAdditionally, the total slash count in the following columns is not divisible by 4: {', '.join(invalid_columns)}"
            else:
                st.session_state.warning_message = f"Game ที่ลูกเเบดไม่ลงตัว: {', '.join(invalid_columns)}"

        updated_df, results = process_table_data(
            df_to_process, shuttle_val, walkin_val, court_val, real_shuttle_val,
            last_row_to_process=dynamic_last_row_to_process
        )
        st.session_state.df = updated_df
        st.session_state.results = results

        st.rerun()
        
if st.session_state.warning_message:
    st.warning(st.session_state.warning_message)

st.header("สรุป")
if st.session_state.results:
    st.write(f"**จำนวนลูกเเบดที่ใช้ทั้งหมด:** {st.session_state.results['total_slashes']/4} units")
    st.write(f"**คิดราคาเเบบเก่า:** {st.session_state.results['old_solution_sum']}")
    st.write(f"**คิดราคาเเบบใหม่:** {st.session_state.results['net_price_sum']}")
    st.write(f"**ราคาใหม่ - ราคาเก่า:** {st.session_state.results['new_solution_minus_old_solution']}")
elif st.session_state.results is None and not st.session_state.warning_message:
    st.write("No calculations performed yet or no valid data to process.")

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
