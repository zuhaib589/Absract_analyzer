import streamlit as st
import pandas as pd
import json
from agents import AbstractAnalysisAgents
from analyzer import detect_move, detect_hedging
from utils import split_into_sentences

st.set_page_config(page_title="Academic Abstract Move Structure Analyzer", layout="wide")

st.sidebar.title("Navigation 🎓")
page = st.sidebar.radio("Go to", [
    "1. Home & Data Input",
    "2. Data Preview",
    "3. Agent Workspace",
    "4. Evidence View",
    "5. Quantitative Summary",
    "6. Theory Check",
    "7. Final Report"
])

import os
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

st.sidebar.markdown("---")
st.sidebar.header("Settings ⚙️")
env_key = os.environ.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key", value=env_key, type="password", help="Enter your Gemini API key to power the AI Agents.")

# State management
if "abstracts" not in st.session_state:
    st.session_state.abstracts = []
if "agent_results" not in st.session_state:
    st.session_state.agent_results = {}

def get_agents():
    return AbstractAnalysisAgents(api_key=api_key)

if page == "1. Home & Data Input":
    st.title("Project Home & Data Input 🏠")
    st.markdown("Welcome to the **Academic Abstract Move Structure Analyzer**. Paste your research abstracts here.")
    
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            disc = st.text_input("Discipline (e.g., Medicine, Linguistics)")
        with col2:
            abstract_id = st.text_input("Abstract ID / Title")
            
        abstract_text = st.text_area("Paste Abstract Text Here", height=200)
        
        submitted = st.form_submit_button("Add Abstract")
        if submitted:
            if not disc or not abstract_text:
                st.error("Please fill in both Discipline and Abstract Text.")
            else:
                st.session_state.abstracts.append({
                    "id": abstract_id or f"Abstract {len(st.session_state.abstracts) + 1}",
                    "discipline": disc,
                    "text": abstract_text
                })
                st.success("Abstract added successfully! Go to 'Data Preview' to view.")
                
    st.markdown("### Or Load from Corpus (abstract_corpus.xlsx)")
    if st.button("Load Default Corpus"):
        try:
            df = pd.read_excel("abstract_corpus.xlsx")
            for _, row in df.iterrows():
                st.session_state.abstracts.append({
                    "id": row.get("ID", f"Corpus-{_}"),
                    "discipline": row.get("Discipline", "Unknown"),
                    "text": row.get("Abstract", "")
                })
            st.success(f"Loaded {len(df)} abstracts from corpus!")
        except Exception as e:
            st.error(f"Failed to load corpus: {e}")

elif page == "2. Data Preview":
    st.title("Data Preview 📊")
    if not st.session_state.abstracts:
        st.warning("No abstracts loaded yet. Go to Home to add data.")
    else:
        df = pd.DataFrame(st.session_state.abstracts)
        st.dataframe(df, use_container_width=True)
        st.metric("Total Abstracts", len(df))

elif page == "3. Agent Workspace":
    st.title("Agent Workspace 🤖")
    st.markdown("Watch the 6 AI Agents perform their specialized roles.")
    
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar settings to use the agents.")
    elif not st.session_state.abstracts:
        st.warning("Please add some abstracts first.")
    else:
        # Select an abstract to run agents on
        abstract_options = {f"{a['id']} ({a['discipline']})": a for a in st.session_state.abstracts}
        selected = st.selectbox("Select Abstract to Analyze", list(abstract_options.keys()))
        selected_abstract = abstract_options[selected]
        
        if st.button("Run Research Analysis"):
            if selected_abstract["id"] in st.session_state.agent_results:
                st.success("Loaded results from cache! No API call was made.")
            else:
                with st.spinner("Gemini AI is conducting a rigorous academic analysis... (Applying throttle delay)"):
                    agents = get_agents()
                    text = selected_abstract["text"]
                    
                    # Single Unified API Call
                    unified_res = agents.analyze_abstract_unified(text)
                    
                    if "Error" in unified_res:
                        st.error(unified_res["Error"])
                        if "Raw" in unified_res:
                            with st.expander("🛠️ Debug: Raw Gemini Output", expanded=True):
                                st.code(unified_res["Raw"])
                    else:
                        st.session_state.agent_results[selected_abstract["id"]] = unified_res
                
        if selected_abstract["id"] in st.session_state.agent_results:
            res = st.session_state.agent_results[selected_abstract["id"]]
            
            st.markdown("### Research Analysis Dashboard")
            
            # Overall Summary & Confidence
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("#### 📝 Academic Summary")
                st.info(res.get("summary", "No summary available."))
            with col2:
                st.markdown("#### 🎯 Overall Confidence")
                conf = res.get("overall_confidence", 0.0)
                st.metric(label="Score", value=f"{conf:.2f}")
                
            # Swales CARS Moves
            st.markdown("#### 🔍 Swales CARS Move Detection")
            moves = res.get("moves", [])
            if moves:
                for m in moves:
                    st.write(f"**{m.get('move', 'Unknown')}** (Confidence: `{m.get('confidence', 0.0)}`)")
                    st.caption(f"> {m.get('sentence', '')}")
            else:
                st.write("No moves detected.")
                
            # Hedging
            st.markdown("#### 🧮 Hedging Extraction")
            hedging = res.get("hedging", {})
            st.write(f"**Total Count:** {hedging.get('count', 0)} (Confidence: `{hedging.get('confidence', 0.0)}`)")
            st.write(f"**Words Detected:** {', '.join(hedging.get('words', [])) if hedging.get('words') else 'None'}")

elif page == "4. Evidence View":
    st.title("Evidence View 🔍")
    st.markdown("Shows quoted sentences from abstracts with move labels using the fallback Rule-Based system for comparison.")
    
    if not st.session_state.abstracts:
        st.warning("No data available.")
    else:
        abstract_options = {f"{a['id']} ({a['discipline']})": a for a in st.session_state.abstracts}
        selected = st.selectbox("Select Abstract", list(abstract_options.keys()))
        selected_abstract = abstract_options[selected]
        
        st.markdown("#### Abstract Text Segmented (Rule-Based Fallback)")
        sentences = split_into_sentences(selected_abstract["text"])
        total = len(sentences)
        
        html = ""
        for i, s in enumerate(sentences):
            move_data = detect_move(s, i, total)
            move = move_data["move"]
            color = "#f8f9fa"
            if "Move 1" in move: color = "#d4edda"
            elif "Move 2" in move: color = "#f8d7da"
            elif "Move 3" in move: color = "#cce5ff"
            interp = move_data.get('interpretation', '')
            html += f'<span style="background-color: {color}; padding: 2px 5px; border-radius: 3px; margin-right: 5px; line-height: 2;" title="{move} - {interp}">{s}</span>'
            
        st.markdown(f'<div>{html}</div><br>', unsafe_allow_html=True)
        st.markdown("**Legend:** <span style='background-color: #d4edda; padding: 2px 5px; border-radius: 3px;'>Move 1: Territory</span> | <span style='background-color: #f8d7da; padding: 2px 5px; border-radius: 3px;'>Move 2: Gap</span> | <span style='background-color: #cce5ff; padding: 2px 5px; border-radius: 3px;'>Move 3: Niche</span>", unsafe_allow_html=True)

elif page == "5. Quantitative Summary":
    st.title("Quantitative Dashboard 📈")
    st.markdown("Hedging Frequency Comparison across disciplines (Rule-Based metrics).")
    
    if not st.session_state.abstracts:
        st.warning("No data available.")
    else:
        data = []
        for a in st.session_state.abstracts:
            sents = split_into_sentences(a["text"])
            total_hedges = sum(detect_hedging(s)["count"] for s in sents)
            data.append({
                "Abstract ID": a["id"],
                "Discipline": a["discipline"],
                "Hedging Count": total_hedges
            })
            
        df = pd.DataFrame(data)
        
        if not df.empty:
            avg_hedging = df.groupby("Discipline")["Hedging Count"].mean().reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Hedging Frequency by Discipline")
                st.bar_chart(avg_hedging.set_index("Discipline"))
            with col2:
                st.subheader("Data Summary")
                st.dataframe(df)
            
            st.info("Note: The student should manually verify at least 5 examples.")

elif page == "6. Theory Check":
    st.title("Theory Check Page 📖")
    st.markdown("Explains whether the analysis matches Swales CARS model.")
    
    st.markdown("""
    ### John Swales' CARS Model (Create A Research Space)
    Swales stated that research abstracts follow predictable moves:
    - **Move 1 (Background):** Sets the context
    - **Move 2 (Gap):** Identifies what is missing
    - **Move 3 (Method):** Explains what the study did
    - **Move 4 (Results):** States findings
    - **Move 5 (Conclusion):** Gives implications
    """)
    
    st.markdown("Select an abstract to view the **Corpus Linguistics Theory Agent's** assessment:")
    if st.session_state.agent_results:
        opts = list(st.session_state.agent_results.keys())
        selected = st.selectbox("View Theory Assessment For:", opts)
        st.write(st.session_state.agent_results[selected].get("Theory", "No theory assessment run yet."))
    else:
        st.warning("Run the agents on an abstract in the Agent Workspace first to see theory assessments.")

elif page == "7. Final Report":
    st.title("Final Report & Limitations Generator 📄")
    
    if st.button("Generate Report"):
        st.markdown("---")
        st.header("Academic Abstract Move Structure Analysis Report")
        st.subheader("Dataset Description")
        st.write(f"Analyzed **{len(st.session_state.abstracts)}** abstracts.")
        
        disciplines = list(set([a["discipline"] for a in st.session_state.abstracts]))
        st.write(f"Disciplines included: {', '.join(disciplines)}")
        
        st.subheader("Move Structure & Hedging Summary")
        st.write("*(See Quantitative Summary tab for full charts)*")
        
        if st.session_state.agent_results:
            st.subheader("Selected Evidence & Agent Findings")
            for abs_id, res in st.session_state.agent_results.items():
                with st.expander(f"Findings for {abs_id}"):
                    st.write("**Lead Agent Summary:**", res.get("Lead", ""))
                    st.write("**Theory Connection:**", res.get("Theory", ""))
        else:
            st.warning("No agent results generated yet. Go to Agent Workspace to run analysis.")
            
        st.subheader("Limitations")
        st.error("""
        **Limitations of AI Analysis:**
        - AI models may misinterpret subtle rhetorical moves.
        - Hedging expressions might be context-dependent and missed by standard rules or agents.
        """)
        st.warning("**Reminder:** The app suggested these patterns. Human verification is required before using in academic writing.")
        
        report_text = f"Academic Abstract Move Structure Analysis Report\nDataset: {len(st.session_state.abstracts)} abstracts\n..."
        st.download_button("Download Report as TXT", report_text, file_name="final_report.txt")
