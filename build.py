"""Builds the Soul on Tenth concept pages from data/services.json and data/staff.json
(both taken from Soul's public Square booking page on November 17, 2026).
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

PAGES = [("index.html", "Home"), ("services.html", "Services"), ("artists.html", "Artists"),
         ("shop.html", "Shop"), ("visit.html", "Visit")]

# Square category -> (display name, group used on the Artists page)
CATS = {
 "Haircuts": ("Haircuts", "Hair"), "Colouring/Blonding": ("Colour & Blonding", "Hair"),
 "Styling": ("Styling & Updos", "Hair"), "In-Salon Hair Treatments": ("Hair Treatments", "Hair"),
 "Hair Extentions": ("Hair Extensions", "Hair"), "Nails": ("Nails", "Nails"),
 "Pedicures": ("Pedicures", "Nails"), "Lashes": ("Lashes", "Lashes & Brows"),
 "Brows": ("Brows", "Lashes & Brows"), "Facials": ("Facials & Skin", "Skin & Hair Removal"),
 "Waxing": ("Waxing", "Skin & Hair Removal"), "Sugaring": ("Sugaring", "Skin & Hair Removal"),
 "Airbrush Tan & Teeth Whitening": ("Airbrush Tan & Teeth Whitening", "Tan & Teeth"),
 "Makeup": ("Makeup", "Makeup"), "Soul Healing": ("Soul Healing", "Body & Wellness"),
 "Other": ("Body Contouring & Massage", "Body & Wellness"),
}
GROUPS = ["Hair", "Nails", "Lashes & Brows", "Skin & Hair Removal", "Tan & Teeth", "Body & Wellness"]

# A few descriptions rewritten to read cleanly; everything else uses Soul's own first sentence.
DESC = {
 "Brazilian Sugaring (New)": "Full bikini-area hair removal. Let hair grow to about 1/4 inch first, and please don't shave.",
 "Brazilian Wax (New)": "Full bikini-area hair removal. Let hair grow to about 1/4 inch first, and please don't shave.",
 "Manzillian": "Full hair removal for the groin area. Hair should be about 1/4 inch long.",
 "Soul-Led Healing Session": "Energy work, sound healing and intuitive guidance for emotional and spiritual renewal.",
}

def ext(url, text, cls="button"):
    return f'<a class="{cls}" href="{url}" target="_blank" rel="noopener">{text}</a>'

def price(s):
    c, pd = s["cents"], (s["pdesc"] or "")
    if s["ptype"] == "fixed" and not pd:
        if not c: return "Free"
        return f"${c/100:.0f}" if c % 100 == 0 else f"${c/100:.2f}"
    m = re.search(r"\$(\d+) and up", pd)
    if m: return f"<i>from</i>${m.group(1)}"
    if "consultation" in pd: return "<i>priced at free consult</i>"
    return "<i>varies by artist</i>"

def short(s):
    if s["name"] in DESC: return DESC[s["name"]]
    d = s["desc"]
    first = re.split(r"(?<=[.!?])\s", d, 1)[0] if d else ""
    return first if len(first) <= 120 else first[:117].rsplit(" ", 1)[0] + "…"

def dur(m):
    h, mm = divmod(m, 60)
    return (f"{h} hr " if h else "") + (f"{mm} min" if mm else "") if m else ""

FILL = re.compile(r"^(.*?) Fill \((\d) weeks?\)$")
def rows(items):
    """Collapse '1/2/3/4 week fill' services into one row with a chip per week."""
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
            html_rows.append(f'<div class="service"><div><b>{e(name)}</b>{f"<small>{e(note)}</small>" if note else ""}<small class="dur">{dur(s["mins"])}</small></div><span class="price">{price(s)}</span>{ext(BOOK+"/"+s["id"],"Book","")}</div>')
        else:
            chips = "".join(f'<a href="{BOOK}/{s["id"]}" target="_blank" rel="noopener">{w} wk <b>{price(s)}</b></a>' for w, s in sorted(val, key=lambda x: x[0]))
            html_rows.append(f'<div class="service service--fill"><div><b>{e(name)}</b><small>Pick the fill that matches how long it has been since your last visit.</small></div><div class="chips">{chips}</div></div>')
    return "".join(html_rows), len(out)

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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Hanken+Grotesk:wght@400;500;600&display=swap">
<link rel="stylesheet" href="assets/theme.css">
</head>
<body>"""

def nav(current):
    return "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == current else ""}>{n}</a>' for f, n in PAGES[1:])

def header(current):
    links = nav(current)
    return f"""
<div class="announcement">Concept preview by Tyler Wedderburn, not the official Soul on Tenth website.</div>
<header class="header"><div class="page-width">
  <a class="header__logo" href="index.html"><img src="assets/img/logo.jpg" alt="Soul on Tenth" width="46" height="46"><span>Soul <i>on Tenth</i></span></a>
  <nav aria-label="Main">{links}</nav>
  <details class="menu-drawer"><summary aria-label="Menu">Menu</summary><nav aria-label="Mobile">{links}</nav></details>
  {ext(BOOK,"Book now","button button--primary")}
</div></header>
<main>"""

def footer():
    return f"""</main>
<footer class="footer"><div class="page-width">
  <div class="grid">
    <div><img src="assets/img/logo.jpg" alt="Soul on Tenth" width="56" height="56"><p>A collective of independent hair, nail, lash, skin and body artists in downtown Brandon.</p></div>
    <div><h4>Explore</h4><ul>{''.join(f'<li><a href="{f}">{n}</a></li>' for f, n in PAGES[1:])}<li>{ext(GIFT,"Gift cards","")}</li></ul></div>
    <div><h4>Visit</h4><ul><li>118 10th Street<br>Brandon, MB R7A 4E6</li><li><a href="tel:+12047286131">204-728-6131</a></li><li>{ext(IG,"Instagram @soulontenth","")}</li></ul></div>
  </div>
  <p class="legal">Concept preview prepared for Soul on Tenth by Tyler Wedderburn, November 2026. Services, prices and artists as listed on Soul's Square booking page on November 17, 2026.</p>
</div></footer>
<div class="sticky-cta">{ext(BOOK,"Book","button button--primary")}<a class="button" href="artists.html">Find an artist</a></div>
</body></html>
"""

def page(fn, title, desc, body):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        f.write(head(title, desc) + header(fn) + body + footer())

def cta():
    return f"""<section class="section scheme-ink center"><div class="page-width">
  <p class="caption">118 10th Street</p>
  <h2>Come as you are. <em>Leave lighter.</em></h2>
  <p class="rte subtle">Pick a service, choose your artist, and see live availability. Booking takes about a minute.</p>
  <div class="buttons">{ext(BOOK,"Book an appointment","button button--primary")}<a class="button" href="artists.html">Meet the artists</a></div>
</div></section>"""

# ---------- artists ----------
def artist_profile(a):
    totals = {}
    for c, n in a["cats"].items():
        g = CATS.get(c, ("", "Body & Wellness"))[1]
        totals[g] = totals.get(g, 0) + n
    main = max(totals, key=totals.get)
    cut = min(totals[main], max(2, 0.2 * totals[main]))  # ignore side services such as a stylist's brow wax
    tags = [g for g in GROUPS if totals.get(g, 0) >= cut]
    if main == "Hair":  # every stylist cuts and colours, so name what sets them apart
        tags = ["Cuts & colour"] + (["Extensions"] if a["cats"].get("Hair Extentions") else []) + [t for t in tags if t != "Hair"]
    if main == "Body & Wellness":
        tags = ["Body contouring" if a["cats"].get("Other") else "Soul Healing sessions"]
    return main, tags

ARTISTS = []
for a in STAFF:
    main, tags = artist_profile(a)
    ARTISTS.append(dict(name=a["first"], main=main, tags=tags, apprentice=a["first"].startswith("Mackenna")))

def artist_cards(group):
    people = sorted((a for a in ARTISTS if a["main"] == group), key=lambda a: a["name"])
    return "".join(
        f'<div class="artist"><div class="initial" aria-hidden="true">{e(a["name"][0])}</div><div><h3>{e(a["name"])}{" <small>Apprentice</small>" if a["apprentice"] else ""}</h3>'
        f'<p class="tags">{" · ".join(e(t) for t in a["tags"])}</p>{ext(BOOK, f"Book with {e(a["name"])} →", "link")}</div></div>'
        for a in people)

# ---------- products ----------
PRODUCTS = [
 ("perk-up-dry-shampoo/456", "amika", "Perk Up Dry Shampoo", "from $21", "p456.jpg"),
 ("the-kure-bond-repair-mask/463", "amika", "The Kure Bond Repair Mask", "from $33", "p463.jpg"),
 ("awaken-shampoo/143", "Surface", "Awaken Therapeutic Shampoo", "from $40.94", "p143.jpg"),
 ("bassu-oil/98", "Surface", "Bassu Oil", "from $38.41", "p98.jpg"),
 ("pink-coconut-whipped-body-butter-91-organic-/494", "Om Skincare", "Pink Coconut Whipped Body Butter", "$34", "p494.jpg"),
 ("coconut-dew-hyaluronic-moisture-cream-91-organic-/490", "Om Skincare", "Coconut Dew Hyaluronic Moisture Cream", "from $24", "p490.jpg"),
 ("glass-action-universal-elixir/455", "amika", "Glass Action Universal Elixir", "$42", "p455.jpg"),
 ("pure-glow-mini-face-set/499", "Om Skincare", "Pure Glow Mini Face Set", "$68", "p499.jpg"),
]
def product_grid(items):
    return '<div class="product-grid">' + "".join(
        f'<a class="card" href="{SHOP}/product/{h}" target="_blank" rel="noopener"><div class="card__media"><img src="assets/img/{img}" alt="{e(v+" "+t)}" loading="lazy" width="400" height="400"></div><span class="card__vendor">{e(v)}</span><span class="card__title">{e(t)}</span><span class="card__price">{e(pr)}</span></a>'
        for h, v, t, pr, img in items) + "</div>"

n_services = sum(len(v) for v in SERVICES.values())
n_artists = len(ARTISTS)

def reviews_placeholder():
    return f"""<section class="section"><div class="page-width">
  <p class="caption">Kind words</p><h2>What clients <em>say.</em></h2>
  <div class="placeholder placeholder--wide"><div><b>Your Google reviews, here.</b><br>On the live site this section shows Soul's star rating and a few favourite reviews, and you can update them anytime.</div></div>
</div></section>"""

# ---------- Home ----------
CARDS = [
 ("Hair", "Cuts, colour, blonding, extensions and updos from {n} stylists.", "Haircuts"),
 ("Nails", "Gel sets, fills, manicures and spa pedicures.", "Nails"),
 ("Lashes & Brows", "Classic to mega volume lashes, lifts, lamination and henna.", "Lashes"),
 ("Skin", "Custom facials, BioRePeel, dermaplaning and peels.", "Facials"),
 ("Hair Removal", "Waxing and all-natural sugaring, head to toe.", "Waxing"),
 ("Tan & Teeth", "SunnaTan airbrush tans and SunnaSmile whitening.", "Airbrush Tan & Teeth Whitening"),
]
hair_n = sum(1 for a in ARTISTS if a["main"] == "Hair")
cat_cards = "".join(
    f'<a class="column column--link" href="services.html#{re.sub(r"[^a-z]+","-",CATS[c][0].lower()).strip("-")}"><p class="caption">{e(t)}</p><p>{e(d.format(n=hair_n))}</p><span class="link">See services →</span></a>'
    for t, d, c in CARDS)

page("index.html", "Soul on Tenth | Salon & Spa Collective in Downtown Brandon, MB",
 "Hair, nails, lashes, brows, facials, waxing, sugaring, tanning and more from 26 independent artists at 118 10th Street, Brandon.",
 f"""
<section class="hero">
  <img src="assets/img/studio.jpg" alt="The Soul on Tenth team standing together outside the salon at 118 10th Street" width="1600" height="1067">
  <div class="hero__text page-width">
    <p class="caption">Salon &amp; spa collective · Downtown Brandon</p>
    <h1>{n_artists} artists. <em>One home on Tenth.</em></h1>
    <p class="rte">Hair, nails, lashes, skin and body care from independent artists who each run their own chair. Find your person, see their real availability, and book in a minute.</p>
    <div class="buttons">{ext(BOOK,"Book an appointment","button button--primary")}<a class="button button--light" href="artists.html">Find your artist</a></div>
  </div>
</section>

<section class="section"><div class="page-width">
  <div class="title-row"><div><p class="caption">The menu</p><h2>Everything, <em>under one roof.</em></h2></div><a class="button" href="services.html">Full menu &amp; prices</a></div>
  <div class="multicolumn">{cat_cards}</div>
</div></section>

<section class="section scheme-2"><div class="page-width image-with-text">
  <div class="image-with-text__media image-with-text__media--crop"><img src="assets/img/surface.jpg" alt="Surface hair care bottles" width="1206" height="1471" loading="lazy"></div>
  <div>
    <p class="caption">How Soul works</p><h2>Every chair is <em>its own studio.</em></h2>
    <p class="rte subtle">Each artist at Soul runs their own business, sets their own prices and keeps their own calendar. That means you get someone who has built a following doing exactly what you came for.</p>
    <p class="rte subtle">Not sure who to book? Browse the artists by specialty, or book a free colour, skin or makeup consultation first.</p>
    <div class="buttons"><a class="button button--primary" href="artists.html">Meet the artists</a>{ext(BOOK,"Book a free consult")}</div>
  </div>
</div></section>

<section class="section"><div class="page-width">
  <div class="title-row"><div><p class="caption">The boutique</p><h2>Take the salon <em>home.</em></h2></div><a class="button" href="shop.html">Shop all</a></div>
  {product_grid(PRODUCTS[:4])}
</div></section>
{reviews_placeholder()}
{cta()}""")

# ---------- Services ----------
blocks, toc = "", ""
for i, (cat, items) in enumerate(SERVICES.items()):
    name = CATS[cat][0]; anchor = re.sub(r"[^a-z]+", "-", name.lower()).strip("-")
    body, count = rows(items)
    toc += f'<a href="#{anchor}">{e(name)}</a>'
    blocks += f'<details id="{anchor}"{" open" if i == 0 else ""}><summary>{e(name)}<small>{count} services</small></summary><div class="service-list">{body}</div></details>'
page("services.html", "Services & Prices | Soul on Tenth, Brandon",
 "The full Soul on Tenth menu: haircuts, colour, extensions, nails, pedicures, lashes, brows, facials, waxing, sugaring, tanning, teeth whitening and body treatments.",
 f"""
<section class="section"><div class="page-width">
  <p class="caption">The menu</p><h1>Services <em>&amp; prices.</em></h1>
  <p class="rte subtle">{n_services} services across {len(SERVICES)} categories. Prices are in Canadian dollars. Because every artist runs their own chair, some hair prices vary by stylist, so just ask your stylist for theirs. Tap Book on any service to go straight to that service in the booking calendar.</p>
  <nav class="toc" aria-label="Service categories">{toc}</nav>
  <div class="collapsible">{blocks}</div>
  <p class="note">Please give 24 hours' notice to cancel or move an appointment. Appointments cancelled with less notice may be charged the full service price.</p>
</div></section>
<script>
function openFromHash(){{var d=location.hash&&document.querySelector(location.hash);if(d&&d.tagName==="DETAILS"){{d.open=true;d.scrollIntoView();}}}}
addEventListener("hashchange",openFromHash);openFromHash();
</script>
{cta()}""")

# ---------- Artists ----------
groups_html = ""
for g in GROUPS:
    cards = artist_cards(g)
    if not cards: continue
    anchor = re.sub(r"[^a-z]+", "-", g.lower()).strip("-")
    groups_html += f'<section class="artist-group" id="{anchor}"><h2>{e(g)}</h2><div class="artist-grid">{cards}</div></section>'
chips = "".join(f'<a href="#{re.sub(r"[^a-z]+","-",g.lower()).strip("-")}">{e(g)}</a>' for g in GROUPS if any(a["main"] == g for a in ARTISTS))
page("artists.html", "Meet the Artists | Soul on Tenth, Brandon",
 f"Meet the {n_artists} independent hair, nail, lash, skin and body artists at Soul on Tenth in Brandon, and book with the right person.",
 f"""
<section class="section"><div class="page-width">
  <p class="caption">The collective</p><h1>Find <em>your</em> artist.</h1>
  <p class="rte subtle">{n_artists} independent artists, grouped by what they do most. Tags show everything else each artist offers.</p>
  <nav class="toc" aria-label="Specialties">{chips}</nav>
  {groups_html}
  <p class="note">Preview note: artist names and specialties come from Soul's Square booking page. On the live site each card would show the artist's photo, a short bio and a link to their Instagram.</p>
</div></section>
{cta()}""")

# ---------- Shop ----------
page("shop.html", "Shop Hair & Skin Care | Soul on Tenth, Brandon",
 "Shop amika, Surface and Om Skincare from Soul on Tenth in Brandon, with shipping or local delivery.",
 f"""
<section class="section"><div class="page-width">
  <p class="caption">The boutique</p><h1>What our artists <em>actually use.</em></h1>
  <p class="rte subtle">Professional hair care from amika and Surface, and organic skin and body care from Om. Order online for shipping or local delivery in Brandon, or pick something up at your next visit.</p>
  {product_grid(PRODUCTS)}
  <div class="buttons">{ext(SHOP+"/s/shop","Shop all 56 products","button button--primary")}{ext(GIFT,"Buy a gift card")}</div>
</div></section>
<section class="section scheme-2"><div class="page-width">
  <div class="multicolumn">
    <div class="column column--plain"><h3>amika</h3><p class="subtle">Perk Up dry shampoo, The Kure bond repair and Normcore, for everyday hair that behaves.</p></div>
    <div class="column column--plain"><h3>Surface</h3><p class="subtle">Awaken, Curls and Bassu. Vegan, sulphate-free and paraben-free salon care.</p></div>
    <div class="column column--plain"><h3>Om Skincare</h3><p class="subtle">Organic cleansers, oils, masks and body care, with Pink Coconut as a fan favourite.</p></div>
  </div>
</div></section>""")

# ---------- Visit ----------
page("visit.html", "Visit Us | Soul on Tenth, 118 10th St, Brandon",
 "Find Soul on Tenth at 118 10th Street in downtown Brandon. Hours, contact details and booking policies.",
 f"""
<section class="section"><div class="page-width">
  <p class="caption">Visit</p><h1>Find us on <em>10th Street.</em></h1>
  <div class="contact">
    <div><h3>The salon</h3><p>118 10th Street<br>Brandon, MB R7A 4E6</p><p><a href="tel:+12047286131">204-728-6131</a><br><a href="mailto:soulontenth@gmail.com">soulontenth@gmail.com</a></p>{ext(MAP,"Get directions")}</div>
    <div><h3>Hours</h3><p>By appointment.</p><p class="subtle">Each artist sets their own schedule, so the booking calendar always shows real, up-to-date availability, including evenings and Saturdays.</p>{ext(BOOK,"See availability","button button--primary")}</div>
    <div><h3>Good to know</h3><ul class="list"><li>Free consultations for colour, skin, makeup, extensions and body contouring</li><li>Gift cards available online</li><li>Book several services, or several artists, in one visit</li></ul></div>
  </div>
</div></section>
<section class="section scheme-2"><div class="page-width rte">
  <p class="caption">Policies</p><h2>Booking <em>&amp; cancellations.</em></h2>
  <p class="subtle">Please give at least 24 hours' notice if you need to cancel or move your appointment. Appointments cancelled with less than 24 hours' notice may be charged the full price of the service.</p>
  <p class="subtle">Questions? Call 204-728-6131 or message us on {ext(IG,"Instagram","")}.</p>
</div></section>
{cta()}""")
print("built", len(PAGES), "pages,", n_services, "services,", n_artists, "artists")
