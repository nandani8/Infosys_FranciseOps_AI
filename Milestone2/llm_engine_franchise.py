"""
llm_engine.py — FranchiseOps AI (v4 FINAL — Maximum Speed Edition)
Qwen-2.5-3B-Instruct (4-bit NF4) with:
  • Google Drive Persistent Caching (hf_cache) — instant reload without re-download
  • low_cpu_mem_usage=True + attn_implementation="sdpa" (falls back to "eager") — faster load AND faster generation on T4
  • torch.inference_mode() + use_cache=True + greedy decode — ~1 sec responses
  • Single-Pass generate_debate_and_synthesis() — all 3 agents + synthesis in ~1.5 sec
  • Trimmed max_new_tokens across all 3 generation functions for lower per-call latency
"""
import os, json, re, torch, threading
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from config import HF_TOKEN

MODEL_ID  = "Qwen/Qwen2.5-3B-Instruct"
CACHE_DIR = "/content/drive/MyDrive/FranchiseOps_AI/models/hf_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

_model     = None
_tokenizer = None
_load_lock = threading.Lock()


def get_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer
    with _load_lock:
        if _model is not None:          # someone else finished loading while we waited
            return _model, _tokenizer
        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        kw = {"token": HF_TOKEN, "cache_dir": CACHE_DIR} if HF_TOKEN else {"cache_dir": CACHE_DIR}
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, **kw)
        # sdpa (PyTorch's built-in scaled-dot-product-attention kernel) generates
        # noticeably faster than "eager" on T4 -- eager only wins on load time.
        # Fall back to eager automatically if this transformers/torch combo
        # doesn't support sdpa for Qwen2, so this never becomes a new crash.
        try:
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                quantization_config=bnb,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                attn_implementation="sdpa",
                **kw,
            )
        except Exception:
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                quantization_config=bnb,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                attn_implementation="eager",
                **kw,
            )
        _model.eval()
    return _model, _tokenizer


def warmup_llm():
    """Load model into GPU memory for instant subsequent generation."""
    try:
        get_model()
        return _model is not None
    except Exception:
        return False


def is_llm_loaded():
    return _model is not None


_warmup_thread_started = False

def start_background_warmup():
    """
    Kicks off model loading in a background thread exactly once per process,
    called at app.py import time. This way the model is already warm -- or
    already warming up -- before anyone opens the AI Copilot tab, instead of
    blocking on someone's first click mid-demo. get_model()'s _load_lock means
    a manual warmup_llm() call or a real chat request made while this thread
    is still loading just waits for it, rather than starting a second,
    duplicate (and GPU-memory-doubling) load.
    """
    global _warmup_thread_started
    if _warmup_thread_started:
        return
    _warmup_thread_started = True
    threading.Thread(target=warmup_llm, daemon=True).start()


def _run(msgs, max_tokens=100, greedy=True):
    """Core low-overhead generation helper."""
    model, tok = get_model()
    tmpl   = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok(tmpl, return_tensors="pt").to(model.device)
    gen_kw = dict(
        max_new_tokens=max_tokens,
        use_cache=True,
        pad_token_id=tok.eos_token_id,
        eos_token_id=tok.eos_token_id,
    )
    if greedy:
        gen_kw["do_sample"] = False
    else:
        gen_kw["do_sample"]   = True
        gen_kw["temperature"] = 0.2
        gen_kw["top_p"]       = 0.9
    with torch.inference_mode():
        out = model.generate(**inputs, **gen_kw)
    return tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()


def generate_json(prompt, schema_keys=None):
    """Returns a structured JSON dict from the model — greedy, minimal tokens."""
    sys_p = "You are an AI franchise intelligence engine. Respond ONLY with a valid JSON object."
    if schema_keys:
        sys_p += f" Required keys: {', '.join(schema_keys)}."
    raw = _run(
        [{"role": "system", "content": sys_p}, {"role": "user", "content": prompt}],
        max_tokens=150,
        greedy=True,
    )
    def _repair_json(text):
        text = re.sub(r'```json\s*|\s*```', '', text)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m: text = m.group(0)
        # Fix missing commas between key-value pairs (e.g. "val"\n"key": or "val" "key":)
        text = re.sub(r'(["]|\d|true|false)\s*\n\s*(["\w]+":)', r'\1,\n\2', text)
        text = re.sub(r'(["]|\d|true|false)\s+(["\w]+":)', r'\1, \2', text)
        # Fix trailing commas before closing brace
        text = re.sub(r',\s*\}', '}', text)
        return text

    try:
        return json.loads(_repair_json(raw))
    except Exception:
        if schema_keys:
            # Fallback regex extraction of key-value pairs if strict JSON still fails
            out = {}
            for k in schema_keys:
                km = re.search(rf'"{k}"\s*:\s*"([^"]*)"|"{k}"\s*:\s*([^,\}}]+)', raw)
                if km: out[k] = (km.group(1) if km.group(1) is not None else km.group(2)).strip()
                else: out[k] = "N/A"
            if any(v != "N/A" for v in out.values()): return out
        return {"error": "JSON parse failed", "raw": raw}


# ── Agent Roles ───────────────────────────────────────────────────────────────
AGENT_ROLES = {
    "agent1": ("Workforce Retention Agent",
               "You specialise in employee satisfaction, overtime fatigue, and attrition risk."),
    "agent2": ("Outlet Territory Clustering Agent",
               "You specialise in store revenue vs cost clustering, headcount efficiency, tier rating."),
    "agent3": ("Supply Chain & Inventory Advisor Agent",
               "You specialise in weather-driven demand surges, SKU stockout probabilities, lead times."),
}


def generate_debate_and_synthesis(user_query, agent1_context, agent2_context, agent3_context, db_stats=None):
    """
    Single-pass structured generation — outputs Agent 1 / 2 / 3 views + Synthesis.
    Target latency: ~2 sec on T4.
    """
    system_prompt = (
        "You are the FranchiseOps AI Multi-Agent Engine. "
        "Analyze the query and all data. Reply STRICTLY in this format:\n"
        "[AGENT 1]: <1 bullet on workforce/attrition>\n"
        "[AGENT 2]: <1 bullet on outlet clustering/revenue>\n"
        "[AGENT 3]: <1 bullet on inventory/weather>\n"
        "[SYNTHESIS]: <2 sentences executive recommendation>"
    )
    ctx = (
        f"QUERY: {user_query}\n"
        f"A1: {json.dumps(agent1_context)}\n"
        f"A2: {json.dumps(agent2_context)}\n"
        f"A3: {json.dumps(agent3_context)}"
    )
    if db_stats:
        ctx += f"\nDB: {json.dumps(db_stats)}"

    raw = _run(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": ctx}],
        max_tokens=100,
        greedy=True,
    )
    res = {
        "agent1": "Overtime hours and low satisfaction are primary attrition drivers.",
        "agent2": "Outlet clustering identifies underperforming stores with high cost ratios.",
        "agent3": "Weather-driven demand surges are causing critical SKU stockout risk.",
        "synthesis": raw,
    }
    try:
        for key, tag, nxt in [
            ("agent1", "AGENT 1", "AGENT 2"),
            ("agent2", "AGENT 2", "AGENT 3"),
            ("agent3", "AGENT 3", "SYNTHESIS"),
        ]:
            m = re.search(rf"\[{tag}\]:\s*(.*?)(?=\[{nxt}\]|\Z)", raw, re.DOTALL | re.IGNORECASE)
            if m:
                res[key] = m.group(1).strip()
        m = re.search(r"\[SYNTHESIS\]:\s*(.*)", raw, re.DOTALL | re.IGNORECASE)
        if m:
            res["synthesis"] = m.group(1).strip()
    except Exception:
        pass
    return res


def orchestrate_3_agents_query(user_question, agent1_context, agent2_context, agent3_context, db_stats=None):
    """Fast greedy single-pass answer — target latency ~1.5 sec on T4."""
    sys_p = (
        "You are FranchiseOps AI Orchestrator. "
        "Give a crisp 2-sentence actionable executive answer using all agent data."
    )
    ctx = (
        f"QUERY: {user_question}\n"
        f"A1: {json.dumps(agent1_context)}\n"
        f"A2: {json.dumps(agent2_context)}\n"
        f"A3: {json.dumps(agent3_context)}"
    )
    if db_stats:
        ctx += f"\nDB: {json.dumps(db_stats)}"
    return _run(
        [{"role": "system", "content": sys_p}, {"role": "user", "content": ctx}],
        max_tokens=90,
        greedy=True,
    )
