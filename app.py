import streamlit as st
import rispy
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from itertools import combinations
from collections import Counter

# --- Advanced Configuration ---
st.set_page_config(page_title="AI Governance Mapper Pro", layout="wide")
st.title("🛡️ AI Education Governance: Network Mapper")
st.markdown("""
    This tool performs **Socio-Semantic Analysis** on your RIS exports from Scopus, WoS, and ERIC.
    It maps the relationship between **Authors (Social)** and **Research Keywords (Semantic)**.
""")

def clean_term(term):
    """Normalize terms to prevent 'AI' and 'Artificial Intelligence' from being separate nodes."""
    term = str(term).lower().strip()
    mapping = {
        "artificial intelligence": "AI",
        "generative ai": "GenAI",
        "higher education": "HigherEd",
        "academic integrity": "Ethics/Integrity",
        "governance": "Governance/Policy"
    }
    return mapping.get(term, term)

# --- Sidebar ---
st.sidebar.header("Filter & Analysis Settings")
node_type = st.sidebar.selectbox("Network Type", ["Co-Authorship", "Keyword Co-occurrence", "Socio-Semantic (Author-Keyword)"])
min_occurrence = st.sidebar.slider("Minimum Node Frequency", 1, 50, 5)
edge_weight = st.sidebar.slider("Minimum Link Strength", 1, 20, 2)

# --- File Upload ---
files = st.file_uploader("Upload RIS files", type="ris", accept_multiple_files=True)

if files:
    all_entries = []
    for f in files:
        content = f.getvalue().decode("utf-8")
        all_entries.extend(rispy.loads(content))
    
    st.sidebar.success(f"Total Records: {len(all_entries)}")

    # Data Processing
    G = nx.Graph()
    term_counts = Counter()
    
    for entry in all_entries:
        authors = [a.strip() for a in entry.get('authors', [])]
        # Consolidate keywords from various RIS tags
        kws = entry.get('keywords', []) or entry.get('notes', [])
        kws = [clean_term(k) for k in kws if len(k) > 2]
        
        if node_type == "Co-Authorship":
            targets = authors
        elif node_type == "Keyword Co-occurrence":
            targets = kws
        else: # Socio-Semantic
            # Connect authors to the keywords they write about
            for a in authors:
                for k in kws:
                    G.add_edge(a, k, weight=G.get_edge_data(a, k, {"weight": 0})["weight"] + 1)
            continue

        if len(targets) > 1:
            for combo in combinations(set(targets), 2):
                w = G.get_edge_data(combo[0], combo[1], {"weight": 0})["weight"]
                G.add_edge(combo[0], combo[1], weight=w + 1)
        
        for t in targets:
            term_counts[t] += 1

    # Pruning the Network
    # Remove nodes that don't meet the frequency threshold
    nodes_to_remove = [n for n, count in term_counts.items() if count < min_occurrence]
    G.remove_nodes_from(nodes_to_remove)
    
    # Remove edges that are too weak
    edges_to_remove = [(u, v) for u, v, d in G.edges(data=True) if d['weight'] < edge_weight]
    G.remove_edges_from(edges_to_remove)
    G.remove_nodes_from(list(nx.isolates(G)))

    # Metrics
    if len(G.nodes) > 0:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"Network Map: {node_type}")
            fig, ax = plt.subplots(figsize=(12, 10))
            pos = nx.spring_layout(G, k=0.3, iterations=50)
            
            # Node size based on Centrality (Importance)
            centrality = nx.degree_centrality(G)
            
            nx.draw(G, pos, 
                    with_labels=True, 
                    node_color="#1f77b4", 
                    node_size=[v * 5000 for v in centrality.values()],
                    width=[d['weight'] for u, v, d in G.edges(data=True)],
                    edge_color="#dddddd",
                    font_size=9,
                    alpha=0.8)
            st.pyplot(fig)

        with col2:
            st.subheader("Top Influencers")
            sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            df_cent = pd.DataFrame(sorted_centrality, columns=["Node", "Centrality Score"])
            st.dataframe(df_cent.head(20))
            
            csv = df_cent.to_csv(index=False)
            st.download_button("Export Metrics to CSV", csv, "network_metrics.csv", "text/csv")
    else:
        st.warning("The filters are too strict. No network could be generated.")
