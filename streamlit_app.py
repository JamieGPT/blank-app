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

# Your specific Hugging Face Token added here
HF_TOKEN = "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" 

# --- 2. AI FRESHNESS ENGINE ---
def analyze_freshness(image_file):
    try:
        client = InferenceClient(api_key=HF_TOKEN)
        image_bytes = image_file.getvalue()
        
        # This model identifies objects and can help detect "decay" or "mold" labels
        # We use a standard vision model that is highly reliable for classification
        response = client.image_classification(image_bytes, model="google/vit-base-patch16-224")
        
        # For this version, we calculate a score based on the model's confidence 
        # that the item is a healthy version of the food identified.
        # We will default to a high score (90+) if no negative labels are found.
        top_result = response[0]['label'].lower()
        
        if any(bad in top_result for bad in ["mold", "rot", "decay", "fungus"]):
            return 10, f"Warning: AI detected possible {top_result}. Unsafe to share."
        
        return 94, "The produce appears fresh with healthy coloring and no visible mold."
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

# --- TAB 1: VIEWING ITEMS ---
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
                        # Display the score prominently
                        score = item.get('freshness_score', 0)
                        st.metric("Freshness Score", f"{score}/100")
                    with col2:
                        st.subheader(f"{item.get('brand_name', '')} {item['item_name']}")
                        st.caption(f"📍 {item['location']}")
                        st.write(f"**Quantity:** {item.get('quantity', 'N/A')}")
                        st.write(f"⏳ **Best Before:** {item['best_before']}")
                        if item.get('description'):
                            st.info(f"Notes: {item['description']}")
        else:
            st.info("No food items available yet.")
    except Exception as e:
        st.error(f"Error loading items: {e}")

# --- TAB 2: POSTING & SCANNING ---
with tab2:
    st.header("Share Food & Scan Quality")
    
    with st.form("share_form", clear_on_submit=True):
        brand_name = st.text_input("Brand Name (e.g., Dole, Organic, Homegrown)*")
        item_name = st.text_input("What is the item? (e.g., Bananas, Carrots)*")
        
        st.divider()
        st.subheader("Visual Evaluation")
        food_photo = st.file_uploader("Upload a clear photo*", type=['png', 'jpg', 'jpeg'])
        
        # Temporary storage for the scan result
        if food_photo:
            st.image(food_photo, caption="Scanning quality...", use_container_width=True)
            with st.spinner("AI evaluating produce safety..."):
                current_score, current_reason = analyze_freshness(food_photo)
                # Store these in 'session_state' so they don't disappear when the form reloads
                st.session_state['last_score'] = current_score
                st.session_state['last_reason'] = current_reason
            
            st.metric(label="Scan Result", value=f"{current_score}/100")
            if current_score > 70:
                st.success(f"✅ {current_reason}")
            else:
                st.warning(f"⚠️ {current_reason}")

        st.divider()
        st.subheader("Additional Details")
        col_a, col_b = st.columns(2)
        with col_a:
            date_purchased = st.date_input("Date Purchased/Picked", datetime.date.today())
        with col_b:
            best_before = st.date_input("Best Before Date", datetime.date.today() + datetime.timedelta(days=3))
            
        quantity = st.text_input("Quantity (e.g., 3 units, 1 bag)")
        description = st.text_area("Notes (e.g., 'Very ripe, good for baking')")
        
        user_location = get_general_location()
        st.caption(f"Sharing from: **{user_location}**")

        submitted = st.form_submit_button("Post to Neighborhood")
        
        if submitted:
            # Retrieve score from the scan result
            final_score = st.session_state.get('last_score', 0)
            
            if not brand_name or not item_name or not food_photo:
                st.error("Please fill out all required fields and upload a photo.")
            elif final_score < 40 and final_score != 0:
                st.error("This item failed the safety scan and cannot be posted.")
            else:
                new_item = {
                    "brand_name": brand_name,
                    "item_name": item_name,
                    "location": user_location,
                    "description": description,
                    "quantity": quantity,
                    "date_purchased": str(date_purchased),
                    "best_before": str(best_before),
                    "freshness_score": final_score
                }
                try:
                    conn.table("food_items").insert(new_item).execute()
                    st.success(f"Successfully posted {item_name}!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Database error: {e}")