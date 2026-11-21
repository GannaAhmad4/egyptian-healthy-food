import json, os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="الأكل المصري الصحي", page_icon="🥗", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html,body,[class*="css"],.stApp,button,input,textarea{font-family:'Cairo',sans-serif!important}
.stApp{direction:rtl}
.block-container{max-width:980px;padding:1.2rem 1rem 4rem}
header[data-testid="stHeader"],footer,#MainMenu,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
h1{font-size:clamp(1.4rem,5vw,2.1rem)!important}
h2,h3{font-size:clamp(1.1rem,4vw,1.5rem)!important}
.hero{background:linear-gradient(135deg,#2e7d4f,#58b77a);border-radius:20px;padding:1.3rem 1rem;text-align:center;margin-bottom:.8rem}
.hero *{color:#fff!important;margin:0}
.hero h1{font-size:clamp(1.3rem,5.5vw,2rem)!important;padding:0}
.hero p{font-size:clamp(.85rem,3.2vw,1rem);opacity:.95;margin-top:.3rem}
.dish-hero{display:flex;align-items:center;gap:1rem;border-radius:18px;padding:1rem 1.2rem;margin:.5rem 0 1rem}
.dish-hero *{color:#1f2d27!important}
.dish-hero .em{font-size:clamp(2.6rem,12vw,4rem);line-height:1}
.dish-hero h2{margin:0 0 .4rem;padding:0}
.chip{display:inline-block;padding:.1rem .7rem;margin-left:.4rem;border-radius:999px;background:rgba(46,125,79,.18);font-size:.85rem}
div[role="radiogroup"]{flex-wrap:wrap;gap:.4rem;justify-content:center}
div[role="radiogroup"] label{background:rgba(46,125,79,.1);border:1px solid rgba(46,125,79,.35);border-radius:999px;padding:.25rem .9rem;margin:0}
div[role="radiogroup"] label>div:first-child,label[data-baseweb="radio"]>div:first-child{display:none!important}
div[role="radiogroup"] label:has(input:checked){background:#2e7d4f;border-color:#2e7d4f}
div[role="radiogroup"] label:has(input:checked) *{color:#fff!important}
.stTabs [data-baseweb="tab-list"]{overflow-x:auto;gap:.3rem}
.stButton>button{border-radius:12px;width:100%}
[data-testid="stAlert"]{border-radius:14px}
img{max-width:100%;border-radius:16px}
@media(max-width:640px){
 .block-container{padding:.7rem .6rem 3rem}
 [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.5rem!important}
 [data-testid="stColumn"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
}
</style>""", unsafe_allow_html=True)

# ---------- البيانات ----------
@st.cache_data
def load():
    with open("egyptian_dishes.json", encoding="utf-8") as f:
        return json.load(f)

DATA = load()
DISHES = DATA["dishes"]
BY_NAME = {d["name"]: d for d in DISHES}
DISCLAIMER = DATA["meta"]["disclaimer"]

# id | دهون(تقليدي,صحي) ملح سكر ألياف (1 قليل - 5 كتير) | مجموعات: g نشويات p بروتين v خضار d ألبان | وسوم التعديل
RAW = """1|42431135|gpv|whole,bake,oil,salt
2|42321134|vpg|lean,oil,whole,bake
3|32321135|vg|whole,veg,oil
4|32421135|vg|whole,veg,oil,salt
5|32321135|vg|bake,whole,veg,oil
6|52321124|gpv|whole,bake,lean,oil
7|52221113|gd|dairy,whole,oil
8|42321124|pg|lean,bake,whole,salt
9|52321112|pv|bake,oil
10|42321123|pv|lean,bake,veg,oil
11|52321124|pvg|bake,veg,lean,oil
12|52321134|v|bake,oil,veg
13|42321134|vp|lean,oil,veg
14|32321134|vp|lean,oil,veg
15|42321113|pv|lean,bake,veg,oil
16|32321145|pv|oil,salt,whole,veg
17|52321135|pv|bake,veg,whole
18|42531112|pv|salt,oil,veg
19|53213213|gd|whole,oil,sugar
20|42531113|dv|salt,veg,dairy
21|52211123|g|bake,oil,salt
22|52421114|gpv|whole,lean,bake,veg
23|31321145|pv|oil,veg,salt
24|31421135|v|salt,oil,veg
25|21311135|v|oil,salt,veg
26|42321124|vd|dairy,bake,veg
27|42115313|gd|dairy,sugar,whole
28|52115312|gd|oil,dairy,sugar
29|42115313|gd|whole,oil,sugar
30|32114212|gd|dairy,sugar,whole"""
AN = {}
for line in RAW.splitlines():
    i, n, g, t = line.split("|")
    n = [int(x) for x in n]
    AN[int(i)] = {"lv": [(n[0], n[1]), (n[2], n[3]), (n[4], n[5]), (n[6], n[7])],
                  "g": list(g), "tags": t.split(",")}

WHY = {
    "bake": ("الشوي أو الخبز بدل القلي الغزير", "القلي الغزير يخلّي الأكل يمتص كمية كبيرة من الزيت. الخبز أو الإيرفراير بيقلل الدهون المضافة ويحافظ على الطعم."),
    "whole": ("حبوب كاملة (أرز بني، برغل، قمح كامل)", "الحبوب الكاملة بتحتفظ بالنخالة فبتدي ألياف ومعادن وفيتامينات ب أكتر. الألياف بتزود الشبع وتساعد على ثبات سكر الدم بعد الأكل."),
    "oil": ("زيت زيتون بكمية قليلة بدل السمنة", "السمنة غنية بالدهون المشبعة، وزيت الزيتون أغلبه دهون أحادية غير مشبعة. الإرشادات الغذائية بتنصح بتقليل المشبعة واستبدالها بغير المشبعة."),
    "lean": ("لحم أو فراخ قليل الدهن ونزع الجلد", "الجلد والدهن الظاهر مصدر كبير للدهون المشبعة. نزعهم بيحافظ على البروتين ويقلل الدهن."),
    "salt": ("تقليل الملح والتتبيل بالأعشاب والليمون", "الإفراط في الصوديوم مرتبط بارتفاع ضغط الدم، ومنظمة الصحة العالمية بتنصح بتقليل الملح. الليمون والثوم والأعشاب بتعوض الطعم."),
    "sugar": ("تقليل السكر واستخدام التمر أو العسل بكمية قليلة", "السكريات الحرة بتدي حلاوة بدون عناصر مفيدة. التمر بيضيف ألياف ومعادن، لكن لازم برضه الاعتدال في الكمية."),
    "dairy": ("ألبان قليلة الدسم", "تقليل الدسم بيخفض الدهون المشبعة مع الحفاظ على البروتين والكالسيوم."),
    "veg": ("زيادة الخضار", "الخضار بتزود الألياف والفيتامينات والمعادن وبتحسن الشبع من غير ما تثقّل الوجبة."),
}
GN = {"v": "خضار وفاكهة", "g": "نشويات", "p": "بروتين", "d": "ألبان"}
PLATE_TARGET = {"v": 50, "g": 25, "p": 25}  # عدّليها حسب الدليل الغذائي المصري المعتمد عندك
SUGGEST = {"v": "سلطة بلدي أو شوربة خضار", "g": "أرز بني أو عيش أسمر أو برغل",
           "p": "فراخ مشوية أو سمك أو عدس أو فول", "d": "زبادي أو لبن قليل الدسم أو جبنة قريش"}
SOURCES = [
    ("WHO – Healthy diet", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet"),
    ("وزارة الصحة والسكان المصرية – الإرشادات الغذائية والطبق الصحي", "https://www.mohp.gov.eg/UserFiles/LibraryFiles/664609.pdf"),
    ("المعهد القومي للتغذية", "https://nni.gov.eg/"),
    ("FAO/INFOODS – جداول التركيب الغذائي للأطعمة المصرية", "https://www.fao.org/infoods/infoods/tables-and-databases/egypt/en/"),
    ("USDA FoodData Central", "https://fdc.nal.usda.gov/"),
    ("WHO – Five keys to safer food", "https://www.who.int/activities/promoting-safe-food-handling/five-key-to-safer-food"),
]
LBL = {1: "قليل جدًا", 2: "قليل", 3: "متوسط", 4: "عالي", 5: "عالي جدًا"}

# ---------- الذكاء الاصطناعي: Groq ثم Gemini ----------
def _models(secret_key, defaults):
    custom = st.secrets.get(secret_key)
    return ([custom] if custom else []) + [m for m in defaults if m != custom]

def call_groq(system, user):
    k = st.secrets.get("GROQ_API_KEY")
    if not k:
        raise RuntimeError("no groq key")
    err = None
    for m in _models("GROQ_MODEL", ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {k}"},
                              json={"model": m, "temperature": 0.3,
                                    "messages": [{"role": "system", "content": system},
                                                 {"role": "user", "content": user}]}, timeout=40)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            err = f"{m}: {e}"
    raise RuntimeError(err)

def call_gemini(system, user):
    k = st.secrets.get("GEMINI_API_KEY")
    if not k:
        raise RuntimeError("no gemini key")
    err = None
    for m in _models("GEMINI_MODEL", ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                              headers={"x-goog-api-key": k},
                              json={"systemInstruction": {"parts": [{"text": system}]},
                                    "contents": [{"parts": [{"text": user}]}]}, timeout=40)
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts if not p.get("thought"))
        except Exception as e:
            err = f"{m}: {e}"
    raise RuntimeError(err)

@st.cache_data(ttl=86400, show_spinner=False)
def _ask(system, user):
    errs = []
    for fn in (call_groq, call_gemini):  # لو Groq خلص أو فشل يروح على Gemini
        try:
            return fn(system, user)
        except Exception as e:
            errs.append(f"{fn.__name__}: {e}")
    raise RuntimeError(" | ".join(errs))

def ask(system, user, limit=20):
    n = st.session_state.setdefault("calls", 0)
    if n >= limit:
        return "⚠️ وصلتي للحد اليومي للأسئلة في الجلسة دي. جربي تاني بعدين."
    try:
        out = _ask(system, user)
        st.session_state.calls = n + 1
        return out
    except Exception as e:
        return f"⚠️ الخدمة مشغولة دلوقتي، جربي بعد شوية.\n\n`تفاصيل للمطورة: {e}`"

CHAT_SYS = ("أنتِ مساعد توعوي لتغذية صحية للأكل المصري، تتكلمين بالعامية المصرية المبسطة. "
            "للأكلة المطلوبة اكتبي: ١) وصفة تقليدية مختصرة ٢) النسخة الصحية بمقاديرها وخطواتها ٣) ليه هي أصح، مع ربطها بمبادئ علمية عامة "
            "(تقليل الدهون المشبعة والملح والسكريات الحرة، وزيادة الألياف والخضار) كما في إرشادات منظمة الصحة العالمية. "
            "ممنوع ذكر أرقام سعرات أو ادعاءات علاجية أو اختراع أبحاث وأرقام وروابط. لو السؤال خارج الأكل والتغذية اعتذري بلطف.")
if os.path.exists("knowledge.md"):  # ضعي هنا نقاط منقولة من المصادر المعتمدة ليجاوب منها الـ AI
    with open("knowledge.md", encoding="utf-8") as _f:
        CHAT_SYS += "\n\nاعتمدي أولاً على المعلومات التالية المنقولة من المصادر المعتمدة، ولا تخالفيها:\n" + _f.read()[:6000]
PLATE_SYS = ('حللي الأكلة المذكورة وارجعي JSON فقط بدون أي كلام آخر بالشكل {"v":عدد,"g":عدد,"p":عدد,"d":عدد} '
             "يمثل النسب التقريبية (مجموعها 100) لمكوناتها: خضار وفاكهة v، نشويات g، بروتين p، ألبان d.")

# ---------- أدوات مشتركة ----------
EMOJI = {1: "🍜", 2: "🥬", 3: "🥬", 4: "🍃", 5: "🍆", 6: "🍚", 7: "🍚", 8: "🍗", 9: "🐟", 10: "🍅",
         11: "🥔", 12: "🍆", 13: "🥘", 14: "🫛", 15: "🥩", 16: "🫘", 17: "🧆", 18: "🍳", 19: "🥞", 20: "🧀",
         21: "🍟", 22: "🥙", 23: "🍲", 24: "🥣", 25: "🥗", 26: "🍆", 27: "🍮", 28: "🍰", 29: "🍰", 30: "🍚"}
COLORS = {"أطباق رئيسية": "#fde8d0", "فطار وأكلات خفيفة": "#fff3c4",
          "شوربة وسلطات": "#dff3df", "حلويات": "#fbe0ec"}

def img(d):
    p = d["image"]
    if p.startswith("http") or os.path.exists(p):  # صورة محلية أو رابط
        st.image(p, use_container_width=True)
    else:  # بدون صورة: كارت إيموجي ملون
        st.markdown(f"<div style='background:{COLORS.get(d['category'], '#eee')};border-radius:16px;"
                    f"padding:28px 0;text-align:center;font-size:64px'>{EMOJI.get(d['id'], '🍽️')}</div>",
                    unsafe_allow_html=True)

def pick(key):
    return BY_NAME[st.selectbox("اختاري الأكلة", [d["name"] for d in DISHES], key=key)]

def sources_box():
    with st.expander("📖 المراجع العلمية"):
        for t, u in SOURCES:
            st.markdown(f"- [{t}]({u})")
        st.caption("الشرح مبني على مبادئ عامة في المراجع دي. راجعي المراجع بنفسك قبل الاعتماد عليها في التقرير. " + DISCLAIMER)

def show_dish(d):
    if d["image"].startswith("http") or os.path.exists(d["image"]):
        st.image(d["image"], use_container_width=True)
    st.markdown(f"<div class='dish-hero' style='background:{COLORS.get(d['category'], '#eee')}'>"
                f"<div class='em'>{EMOJI.get(d['id'], '🍽️')}</div><div><h2>{d['name']}</h2>"
                f"<span class='chip'>{d['category']}</span><span class='chip'>🌱 {d['healthy_method']}</span></div></div>",
                unsafe_allow_html=True)
    t1, t2 = st.tabs(["🍽️ التقليدية", "🌱 الصحية"])
    for tab, k in ((t1, "traditional"), (t2, "healthy")):
        with tab:
            st.markdown("**المقادير**")
            st.markdown("\n".join(f"- {x}" for x in d[k]["ingredients"]))
            st.markdown("**طريقة التحضير**")
            st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(d[k]["steps"], 1)))
    st.success("**إيه اللي اتغير؟**\n\n" + "\n".join(f"- {x}" for x in d["what_changed"]))
    if d.get("tips"):
        st.info("💡 " + " • ".join(d["tips"]))

# ---------- الصفحات ----------
def page_library():
    st.title("📚 مكتبة الأكل المصري")
    c1, c2, c3 = st.columns(3)
    q = c1.text_input("ابحثي بالاسم")
    cat = c2.selectbox("القسم", ["الكل"] + DATA["meta"]["categories"])
    meth = c3.selectbox("طريقة الطهي الصحية", ["الكل"] + sorted({d["healthy_method"] for d in DISHES}))
    items = [d for d in DISHES if (not q or q in d["name"]) and (cat == "الكل" or d["category"] == cat)
             and (meth == "الكل" or d["healthy_method"] == meth)]
    if not items:
        st.info("مفيش نتائج، جربي بحث تاني.")
        return
    names = [d["name"] for d in items]
    if st.session_state.get("dish") not in names:
        st.session_state.dish = names[0]
    st.selectbox("اختاري الأكلة من المينيو", names, key="dish")
    show_dish(BY_NAME[st.session_state.dish])
    with st.expander("🖼️ تصفحي بالصور"):
        cols = st.columns(3)
        for i, d in enumerate(items):
            with cols[i % 3]:
                st.button(f"{EMOJI.get(d['id'], '🍽️')} {d['name']}", key=f"b{d['id']}", use_container_width=True,
                          on_click=lambda n=d["name"]: st.session_state.update(dish=n))

def page_compare():
    st.title("⚖️ مقارنة طرق الطبخ")
    d = pick("cmp")
    a = AN[d["id"]]
    st.caption("التقييم نوعي (من قليل لعالي) مبني على المقادير وطريقة الطهي وليس تحليلاً معملياً، وبدون سعرات.")
    c1, c2 = st.columns(2)
    c1.markdown("### 🍽️ التقليدية")
    c2.markdown("### 🌱 الصحية")
    for (name, (t, h)) in zip(["🧈 الدهون", "🧂 الملح", "🍬 السكر", "🌾 الألياف"], a["lv"]):
        c1.progress(t / 5, text=f"{name}: {LBL[t]}")
        c2.progress(h / 5, text=f"{name}: {LBL[h]}")
    st.info("الدهون والملح والسكر الأفضل فيهم أقل، أما الألياف فالأفضل أكتر.")

def page_why():
    st.title("🔬 ليه أصح؟")
    d = pick("why")
    for t in AN[d["id"]]["tags"]:
        title, text = WHY[t]
        with st.expander(f"✅ {title}", expanded=True):
            st.write(text)
    st.markdown("**تعديلات الأكلة دي بالتفصيل:**")
    st.markdown("\n".join(f"- {x}" for x in d["what_changed"]))

def comp(name, custom):
    if name in custom:
        return custom[name]
    g = AN[BY_NAME[name]["id"]]["g"]
    return {k: (100 / len(g) if k in g else 0) for k in GN}

def page_plate():
    st.title("🍽️ الطبق الصحي")
    st.caption("اختاري أكلاتك، وهنوريكي توزيع طبقك مقارنة بالطبق الصحي، والعنصر الناقص. (تقدير مبسط)")
    custom = st.session_state.setdefault("custom", {})
    txt = st.text_input("أكلة مش في المكتبة؟ اكتبيها وهنحلل مكوناتها")
    if st.button("حلّلي الأكلة") and txt:
        try:
            s = ask(PLATE_SYS, txt)
            r = json.loads(s[s.find("{"):s.rfind("}") + 1])
            custom[txt] = {k: float(r.get(k, 0)) for k in GN}
            st.success(f"{txt}: " + "، ".join(f"{GN[k]} {int(custom[txt][k])}٪" for k in GN))
        except Exception:
            st.warning("معرفتش أحلل الأكلة دي، جربي اسم تاني.")
    chosen = st.multiselect("اختاري الأكلات", [d["name"] for d in DISHES] + list(custom))
    if not chosen:
        return
    tot = {k: sum(comp(n, custom)[k] for n in chosen) / len(chosen) for k in GN}
    base = sum(tot[k] for k in PLATE_TARGET) or 1
    mine = {k: round(tot[k] / base * 100) for k in PLATE_TARGET}
    df = pd.DataFrame({"طبقك": [mine[k] for k in PLATE_TARGET],
                       "الطبق الصحي": [PLATE_TARGET[k] for k in PLATE_TARGET]},
                      index=[GN[k] for k in PLATE_TARGET])
    st.bar_chart(df)
    missing = [k for k in PLATE_TARGET if mine[k] < PLATE_TARGET[k] * 0.6]
    if tot["d"] == 0:
        missing.append("d")
    if missing:
        for k in missing:
            st.warning(f"ناقص: **{GN[k]}**. جربي تضيفي: {SUGGEST[k]}")
    else:
        st.success("طبقك متوازن تقريبًا 👏")

def page_chat():
    st.title("🤖 المساعد الذكي")
    st.caption("اسألي عن أي أكلة وهقترح نسخة صحية منها.")
    msgs = st.session_state.setdefault("msgs", [])
    for m in msgs:
        st.chat_message(m["role"]).write(m["content"])
    q = st.chat_input("اكتبي اسم الأكلة أو سؤالك...")
    if not q:
        return
    msgs.append({"role": "user", "content": q})
    st.chat_message("user").write(q)
    hit = next((d for d in DISHES if d["name"] in q), None)
    if hit:
        ans = (f"الأكلة دي موجودة في المكتبة 🎉\n\n**النسخة الصحية من {hit['name']}:**\n\n"
               + "\n".join(f"- {x}" for x in hit["healthy"]["ingredients"]) + "\n\n"
               + "\n".join(f"{i}. {x}" for i, x in enumerate(hit["healthy"]["steps"], 1))
               + "\n\n**التعديلات:**\n" + "\n".join(f"- {x}" for x in hit["what_changed"]))
    else:
        with st.spinner("بفكر..."):
            ans = ask(CHAT_SYS, q)
    if not ans.startswith("⚠️"):
        ans += "\n\n---\n*" + DISCLAIMER + "*\n\n**المراجع:** " + " | ".join(f"[{t.split(' – ')[0]}]({u})" for t, u in SOURCES)
    msgs.append({"role": "assistant", "content": ans})
    st.chat_message("assistant").write(ans)

PAGES = {"📚 مكتبة الأكل": page_library, "⚖️ مقارنة الطبخ": page_compare, "🔬 ليه أصح؟": page_why,
         "🍽️ الطبق الصحي": page_plate, "🤖 المساعد الذكي": page_chat}
st.markdown("<div class='hero'><h1>🥗 الأكل المصري بنسخة صحية</h1>"
            "<p>30 أكلة مصرية بالطريقة التقليدية والصحية</p></div>", unsafe_allow_html=True)
PAGES[st.radio("القائمة", list(PAGES), horizontal=True, label_visibility="collapsed")]()
st.divider()
sources_box()
