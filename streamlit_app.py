import streamlit as st
from st_supabase_connection import SupabaseConnection

# --- 1. INITIALIZE DATABASE ---
# We are providing the URL and Key directly here to fix the "URL not provided" error.
url = "https://prunimqonushhewbipvpe.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydW5pbXFvbnVzaGhld2JpcHZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzA0ODQsImV4cCI6MjA4NDQ0NjQ4NH0.QluCg-adJwegpWYXeV7ZKOYrkUUUvTb_xWhhHKCHFBI"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# --- 2. APP INTERFACE ---
st.title("Neighborhood Food Share 🍎")
st.write("Connect with neighbors to share extra food and reduce waste.")

# Create two tabs for the app
tab1, tab2 = st.tabs(["Find Food", "Share Food"])

with tab1:
    st.header("Available Food")
    try:
        # Pull data from your Supabase table named 'food_items'
        items = conn.table("food_items").select("*").execute()
        
        if items.data:
            for item in items.data:
                with st.container():
                    st.subheader(f"{item['item_name']}")
                    st.write(f"📍 **Location:** {item['location']}")
                    st.write(f"📝 **Description:** {item['description']}")
                    st.divider()
        else:
            st.info("No food items available right now. Check back later!")
    except Exception as e:
        st.error(f"Could not load items: {e}")

with tab2:
    st.header("Post an Item")
    with st.form("share_form", clear_on_submit=True):
        item_name = st.text_input("What are you sharing? (e.g., Extra Apples)")
        location = st.text_input("General Location (e.g., North Street)")
        description = st.text_area("Details (Best before date, quantity, etc.)")
        
        submitted = st.form_submit_button("Post to Neighborhood")
        
        if submitted:
            if item_name and location:
                # Add the new item to your Supabase table
                new_item = {
                    "item_name": item_name,
                    "location": location,
                    "description": description
                }
                conn.table("food_items").insert(new_item).execute()
                st.success("Item posted successfully!")
                st.balloons()
            else:
                st.warning("Please fill out the item name and location.")