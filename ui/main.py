"""Streamlit client for the RAG-LAW retrieval API."""

import os

import requests
import streamlit as st


API_URL = os.environ.get("RAGLAW_API_URL", "http://127.0.0.1:8000").rstrip("/")
EXAMPLE_QUERY = "Chi paga le riparazioni straordinarie in una casa in affitto?"

st.set_page_config(page_title="RAG-LAW · Legal search", layout="wide")
st.markdown(
    """
    <style>
      .stMainBlockContainer { max-width: 59rem; padding-top: 2.5rem; }
      h1 { font-size: clamp(2.2rem, 6vw, 3.4rem) !important; letter-spacing: -0.045em; }
      [data-testid="stForm"] { background: var(--secondary-background-color);
        border-radius: 1rem; padding: 1.25rem; }
      [data-testid="stExpander"] { border-radius: 0.7rem; }
      [data-testid="stCaptionContainer"] { font-size: 0.91rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.caption("RAG-LAW  /  Italian legal search")
st.title("Search legal articles by meaning")
st.write("Ask a question in Italian and read the retrieved passages in context.")

with st.form("search"):
    query = st.text_input("Your question", value=EXAMPLE_QUERY, max_chars=1000)
    settings, submit = st.columns([3, 2], vertical_alignment="bottom")
    with settings:
        top_k = st.select_slider("Number of passages", options=[1, 2, 3, 5, 10], value=3)
    with submit:
        submitted = st.form_submit_button("Search articles", type="primary", width="stretch")

if submitted:
    st.session_state.pop("search_response", None)
    query = query.strip()
    if not query:
        st.warning("Enter a question to search the corpus.")
    else:
        try:
            with st.spinner("Finding relevant passages…"):
                response = requests.post(
                    f"{API_URL}/search",
                    json={"query": query, "top_k": top_k},
                    timeout=(3, 30),
                )
                response.raise_for_status()
                st.session_state.search_response = response.json()
        except requests.exceptions.Timeout:
            st.error("The search timed out. Try again when the API is ready.")
        except requests.exceptions.RequestException:
            st.error("The search API is unavailable. Check that the backend is running.")

if result := st.session_state.get("search_response"):
    hits = result["results"]
    if hits:
        heading, details = st.columns([3, 2], vertical_alignment="center")
        with heading:
            st.subheader("Search results")
        with details:
            unit = "passage" if len(hits) == 1 else "passages"
            st.caption(f"{len(hits)} {unit} ranked by similarity")
        for rank, hit in enumerate(hits, start=1):
            label = f"Article {hit['article_number']}"
            if hit.get("title"):
                label = f"{label} · {hit['title']}"
            with st.expander(label, expanded=rank == 1):
                st.caption("Matched passage")
                st.write(hit["chunk_content"])
                if hit["full_article"] != hit["chunk_content"]:
                    with st.popover("Read full article"):
                        st.write(hit["full_article"])
    else:
        st.info("The search returned no passages.")
    corpus = result.get("corpus", {})
    if corpus.get("kind") == "demo":
        st.caption("The included demo corpus is fictional. For research and demonstration only.")
    elif corpus.get("kind") == "civil_code":
        st.caption(
            f"Source: [Normattiva]({corpus['url']}) · Snapshot {corpus['as_of']} · "
            "Riproduzione non autentica e gratuita."
        )
