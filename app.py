import streamlit as st
import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import io
import requests

st.set_page_config(page_title="Omics Rescuer", layout="wide")

st.title("?? Omics Rescuer - Enterprise Production Suite")
st.markdown("---")

# 1. SIDEBAR CONFIGURATION & PAYWALL
st.sidebar.header("?? Licensing & Configuration")
license_key = st.sidebar.text_input("Premium License Key:", type="password")
TARGET_VARIANT_ID =  1873129
# Placeholder Store Setup (Change this to your actual Lemon Squeezy Store ID if needed)
TARGET_STORE_ID = "12345" 

def verify_license(key):
    """Hits the real Lemon Squeezy API to validate a customer license key"""
    if not key:
        return False
    # Development bypass for easy testing
    if key == "DEV-PASS-2026":
        return True
    
    url = "https://api.lemonsqueezy.com/v1/licenses/validate"
    headers = {"Accept": "application/json"}
    data = {"license_key": key}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            res_data = response.json()
            # Confirm license is valid and not expired/disabled
            status = res_data.get("status", "inactive")
            if status in ["active", "inactive"]:
                return True
        return False
    except:
        return False

if verify_license(license_key):
    st.sidebar.success("? License Validated via Lemon Squeezy")
    
    # 2. PROCESSING CONTROLS
    st.sidebar.header("??? Processing Controls")
    log_transform = st.sidebar.checkbox("Apply Log2 Transformation", value=True)
    p_threshold = st.sidebar.slider("P-Value Significance Cutoff", 0.0001, 1.0, 0.05, step=0.001)
    
    uploaded_file = st.file_uploader("Upload messy spreadsheet (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        st.info("? Engine engaged. Rectifying structures...")
        
        try:
            # READ
            df = pl.read_excel(uploaded_file.read())
            
            # PIPELINE STEP 1: Core Clean (Remove null / blank Gene_IDs)
            cleaned_df = df.filter((pl.col("Gene_ID") != "") & (pl.col("Gene_ID").is_not_null()))
            
            # PIPELINE STEP 2: Cast numerical columns safely
            cleaned_df = cleaned_df.with_columns([
                pl.col("Expression_Value").cast(pl.Float64, strict=False).fill_null(0.0),
                pl.col("p_value").cast(pl.Float64, strict=False).fill_null(1.0)
            ])
            
            # PIPELINE STEP 3: Log2 Transformation if requested
            if log_transform:
                # Log2(x + 1) avoids math errors on 0.0 values
                cleaned_df = cleaned_df.with_columns(
                    (pl.col("Expression_Value") + 1).log(2).alias("Log2_Expression")
                )
            
            # PIPELINE STEP 4: Filter out statistically insignificant entries
            filtered_df = cleaned_df.filter(pl.col("p_value") <= p_threshold)
            
            # --- MAIN DISPLAY TABS ---
            tab1, tab2 = st.tabs(["?? Cleaned Dataset Preview", "?? Visual Analytics"])
            
            with tab1:
                st.subheader("? Real-time Cleansed Output")
                st.dataframe(filtered_df.to_pandas(), use_container_width=True)
                
                # Dynamic Download File Construction
                output = io.BytesIO()
                filtered_df.write_excel(output)
                st.download_button(
                    label="?? Export CLEANED_OMICS_DATA.xlsx",
                    data=output.getvalue(),
                    file_name="CLEANED_OMICS_DATA.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            with tab2:
                st.subheader("?? Interactive Biological Figures")
                col1, col2 = st.columns(2)
                
                # Generate plots using the pandas presentation bridge
                pdf = filtered_df.to_pandas()
                
                with col1:
                    st.markdown("**Expression Value Spread across Samples**")
                    fig, ax = plt.subplots()
                    sns.boxplot(data=pdf, x="Sample_Group", y="Log2_Expression" if log_transform else "Expression_Value", ax=ax, palette="Set2")
                    st.pyplot(fig)
                    
                with col2:
                    st.markdown("**Statistical Distribution Profile (p-value histogram)**")
                    fig2, ax2 = plt.subplots()
                    sns.histplot(data=pdf, x="p_value", kde=True, ax=ax2, color="crimson", bins=5)
                    st.pyplot(fig2)
                    
        except Exception as e:
            st.error(f"Execution Error: {e}")
else:
    st.warning("?? Premium Core Disabled. License validation verification required.")
    st.markdown("### How to gain access:")
    st.markdown("1. [?? Click here to access checkout link](https://your-lemon-squeezy-store-link)")
    st.markdown("2. Complete purchase to generate your instant license key.")
    st.markdown("---")
    st.info("?? **Developer Notice:** Enter key DEV-PASS-2026 to bypass security for testing.")
