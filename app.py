import streamlit as st
import rispy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations

# --- ADVANCED TYPOLOGY CONFIGURATION ---
# Based on the SLM methodology in Lim et al. (2023)
DOMAINS = {
    "Domain 1": "AI System Design & Check",
    "Domain 2": "Assessment Construction & Rollout",
    "Domain 3": "Data Stewardship & Surveillance",
    "Domain 4": "Administrative Governance",
    "Domain 5": "AI-Facilitated Evaluation"
}

# Expanded Normalization Map for Higher Resolution Thematic Extraction
# Includes Ethics principles [cite: 828, 290-330] and Research Domains [cite: 826, 827]
NORMALIZATION_MAP = {
    # AI Technology & Assessment Layers
    "artificial intelligence": "AI", "generative ai": "GenAI", "chatgpt": "GenAI",
    "crystallized intelligence": "Crystallized Intel", "fluid intelligence": "Fluid Intel",
    
    # Core Ethics Principles [cite: 290-330, 50]
    "accountability": "Accountability", "accuracy": "Accuracy", "auditability": "Auditability",
    "explainability": "Explainability", "fairness": "Fairness", "human centricity": "Human Centricity",
    "inclusivity": "Inclusivity", "privacy": "Privacy", "trust": "Trust", "integrity": "Integrity",
    "bias": "Fairness", "equity": "Fairness", "transparency": "Explainability",
    
    # Governance & Policy Archetypes 
    "institutional policy": "Domain 4: Admin Governance", "governance": "Domain 4: Admin Governance",
    "data stewardship": "Domain 3: Data Stewardship", "surveillance": "Domain 3: Data Stewardship",
    "automated grading": "Domain 5: AI Evaluation", "feedback": "Domain 5: AI Evaluation",
    "higher education": "Higher Ed", "university": "Higher Ed"
}

def advanced_normalize(term):
    term = str(term).lower().strip()
    for key, val in NORMALIZATION_MAP.items():
        if key in term: return val
    return term.title()

# --- APP INTERFACE ---
st.set_page_config(page_title="CorTexT Pro - AI Governance Mapper", layout="wide")
st.title("🔬 CorTexT Pro: AI Education Governance Analytics")
st.markdown("Mapping **Socio-Semantic Dynamics** across the AI Assessment Pipeline.")

# Sidebar Controls
st.sidebar.header("Network Parameters")
min_freq = st.sidebar.slider("Minimum Term Frequency", 1, 150, 20)
min_link = st.sidebar.slider("Minimum Co-occurrence", 1, 50, 5)
layout_engine = st.sidebar.selectbox("Layout Engine", ["Kamada-Kawai (Thematic)", "Spring (Social)"])

files = st.file_uploader("Upload RIS (Scopus/WoS/ERIC)", type="ris", accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        all_data.extend(rispy.loads(f.getvalue().decode("utf-8")))
    
    # 1. THEMATIC EXTRACTION
    term_counts = Counter()
    doc_matrix = []
    
    for doc in all_data:
        # Extract keywords and titles for richer theme mapping
        raw_kws = doc.get('keywords', []) or doc.get('notes', [])
        clean_kws = list(set([advanced_normalize(k) for k in raw_kws if len(k) > 2]))
        
        if clean_kws:
            doc_matrix.append(clean_kws)
            term_counts.update(clean_kws)

    # 2. NETWORK GENERATION
    G = nx.Graph()
    valid_nodes = {n for n, c in term_counts.items() if c >= min_freq}
    
    for themes in doc_matrix:
        filtered = [t for t in themes if t in valid_nodes]
        if len(filtered) > 1:
            for pair in combinations(sorted(filtered), 2):
                weight = G.get_edge_data(*pair, {"weight": 0})["weight"]
                G.add_edge(pair[0], pair[1], weight=weight + 1)

    # Filter by Link Strength
    G = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] >= min_link])
    G.remove_nodes_from(list(nx.isolates(G)))

    # 3. VISUALIZATION
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Socio-Semantic Thematic Clusters")
        fig, ax = plt.subplots(figsize=(14, 10))
        
        pos = nx.kamada_kawai_layout(G) if layout_engine == "Kamada-Kawai (Thematic)" else nx.spring_layout(G)
        
        # Color coding by Typology (Ethics vs. Domain)
        node_colors = ["#FF7F50" if "Domain" in n else "#87CEEB" for n in G.nodes]
        
        nx.draw(G, pos, with_labels=True, 
                node_size=[term_counts[n] * 12 for n in G.nodes],
                node_color=node_colors, 
                width=[d['weight'] * 0.3 for u, v, d in G.edges(data=True)],
                edge_color="#D3D3D3", font_size=10, alpha=0.8)
        st.pyplot(fig)
        st.caption("Orange: Research Domains | Blue: Ethical Principles & AI Themes")

    with col2:
        st.subheader("Thematic Influence (Centrality)")
        centrality = nx.degree_centrality(G)
        df_cent = pd.DataFrame(centrality.items(), columns=["Theme", "Centrality"]).sort_values("Centrality", ascending=False)
        st.dataframe(df_cent)
        
        # Research Agenda Export
        csv = df_cent.to_csv(index=False).encode('utf-8')
        st.download_button("Export Research Agenda Data", csv, "ai_governance_agenda.csv", "text/csv")

else:
    st.info("Upload your 1,839 results (RIS) to map the 'Governance in AI Education' landscape.")
