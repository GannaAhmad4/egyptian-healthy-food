import json, os, time
import requests
import streamlit as st

st.set_page_config(page_title="Healthy Egyptian Food", page_icon="🥗", layout="centered",
                   initial_sidebar_state="collapsed")
L = st.session_state.get("lang") or "ar"  # اللغة الحالية: ar أو en
def t(ar, en):
    return en if L == "en" else ar

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html,body,[class*="css"],.stApp,button,input,textarea{font-family:'Cairo',sans-serif!important}
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
st.markdown(f"<style>.stApp{{direction:{'ltr' if L == 'en' else 'rtl'}}}</style>", unsafe_allow_html=True)

# ---------- البيانات ----------
@st.cache_data
def load():
    with open("egyptian_dishes.json", encoding="utf-8") as f:
        return json.load(f)

DATA = load()
DISHES = DATA["dishes"]
BY_ID = {d["id"]: d for d in DISHES}
DISCLAIMER = t(DATA["meta"]["disclaimer"],
               "This information is for education only and is not a substitute for advice from a dietitian or doctor, "
               "especially for people with chronic conditions.")
CAT_EN = {"أطباق رئيسية": "Main dishes", "فطار وأكلات خفيفة": "Breakfast & snacks",
          "شوربة وسلطات": "Soups & salads", "حلويات": "Desserts"}
METH_EN = {"مطبوخ": "Cooked", "مسلوق": "Boiled", "فرن": "Baked", "مشوي": "Grilled", "نيء": "Raw"}
def cat_l(c): return CAT_EN.get(c, c) if L == "en" else c
def meth_l(m): return METH_EN.get(m, m) if L == "en" else m

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
    i, n, g, tg = line.split("|")
    n = [int(x) for x in n]
    AN[int(i)] = {"lv": [(n[0], n[1]), (n[2], n[3]), (n[4], n[5]), (n[6], n[7])],
                  "g": list(g), "tags": tg.split(",")}

# وسم: (عنوان عربي، شرح عربي، عنوان إنجليزي، شرح إنجليزي)
WHY = {
    "bake": ("الشوي أو الخبز بدل القلي الغزير", "القلي الغزير يخلّي الأكل يمتص كمية كبيرة من الزيت. الخبز أو الإيرفراير بيقلل الدهون المضافة ويحافظ على الطعم.",
             "Baking or grilling instead of deep frying", "Deep frying makes food absorb a lot of oil. Baking or air-frying cuts added fat while keeping the flavor."),
    "whole": ("حبوب كاملة (أرز بني، برغل، قمح كامل)", "الحبوب الكاملة بتحتفظ بالنخالة فبتدي ألياف ومعادن وفيتامينات ب أكتر. الألياف بتزود الشبع وتساعد على ثبات سكر الدم بعد الأكل.",
              "Whole grains (brown rice, bulgur, whole wheat)", "Whole grains keep the bran, so they give more fiber, minerals and B vitamins. Fiber increases fullness and helps keep blood sugar steadier after meals."),
    "oil": ("زيت زيتون بكمية قليلة بدل السمنة", "السمنة غنية بالدهون المشبعة، وزيت الزيتون أغلبه دهون أحادية غير مشبعة. الإرشادات الغذائية بتنصح بتقليل المشبعة واستبدالها بغير المشبعة.",
            "A little olive oil instead of ghee", "Ghee is rich in saturated fat, while olive oil is mostly monounsaturated fat. Dietary guidelines advise reducing saturated fat and replacing it with unsaturated fat."),
    "lean": ("لحم أو فراخ قليل الدهن ونزع الجلد", "الجلد والدهن الظاهر مصدر كبير للدهون المشبعة. نزعهم بيحافظ على البروتين ويقلل الدهن.",
             "Lean meat or skinless chicken", "Skin and visible fat are a major source of saturated fat. Removing them keeps the protein and lowers the fat."),
    "salt": ("تقليل الملح والتتبيل بالأعشاب والليمون", "الإفراط في الصوديوم مرتبط بارتفاع ضغط الدم، ومنظمة الصحة العالمية بتنصح بتقليل الملح. الليمون والثوم والأعشاب بتعوض الطعم.",
             "Less salt, more herbs and lemon", "Too much sodium is linked to high blood pressure, and the WHO advises reducing salt. Lemon, garlic and herbs make up for the flavor."),
    "sugar": ("تقليل السكر واستخدام التمر أو العسل بكمية قليلة", "السكريات الحرة بتدي حلاوة بدون عناصر مفيدة. التمر بيضيف ألياف ومعادن، لكن لازم برضه الاعتدال في الكمية.",
              "Less sugar; a little date or honey instead", "Free sugars add sweetness without useful nutrients. Dates add fiber and minerals, but moderation still matters."),
    "dairy": ("ألبان قليلة الدسم", "تقليل الدسم بيخفض الدهون المشبعة مع الحفاظ على البروتين والكالسيوم.",
              "Low-fat dairy", "Lower-fat dairy reduces saturated fat while keeping protein and calcium."),
    "veg": ("زيادة الخضار", "الخضار بتزود الألياف والفيتامينات والمعادن وبتحسن الشبع من غير ما تثقّل الوجبة.",
            "More vegetables", "Vegetables add fiber, vitamins and minerals and improve fullness without making the meal heavy."),
}
GN = {"v": ("خضار وفاكهة", "Vegetables & fruit"), "g": ("نشويات", "Starches"),
      "p": ("بروتين", "Protein"), "d": ("ألبان", "Dairy")}
def gn(k): return GN[k][1 if L == "en" else 0]
PLATE_TARGET = {"v": 50, "g": 25, "p": 25}  # عدّليها حسب الدليل الغذائي المصري المعتمد عندك
SUGGEST = {"v": ("سلطة بلدي أو شوربة خضار", "a baladi salad or vegetable soup"),
           "g": ("أرز بني أو عيش أسمر أو برغل", "brown rice, whole-wheat bread or bulgur"),
           "p": ("فراخ مشوية أو سمك أو عدس أو فول", "grilled chicken, fish, lentils or fava beans"),
           "d": ("زبادي أو لبن قليل الدسم أو جبنة قريش", "plain yogurt, low-fat milk or cottage cheese")}
SOURCES = [
    ("WHO – Healthy diet", "WHO – Healthy diet", "https://www.who.int/news-room/fact-sheets/detail/healthy-diet"),
    ("وزارة الصحة والسكان المصرية – الإرشادات الغذائية والطبق الصحي", "Egypt MoHP – Dietary guidelines & healthy plate", "https://www.mohp.gov.eg/UserFiles/LibraryFiles/664609.pdf"),
    ("المعهد القومي للتغذية", "National Nutrition Institute (NNI)", "https://nni.gov.eg/"),
    ("FAO/INFOODS – جداول التركيب الغذائي للأطعمة المصرية", "FAO/INFOODS – Egypt food composition tables", "https://www.fao.org/infoods/infoods/tables-and-databases/egypt/en/"),
    ("USDA FoodData Central", "USDA FoodData Central", "https://fdc.nal.usda.gov/"),
    ("WHO – Five keys to safer food", "WHO – Five keys to safer food", "https://www.who.int/activities/promoting-safe-food-handling/five-key-to-safer-food"),
]
def src_title(s): return s[1] if L == "en" else s[0]
LBL = {1: ("قليل جدًا", "Very low"), 2: ("قليل", "Low"), 3: ("متوسط", "Medium"), 4: ("عالي", "High"), 5: ("عالي جدًا", "Very high")}
def lbl(n): return LBL[n][1 if L == "en" else 0]

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
                                    **({"reasoning_effort": "low"} if "gpt-oss" in m else {}),
                                    "messages": [{"role": "system", "content": system},
                                                 {"role": "user", "content": user}]}, timeout=45)
            r.raise_for_status()
            out = (r.json()["choices"][0]["message"].get("content") or "").strip()
            if not out:
                raise ValueError("empty reply")
            return out
        except Exception as e:
            err = f"{m}: {e}"
            if getattr(getattr(e, "response", None), "status_code", None) not in (404, 429, 503) and not isinstance(e, ValueError):
                break  # 404 اسم غلط، 429 حد الاستخدام (لكل موديل حد مستقل)، 503 مشغول: جربي اللي بعده
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
                                    "contents": [{"parts": [{"text": user}]}]}, timeout=45)
            r.raise_for_status()
            parts = r.json()["candidates"][0]["content"]["parts"]
            out = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            if not out:
                raise ValueError("empty reply")
            return out
        except Exception as e:
            err = f"{m}: {e}"
            if getattr(getattr(e, "response", None), "status_code", None) not in (404, 429, 503) and not isinstance(e, ValueError):
                break  # 404 اسم غلط، 429 حد الاستخدام (لكل موديل حد مستقل)، 503 مشغول: جربي اللي بعده
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
        return t("⚠️ وصلتي للحد اليومي للأسئلة في الجلسة دي. جربي تاني بعدين.",
                 "⚠️ You reached the question limit for this session. Please try again later.")
    try:
        out = _ask(system, user)
        st.session_state.calls = n + 1
        return out
    except Exception as e:
        return t("⚠️ الخدمة مشغولة دلوقتي، جربي بعد شوية.", "⚠️ The service is busy right now, please try again shortly.") + f"\n\n`{e}`"

def parse_obj(s):
    return json.loads(s[s.find("{"):s.rfind("}") + 1])

# ---------- ترجمة المحتوى للإنجليزية (مرة واحدة وتتخزن لكل المستخدمين) ----------
NAMES_SYS = ("Translate these Egyptian dish names from Arabic to their common English names (e.g. Koshary, Molokhia). "
             "Return ONLY a JSON object with the same keys and no other text.")
DISH_SYS = ("Translate this JSON of Egyptian recipes from Arabic to clear, simple English. Keep exactly the same keys and structure, "
            "translate only the string values. Return ONLY the JSON, no other text.")

@st.cache_data(ttl=604800, show_spinner=False)
def tr_names():
    r = parse_obj(_ask(NAMES_SYS, json.dumps({str(d["id"]): d["name"] for d in DISHES}, ensure_ascii=False)))
    assert len(r) >= 25
    return {int(k): v for k, v in r.items()}

@st.cache_data(ttl=604800, show_spinner=False)
def tr_dish(did):
    d = BY_ID[did]
    keep = {k: d[k] for k in ("traditional", "healthy", "what_changed", "tips")}
    r = parse_obj(_ask(DISH_SYS, json.dumps(keep, ensure_ascii=False)))
    assert all(k in r for k in keep) and isinstance(r["traditional"]["steps"], list) and isinstance(r["healthy"]["steps"], list)
    return r

@st.cache_resource
def _fails():
    return {}

def guarded(key, fn, *args):
    """لو الترجمة فشلت من أقل من 5 دقايق منحاولش تاني (عشان الصفحة ما تعلقش)"""
    f = _fails()
    if time.time() - f.get(key, 0) < 300:
        raise RuntimeError("recent failure")
    try:
        return fn(*args)
    except Exception:
        f[key] = time.time()
        raise

def _names():
    if L != "en":
        return {}
    try:
        return guarded("names", tr_names)
    except Exception:
        return {}
EN = _names()
def dname(i): return (EN.get(i) or BY_ID[i]["name"]) if L == "en" else BY_ID[i]["name"]

def full(d):
    """الأكلة بلغة العرض الحالية"""
    v = dict(d)
    v["name"] = dname(d["id"])
    v["category"], v["healthy_method"] = cat_l(d["category"]), meth_l(d["healthy_method"])
    if L == "en":
        try:
            with st.spinner("Translating..."):
                v.update(guarded(f"d{d['id']}", tr_dish, d["id"]))
        except Exception:
            st.caption("⚠️ English translation is unavailable right now, showing Arabic.")
    return v

CHAT_SYS = ("أنتِ مساعد توعوي لتغذية صحية للأكل المصري، تتكلمين بالعامية المصرية المبسطة. "
            "للأكلة المطلوبة اكتبي: ١) وصفة تقليدية مختصرة ٢) النسخة الصحية بمقاديرها وخطواتها ٣) ليه هي أصح، مع ربطها بمبادئ علمية عامة "
            "(تقليل الدهون المشبعة والملح والسكريات الحرة، وزيادة الألياف والخضار) كما في إرشادات منظمة الصحة العالمية. "
            "في آخر إجابتك اكتبي سطراً منفصلاً بالشكل بالظبط: LEVELS: {'fat':[x,y],'salt':[x,y],'sugar':[x,y],'fiber':[x,y]} "
            "حيث x للوصفة التقليدية وy للصحية، وكل رقم من 1 (قليل) إلى 5 (كتير). "
            "ممنوع ذكر أرقام سعرات أو ادعاءات علاجية أو اختراع أبحاث وأرقام وروابط. لو السؤال خارج الأكل والتغذية اعتذري بلطف.")
if os.path.exists("knowledge.md"):  # ضعي هنا نقاط منقولة من المصادر المعتمدة ليجاوب منها الـ AI
    with open("knowledge.md", encoding="utf-8") as _f:
        CHAT_SYS += "\n\nاعتمدي أولاً على المعلومات التالية المنقولة من المصادر المعتمدة، ولا تخالفيها:\n" + _f.read()[:6000]
PLATE_SYS = ('حللي الأكلة المذكورة وارجعي JSON فقط بدون أي كلام آخر بالشكل {"v":عدد,"g":عدد,"p":عدد,"d":عدد} '
             "يمثل النسب التقريبية (مجموعها 100) لمكوناتها: خضار وفاكهة v، نشويات g، بروتين p، ألبان d.")
def chat_sys():
    return CHAT_SYS + ("\n\nIMPORTANT: Write the whole answer in clear, simple English (keep the LEVELS line as specified)." if L == "en" else "")

# ---------- أدوات مشتركة ----------
EMOJI = {1: "🍜", 2: "🥬", 3: "🥬", 4: "🍃", 5: "🍆", 6: "🍚", 7: "🍚", 8: "🍗", 9: "🐟", 10: "🍅",
         11: "🥔", 12: "🍆", 13: "🥘", 14: "🫛", 15: "🥩", 16: "🫘", 17: "🧆", 18: "🍳", 19: "🥞", 20: "🧀",
         21: "🍟", 22: "🥙", 23: "🍲", 24: "🥣", 25: "🥗", 26: "🍆", 27: "🍮", 28: "🍰", 29: "🍰", 30: "🍚"}
COLORS = {"أطباق رئيسية": "#fde8d0", "فطار وأكلات خفيفة": "#fff3c4",
          "شوربة وسلطات": "#dff3df", "حلويات": "#fbe0ec"}


def pick(key):
    return BY_ID[st.selectbox(t("اختاري الأكلة", "Choose a dish"), [d["id"] for d in DISHES], format_func=dname, key=key)]

def sources_box():
    with st.expander(t("📖 المراجع العلمية", "📖 Scientific references")):
        for s in SOURCES:
            st.markdown(f"- [{src_title(s)}]({s[2]})")
        st.caption(t("الشرح مبني على مبادئ عامة في المراجع دي. راجعي المراجع بنفسك قبل الاعتماد عليها في التقرير. ",
                     "The explanations follow general principles from these references. Check them yourself before relying on them. ")
                   + DISCLAIMER)

def render_compare(lv):
    st.caption(t("التقييم نوعي (من قليل لعالي) وليس تحليلاً معملياً، وبدون سعرات. الأفضل: دهون وملح وسكر أقل، وألياف أكتر.",
                 "Qualitative rating (low to high), not lab analysis, and no calories. Better: less fat, salt and sugar; more fiber."))
    c1, c2 = st.columns(2)
    c1.markdown(t("**🍽️ التقليدية**", "**🍽️ Traditional**"))
    c2.markdown(t("**🌱 الصحية**", "**🌱 Healthy**"))
    names = [t("🧈 الدهون", "🧈 Fat"), t("🧂 الملح", "🧂 Salt"), t("🍬 السكر", "🍬 Sugar"), t("🌾 الألياف", "🌾 Fiber")]
    for name, (a, b) in zip(names, lv):
        c1.progress(a / 5, text=f"{name}: {lbl(a)}")
        c2.progress(b / 5, text=f"{name}: {lbl(b)}")

def split_levels(text):
    i = text.rfind("LEVELS:")
    if i < 0:
        return text, None
    try:
        tail = text[i + 7:]
        d = json.loads(tail[tail.find("{"):tail.rfind("}") + 1].replace("'", '"'))
        lv = [tuple(max(1, min(5, int(x))) for x in d[k][:2]) for k in ("fat", "salt", "sugar", "fiber")]
    except Exception:
        lv = None
    before = text[:i].rstrip(" \n`")
    if not before:  # الموديل كتب LEVELS الأول: خدي اللي بعد السطر
        before = tail[tail.rfind("}") + 1:].strip(" \n`")
    return before, lv

def show_dish(d0):
    d = full(d0)
    if d0["image"].startswith("http") or os.path.exists(d0["image"]):
        st.image(d0["image"], use_container_width=True)
    st.markdown(f"<div class='dish-hero' style='background:{COLORS.get(d0['category'], '#eee')}'>"
                f"<div class='em'>{EMOJI.get(d0['id'], '🍽️')}</div><div><h2>{d['name']}</h2>"
                f"<span class='chip'>{d['category']}</span><span class='chip'>🌱 {d['healthy_method']}</span></div></div>",
                unsafe_allow_html=True)
    t1, t2, t3 = st.tabs([t("🍽️ التقليدية", "🍽️ Traditional"), t("🌱 الصحية", "🌱 Healthy"), t("⚖️ المقارنة", "⚖️ Comparison")])
    for tab, k in ((t1, "traditional"), (t2, "healthy")):
        with tab:
            st.markdown(t("**المقادير**", "**Ingredients**"))
            st.markdown("\n".join(f"- {x}" for x in d[k]["ingredients"]))
            st.markdown(t("**طريقة التحضير**", "**Method**"))
            st.markdown("\n".join(f"{i}. {x}" for i, x in enumerate(d[k]["steps"], 1)))
    with t3:
        render_compare(AN[d0["id"]]["lv"])
    st.success(t("**إيه اللي اتغير؟**", "**What changed?**") + "\n\n" + "\n".join(f"- {x}" for x in d["what_changed"]))
    if d.get("tips"):
        st.info("💡 " + " • ".join(d["tips"]))

# ---------- الصفحات ----------
def page_library():
    st.title(t("📚 مكتبة الأكل المصري", "📚 Egyptian Food Library"))
    c1, c2, c3 = st.columns(3)
    q = c1.text_input(t("ابحثي بالاسم", "Search by name")).strip().lower()
    cat = c2.selectbox(t("القسم", "Category"), ["all"] + DATA["meta"]["categories"],
                       format_func=lambda x: t("الكل", "All") if x == "all" else cat_l(x))
    meth = c3.selectbox(t("طريقة الطهي الصحية", "Healthy cooking method"), ["all"] + sorted({d["healthy_method"] for d in DISHES}),
                        format_func=lambda x: t("الكل", "All") if x == "all" else meth_l(x))
    items = [d for d in DISHES if (not q or q in d["name"] or q in EN.get(d["id"], "").lower())
             and (cat == "all" or d["category"] == cat) and (meth == "all" or d["healthy_method"] == meth)]
    if not items:
        st.info(t("مفيش نتائج، جربي بحث تاني.", "No results, try another search."))
        return
    ids = [d["id"] for d in items]
    if st.session_state.get("dish") not in ids:
        st.session_state.dish = ids[0]
    st.selectbox(t("اختاري الأكلة من المينيو", "Choose a dish from the menu"), ids, format_func=dname, key="dish")
    show_dish(BY_ID[st.session_state.dish])
    with st.expander(t("🖼️ تصفحي بالأيقونات", "🖼️ Browse all dishes")):
        cols = st.columns(3)
        for i, d in enumerate(items):
            with cols[i % 3]:
                st.button(f"{EMOJI.get(d['id'], '🍽️')} {dname(d['id'])}", key=f"b{d['id']}", use_container_width=True,
                          on_click=lambda n=d["id"]: st.session_state.update(dish=n))

def page_why():
    st.title(t("🔬 ليه أصح؟", "🔬 Why is it healthier?"))
    d0 = pick("why")
    d = full(d0)
    for tg in AN[d0["id"]]["tags"]:
        w = WHY[tg]
        with st.expander("✅ " + t(w[0], w[2]), expanded=True):
            st.write(t(w[1], w[3]))
    st.markdown(t("**تعديلات الأكلة دي بالتفصيل:**", "**This dish's changes in detail:**"))
    st.markdown("\n".join(f"- {x}" for x in d["what_changed"]))

PCOL = {"v": "#4caf50", "g": "#f5a623", "p": "#e5665e"}

def donut(vals, title):
    acc, parts = 0, []
    keys = list(PLATE_TARGET)
    for i, k in enumerate(keys):
        end = 100 if i == len(keys) - 1 else acc + vals[k]
        parts.append(f"{PCOL[k]} {acc}% {end}%")
        acc = end
    hole = "radial-gradient(circle,transparent 52%,#000 53%)"
    return (f"<div style='text-align:center'><div style='width:min(150px,36vw);aspect-ratio:1;border-radius:50%;"
            f"margin:0 auto .4rem;background:conic-gradient({','.join(parts)});-webkit-mask:{hole};mask:{hole}'></div>"
            f"<b>{title}</b></div>")

def comp(item, custom):
    if isinstance(item, str):
        return custom[item]
    g = AN[item]["g"]
    return {k: (100 / len(g) if k in g else 0) for k in GN}

def page_plate():
    st.title(t("🍽️ الطبق الصحي", "🍽️ Healthy Plate"))
    st.caption(t("اختاري أكلاتك، وهنوريكي توزيع طبقك مقارنة بالطبق الصحي، والعنصر الناقص. (تقدير مبسط)",
                 "Pick your dishes and see how your plate compares with the healthy plate, and what is missing. (Simplified estimate)"))
    custom = st.session_state.setdefault("custom", {})
    txt = st.text_input(t("أكلة مش في المكتبة؟ اكتبيها وهنحلل مكوناتها", "A dish not in the library? Type it and we'll analyze its components"))
    if st.button(t("حلّلي الأكلة", "Analyze dish")) and txt:
        try:
            s = ask(PLATE_SYS, txt)
            r = parse_obj(s)
            custom[txt] = {k: float(r.get(k, 0)) for k in GN}
            st.success(f"{txt}: " + ("، " if L == "ar" else ", ").join(f"{gn(k)} {int(custom[txt][k])}%" for k in GN))
        except Exception:
            st.warning(t("معرفتش أحلل الأكلة دي، جربي اسم تاني.", "Couldn't analyze this dish, try another name."))
    options = [d["id"] for d in DISHES] + list(custom)
    chosen = st.multiselect(t("اختاري الأكلات", "Choose dishes"), options,
                            format_func=lambda x: dname(x) if isinstance(x, int) else x)
    if not chosen:
        return
    tot = {k: sum(comp(n, custom)[k] for n in chosen) / len(chosen) for k in GN}
    base = sum(tot[k] for k in PLATE_TARGET) or 1
    mine = {k: round(tot[k] / base * 100) for k in PLATE_TARGET}
    c1, c2 = st.columns(2)
    c1.markdown(donut(mine, t("🍽️ طبقك", "🍽️ Your plate")), unsafe_allow_html=True)
    c2.markdown(donut(PLATE_TARGET, t("🥗 الطبق الصحي", "🥗 Healthy plate")), unsafe_allow_html=True)
    st.markdown("<div style='margin:.8rem 0'>" + "".join(
        f"<div style='margin:.25rem 0'><span style='display:inline-block;width:12px;height:12px;border-radius:50%;"
        f"background:{PCOL[k]};margin-inline-end:.45rem'></span>{gn(k)}: {t('طبقك', 'yours')} <b>{mine[k]}%</b> • "
        f"{t('الهدف', 'target')} <b>{PLATE_TARGET[k]}%</b></div>" for k in PLATE_TARGET) + "</div>", unsafe_allow_html=True)
    missing = [k for k in PLATE_TARGET if mine[k] < PLATE_TARGET[k] * 0.6]
    if tot["d"] == 0:
        missing.append("d")
    if missing:
        for k in missing:
            st.warning(t(f"ناقص: **{gn(k)}**. جربي تضيفي: {SUGGEST[k][0]}", f"Missing: **{gn(k)}**. Try adding: {SUGGEST[k][1]}"))
    else:
        st.success(t("طبقك متوازن تقريبًا 👏", "Your plate looks fairly balanced 👏"))

def show_msg(m):
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("lv"):
            st.markdown(t("### ⚖️ مقارنة سريعة", "### ⚖️ Quick comparison"))
            render_compare(m["lv"])
        if m.get("foot"):
            st.markdown(m["foot"])

def page_chat():
    st.title(t("🤖 المساعد الذكي", "🤖 Smart Assistant"))
    st.caption(t("اسألي عن أي أكلة وهقترح نسخة صحية منها مع مقارنة بالأصلية.",
                 "Ask about any dish and I'll suggest a healthier version with a comparison."))
    msgs = st.session_state.setdefault("msgs", [])
    for m in msgs:
        show_msg(m)
    q = st.chat_input(t("اكتبي اسم الأكلة أو سؤالك...", "Type a dish name or your question..."))
    if not q:
        return
    msgs.append({"role": "user", "content": q})
    show_msg(msgs[-1])
    hit = next((d for d in DISHES if d["name"] in q or (EN.get(d["id"]) and EN[d["id"]].lower() in q.lower())), None)
    lv = None
    if hit:
        h = full(hit)
        ans = (t(f"الأكلة دي موجودة في المكتبة 🎉\n\n**النسخة الصحية من {h['name']}:**\n\n",
                 f"This dish is in the library 🎉\n\n**Healthy version of {h['name']}:**\n\n")
               + "\n".join(f"- {x}" for x in h["healthy"]["ingredients"]) + "\n\n"
               + "\n".join(f"{i}. {x}" for i, x in enumerate(h["healthy"]["steps"], 1))
               + t("\n\n**التعديلات:**\n", "\n\n**Changes:**\n") + "\n".join(f"- {x}" for x in h["what_changed"]))
        lv = AN[hit["id"]]["lv"]
    else:
        with st.spinner(t("بفكر...", "Thinking...")):
            ans, lv = split_levels(ask(chat_sys(), q))
            if not ans.strip():
                ans = t("⚠️ مجاش رد، جربي تكتبي السؤال بشكل تاني.", "⚠️ No answer came back, please rephrase your question.")
    foot = None
    if not ans.startswith("⚠️"):
        foot = ("---\n*" + DISCLAIMER + "*\n\n**" + t("المراجع", "References") + ":** "
                + " | ".join(f"[{src_title(s).split(' – ')[0]}]({s[2]})" for s in SOURCES))
    else:
        lv = None
    msgs.append({"role": "assistant", "content": ans, "lv": lv, "foot": foot})
    show_msg(msgs[-1])

PAGES = {"lib": (page_library, "📚 مكتبة الأكل", "📚 Library"), "why": (page_why, "🔬 ليه أصح؟", "🔬 Why healthier?"),
         "plate": (page_plate, "🍽️ الطبق الصحي", "🍽️ Healthy plate"), "chat": (page_chat, "🤖 المساعد الذكي", "🤖 Assistant")}

st.pills("language", ["ar", "en"], format_func=lambda x: "العربية" if x == "ar" else "English", key="lang",
         default="ar", label_visibility="collapsed")
st.markdown(f"<div class='hero'><h1>{t('🥗 الأكل المصري بنسخة صحية', '🥗 Healthy Egyptian Food')}</h1>"
            f"<p>{t('30 أكلة مصرية بالطريقة التقليدية والصحية', '30 Egyptian dishes: traditional and healthy versions')}</p></div>",
            unsafe_allow_html=True)
page = st.pills("menu", list(PAGES), format_func=lambda k: PAGES[k][2 if L == "en" else 1],
                default="lib", key="page", label_visibility="collapsed") or "lib"
PAGES[page][0]()
st.divider()
sources_box()

# 🛠️ لوحة تشخيص: تظهر فقط لو أضفتي ?debug=1 لرابط التطبيق (شيليها قبل التسليم لو حبيتي)
if st.query_params.get("debug"):
    def _has(k):
        try:
            return bool(st.secrets.get(k))
        except Exception:
            return False
    with st.expander("🛠️ Diagnostics", expanded=True):
        st.write({"GROQ_API_KEY set": _has("GROQ_API_KEY"), "GEMINI_API_KEY set": _has("GEMINI_API_KEY")})
        if st.button("Test AI connection"):
            for fn in (call_groq, call_gemini):
                try:
                    st.success(f"{fn.__name__}: {fn('Reply with the single word OK.', 'ping')[:80]}")
                except Exception as e:
                    st.error(f"{fn.__name__}: {e}")
        if st.button("Clear cache"):
            st.cache_data.clear()
            st.success("cache cleared")
