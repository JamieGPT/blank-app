import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import datetime

# --- 1. INITIALIZE DATABASE ---
url = "https://prunimqonushhewbipvpe.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydW5pbXFvbnVzaGhld2JpcHZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzA0ODQsImV4cCI6MjA4NDQ0NjQ4NH0.QluCg-adJwegpWYXeV7ZKOYrkUUUvTb_xWhhHKCHFBI"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. LOCATION SCRAMBLER FUNCTION ---
def get_general_location():
    try:
        # This looks up the town/city based on the user's internet connection
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        return f"{data.get('city', 'Unknown City')}, {data.get('region', '')}"
    except:
        return "Local Neighborhood"

# --- 3. APP INTERFACE ---
st.title("Neighborhood Food Share 🍎")

tab1, tab2 = st.tabs(["Find Food", "Share Food"])

with tab1:
    st.header("Available Food")
    try:
        items = conn.table("food_items").select("*").order("created_at", desc=True).execute()
        if items.data:
            for item in items.data:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        # Display photo if available
                        if item.get('image_url'):
                            st.image(item['image_url'])
                    with col2:
                        st.subheader(item['item_name'])
                        st.caption(f"📍 Location: {item['location']}")
                        st.write(f"**Quantity:** {item['quantity']}")
                        st.write(f"⏳ **Best Before:** {item['best_before']}")
                        st.write(f"📅 **Purchased:** {item['date_purchased']}")
                        if item.get('description'):
                            st.info(f"Notes: {item['description']}")
        else:
            st.info("No food items available. Be the first to share!")
    except Exception as e:
        st.error(f"Error loading items: {e}")

with tab2:
    st.header("Post an Item")
    st.write("Fill out the details below to share with your neighbors.")
    
    with st.form("share_form", clear_on_submit=True):
        # Mandatory Fields
        item_name = st.text_input("What are you sharing? (Required)*")
        food_photo = st.file_uploader("Upload a Photo (Required)*", type=['png', 'jpg', 'jpeg'])
        
        # Specific Dates
        col_a, col_b = st.columns(2)
        with col_a:
            date_purchased = st.date_input("Date Purchased", datetime.date.today())
        with col_b:
            best_before = st.date_input("Best Before Date", datetime.date.today() + datetime.timedelta(days=3))
            
        # Quantity & Notes
        quantity = st.text_input("Quantity (e.g., 3 bags, 1 dozen, 500g)")
        description = st.text_area("Extra Notes (e.g., 'Organic', 'Needs to be used today')")
        
        # Auto-Location
        user_location = get_general_location()
        st.caption(f"Detecting general location: **{user_location}**")

        submitted = st.form_submit_button("Post to Neighborhood")
        
        if submitted:
            if not item_name or not food_photo:
                st.error("Please provide both a Name and a Photo!")
            else:
                # In a full app, we would upload the photo to Supabase Storage first.
                # For this step, we'll save the text data to get the form working!
                new_item = {
                    "item_name": item_name,
                    "location": user_location,
                    "description": description,
                    "quantity": quantity,
                    "date_purchased": str(date_purchased),
                    "best_before": str(best_before)
                }
                try:
                    conn.table("food_items").insert(new_item).execute()
                    st.success(f"Successfully posted {item_name}!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error saving to database: {e}")