"""Builds the Soul on Tenth concept pages from data/services.json and data/staff.json
(both taken from Soul's public Square booking page on November 17, 2026).
Design direction: "Soul after dark", black-and-white editorial, wide grotesk type, blush accent.
Run: python build.py  (writes the .html files next to this script)"""
import html, json, os, re

OUT = os.path.dirname(os.path.abspath(__file__))
BOOK = "https://book.squareup.com/appointments/bp8okbmrqv0b9o/location/DH0CR95W0RNAC/services"
SHOP = "https://soulontenth.square.site"
GIFT = "https://squareup.com/gift/7G8EJMYGEEBGZ/order"
IG = "https://www.instagram.com/soulontenth"
MAP = "https://www.google.com/maps/search/?api=1&amp;query=Soul+118+10th+St+Brandon+MB"
e = html.escape

SERVICES = json.load(open(os.path.join(OUT, "data/services.json"), encoding="utf-8"))
STAFF = json.load(open(os.path.join(OUT, "data/staff.json"), encoding="utf-8"))

PAGES = [("index.html", "Home"), ("services.html", "Menu"), ("artists.html", "Artists"),
         ("shop.html", "Shop"), ("visit.html", "Visit")]

# Square category -> (display name, group used on the Artists page)
CATS = {
 "Haircuts": ("Haircuts", "Hair"), "Colouring/Blonding": ("Colour & Blonding", "Hair"),
 "Styling": ("Styling & Updos", "Hair"), "In-Salon Hair Treatments": ("Hair Treatments", "Hair"),
 "Hair Extentions": ("Hair Extensions", "Hair"), "Nails": ("Nails", "Nails"),
 "Pedicures": ("Pedicures", "Nails"), "Lashes": ("Lashes", "Lashes & Brows"),
 "Brows": ("Brows", "Lashes & Brows"), "Facials": ("Facials & Skin", "Skin & Hair Removal"),
 "Waxing": ("Waxing", "Skin & Hair Removal"), "Sugaring": ("Sugaring", "Skin & Hair Removal"),
 "Airbrush Tan & Teeth Whitening": ("Tan & Teeth Whitening", "Tan & Teeth"),
 "Makeup": ("Makeup", "Makeup"), "Soul Healing": ("Soul Healing", "Body & Wellness"),
 "Other": ("Body Contouring & Massage", "Body & Wellness"),
}
GROUPS = ["Hair", "Nails", "Lashes & Brows", "Skin & Hair Removal", "Tan & Teeth", "Body & Wellness"]

DESC = {
 "Brazilian Sugaring (New)": "Full bikini-area hair removal. Let hair grow to about 1/4 inch first, and please don't shave.",
 "Brazilian Wax (New)": "Full bikini-area hair removal. Let hair grow to about 1/4 inch first, and please don't shave.",
 "Manzillian": "Full hair removal for the groin area. Hair should be about 1/4 inch long.",
 "Soul-Led Healing Session": "Energy work, sound healing and intuitive guidance for emotional and spiritual renewal.",
}

def slug(s): return re.sub(r"[^a-z]+", "-", s.lower()).strip("-")

def ext(url, text, cls="btn"):
    return f'<a class="{cls}" href="{url}" target="_blank" rel="noopener">{text}</a>'

def price(s):
    c, pd = s["cents"], (s["pdesc"] or "")
    if s["ptype"] == "fixed" and not pd:
        if not c: return "Free"
        return f"${c/100:.0f}" if c % 100 == 0 else f"${c/100:.2f}"
    m = re.search(r"\$(\d+) and up", pd)
    if m: return f"<i>from</i> ${m.group(1)}"
    if "consultation" in pd: return "<i>at consult</i>"
    return "<i>by artist</i>"

def short(s):
    if s["name"] in DESC: return DESC[s["name"]]
    d = s["desc"]
    first = re.split(r"(?<=[.!?])\s", d, 1)[0] if d else ""
    return first if len(first) <= 110 else first[:107].rsplit(" ", 1)[0] + "…"

def dur(m):
    h, mm = divmod(m, 60)
    return ((f"{h}h " if h else "") + (f"{mm}m" if mm else "")).strip() if m else ""

FILL = re.compile(r"^(.*?) Fill \((\d) weeks?\)$")
def rows(items):
    fills, out = {}, []
    for s in sorted(items, key=lambda s: s["name"].lower()):
        m = FILL.match(s["name"])
        if m:
            key = m.group(1) + " Fill"
            if key not in fills:
                fills[key] = []; out.append(("fill", key, fills[key]))
            fills[key].append((int(m.group(2)), s))
        else:
            out.append(("one", s["name"], s))
    html_rows = []
    for kind, name, val in out:
        if kind == "one":
            s = val; note = short(s)
            html_rows.append(
                f'<a class="row" href="{BOOK}/{s["id"]}" target="_blank" rel="noopener" data-q="{e((name+" "+note).lower())}">'
                f'<span class="row__name">{e(name)}<small>{e(note)}</small></span><span class="row__dots" aria-hidden="true"></span>'
                f'<span class="row__meta">{dur(s["mins"])}</span><span class="row__price">{price(s)}</span><span class="row__go" aria-hidden="true">↗</span></a>')
        else:
            chips = "".join(f'<a href="{BOOK}/{s["id"]}" target="_blank" rel="noopener">{w} wk · {price(s)}</a>' for w, s in sorted(val, key=lambda x: x[0]))
            html_rows.append(f'<div class="row row--fill" data-q="{e(name.lower())} fill"><span class="row__name">{e(name)}<small>Weeks since your last set:</small></span><span class="chips">{chips}</span></div>')
    return "".join(html_rows), len(out)

# ---------- artists ----------
def artist_profile(a):
    totals = {}
    for c, n in a["cats"].items():
        g = CATS.get(c, ("", "Body & Wellness"))[1]
        totals[g] = totals.get(g, 0) + n
    main = max(totals, key=totals.get)
    cut = min(totals[main], max(2, 0.2 * totals[main]))
    tags = [g for g in GROUPS if totals.get(g, 0) >= cut]
    groups = list(tags)
    if main == "Hair":
        tags = ["Cuts & colour"] + (["Extensions"] if a["cats"].get("Hair Extentions") else []) + [t for t in tags if t != "Hair"]
    if main == "Body & Wellness":
        tags = ["Body contouring" if a["cats"].get("Other") else "Soul Healing"]
    return main, tags, groups

ARTISTS = []
for a in STAFF:
    main, tags, groups = artist_profile(a)
    ARTISTS.append(dict(name=a["first"], main=main, tags=tags, groups=groups, apprentice=a["first"].startswith("Mackenna")))
ARTISTS.sort(key=lambda a: (GROUPS.index(a["main"]), a["name"]))
n_artists = len(ARTISTS)
n_services = sum(len(v) for v in SERVICES.values())

PRODUCTS = [
 ("perk-up-dry-shampoo/456", "amika", "Perk Up Dry Shampoo", "from $21", "p456.jpg"),
 ("the-kure-bond-repair-mask/463", "amika", "The Kure Bond Repair Mask", "from $33", "p463.jpg"),
 ("awaken-shampoo/143", "Surface", "Awaken Therapeutic Shampoo", "from $40.94", "p143.jpg"),
 ("bassu-oil/98", "Surface", "Bassu Oil", "from $38.41", "p98.jpg"),
 ("pink-coconut-whipped-body-butter-91-organic-/494", "Om Skincare", "Pink Coconut Whipped Body Butter", "$34", "p494.jpg"),
 ("coconut-dew-hyaluronic-moisture-cream-91-organic-/490", "Om Skincare", "Coconut Dew Moisture Cream", "from $24", "p490.jpg"),
 ("glass-action-universal-elixir/455", "amika", "Glass Action Universal Elixir", "$42", "p455.jpg"),
 ("pure-glow-mini-face-set/499", "Om Skincare", "Pure Glow Mini Face Set", "$68", "p499.jpg"),
]
def products(items):
    return '<div class="products">' + "".join(
        f'<a class="product" href="{SHOP}/product/{h}" target="_blank" rel="noopener"><span class="product__img"><img src="assets/img/{img}" alt="{e(v+" "+t)}" loading="lazy" width="400" height="400"></span>'
        f'<span class="product__brand">{e(v)}</span><span class="product__name">{e(t)}</span><span class="product__price">{e(pr)}</span></a>'
        for h, v, t, pr, img in items) + "</div>"

TICKER = ["Balayage", "Mega volume lashes", "Brazilian sugaring", "SunnaTan airbrush", "Boujee gel sets",
          "BioRePeel", "Brow lamination", "Weft extensions", "Teeth whitening", "Lymphatic drainage",
          "Hot stone", "Updos", "Gua sha", "Soul healing"]
def ticker():
    items = "".join(f"<span>{e(t)}</span><b aria-hidden='true'>✦</b>" for t in TICKER)
    return f'<div class="ticker" aria-label="Some of what we do"><div class="ticker__track">{items}{items}</div></div>'

# ---------- shared layout ----------
def head(title, desc):
    return f"""<!doctype html>
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="icon" href="assets/img/logo.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Instrument+Serif:ital@0;1&display=swap">
<link rel="stylesheet" href="assets/theme.css">
</head>
<body>"""

def header(current):
    left = "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == current else ""}>{n}</a>' for f, n in PAGES[1:3])
    right = "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == current else ""}>{n}</a>' for f, n in PAGES[3:])
    allnav = "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == current else ""}>{n}</a>' for f, n in PAGES)
    return f"""
<div class="notice">Concept preview by Tyler Wedderburn · not the official Soul on Tenth website</div>
<header class="nav">
  <nav class="nav__side" aria-label="Main, left">{left}</nav>
  <a class="nav__logo" href="index.html" aria-label="Soul on Tenth home"><img src="assets/img/logo.jpg" alt="" width="52" height="52"></a>
  <nav class="nav__side nav__side--right" aria-label="Main, right">{right}</nav>
  <details class="nav__menu"><summary>Menu</summary><nav aria-label="Mobile">{allnav}</nav></details>
</header>
<main>"""

BADGE = f"""<a class="badge" href="{BOOK}" target="_blank" rel="noopener" aria-label="Book an appointment">
  <svg viewBox="0 0 120 120" aria-hidden="true"><defs><path id="ring" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0"/></defs>
  <text><textPath href="#ring">BOOK NOW ✦ BOOK NOW ✦ BOOK NOW ✦ </textPath></text></svg>
  <span>↗</span></a>"""

def footer():
    return f"""</main>
<footer class="foot">
  <div class="foot__big" aria-hidden="true">SOUL<i>on tenth</i></div>
  <div class="foot__grid wrap">
    <div><h4>Find us</h4><p>118 10th Street<br>Brandon, MB R7A 4E6</p><p><a href="tel:+12047286131">204-728-6131</a></p></div>
    <div><h4>Explore</h4><p>{"<br>".join(f'<a href="{f}">{n}</a>' for f, n in PAGES)}</p></div>
    <div><h4>Elsewhere</h4><p>{ext(IG,"Instagram","")}<br>{ext(GIFT,"Gift cards","")}<br>{ext(BOOK,"Book online","")}</p></div>
  </div>
  <p class="foot__legal wrap">Concept preview prepared for Soul on Tenth by Tyler Wedderburn, November 2026. Services, prices and artists as listed on Soul's Square booking page on November 17, 2026.</p>
</footer>
{BADGE}
</body></html>
"""

def page(fn, title, desc, body, script=""):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write(head(title, desc) + header(fn) + body + (f"<script>{script}</script>" if script else "") + footer())

# ---------- Home ----------
group_counts = {g: sum(1 for a in ARTISTS if g in a["groups"]) for g in GROUPS}
LANES = [
 ("Hair", "Cuts, colour, blonding, extensions, updos", "haircuts"),
 ("Nails", "Gel sets, fills, manis, spa pedis", "nails"),
 ("Lashes & Brows", "Classic to mega volume, lifts, lamination, henna", "lashes"),
 ("Skin & Hair Removal", "Facials, peels, waxing, sugaring", "facials-skin"),
 ("Tan & Teeth", "SunnaTan airbrush, SunnaSmile whitening", "tan-teeth-whitening"),
 ("Body & Wellness", "Contouring, lymphatic massage, healing", "body-contouring-massage"),
]
lanes = "".join(
    f'<a class="lane" href="artists.html?for={slug(g)}"><span class="lane__n">0{i+1}</span><span class="lane__t">{e(g)}</span>'
    f'<span class="lane__d">{e(d)}</span><span class="lane__c">{group_counts[g]} artist{"s" if group_counts[g]!=1 else ""} →</span></a>'
    for i, (g, d, _) in enumerate(LANES))
faces = "".join(f'<a class="face" href="artists.html#{slug(a["name"])}" title="{e(a["name"])}"><span>{e(a["name"][0])}</span><em>{e(a["name"])}</em></a>' for a in ARTISTS)

page("index.html", "Soul on Tenth | Salon & Spa Collective in Downtown Brandon, MB",
 "Hair, nails, lashes, brows, facials, waxing, sugaring, tanning and more from 26 independent artists at 118 10th Street, Brandon.",
 f"""
<section class="hero">
  <img class="hero__img" src="assets/img/studio.jpg" alt="The Soul on Tenth team standing together outside the salon at 118 10th Street" width="1600" height="1067">
  <div class="hero__copy wrap">
    <p class="kicker">118 10th St · Downtown Brandon</p>
    <p class="hero__line">{n_artists} independent artists.<br><i>One very good address.</i></p>
    <div class="cta">{ext(BOOK,"Book an appointment","btn btn--blush")}<a class="btn btn--ghost" href="artists.html">Find your artist</a></div>
  </div>
  <h1 class="hero__word" aria-label="Soul on Tenth">SOUL</h1>
</section>
{ticker()}

<section class="block wrap">
  <div class="split-head"><h2>What are you<br><i>here for?</i></h2><p class="lede">Pick a lane and we'll show you who does it best. Every artist at Soul runs their own chair, so you're booking a specialist, not whoever's free.</p></div>
  <div class="lanes">{lanes}</div>
</section>

<section class="block block--ink">
  <div class="wrap">
    <div class="split-head"><h2>The <i>roster.</i></h2><p class="lede">Tap anyone to see what they do. On the live site, every circle is a real headshot.</p></div>
    <div class="faces">{faces}</div>
  </div>
</section>

<section class="manifesto wrap">
  <p>Every chair here is <i>its own studio.</i> Twenty-six businesses, one front door, and a back bar stocked with the stuff they actually use.</p>
</section>

<section class="block block--blush">
  <div class="wrap">
    <div class="split-head"><h2>The <i>back bar.</i></h2><p class="lede">amika, Surface and Om Skincare. Shipping or local delivery, or grab it at your next visit.</p></div>
    {products(PRODUCTS[:4])}
    <div class="cta"><a class="btn" href="shop.html">Shop the boutique</a></div>
  </div>
</section>

<section class="block wrap reviews">
  <h2>Said <i>about us.</i></h2>
  <div class="slot">Your best Google reviews go here, in the reviewers' own words, with your star rating up top. You can update them yourself anytime.</div>
</section>
""")

# ---------- Services ----------
cats_html, side = "", ""
for cat, items in SERVICES.items():
    name = CATS[cat][0]; a = slug(name)
    body, count = rows(items)
    side += f'<a href="#{a}">{e(name)}<span>{count}</span></a>'
    cats_html += f'<section class="menu__cat" id="{a}"><h2>{e(name)}</h2>{body}</section>'
page("services.html", "The Menu | Soul on Tenth, Brandon",
 "The full Soul on Tenth menu: haircuts, colour, extensions, nails, pedicures, lashes, brows, facials, waxing, sugaring, tanning, teeth whitening and body treatments.",
 f"""
<section class="pagehead pagehead--ink">
  <div class="wrap">
    <p class="kicker">{n_services} services · {len(SERVICES)} categories</p>
    <h1>The <i>menu.</i></h1>
    <label class="search"><span class="sr">Search services</span><input id="q" type="search" placeholder="Search: balayage, brazilian, lash fill…" autocomplete="off"><output id="count">{n_services} services</output></label>
  </div>
</section>
<div class="menu wrap">
  <nav class="menu__side" aria-label="Categories">{side}</nav>
  <div class="menu__list">
    {cats_html}
    <p class="empty" id="empty" hidden>Nothing matches that. Try a shorter word, or <a href="tel:+12047286131">call the salon</a>.</p>
    <p class="fine">Prices in CAD. Each artist runs their own chair, so some hair prices are set by your stylist. Tap any service to book it directly. Please give 24 hours' notice to cancel; late cancellations may be charged the full service.</p>
  </div>
</div>""",
 """
const q=document.getElementById('q'),rows=[...document.querySelectorAll('.row')],cats=[...document.querySelectorAll('.menu__cat')],out=document.getElementById('count'),empty=document.getElementById('empty');
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();let n=0;
 rows.forEach(r=>{const hit=!v||r.dataset.q.includes(v);r.hidden=!hit;if(hit)n++;});
 cats.forEach(c=>{const hit=!v||c.querySelector('h2').textContent.toLowerCase().includes(v);if(hit&&v){c.querySelectorAll('.row').forEach(r=>{if(r.hidden){r.hidden=false;n++;}})}c.hidden=!c.querySelector('.row:not([hidden])');});
 out.textContent=n+(n===1?' service':' services');empty.hidden=n>0;});
""")

# ---------- Artists ----------
chips = '<button type="button" class="chip" aria-pressed="true" data-g="all">Everyone</button>' + "".join(
    f'<button type="button" class="chip" aria-pressed="false" data-g="{slug(g)}">{e(g)}</button>' for g in GROUPS)
cards = "".join(
    f'<article class="artist" id="{slug(a["name"])}" data-g="{" ".join(slug(g) for g in a["groups"])}">'
    f'<span class="artist__no">{i+1:02d}</span><span class="artist__initial" aria-hidden="true">{e(a["name"][0])}</span>'
    f'<h3>{e(a["name"])}</h3>{"<span class=artist__app>Apprentice</span>" if a["apprentice"] else ""}'
    f'<p class="artist__tags">{"".join(f"<span>{e(t)}</span>" for t in a["tags"])}</p>{ext(BOOK, f"Book {e(a["name"])} ↗", "artist__book")}</article>'
    for i, a in enumerate(ARTISTS))
page("artists.html", "The Artists | Soul on Tenth, Brandon",
 f"Meet the {n_artists} independent hair, nail, lash, skin and body artists at Soul on Tenth in Brandon, and book the right person.",
 f"""
<section class="pagehead">
  <div class="wrap">
    <p class="kicker">The collective</p>
    <h1>{n_artists} <i>artists.</i></h1>
    <p class="lede">Filter by what you're after. Specialties come from the services each artist offers; on the live site each card gets a headshot, a short bio and their Instagram.</p>
    <div class="chips-bar" role="group" aria-label="Filter artists">{chips}</div>
  </div>
</section>
<section class="wrap"><div class="artists">{cards}</div></section>""",
 """
const chips=[...document.querySelectorAll('.chip')],cards=[...document.querySelectorAll('.artist')];
function show(g){chips.forEach(c=>c.setAttribute('aria-pressed',String(c.dataset.g===g)));cards.forEach(a=>a.hidden=!(g==='all'||a.dataset.g.split(' ').includes(g)));}
chips.forEach(c=>c.addEventListener('click',()=>{show(c.dataset.g);history.replaceState(null,'',c.dataset.g==='all'?'artists.html':'?for='+c.dataset.g);}));
const p=new URLSearchParams(location.search).get('for');if(p&&chips.some(c=>c.dataset.g===p))show(p);
""")

# ---------- Shop ----------
brands = {}
for p in PRODUCTS: brands.setdefault(p[1], []).append(p)
BRAND_COPY = {"amika": "Perk Up, The Kure, Normcore. Everyday hair that behaves.",
              "Surface": "Awaken, Curls, Bassu. Vegan, sulphate-free salon care.",
              "Om Skincare": "Organic cleansers, oils and body care. Pink Coconut is the cult favourite."}
shelves = "".join(f'<section class="shelf"><div class="shelf__head"><h2>{e(b)}</h2><p>{e(BRAND_COPY[b])}</p></div>{products(items)}</section>' for b, items in brands.items())
page("shop.html", "The Boutique | Soul on Tenth, Brandon",
 "Shop amika, Surface and Om Skincare from Soul on Tenth in Brandon, with shipping or local delivery.",
 f"""
<section class="pagehead pagehead--blush">
  <div class="wrap">
    <p class="kicker">The boutique · 56 products</p>
    <h1>The <i>back bar.</i></h1>
    <p class="lede">What our artists actually reach for, sorted by brand. Shipping or local delivery in Brandon, or pick it up at your next visit.</p>
    <div class="cta">{ext(SHOP+"/s/shop","Shop all 56 products","btn")}{ext(GIFT,"Buy a gift card","btn btn--ghost-ink")}</div>
  </div>
</section>
<div class="wrap">{shelves}</div>""")

# ---------- Visit ----------
page("visit.html", "Visit | Soul on Tenth, 118 10th St, Brandon",
 "Find Soul on Tenth at 118 10th Street in downtown Brandon. Hours, contact details and booking policies.",
 f"""
<section class="visit">
  <div class="wrap">
    <p class="kicker">Visit</p>
    <h1 class="visit__addr">118<br>10th St.</h1>
    <p class="lede">Downtown Brandon, MB R7A 4E6. Look for the black door and the round sign.</p>
    <div class="cta">{ext(MAP,"Get directions","btn btn--blush")}<a class="btn btn--ghost" href="tel:+12047286131">Call 204-728-6131</a></div>
  </div>
</section>
<section class="block wrap">
  <div class="facts">
    <div><h3>Hours</h3><p>By appointment. Every artist keeps their own schedule, so the booking calendar always shows real availability, evenings and Saturdays included.</p>{ext(BOOK,"See availability ↗","link")}</div>
    <div><h3>Free consults</h3><p>Not sure what you need? Book a free consult for colour, skin, makeup, extensions or body contouring first.</p></div>
    <div><h3>Cancellations</h3><p>Please give 24 hours' notice to cancel or move. Late cancellations may be charged the full price of the service.</p></div>
    <div><h3>Say hi</h3><p><a href="mailto:soulontenth@gmail.com">soulontenth@gmail.com</a><br>{ext(IG,"@soulontenth on Instagram","")}</p></div>
  </div>
</section>""")
print("built", len(PAGES), "pages,", n_services, "services,", n_artists, "artists")
