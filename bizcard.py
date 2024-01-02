%%writefile bizcard.py
import easyocr
import cv2
import pandas as pd
import re
import sqlite3
import streamlit as st

# -------------------------------------------Establishing connection to database-------------------------------------------------------
conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
# -----------------------------------Creating table in sql------------------------------------------------------------------------------
table_create_sql = 'CREATE TABLE IF NOT EXISTS mytables(ID INTEGER PRIMARY KEY AUTOINCREMENT,Name TEXT,Designation TEXT,Company_name TEXT,Address TEXT,Contact_number TEXT,Mail_id TEXT,Website_link TEXT,Image BLOB);'
cursor.execute(table_create_sql)
# Commit changes and close the connection
conn.commit()




def upload_database(image):
    # ----------------------------------------Getting data from image using easyocr------------------------------------------------------
    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image, paragraph=True, decoder='wordbeamsearch')
    # -----------------------------------------converting got data to single string------------------------------------------------------
    data = []
    j = 0
    for i in result:
        data.append(result[j][1])
        j += 1
    data
    org_reg = " ".join(data)
    reg = " ".join(data)
    # ------------------------------------------Separating EMAIL---------------------------------------------------------------------------
    email_regex = re.compile(r'''(
	      [a-zA-z0-9]+
	      @
	      [a-zA-z0-9]+
	      \.[a-zA-Z]{2,10}
	      )''', re.VERBOSE)
    email = ''
    for i in email_regex.findall(reg):
        email += i
        reg = reg.replace(i, '')
    # ------------------------------------------Separating phone number---------------------------------------------------------------------------
    phoneNumber_regex = re.compile(r'\+*\d{2,3}-\d{3,10}-\d{3,10}')
    phone_no = ''
    for numbers in phoneNumber_regex.findall(reg):
        phone_no = phone_no + ' ' + numbers
        reg = reg.replace(numbers, '')
    # ------------------------------------------Separating Address---------------------------------------------------------------------------
    address_regex = re.compile(r'\d{2,4}.+\d{6}')
    address = ''
    for addr in address_regex.findall(reg):
        address += addr
        reg = reg.replace(addr, '')
    # ------------------------------------------Separating website link---------------------------------------------------------------------------
    link_regex = re.compile(r'www.?[\w.]+', re.IGNORECASE)
    link = ''
    for lin in link_regex.findall(reg):
        link += lin
        reg = reg.replace(lin, '')
    # ------------------------------------------Separating Designation (only suitable for this dataset)----------------------------------------
    desig_list = ['DATA MANAGER', 'CEO & FOUNDER',
                  'General Manager', 'Marketing Executive', 'Technical Manager']
    designation = ''
    for i in desig_list:
        if re.search(i, reg):
            designation += i
            reg = reg.replace(i, '')
    # ------------------------------------------Separating Company name (only suitable for this dataset)--------------------------------------
    # ----------------------------------to overcome this combine all the three datas to single column ----------------------------------------
    comp_name_list = ['selva digitals', 'GLOBAL INSURANCE',
                      'BORCELLE AIRLINES', 'Family Restaurant', 'Sun Electricals']
    company_name = ''
    for i in comp_name_list:
        if re.search(i, reg, flags=re.IGNORECASE):
            company_name += i
            reg = reg.replace(i, '')
    name = reg.strip()

    # ------------------------------------reading and getting byte values of image-----------------------------------------------------------
    with open(image, 'rb') as file:
        blobimg = file.read()
    # ------------------------------------------Check if the record with the same name already exists-----------------------
    cursor.execute("SELECT ID FROM mytables WHERE Name=?", (name,))
    existing_record = cursor.fetchone()
    if existing_record:
        print(f"Duplicate entry found for '{name}'. Not inserting.")
        return False 


    # -----------------------------------------inserting data into table---------------------------------------------------------------------
    else:
        image_insert = 'INSERT INTO mytables (Name, Designation, Company_name, Address, Contact_number,Mail_id,Website_link,Image) VALUES (?,?,?,?,?,?,?,?);'
        cursor.execute(image_insert, (name, designation, company_name,
                      address, phone_no, email, link, blobimg))
        conn.commit()
        print(f"Record for '{name}' inserted successfully.")
        return True




def extracted_data(image):
    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(image, paragraph=True, decoder='wordbeamsearch')
    img = cv2.imread(image)
    for detection in result:
        top_left = tuple([int(val) for val in detection[0][0]])
        bottom_right = tuple([int(val) for val in detection[0][2]])
        text = detection[1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        img = cv2.rectangle(img, top_left, bottom_right, (204, 0, 34), 5)
        img = cv2.putText(img, text, top_left, font, 0.8,
                          (0, 0, 255), 2, cv2.LINE_AA)

    # plt.figure(figsize=(10, 10))
    # plt.imshow(img)
    # plt.show()
    return img


def show_database():
    new_df = pd.read_sql("SELECT * FROM mytables", con=conn)
    return new_df


# ------------------------------------------setting page configuration in streamlit---------------------------------------------------------
st.set_page_config(page_title='Bizcardx Extraction', layout="wide")

st.balloons()
st.title(':violet[Bizcardx Data Extraction🖼️]')

data_extraction, database_side,update_database,delete= st.tabs(
    ['Data uploading and Viewing', 'Database side','Update or Modify','Delete'])
file_name = 'thiru'
with data_extraction:
    st.markdown(
        "![Alt Text](https://cdn.dribbble.com/users/393235/screenshots/1643374/media/b32f920793005f554f22129c96627c56.gif)")
    st.subheader(':violet[Choose image file to extract data]')
    # ---------------------------------------------- Uploading file to streamlit app ------------------------------------------------------
    uploaded = st.file_uploader('Choose a image file')
    # --------------------------------------- Convert binary values of image to IMAGE ---------------------------------------------------
    if uploaded is not None:
        with open(f'{file_name}.png', 'wb') as f:
            f.write(uploaded.getvalue())
        # ----------------------------------------Extracting data from image (Image view)-------------------------------------------------
        st.subheader(':violet[Image view of Data]')
        if st.button('Extract Data from Image'):
              extracted = extracted_data(f'{file_name}.png')
              st.image(extracted)

        # ----------------------------------------upload data to database----------------------------------------------------------------
        st.subheader(':violet[Upload extracted to Database]')
        if st.button('Upload data'):
            upload_database(f'{file_name}.png')
# --------------------------------------------getting data from database and storing in df variable---------------------------------------
df = show_database()
with database_side:
    st.markdown(
        "![Alt Text](https://cdn.dribbble.com/users/2037413/screenshots/4144417/ar_businesscard.gif)")
    # ----------------------------------------Showing all datas in database---------------------------------------------------------------
    st.title(':violet[All Data in Database]')
    if st.button('Show All'):
        st.dataframe(df)
    # -----------------------------------------Search data in the database----------------------------------------------------------------
    st.subheader(':violet[Search Data by Column]')
    column = str(st.radio('Select column to search', ('Name', 'Designation',
                 'Company_name', 'Address', 'Contact_number', 'Mail_id', 'Website_link'), horizontal=True))
    value = str(st.selectbox('Please select value to search', df[column]))
    if st.button('Search Data'):
        st.dataframe(df[df[column] == value])
#Modify table
# Function to update data
def update_data(conn, cursor, condition_column, condition_value, update_column, new_value):
    update_data_sql = f"UPDATE mytables SET {update_column}=? WHERE {condition_column}=?;"
    cursor.execute(update_data_sql, (new_value, condition_value))
    conn.commit()
    st.success("Data updated successfully.")

# Streamlit app
with update_database:
    st.title("SQLite Data Update")

    # Input for condition and update values
    condition_column = st.radio('Select column to set condition', ('Name', 'Designation', 'Company_name', 'Address', 'Contact_number', 'Mail_id', 'Website_link'), index=0)
    condition_value = st.selectbox('Please select value for condition', df[condition_column])

    update_column = st.radio('Select column to update', ('Name', 'Designation', 'Company_name', 'Address', 'Contact_number', 'Mail_id', 'Website_link'), index=0)
    new_value = st.text_input(f'Enter new value for {update_column}')

    # Button to trigger update
    if st.button("Update Data"):
        if condition_column and condition_value and update_column and new_value:
            update_data(conn, cursor, condition_column, condition_value, update_column, new_value)
        else:
            st.warning("Please enter all required values.")


# Delete
# Function to delete data
def delete_data(condition_value):
    delete_data_sql = f"DELETE FROM mytables WHERE {condition_value} = ?;"
    cursor.execute(delete_data_sql, (value,))
    conn.commit()
    st.success("Data deleted successfully.")

# Streamlit app
with delete:
  st.title("SQLite Data Deletion ")

  # Input for condition value
  condition_value = st.radio('Select column to delete', ('Name', 'Designation',
                        'Company_name', 'Address', 'Contact_number', 'Mail_id', 'Website_link'),horizontal=True, index=0, key="delete_column")
  value = st.selectbox('Please select value to delete', df[condition_value])

  # Button to trigger deletion
  if st.button("Delete Data"):
      if condition_value:
          delete_data(condition_value)
      else:
          st.warning("Please enter a condition value.")


