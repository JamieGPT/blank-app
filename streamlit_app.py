import streamlit as st
from st_supabase_connection import SupabaseConnection

# --- 1. INITIALIZE DATABASE ---
# This connects your website to your free Supabase "memory"
conn = st.connection("supabase", type=SupabaseConnection)

st.title("Neighborhood Food Share 🍎")

# --- 2. THE SEARCH & LIST TAB ---
tab1, tab2 = st.tabs(["🔍 Find Food", "➕ Share Food"])

with tab1:
    st.subheader("Available Near You")
    # Pull the live list from your database
    try:
        items = conn.query("*", table="food_items", ttl=0).execute()
        if not items.data:
            st.info("No food posted yet! Be the first to help out.")
        else:
            for item in items.data:
                with st.container(border=True):
                    st.write(f"### {item['name']}")
                    st.write(f"📍 Location: {item['area']}")
                    st.caption(f"Best Before: {item['expiry']}")
                    if st.button("I'm interested!", key=item['id']):
                        st.success("Chat feature coming next! For now, contact the poster.")
    except:
        st.warning("Please connect your Supabase keys in Settings to see live data.")

# --- 3. THE POSTING TAB ---
with tab2:
    st.subheader("Post an Item")
    with st.form("food_entry"):
        name = st.text_input("What are you sharing?")
        expiry = st.date_input("Best Before Date")
        area = st.text_input("Neighborhood/Street (No house numbers!)")
        
        submitted = st.form_submit_button("Post to Neighborhood")
        if submitted and name:
            # Save the data permanently to Supabase
            new_row = {"name": name, "expiry": str(expiry), "area": area}
            conn.table("food_items").insert(new_row).execute()
            st.balloons()
            st.success(f"Posted {name}! Refresh the 'Find Food' tab to see it.")