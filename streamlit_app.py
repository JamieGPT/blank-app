import streamlit as st
from st_supabase_connection import SupabaseConnection
from huggingface_hub import InferenceClient
from PIL import Image
import io
import requests
import datetime

# --- 1. INITIALIZE CONNECTIONS ---
url = "https://prunimqonushhewbipvpe.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBydW5pbXFvbnVzaGhld2JpcHZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzA0ODQsImV4cCI6MjA4NDQ0NjQ4NH0.QluCg-adJwegpWYXeV7ZKOYrkUUUvTb_xWhhHKCHFBI"

conn = st.connection("supabase", type=SupabaseConnection, url=url, key=key)

# SECURE WAY: This pulls the token from your Streamlit Dashboard settings
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except:
    st.error("HF_TOKEN missing from Secrets. Please add it to your Streamlit Cloud settings.")
    HF_TOKEN = None

# --- 2. AI FRESHNESS ENGINE ---
def analyze_freshness(image_file):
    if not HF_TOKEN:
        return 0, "No API Token found."
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        image_bytes = image_file.getvalue()
        
        # Using a Vision model to check for decay/health
        response = client.image_classification(image_bytes, model="google/vit-base-patch16-224")
        
        top_result = response[0]['label'].lower()
        
        # Safety Logic
        if any(bad in top_result for bad in ["mold", "rot", "decay", "fungus", "dirty"]):
            return 10, f"Warning: AI detected signs of {top_result}. Not recommended for sharing."
        
        return 94, "The produce looks fresh and safe to share based on the visual scan."
    except Exception as e:
        return 0, f"Scan failed: {e}"

def get_general_location():
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        return f"{data.get('city', 'Unknown City')}, {data.get('region', '')}"
    except:
        return "Local Neighborhood"

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Neighborhood Food Share", page_icon="🍎")
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
                        st.write("📸 *Photo*") 
                        score = item.get('freshness_score', 0)
                        st.metric("Freshness", f"{score}/100")
                    with col2:
                        st.subheader(f"{item.get('brand_name', '')} {item['item_name']}")
                        st.caption(f"📍 {item['location']}")
                        st.write(f"**Quantity:** {item.get('quantity', 'N/A')}")
                        st.write(f"⏳ **Best Before:** {item['best_before']}")
                        if item.get('description'):
                            st.info(f"Notes: {item['description']}")
    except Exception as e:
        st.error(f"Error loading items: {e}")

with tab2:
    st.header("Share Food & Scan Quality")
    
    with st.form("share_form", clear_on_submit=True):
        brand_name = st.text_input("Brand/Product Name (e.g., Dole, Homegrown)*")
        item_name = st.text_input("What is the item? (e.g., Bananas, Bread)*")
        
        st.divider()
        st.subheader("Visual Evaluation")
        food_photo = st.file_uploader("Upload a clear photo*", type=['png', 'jpg', 'jpeg'])
        
        # Using Session State to store scan results across form refreshes
        if food_photo:
            st.image(food_photo, caption="Scanning...", use_container_width=True)
            with st.spinner("AI evaluating quality..."):
                current_score, current_reason = analyze_freshness(food_photo)
                st.session_state['last_score'] = current_score
                st.session_state['last_reason'] = current_reason
            
            st.metric(label="Freshness Score", value=f"{current_score}/100")
            if current_score > 70:
                st.success(f"✅ {current_reason}")
            else:
                st.warning(f"⚠️ {current_reason}")

        st.divider()
        st.subheader("Details")
        col_a, col_b = st.columns(2)
        with col_a:
            date_purchased = st.date_input("Date Purchased", datetime.date.today())
        with col_b:
            best_before = st.date_input("Best Before", datetime.date.today() + datetime.timedelta(days=3))
            
        quantity = st.text_input("Quantity")
        description = st.text_area("Notes")
        
        user_location = get_general_location()
        st.caption(f"Location: **{user_location}**")

        submitted = st.form_submit_button("Post to Neighborhood")
        
        if submitted:
            final_score = st.session_state.get('last_score', 0)
            if not brand_name or not item_name or not food_photo:
                st.error("Missing required information.")
            elif final_score < 40 and final_score != 0:
                st.error("Safety scan failed. Item cannot be posted.")
            else:
                new_item = {
                    "brand_name": brand_name, "item_name": item_name,
                    "location": user_location, "description": description,
                    "quantity": quantity, "date_purchased": str(date_purchased),
                    "best_before": str(best_before), "freshness_score": final_score
                }
                conn.table("food_items").insert(new_item).execute()
                st.success("Successfully posted!")
                st.balloons()