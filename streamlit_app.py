import streamlit as st
from st_supabase_connection import SupabaseConnection
import requests
import datetime

# --- 1. INITIALIZE DATABASE ---
url = "https://prunimqonushhewbipvpe.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydW5pbXFvbnVzaGhld2JpcHZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzA0ODQsImV4cCI6MjA4NDQ0NjQ4NH0.QluCg-adJwegpWYXeV7ZKOYrkUUUvTb_xWhhHKCHFBI"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

def get_general_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        return f"{data.get('city', 'Unknown City')}, {data.get('region', '')}"
    except:
        return "Local Neighborhood"

# --- 2. APP INTERFACE ---
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
                        if item.get('image_url'):
                            st.image(item['image_url'])
                        else:
                            st.info("No Image")
                    with col2:
                        st.subheader(f"{item['brand_name']} - {item['item_name']}")
                        st.caption(f"📍 {item['location']}")
                        st.write(f"**Quantity:** {item['quantity']}")
                        st.write(f"⏳ **Best Before:** {item['best_before']}")
                        if item.get('description'):
                            st.info(f"Notes: {item['description']}")
        else:
            st.info("No food items available yet.")
    except Exception as e:
        st.error(f"Error loading items: {e}")

with tab2:
    st.header("Post an Item")
    
    with st.form("share_form", clear_on_submit=True):
        st.subheader("1. Product Details")
        brand_name = st.text_input("Brand Name (e.g., Dole, Kellogg's, or 'Homegrown')*")
        item_name = st.text_input("Product Name (e.g., Bananas, Cereal)*")
        
        st.subheader("2. Photo & Quality Check")
        food_photo = st.file_uploader("Upload a clear photo of the item*", type=['png', 'jpg', 'jpeg'])
        
        is_produce = st.checkbox("Is this loose produce? (Unpackaged fruit/veg)")
        
        if is_produce and food_photo:
            st.warning("🔍 AI Quality Scan Active: Ensure the photo shows any bruises or soft spots.")
        
        st.subheader("3. Shelf Life & Quantity")
        col_a, col_b = st.columns(2)
        with col_a:
            date_purchased = st.date_input("Date Purchased/Picked", datetime.date.today())
        with col_b:
            best_before = st.date_input("Best Before Date", datetime.date.today() + datetime.timedelta(days=3))
            
        quantity = st.text_input("Quantity (e.g., 2 bunches, 1 box)")
        description = st.text_area("Extra Notes (Allergens, storage instructions, etc.)")
        
        user_location = get_general_location()
        st.caption(f"Posting from: **{user_location}**")

        submitted = st.form_submit_button("Post to Neighborhood")
        
        if submitted:
            if not brand_name or not item_name or not food_photo:
                st.error("Brand, Product Name, and Photo are all required!")
            else:
                # Placeholder for Quality Check Logic
                quality_passed = True 
                if is_produce:
                    # In a production app, we'd send 'food_photo' to a Vision AI here
                    st.toast("AI scanned produce for freshness...")
                
                if quality_passed:
                    new_item = {
                        "brand_name": brand_name,
                        "item_name": item_name,
                        "location": user_location,
                        "description": description,
                        "quantity": quantity,
                        "date_purchased": str(date_purchased),
                        "best_before": str(best_before)
                    }
                    try:
                        conn.table("food_items").insert(new_item).execute()
                        st.success(f"Posted {brand_name} {item_name}!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Database error: {e}")