"""M4: Streamlit UI — Presenter only, no business logic"""
import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from parser import ComfyUIParser
from core.database import Database

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'generation.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = Database(DB_PATH)
parser = ComfyUIParser()

st.set_page_config(page_title="Generation Vault", layout="wide")

# ---- Sidebar ----
st.sidebar.title("Generation Vault")
page = st.sidebar.radio("", ["Import", "Search", "Detail", "Health"])
st.sidebar.markdown("---")
st.sidebar.caption(f"v0.4.0 | {db.count()} generations")

# ---- Health ----
if page == "Health":
    st.title("Health")
    col1, col2, col3 = st.columns(3)
    col1.metric("Generations", db.count())
    col2.metric("Parser", "ComfyUI ✅")
    col3.metric("Version", "v0.4.0")
    st.code("PNG → ComfyUIParser → Generation → SQLite → Query", language=None)

# ---- Import ----
elif page == "Import":
    st.title("Import")
    uploaded = st.file_uploader("Drop AI-generated PNG", type=["png"], key="import")

    if uploaded:
        # Save temp
        tmp = os.path.join(tempfile.gettempdir(), uploaded.name)
        with open(tmp, "wb") as f:
            f.write(uploaded.read())

        if parser.can_parse(tmp):
            gen = parser.parse(tmp)
            gen_id = db.insert(gen)
            st.success(f"Imported! ID: {gen_id}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Prompt", gen.prompt[:60] + "..." if len(gen.prompt) > 60 else gen.prompt)
                st.metric("Model", gen.model_name or "—")
                st.metric("Seed", gen.seed)
            with col2:
                st.metric("Negative", gen.negative[:60] + "..." if len(gen.negative) > 60 else gen.negative)
                st.metric("Sampler", f"{gen.sampler} / CFG {gen.cfg} / {gen.steps} steps")
                if gen.loras:
                    st.metric("LoRAs", ", ".join(l.name for l in gen.loras))
            os.unlink(tmp)
        else:
            st.error("Not a ComfyUI PNG. No workflow metadata found.")

# ---- Search ----
elif page == "Search":
    st.title("Search")
    keyword = st.text_input("Keyword", placeholder="Search prompt / model / LoRA / seed...")

    if keyword:
        results = db.query(keyword)
        if not results:
            results = db.query_by_model(keyword)
        if not results and keyword.isdigit():
            results = db.query_by_seed(int(keyword))

        st.caption(f"{len(results)} results")
        for gen in results:
            with st.expander(f"#{gen.id} — {gen.prompt[:60]}", expanded=False):
                c1, c2 = st.columns(2)
                c1.write(f"**Prompt:** {gen.prompt}")
                c1.write(f"**Negative:** {gen.negative}")
                c2.write(f"**Model:** {gen.model_name}")
                c2.write(f"**Seed:** {gen.seed}")
                c2.write(f"**Sampler:** {gen.sampler} CFG:{gen.cfg} Steps:{gen.steps}")
                if gen.loras:
                    c2.write(f"**LoRAs:** {', '.join(f'{l.name}({l.weight})' for l in gen.loras)}")
                c2.write(f"**Source:** {gen.parser_name}")

# ---- Detail ----
elif page == "Detail":
    st.title("Detail")
    gen_id = st.number_input("Generation ID", min_value=1, step=1)

    if st.button("Load", use_container_width=True):
        gen = db.get(gen_id)
        if gen:
            st.json(gen.to_dict())
        else:
            st.error("Not found")
