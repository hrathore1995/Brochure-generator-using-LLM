import streamlit as st
from brochure import generate_brochure

st.title("Brochure Generator")
st.write("Developed by Harshwardhan")
st.write("Enter a company website URL to generate a professional and engaging brochure.")

company_name = st.text_input("Company Name")
url = st.text_input("Company Website URL")

# Language selection
language = st.selectbox("Choose Language", ["English", "Spanish"])

if st.button("Generate Brochure"):
    if company_name and url:
        with st.spinner("Generating brochure..."):
            brochure = generate_brochure(company_name, url, language)
            st.markdown(brochure)
    else:
        st.error("Please enter both a company name and URL.")
