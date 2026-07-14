"""Generation Vault — v0.5.0 精简UI: Drop. Search. Found."""
import sys, os, tempfile, json, struct, zlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from parser import ComfyUIParser
from core.database import Database

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'generation.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = Database(DB_PATH)
parser = ComfyUIParser()

st.set_page_config(page_title="Generation Vault", layout="centered")
st.markdown("""
<style>
    .main-header { text-align:center; font-size:2.2rem; font-weight:800;
        background:linear-gradient(135deg,#667eea,#764ba2);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        margin-bottom:4px; }
    .sub-header { text-align:center; color:#888; font-size:0.95rem; margin-bottom:28px; }
    .result-card { background:#f8f9fa; border-radius:12px; padding:16px 20px; margin:8px 0; border:1px solid #eee; }
    .result-label { color:#667eea; font-weight:600; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.5px; }
    .result-value { font-size:0.95rem; color:#333; margin-top:2px; word-break:break-all; }
    .stat-badge { display:inline-block; background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:12px; font-size:0.8rem; margin:2px; }
    .footer { text-align:center; color:#bbb; font-size:0.75rem; margin-top:40px; }
    .stButton>button { border-radius:8px; }
    div[data-testid="stFileUploader"] { border:2px dashed #667eea; border-radius:16px; padding:24px; text-align:center; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Generation Vault</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Drop a ComfyUI PNG. See every setting instantly. Search everything later.</div>', unsafe_allow_html=True)

# ====== 生成Demo PNG数据 ======
def make_demo_png():
    """创建内置Demo PNG（含ComfyUI元数据）"""
    demo_workflow = json.dumps({
        "6": {"inputs": {"text":"cinematic portrait of a woman with flowing red hair, volumetric lighting, intricate details, hyperrealistic, 8k"},
              "class_type":"CLIPTextEncode"},
        "7": {"inputs": {"text":"blurry, low quality, distorted, ugly, bad anatomy"},
              "class_type":"CLIPTextEncode"},
        "3": {"inputs": {"seed": 172839456, "steps":30, "cfg":7.0, "sampler_name":"euler", "scheduler":"normal"},
              "class_type":"KSampler"},
        "4": {"inputs": {"ckpt_name":"dreamshaper_8.safetensors"},
              "class_type":"CheckpointLoaderSimple"},
        "8": {"inputs": {"lora_name":"detail_enhancer.safetensors", "strength_model":0.6, "strength_clip":0.6},
              "class_type":"LORALoader"},
        "5": {"inputs": {"seed": 172839456},
              "class_type":"EmptyLatentImage"}
    })
    # 构造合法PNG: 签名+IHDR+tEXt(workflow)+IDAT+IEND
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(ctype, data):
        c = struct.pack('>I', len(data)) + ctype + data
        return c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    text_data = b'prompt\0' + demo_workflow.encode()
    text_chunk = chunk(b'tEXt', text_data)
    raw = b'\x00'  # 1px black filter byte
    compressed = zlib.compress(raw)
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')
    return sig + ihdr + text_chunk + idat + iend

# ====== Import区（首页唯一内容）=======
uploaded = st.file_uploader(" ", type=["png"], label_visibility="collapsed")

# "Try Demo" 按钮
col_demo, _ = st.columns([1, 4])
with col_demo:
    try_demo = st.button("🎯 Try Demo", use_container_width=True, type="primary")

if try_demo:
    demo_bytes = make_demo_png()
    tmp = os.path.join(tempfile.gettempdir(), "_demo.png")
    with open(tmp, "wb") as f: f.write(demo_bytes)
    if parser.can_parse(tmp):
        gen = parser.parse(tmp)
        gen_id = db.insert(gen)
        st.balloons()
        st.success(f"Demo imported! ID: {gen_id}")
        show_result(gen)
        st.info("💡 Now try dropping your own ComfyUI PNG above, or search below.")
    os.unlink(tmp)

if uploaded:
    tmp = os.path.join(tempfile.gettempdir(), uploaded.name)
    with open(tmp, "wb") as f: f.write(uploaded.read())
    if parser.can_parse(tmp):
        gen = parser.parse(tmp)
        gen_id = db.insert(gen)
        st.balloons()
        st.success(f"Imported! ID: {gen_id}")
        show_result(gen)
    else:
        st.error("Not a ComfyUI PNG. No workflow metadata found.")
    os.unlink(tmp)

def show_result(gen):
    """显示格式化的导入结果"""
    c1, c2 = st.columns(2)
    with c1:
        card("Prompt", gen.prompt[:200] + ("..." if len(gen.prompt) > 200 else ""))
        card("Negative", gen.negative[:200] + ("..." if len(gen.negative) > 200 else "") if gen.negative else "—")
    with c2:
        card("Model", gen.model_name or "—")
        card("Seed", str(gen.seed))
        card("Sampler", f"{gen.sampler} · CFG {gen.cfg} · {gen.steps} steps")
        if gen.loras:
            lora_str = ", ".join(f"{l.name} ({l.weight})" for l in gen.loras)
            card("LoRAs", lora_str)

def card(label, value):
    st.markdown(f'<div class="result-card"><div class="result-label">{label}</div><div class="result-value">{value}</div></div>', unsafe_allow_html=True)

# ====== Search（折叠在下方）=======
st.markdown("---")
st.markdown("### 🔍 Search your generations")
keyword = st.text_input("", placeholder="Search prompt / model / LoRA / seed...", label_visibility="collapsed")

if keyword:
    results = db.query(keyword)
    if not results: results = db.query_by_model(keyword)
    if not results and keyword.isdigit(): results = db.query_by_seed(int(keyword))
    
    st.caption(f"{len(results)} results")
    for gen in results:
        with st.expander(f"#{gen.id} — {gen.prompt[:60]}", expanded=False):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Prompt:** {gen.prompt}")
            c1.markdown(f"**Negative:** {gen.negative}")
            c2.markdown(f"**Model:** {gen.model_name}")
            c2.markdown(f"**Seed:** {gen.seed}")
            c2.markdown(f"**Sampler:** {gen.sampler} CFG:{gen.cfg} Steps:{gen.steps}")
            if gen.loras:
                c2.markdown(f"**LoRAs:** {', '.join(f'{l.name}({l.weight})' for l in gen.loras)}")
            c2.markdown(f"**Parser:** {gen.parser_name}")
            c2.markdown(f"**Created:** {gen.created_at}")

# ====== Footer ======
total = db.count()
st.markdown(f'<div class="footer">v0.5.0 · {total} generation{"s" if total != 1 else ""} stored locally · MIT</div>', unsafe_allow_html=True)
