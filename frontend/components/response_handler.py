import streamlit as st
import time

def handle_response(response, success_message:str):
    if response.status_code == 200:
        st.success(success_message)
        result = response.json()
        if "documents_processed" in result:
            st.info(f"Processed {result['documents_processed']} documents")
        time.sleep(1.5)
        return True
    else:
        st.error(f"Operation failed: {response.text}")
        return False