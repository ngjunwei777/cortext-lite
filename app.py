import streamlit as st
import rispy
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
from collections import Counter

# --- App Configuration ---
st.set_page_config(page_title="CorTexT Lite - RIS Analyzer", layout="wide")
st.title("🔬 CorTexT Lite: RIS Network Analyzer")
st.markdown("Upload your RIS file to visualize the socio-semantic network of Authors and Keywords.")

# --- File Upload ---
uploaded_file = st.file_uploader("Choose an RIS file", type="ris")

if uploaded_file is not None:
    # 1. Parse RIS File
    content = uploaded_file.getvalue().decode("utf-8")
    entries = rispy.loads(content)
    
    st.success(f"Successfully loaded {len(entries)} records!")

    # 2. Extract Data for Analysis
    author_keyword_map = []
    all_authors = []
    
    for entry in entries:
        authors = entry.get('authors', [])
        # Keywords are often under 'keywords' or 'notes' depending on the source
        keywords = entry.get('keywords', []) or entry.get('notes', [])
        
        if authors and keywords:
            # We treat each paper as a 'club' where authors and keywords meet
            author_keyword_map.append({'authors': authors, 'keywords': keywords})
            all_authors.extend(authors)

    # 3. Sidebar Controls
    st.sidebar.header("Network Settings")
    min_weight = st.sidebar.slider("Minimum Connection Strength", 1, 10, 1)
    
    # 4. Build Co-authorship Network
    # We'll link authors if they share keywords (Socio-semantic approach)
    G = nx.Graph()
    
    pair_list = []
    for paper in author_keyword_map:
        # Create pairs of authors who collaborated
        if len(paper['authors']) > 1:
            pair_list.extend(list(combinations(paper['authors'], 2)))

    counts = Counter(pair_list)
    
    for (a1, a2), weight in counts.items():
        if weight >= min_weight:
            G.add_edge(a1, a2, weight=weight)

    # 5. Visualization
    st.subheader("Author Collaboration Network")
    if len(G.nodes) > 0:
        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.spring_layout(G, k=0.5)
        
        # Node size based on degree (how many connections they have)
        d = dict(G.degree)
        nx.draw(G, pos, 
                with_labels=True, 
                node_color='orange', 
                node_size=[v * 100 for v in d.values()],
                edge_color='#BBBBBB',
                width=[G[u][v]['weight'] for u, v in G.edges()],
                font_size=8,
                ax=ax)
        
        st.pyplot(fig)
    else:
        st.warning("Not enough connections found. Try lowering the 'Minimum Connection Strength'.")

    # 6. Data Preview
    with st.expander("View Raw Data"):
        st.write(entries[:5]) # Show first 5 records

else:
    st.info("Please upload an RIS file exported from Scopus, Web of Science, or Zotero.")
