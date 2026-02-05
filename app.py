import streamlit as st
import rispy
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations

# --- CONFIGURATION & NORMALIZATION ---
st.set_page_config(page_title="CorTexT Pro - AI Governance", layout="wide")

# Automatic Term Normalization Dictionary 
# Consolidated based on Lim et al. (2023) triadic ontological framework
NORMALIZATION_MAP = {
    "artificial intelligence": "AI",
    "generative ai": "GenAI",
    "chatgpt": "GenAI",
    "academic integrity": "Ethics/Integrity",
    "plagiarism": "Ethics/Integrity",
    "assessment scale": "AI Assessment Scale (AIAS)",
    "higher education": "Higher Ed",
    "institutional policy": "Governance/Policy",
    "accountability": "Accountability",
    "transparency": "Transparency/Explainability",
    "fairness": "Fairness/Equity"
}

def normalize(term):
    term = str(term).lower().strip()
    for key, val in NORMALIZATION_MAP.items():
        if key in term: return val
    return term.title()

# --- APP INTERFACE ---
st.title("🛡️ CorTexT Pro: Governance in AI Education")
st.markdown("### Socio-Semantic Network & Research Agenda Mapper")

# Sidebar for CorTexT-style filtering
st.sidebar.header("Network Controls")
min_freq = st.sidebar.slider("Min Term Frequency", 1, 100, 15)
min_link = st.sidebar.slider("Min Link Strength", 1, 50, 5)
layout_engine = st.sidebar.selectbox("Layout Engine", ["Kamada-Kawai (Thematic)", "Spring (Social)"])

files = st.file_uploader("Upload Scopus/WoS/ERIC RIS Files", type="ris", accept_multiple_files=True)

if files:
    all_docs = []
    for f in files:
        all_docs.extend(rispy.loads(f.getvalue().decode("utf-8")))
    
    # 1. DATA EXTRACTION
    term_counts = Counter()
    doc_terms = []
    
    for doc in all_docs:
        # Extract and Normalize Keywords
        raw_kws = doc.get('keywords', []) or doc.get('notes', [])
        clean_kws = list(set([normalize(k) for k in raw_kws if len(k) > 2]))
        
        if clean_kws:
            doc_terms.append(clean_kws)
            term_counts.update(clean_kws)

    # 2. NETWORK CONSTRUCTION
    G = nx.Graph()
    # Apply Frequency Filter (Node Level)
    valid_nodes = {n for n, c in term_counts.items() if c >= min_freq}
    
    for kws in doc_terms:
        filtered = [k for k in kws if k in valid_nodes]
        if len(filtered) > 1:
            for pair in combinations(sorted(filtered), 2):
                w = G.get_edge_data(*pair, {"weight": 0})["weight"]
                G.add_edge(pair[0], pair[1], weight=w + 1)

    # Apply Weight Filter (Edge Level)
    G = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] >= min_link])
    G.remove_nodes_from(list(nx.isolates(G)))

    # 3. VISUALIZATION & METRICS
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Socio-Semantic Thematic Map")
        fig, ax = plt.subplots(figsize=(12, 9))
        
        pos = nx.kamada_kawai_layout(G) if layout_engine == "Kamada-Kawai (Thematic)" else nx.spring_layout(G)
        
        # Scaling
        node_sizes = [term_counts[n] * 15 for n in G.nodes]
        edge_widths = [d['weight'] * 0.4 for u, v, d in G.edges(data=True)]
        
        nx.draw(G, pos, with_labels=True, node_size=node_sizes, width=edge_widths,
                node_color="#87CEEB", edge_color="#D3D3D3", font_size=10, alpha=0.8)
        st.pyplot(fig)

    with col2:
        st.subheader("Thematic Influence")
        centrality = nx.degree_centrality(G)
        df_metrics = pd.DataFrame(centrality.items(), columns=["Theme", "Centrality"])
        df_metrics = df_metrics.sort_values("Centrality", ascending=False)
        st.dataframe(df_metrics)
        
        # Export for Research Agenda
        st.download_button("Download Analysis", df_metrics.to_csv(), "ai_governance_themes.csv")

else:
    st.info("Upload your search results to map the AI Education Governance landscape.")
