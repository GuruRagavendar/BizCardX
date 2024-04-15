import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import re
import easyocr
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
from io import BytesIO
import base64
from sqlalchemy import text 

# Defining a function to extract the image details
def upload_image(image_bytes):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_bytes, detail = 0)
    result_withcoordinates = reader.readtext(image_bytes)
    name = []
    designation = []
    contact = []
    email = []
    website = []
    street = []
    city = []
    state = []
    pincode = []
    company = []

    for detail in result:
        match1 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+). ([a-zA-Z]+)', detail)
        match2 = re.findall('([0-9]+ [A-Z]+ [A-Za-z]+)., ([a-zA-Z]+)', detail)
        match3 = re.findall('^[E].+[a-z]', detail)
        match4 = re.findall('([A-Za-z]+) ([0-9]+)', detail)
        match5 = re.findall('([0-9]+ [a-zA-z]+)', detail)
        match6 = re.findall('.com$', detail)
        match7 = re.findall('([0-9]+)', detail)

        if detail == result[0]:
            name.append(detail)
        elif detail == result[1]:
            designation.append(detail)
        elif '-' in detail:
            contact.append(detail)
        elif '@' in detail:
            email.append(detail)
        elif "www " in detail.lower() or "www." in detail.lower():
            website.append(detail)
        elif "WWW" in detail:
            website.append(detail + "." + result[result.index(detail) + 1])
        elif match6:
            pass
        elif match1:
            street.append(match1[0][0])
            city.append(match1[0][1])
            state.append(match1[0][2])
        elif match2:
            street.append(match2[0][0])
            city.append(match2[0][1])
        elif match3:
            city.append(match3[0])
        elif match4:
            state.append(match4[0][0])
            pincode.append(match4[0][1])
        elif match5:
            street.append(match5[0] + ' St,')
        elif match7:
            pincode.append(match7[0])
        else:
            company.append(detail)

    if len(company) > 1:
        comp = company[0] + ' ' + company[1]
    else:
        comp = company[0]

    contact_number = contact[0] if contact else None
    alternative_number = contact[1] if len(contact) > 1 else None

    image_details = {'Name': name[0].title(), 'Designation': designation[0].title(), 'Company_Name': comp.title(),
                    'Contact': contact_number, 'Alternative_Contact': alternative_number, 'Email': email[0],
                    'Website': website[0], 'Street': street[0], 'City': city[0], 'State': state[0],
                    'Pincode': pincode[0]}
    
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    return image_details,result_withcoordinates,image_base64

# Creating the StreamLit Page Configuration  
st.set_page_config(
    page_title="BizCardX",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
     )

# Creating the Sidebar
with st.sidebar:
    selected = option_menu("Main Menu", ["Home","Extract Image Details",'Display Data',], 
                icons=['house', 'file-earmark-image','file-earmark-richtext-fill',], menu_icon="menu-button-fill", default_index=0,
                styles={"nav-link-selected": {"background-color": "black"} })
    
    if selected == "Display Data":
        option = st.radio("**Data Manipulation**",["Show Data", "Modify Data", "Delete Data"],
                captions = ["View the data", "Edit the data", "Delete the data"])
        
if selected == "Home":
    st.title(":green[BizCardX:] Extracting Business Card Data with OCR 🗃️")
    st.write("""**The project would require skills in image processing, OCR, GUI development, and
            database management. It would also require careful design and planning of the
            application architecture to ensure that it is scalable, maintainable, and extensible.
            Good documentation and code organization would also be important for the project.
            Overall, the result of the project would be a useful tool for businesses and individuals
            who need to manage business card information efficiently.**""")
    st.subheader(":blue[Technologies Used]",divider='grey')
    st.text("> OCR")
    st.text("> StreamLit GUI")
    st.text("> SQL")
    st.text("> Data Extraction and Manipulation")
    st.subheader('',divider='grey')

#Extracting the text from image
elif selected == 'Extract Image Details':
    st.title("Extracting the Text from the Business Cards")
    uploaded_file = st.file_uploader("**Upload a business card image**", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image_bytes = uploaded_file.read()
        image_details, result,image_base64 = upload_image(image_bytes)
        
        # Convert the bytes to a PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)
        
        
        # Draw bounding boxes around the detected text
        for bbox, text, confidence in result:
            x_min, y_min = bbox[0]
            x_max, y_max = bbox[2]
            draw.rectangle([x_min, y_min, x_max, y_max], outline="green", width=2)
                  
        # Convert the PIL Image back to bytes for display
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        st.image(img_bytes, caption="Uploaded Image with Text Overlay", use_column_width=True)
        df = pd.DataFrame([image_details])
        st.dataframe(df,hide_index = True,use_container_width=True)
    else:
        st.empty()
    if st.button('Add to SQL'):
        engine = create_engine('mysql+mysqlconnector://root:7295*MAthew@localhost/bizcardx')
        try:
            df['Image_Bytes'] = image_base64
            df.to_sql('bizcardx', con=engine, if_exists='append', index_label='ID')
            st.success('Successfully uploaded the Bussiness Card to SQL Database',icon='✔️')
        except Exception as e:
            st.error(f"{e} while adding the data to SQL Database")

elif selected == "Display Data":
    
    # Creating an Engine to connect to MySql Database using SQlAlchemy
    engine = create_engine('mysql+mysqlconnector://root:7295*MAthew@localhost/bizcardx')
    if option == "Show Data":
        st.title('Displaying the Data from :blue[SQL]')
        t1,t2 = st.tabs(["📅 Show table","📇 Show Extracted images"])

        with t1:
            if st.button("Show table"):
                query = "SELECT * FROM bizcardx"
                sqdf = pd.read_sql_query(query, engine)
                st.dataframe(sqdf,hide_index = True, column_order=[col for col in sqdf.columns if col != 'Image_Bytes'],use_container_width=True)
        with t2:
            if st.button("Show Business Cards"):
                query = "select Company_Name,Image_Bytes from bizcardx"
                sqdf = pd.read_sql_query(query, engine)
                for companyname,image in sqdf.to_records(index=False).tolist():
                    image_bytes = base64.b64decode(image)
                    st.image(io.BytesIO(image_bytes), caption=f'{companyname}')
    elif option == "Modify Data":
        engine = create_engine('mysql+mysqlconnector://root:7295*MAthew@localhost/bizcardx')
        def fetch_data():
            query = "SELECT * FROM bizcardx"
            df = pd.read_sql_query(query, engine)
            return df
        st.title('Updating the Data retrieved from :blue[SQL]')
        with st.expander("Show table", expanded=True):
            df = fetch_data()
            edited_df = st.data_editor(df,hide_index = True)
        if st.button("Update Database") and edited_df is not None:
                alter_statement = text("truncate table bizcardx")
                with engine.connect() as connection:
                    connection.execute(alter_statement)
                edited_df.to_sql('bizcardx', con=engine, if_exists='append',index=False)
                st.success("Table updated successfully!")
    elif option == "Delete Data":
        engine = create_engine('mysql+mysqlconnector://root:7295*MAthew@localhost/bizcardx')
        def fetch_data():
            query = "SELECT * FROM bizcardx"
            df = pd.read_sql_query(query, engine)
            return df
        st.title('Updating the Data retrieved from :blue[SQL]')
        with st.expander("Show table", expanded=True):
            df = fetch_data()
            edited_df = st.data_editor(df,hide_index = True,num_rows="dynamic")
        if st.button("Update Database") and edited_df is not None:
                alter_statement = text("truncate table bizcardx")
                with engine.connect() as connection:
                    connection.execute(alter_statement)
                edited_df.to_sql('bizcardx', con=engine, if_exists='append',index=False)
                st.success("Deleted selected rows from table successfully!")     
        