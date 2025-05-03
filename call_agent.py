
import streamlit as st
import pandas as pd
from datetime import datetime

def call_agent_page():
    st.title("Call Campaign Launcher")
    
    # Add a nice subheader with the current date
    current_date = datetime.now().strftime("%B %d, %Y")
    st.subheader(f"Launch a new campaign to get the latest offers - {current_date}")
    
    # Add some spacing
    st.markdown("---")
    
    with st.container():
        st.markdown("### Campaign Settings")
        
        # Mock company data - in a real app this would come from a database
        companies = ["TechNova Inc.", "Global Solutions LLC", "Summit Enterprises", 
                    "Horizon Communications", "Pinnacle Systems", "Atlas Corporation",
                    "Quantum Industries", "Nexus Group", "Synergy Partners"]
        
        # Create a multiselect dropdown with "All" option separately
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if "select_all_state" in st.session_state and st.session_state.select_all_state:
                # When "Select All" is active, pass all companies as default
                selected_companies = st.multiselect(
                    "Select companies to call:",
                    options=companies,
                    default=companies,
                    key="companies_select"
                )
            else:
                # Normal selection mode
                selected_companies = st.multiselect(
                    "Select companies to call:",
                    options=companies,
                    default=None,
                    key="companies_select"
                )
        
        # Initialize session state for tracking "select all" status
        if "select_all_state" not in st.session_state:
            st.session_state.select_all_state = False
            
        # Pre-populate companies if "select all" is active
        if st.session_state.select_all_state:
            selected_companies = companies
        
        with col2:
            if st.button("Select All", key="select_all"):
                # Toggle the select all state
                st.session_state.select_all_state = not st.session_state.select_all_state
                st.rerun()
        
        # Display the count of selected companies
        if selected_companies:
            st.info(f"{len(selected_companies)} companies selected for this campaign")
        else:
            st.warning("Please select at least one company to proceed")
    
    st.markdown("### Additional Instructions")
    
    # Text area for additional information
    additional_info = st.text_area(
        "Share any specific information to be handled during calls:",
        placeholder="Example: Focus on the new premium service tier. All clients should be informed about the 20% discount for early adoption...",
        height=150
    )
    
    # Campaign priority
    st.markdown("### Campaign Priority")
    priority = st.select_slider(
        "Set campaign priority:",
        options=["Low", "Medium", "High", "Urgent"],
        value="Medium"
    )
    
    # Notification preference
    notification_pref = st.radio(
        "How would you like to be notified about the campaign progress?",
        options=["Email", "Dashboard", "Both"],
        horizontal=True
    )
    
    # Add some spacing
    st.markdown("---")
    
    # Campaign stats preview in columns
    st.markdown("### Campaign Preview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Calls", f"{len(selected_companies) if selected_companies else 0}")
    
    with col2:
        st.metric("Estimated Duration", f"{len(selected_companies) * 7 if selected_companies else 0} mins")
    
    with col3:
        st.metric("Agent Availability", "3 Available")
    
    # Launch button with conditions
    if selected_companies:
        if st.button("Launch Campaign", type="primary", use_container_width=True):
            # In a real app, this would trigger the campaign to start
            st.success("Campaign successfully launched!")
            st.balloons()
            
            # Display campaign summary
            with st.expander("Campaign Summary", expanded=True):
                st.write(f"**Companies:** {', '.join(selected_companies)}")
                st.write(f"**Priority:** {priority}")
                st.write(f"**Notification Method:** {notification_pref}")
                if additional_info:
                    st.write(f"**Additional Instructions:** {additional_info}")
                st.write(f"**Launch Time:** {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.button("Launch Campaign", type="primary", use_container_width=True, disabled=True)
        
    # Footer with helpful information
    st.markdown("---")
    st.caption("Need help? Contact the support team at support@company.com")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Call Campaign Launcher",
        page_icon="📞",
        layout="wide",
        initial_sidebar_state="expanded"
    )