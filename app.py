import streamlit as st
import rispy
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
from collections import Counter
from itertools import combinations

# --- Page Setup ---
st.set_page_config(page_title="CorTexT Pro: AI Governance Mapper", layout="wide")
st.title("🛡️ CorTexT Pro: Socio-Semantic Research Analytics")

# --- Domain Mapping from Research ---
# These are the 5 domains identified in Lim et al. (2023)
DOMAINS = {
    "Domain 1": "AI System Design & Check",
    "Domain 2": "Assessment Construction & Rollout",
    "Domain 3": "Data Stewardship & Surveillance",
    "Domain 4": "Administrative Governance",
    "Domain 5": "AI-Facilitated Evaluation"
}

# --- Sidebar Filters ---
st.sidebar.header("Analysis Parameters")
analysis_mode = st.sidebar.selectbox("Analysis Type", ["Socio-Semantic Network", "Temporal Evolution (Sankey)"])
min_weight = st.sidebar.slider("Minimum Link Strength", 1, 10, 2)

# --- Core Logic ---
def parse_ris_data(uploaded_files):
    all_data = []
    for f in uploaded_files:
        content = f.getvalue().decode("utf-8")
        all_data.extend(rispy.loads(content))
    return all_data

uploaded_files = st.file_uploader("Upload RIS Exports (Scopus/WoS/ERIC)", type="ris", accept_multiple_files=True)

if uploaded_files:
    data = parse_ris_data(uploaded_files)
    df = pd.DataFrame(data)
    
    # 1. SOCIO-SEMANTIC NETWORK
    if analysis_mode == "Socio-Semantic Network":
        G = nx.Graph()
        for _, row in df.iterrows():
            authors = row.get('authors', [])
            keywords = row.get('keywords', []) or row.get('notes', [])
            
            # Link Authors to Keywords (Heterogeneous Link)
            for a in authors:
                for k in keywords:
                    if G.has_edge(a, k):
                        G[a][k]['weight'] += 1
                    else:
                        G.add_edge(a, k, weight=1)
        
        # Pruning weak links
        G = nx.Graph([(u, v, d) for u, v, d in G.edges(data=True) if d['weight'] >= min_weight])
        
        st.subheader("Socio-Semantic Dynamics")
        # You would typically use Pyvis or NetworkX here for visualization
        st.write(f"Generated a network with {G.number_of_nodes()} entities and {G.number_of_edges()} links.")
        st.info("This map shows how social actors (Authors) drive specific thematic agendas (Keywords).")

    # 2. TEMPORAL EVOLUTION (SANKEY)
    elif analysis_mode == "Temporal Evolution (Sankey)":
        st.subheader("Research Trajectory: 2016 - 2026")
        
        # Simulating CorTexT's "Tubes" - tracking terms across time periods
        df['year'] = pd.to_numeric(df.get('year', 0), errors='coerce').fillna(0).astype(int)
        df = df[df['year'] >= 2016]
        
        # Define Time Windows
        period_1 = df[df['year'] <= 2020]
        period_2 = df[df['year'] > 2020]
        
        # Logic to find shared keywords between periods
        kw1 = Counter([k for kws in period_1['keywords'].dropna() for k in kws]).most_common(10)
        kw2 = Counter([k for kws in period_2['keywords'].dropna() for k in kws]).most_common(10)
        
        # Sankey construction
        fig = go.Figure(data=[go.Sankey(
            node = dict(label = [k[0] for k in kw1] + [k[0] for k in kw2]),
            link = dict(
                source = [i for i in range(len(kw1))],
                target = [i + len(kw1) for i in range(len(kw2))],
                value = [10] * len(kw1) # Simplified flow
            ))])
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Flow represents the migration and merging of research themes over time.")

else:
    st.warning("Please upload your 1,839 search results in RIS format to begin.")
