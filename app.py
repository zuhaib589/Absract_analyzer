import streamlit as st
import pandas as pd
from utils import split_into_sentences
from analyzer import detect_move, detect_hedging

st.set_page_config(page_title="Abstract Move Structure Analyzer", layout="wide")

st.title("Academic Abstract Move Structure Analyzer")
st.markdown("Analyze research paper abstracts and identify rhetorical \"moves\" (Aim, Method, Result) in each sentence.")

input_method = st.radio("Choose Input Method", ["Paste Text", "Select from Corpus"], horizontal=True)

if input_method == "Paste Text":
    abstract_text = st.text_area("Enter Research Abstract", height=200, placeholder="Paste your abstract here...")
else:
    try:
        corpus_df = pd.read_excel("abstract_corpus.xlsx")
        corpus_df["Display"] = corpus_df["ID"].astype(str) + " - " + corpus_df["Title"]
        selected_display = st.selectbox("Select an Abstract from Corpus", corpus_df["Display"].tolist())
        selected_row = corpus_df[corpus_df["Display"] == selected_display].iloc[0]
        abstract_text = st.text_area(f"Selected Abstract (Discipline: {selected_row['Discipline']})", value=selected_row["Abstract"], height=200)
    except Exception as e:
        st.error(f"Error loading abstract_corpus.xlsx: {e}")
        abstract_text = ""

def get_move_color(move):
    if move == "Aim":
        return "background-color: #d4edda; color: #155724;" # Green
    elif move == "Method":
        return "background-color: #cce5ff; color: #004085;" # Blue
    elif move == "Result":
        return "background-color: #fff3cd; color: #856404;" # Yellow
    else:
        return "background-color: #f8f9fa; color: #383d41;" # Gray

if st.button("Analyze Abstract"):
    if not abstract_text.strip():
        st.warning("Please enter an abstract to analyze.")
    else:
        sentences = split_into_sentences(abstract_text)
        
        results = []
        for sentence in sentences:
            move = detect_move(sentence)
            hedging = detect_hedging(sentence)
            hedging_str = ", ".join(hedging) if hedging else "-"
            
            results.append({
                "Sentence": sentence,
                "Move": move,
                "Hedging Words": hedging_str
            })
            
        df = pd.DataFrame(results)
        
        st.subheader("Analysis Results")
        
        # Style the dataframe based on the move
        styled_df = df.style.apply(
            lambda x: [get_move_color(v) if k == "Move" else "" for k, v in x.items()],
            axis=1
        )
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Also provide a visual paragraph view
        st.subheader("Annotated Text")
        annotated_html = ""
        for item in results:
            color = ""
            if item["Move"] == "Aim": color = "#d4edda"
            elif item["Move"] == "Method": color = "#cce5ff"
            elif item["Move"] == "Result": color = "#fff3cd"
            
            if color:
                annotated_html += f'<span style="background-color: {color}; padding: 2px 5px; border-radius: 3px; margin-right: 5px;" title="{item["Move"]}">{item["Sentence"]}</span>'
            else:
                annotated_html += f'<span style="margin-right: 5px;">{item["Sentence"]}</span>'
                
        st.markdown(f'<div style="line-height: 1.6;">{annotated_html}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**Legend:** <span style='background-color: #d4edda; padding: 2px 5px; border-radius: 3px;'>Aim</span> | <span style='background-color: #cce5ff; padding: 2px 5px; border-radius: 3px;'>Method</span> | <span style='background-color: #fff3cd; padding: 2px 5px; border-radius: 3px;'>Result</span> | Other", unsafe_allow_html=True)
