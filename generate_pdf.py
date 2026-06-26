"""
Fountainhead wine list PDF generator.
All measurements from FountainHead - Tall.idml paragraph-level overrides.

Page: 453.54 × 1190.55pt (160 × 420mm)
Margins: 34pt all sides

Tab stops (from frame left, as paragraph overrides in story XML):
  - Vintage:  RightAlign @ 14.17pt
  - Producer: LeftAlign  @ 19.84pt
  - Price:    RightAlign @ 385.51pt  (= full frame width, dot leader '.')

Typography:
  - Body:     9pt Courier New, 10pt leading
  - Category: 11pt Mezalia Bold Cursive
  - Section:  12pt Mezalia Extra Bold, centred, SpaceAfter 5.67pt
  - Footer:   9pt Courier New, centred

SpaceAfter 2.83pt after every category heading paragraph and every grapes/price line.

Frame positions (PDF y from bottom):
  Page 1 – BTG frame:      top=1041.52  bottom=409.26
  Page 1 – BTB frame:      top=379.10   bottom=90.53
  Page 2 – BTB frame:      top=1156.53  bottom=34.00
"""
import os
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from io import BytesIO

HERE = os.path.dirname(os.path.abspath(__file__))


def _font_path(name):
    return os.path.join(HERE, name)


def register_fonts():
    pdfmetrics.registerFont(TTFont("CourierNew",        _font_path("Courier New.ttf")))
    pdfmetrics.registerFont(TTFont("CourierNew-Bold",   _font_path("Courier New Bold.ttf")))
    pdfmetrics.registerFont(TTFont("CourierNew-Italic", _font_path("Courier New Italic.ttf")))
    pdfmetrics.registerFont(TTFont("Mezalia-Cursive",   _font_path("MezaliaCursive.ttf")))
    pdfmetrics.registerFont(TTFont("Mezalia-ExtraBold", _font_path("MezaliaExtraBold.ttf")))


# ── page & frame geometry ──────────────────────────────────────────────────
PAGE_W  = 453.54
PAGE_H  = 1190.55
MARGIN  = 34.0

FRAME_L = MARGIN                  # 34pt from page left
FRAME_W = 385.51                  # text frame width
FRAME_R = FRAME_L + FRAME_W       # 419.51pt from page left

# tab positions (absolute from page left)
TAB_VINT = FRAME_L + 14.17        # 48.17pt  – vintage right-aligns here
TAB_PROD = FRAME_L + 19.84        # 53.84pt  – producer left-aligns here
TAB_PRICE = FRAME_L + 385.51      # 419.51pt – price right-aligns here (= FRAME_R)

# typography
SZ_BODY     = 9.0
SZ_CATEGORY = 11.0
SZ_SECTION  = 12.0
SZ_FOOTER   = 9.0
LEADING     = 10.0
SP_AFTER    = 2.83    # SpaceAfter on category headings and grapes lines
SP_AFTER_SECTION = 5.67  # SpaceAfter Head 1

# frame y positions (PDF y from bottom)
BTG_TOP      = PAGE_H - 149.03   # 1041.52
BTG_BOTTOM   = PAGE_H - 781.29   # 409.26
BTB_P1_TOP   = PAGE_H - 811.45   # 379.10
BTB_P1_BOTTOM = PAGE_H - 1100.02 # 90.53
BTB_P2_TOP   = PAGE_H - MARGIN   # 1156.55
BTB_P2_BOTTOM = MARGIN           # 34.00


# ── fixed BTG sections (Vermouth / Digestif / Non Alc) ────────────────────
FIXED_BTG_SECTIONS = [
    {
        "heading": "Vermouth",
        "items": [
            ("Chinati Vergano", "Vermouth Bianco & Soda", "$19"),
            ("Chinati Vergano", "Americano & Soda",       "$20"),
        ],
    },
    {
        "heading": "Digestif",
        "items": [
            ("Capellano",        "Barolo Chinato (60ml)",               "$23"),
            ("Bourgoin",         "Raisin Double Zero Eau de Vie (30ml)", "$22"),
            ("Chateau du Prada", "Bas Armagnac XO (30ml)",              "$24"),
        ],
    },
    {
        "heading": "Non Alc",
        "items": [
            ("Vichy Catalan",            "Spanish salty mineral water (1L)", "$12"),
            ("T.I.N.A Table Tea",        "Sparkling Jasmine Tea, Marigold",  "$16"),
            ("By No Means Pinot Grigio", "Peach, Curry Leaf, Thyme",         "$18"),
            ("By No Means Rosé",         "White Tea, Raspberry, Rose",        "$18"),
            ("By No Means Pinot Noir",   "Hibiscus, Cranberry, Vanilla",      "$18"),
        ],
    },
]


# ── drawing helpers ────────────────────────────────────────────────────────

def sw(c, text, font, size):
    return c.stringWidth(text, font, size)


def dot_fill(c, x0, x1, y):
    """Fill x0..x1 with dots in CourierNew body size."""
    dw = sw(c, ".", "CourierNew", SZ_BODY)
    pad = 1.5
    n = int((x1 - x0 - pad * 2) / dw)
    if n > 0:
        c.setFont("CourierNew", SZ_BODY)
        c.drawString(x0 + pad, y, "." * n)


def draw_logo(c):
    """Draw logo centred at top margin. Returns PDF y of logo bottom."""
    logo = _font_path("logo.png")
    from PIL import Image as PILImage
    img = PILImage.open(logo)
    w = 122.0
    h = w * img.size[1] / img.size[0]
    x = (PAGE_W - w) / 2
    y_top = PAGE_H - MARGIN           # top of logo
    c.drawImage(logo, x, y_top - h, width=w, height=h, preserveAspectRatio=True)
    return y_top - h                  # bottom of logo


def draw_section_title(c, text, y_baseline):
    """Draw centred section title at 90% horizontal scale. Returns y ready for first category."""
    c.setFont("Mezalia-ExtraBold", SZ_SECTION)
    text_w = sw(c, text, "Mezalia-ExtraBold", SZ_SECTION)
    HSCALE = 0.9
    c.saveState()
    c.transform(HSCALE, 0, 0, 1, 0, 0)
    x = (PAGE_W / HSCALE - text_w) / 2
    c.drawString(x, y_baseline, text)
    c.restoreState()
    return y_baseline - LEADING - SP_AFTER_SECTION


def draw_category(c, text, y):
    """
    Category heading from IDML: paragraph starts with a forced Br (blank line),
    then \t\t positions to TAB_PROD, then heading at 11pt Mezalia, SpaceAfter 2.83.
    y = first baseline of the paragraph (blank line).
    Returns y ready for first wine.
    """
    # blank first line (the Br at para start — 10pt leading, no visible text)
    y_head = y - LEADING
    c.setFont("Mezalia-Cursive", SZ_CATEGORY)
    c.drawString(TAB_PROD, y_head, text)
    return y_head - LEADING - SP_AFTER


def draw_wine_btg(c, wine, y):
    """
    Two-line BTG entry from IDML:
    Line 1 (no SpaceAfter): \t[vintage right@TAB_VINT]\t[producer+cuvee left@TAB_PROD]
    Line 2 (SpaceAfter 2.83): \t\t[grapes bold left@TAB_PROD] [loc]\t[price right@TAB_PRICE]
    """
    vintage  = wine.get("vintage", "")
    producer = wine.get("producer", "")
    cuvee    = wine.get("cuvee", "")
    grapes   = wine.get("grapes", "")
    region   = wine.get("region", "")
    country  = wine.get("country", "")
    btg_p    = wine.get("btg_price")
    btl_p    = wine.get("btl_price")

    # line 1
    vint_str = f"`{vintage}" if vintage and vintage.upper() != "NV" else (vintage or "")
    c.setFont("CourierNew", SZ_BODY)
    c.drawRightString(TAB_VINT, y, vint_str)
    c.drawString(TAB_PROD, y, producer + " ")
    prod_w = sw(c, producer + " ", "CourierNew", SZ_BODY)
    c.setFont("CourierNew-Italic", SZ_BODY)
    c.drawString(TAB_PROD + prod_w, y, cuvee)

    # line 2 — grapes at TAB_PROD (two tabs in IDML, same indent as producer)
    y2 = y - LEADING
    c.setFont("CourierNew-Bold", SZ_BODY)
    c.drawString(TAB_PROD, y2, grapes)
    g_w = sw(c, grapes, "CourierNew-Bold", SZ_BODY)

    loc = f" {region}, {country}" if region else f" {country}"
    c.setFont("CourierNew", SZ_BODY)
    c.drawString(TAB_PROD + g_w, y2, loc)
    text_end = TAB_PROD + g_w + sw(c, loc, "CourierNew", SZ_BODY)

    def fmt(p): return str(p) if str(p).startswith("$") else f"${int(p)}"
    price_str = f"{fmt(btg_p)}/{fmt(btl_p)}" if btg_p else fmt(btl_p)
    p_w = sw(c, price_str, "CourierNew", SZ_BODY)
    c.setFont("CourierNew", SZ_BODY)
    c.drawString(TAB_PRICE - p_w, y2, price_str)
    dot_fill(c, text_end, TAB_PRICE - p_w, y2)

    return y2 - LEADING - SP_AFTER


def draw_wine_btb(c, wine, y):
    """Two-line BTB entry — same tab structure as BTG."""
    vintage  = wine.get("vintage", "")
    producer = wine.get("producer", "")
    cuvee    = wine.get("cuvee", "")
    grapes   = wine.get("grapes", "")
    region   = wine.get("region", "")
    country  = wine.get("country", "")
    btl_p    = wine.get("btl_price")
    note     = wine.get("note", "")

    vint_str = f"`{vintage}" if vintage and vintage.upper() != "NV" else (vintage or "")
    c.setFont("CourierNew", SZ_BODY)
    c.drawRightString(TAB_VINT, y, vint_str)
    c.drawString(TAB_PROD, y, producer + " ")
    prod_w = sw(c, producer + " ", "CourierNew", SZ_BODY)
    c.setFont("CourierNew-Italic", SZ_BODY)
    c.drawString(TAB_PROD + prod_w, y, cuvee)

    # line 2 — grapes at TAB_PROD
    y2 = y - LEADING
    c.setFont("CourierNew-Bold", SZ_BODY)
    c.drawString(TAB_PROD, y2, grapes)
    g_w = sw(c, grapes, "CourierNew-Bold", SZ_BODY)

    loc_parts = [p for p in [region, country] if p]
    if note:
        loc_parts.append(f"({note})")
    loc = " " + ", ".join(loc_parts) if loc_parts else ""
    c.setFont("CourierNew", SZ_BODY)
    c.drawString(TAB_PROD + g_w, y2, loc)
    text_end = TAB_PROD + g_w + sw(c, loc, "CourierNew", SZ_BODY)

    price_str = str(btl_p) if str(btl_p).startswith("$") else f"${int(btl_p)}"
    p_w = sw(c, price_str, "CourierNew", SZ_BODY)
    c.drawString(TAB_PRICE - p_w, y2, price_str)
    dot_fill(c, text_end, TAB_PRICE - p_w, y2)

    return y2 - LEADING - SP_AFTER


def draw_fixed_item(c, bold_name, italic_desc, price_str, y):
    """Single-line fixed item — also indented to TAB_PROD."""
    c.setFont("CourierNew-Bold", SZ_BODY)
    c.drawString(TAB_PROD, y, bold_name + " ")
    b_w = sw(c, bold_name + " ", "CourierNew-Bold", SZ_BODY)
    c.setFont("CourierNew-Italic", SZ_BODY)
    c.drawString(TAB_PROD + b_w, y, italic_desc)
    i_w = sw(c, italic_desc, "CourierNew-Italic", SZ_BODY)
    text_end = TAB_PROD + b_w + i_w

    p_w = sw(c, price_str, "CourierNew", SZ_BODY)
    c.setFont("CourierNew", SZ_BODY)
    c.drawString(TAB_PRICE - p_w, y, price_str)
    dot_fill(c, text_end, TAB_PRICE - p_w, y)

    return y - LEADING - SP_AFTER


def draw_footer(c):
    for i, line in enumerate(["The basement, 54 Doggett St. Newstead",
                               "fountainheadwinehouse.com"]):
        y = MARGIN + 10.0 + (1 - i) * LEADING
        c.setFont("Mezalia-ExtraBold", 10.0)
        c.drawString((PAGE_W - sw(c, line, "Mezalia-ExtraBold", 10.0)) / 2, y, line)


# ── main generator ─────────────────────────────────────────────────────────

def generate(data: dict) -> bytes:
    """
    data: {
      "btg_sections":  [{"heading": str, "wines": [wine_dict, ...]}],
      "btb_sections":  [{"heading": str, "wines": [wine_dict, ...]}],
        wine_dict keys: vintage, producer, cuvee, grapes, region, country,
                        btg_price (BTG only), btl_price, note (BTB optional)
    }
    BTB sections 0-1 go on page 1 (Champagne + Sparkling & Pet Nat).
    BTB sections 2+ go on page 2.
    """
    register_fonts()
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(black)

    # ── PAGE 1 ────────────────────────────────────────────────────────────

    draw_logo(c)

    # BTG frame: starts at BTG_TOP, first baseline = BTG_TOP - LEADING
    y = BTG_TOP - LEADING
    y = draw_section_title(c, "WINES WE ARE POURING BY THE GLASS", y)

    for section in data.get("btg_sections", []):
        y = draw_category(c, section["heading"], y)
        for wine in section["wines"]:
            y = draw_wine_btg(c, wine, y)

    y -= (LEADING - SP_AFTER)  # extra <Br/> before Vermouth in IDML = 30pt gap
    for section in FIXED_BTG_SECTIONS:
        y = draw_category(c, section["heading"], y)
        for bold_name, italic_desc, price_str in section["items"]:
            y = draw_fixed_item(c, bold_name, italic_desc, price_str, y)

    # BTB frame on page 1: Champagne + Sparkling & Pet Nat (first 2 sections)
    btb_all = data.get("btb_sections", [])
    btb_p1  = btb_all[:2]
    btb_p2  = btb_all[2:]

    y = BTB_P1_TOP - LEADING
    y = draw_section_title(c, "WINES WE LOVE BY THE BOTTLE", y)

    for section in btb_p1:
        y = draw_category(c, section["heading"], y)
        for wine in section["wines"]:
            y = draw_wine_btb(c, wine, y)

    draw_footer(c)

    # ── PAGE 2 ────────────────────────────────────────────────────────────
    c.showPage()
    c.setFillColor(black)

    y = BTB_P2_TOP - LEADING

    for section in btb_p2:
        y = draw_category(c, section["heading"], y)
        for wine in section["wines"]:
            y = draw_wine_btb(c, wine, y)

    c.save()
    return buf.getvalue()


# ── smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = {
        "btg_sections": [
            {"heading": "Sparkling", "wines": [
                {"vintage": "23", "producer": "Silver Heights", "cuvee": "Bloom",
                 "grapes": "Chardonnay, Pinot Noir, Rice", "region": "Ningxia", "country": "CHN",
                 "btg_price": 32, "btl_price": 107},
                {"vintage": "NV", "producer": "Fangareggi", "cuvee": "Vigna Rosa",
                 "grapes": "Lambrusco di Sorbara, Fortana", "region": "Emilia Romagna", "country": "ITA",
                 "btg_price": 25, "btl_price": 81},
            ]},
            {"heading": "White", "wines": [
                {"vintage": "23", "producer": "Alla Costiera", "cuvee": "Bianco Costiera",
                 "grapes": "Friulano, Garganega, Moscato", "region": "Veneto", "country": "ITA",
                 "btg_price": 19, "btl_price": 69},
                {"vintage": "24", "producer": "Mattias Riccitelli", "cuvee": "The Apple Falls",
                 "grapes": "Torrontes", "region": "Uco Valley", "country": "ARG",
                 "btg_price": 21, "btl_price": 72},
                {"vintage": "22", "producer": "Ezio Cerruti", "cuvee": "Fol",
                 "grapes": "Moscato", "region": "Piedmont", "country": "ITA",
                 "btg_price": 22, "btl_price": 76},
                {"vintage": "24", "producer": "Marco Lubiana", "cuvee": "Chardonnay",
                 "grapes": "Chardonnay", "region": "Derwent Valley", "country": "TAS",
                 "btg_price": 32, "btl_price": 103},
            ]},
            {"heading": "Rosé", "wines": [
                {"vintage": "24", "producer": "La Grande Bauquiere", "cuvee": "La Belle Montagne",
                 "grapes": "Grenache, Cinsault, Syrah", "region": "Provence", "country": "FRA",
                 "btg_price": 18, "btl_price": 72},
            ]},
            {"heading": "Skin Contact", "wines": [
                {"vintage": "24", "producer": "Xiao Pu", "cuvee": "Tangerine",
                 "grapes": "Chardonnay, Viognier, Petit Manseng", "region": "Ningxia", "country": "CHN",
                 "btg_price": 23, "btl_price": 74},
            ]},
            {"heading": "Red", "wines": [
                {"vintage": "24", "producer": "Josep Grau", "cuvee": "Volador Tinto (Chilled)",
                 "grapes": "Garnacha, Cariñena", "region": "Montsant", "country": "ESP",
                 "btg_price": 21, "btl_price": 74},
                {"vintage": "21", "producer": "Tarrington Vineyards", "cuvee": "Estate Pinot Noir",
                 "grapes": "Pinot Noir", "region": "Henty", "country": "VIC",
                 "btg_price": 29, "btl_price": 103},
                {"vintage": "24", "producer": "Biscaris", "cuvee": "Costa Jatta",
                 "grapes": "Frappato", "region": "Sicily", "country": "ITA",
                 "btg_price": 24, "btl_price": 77},
                {"vintage": "20", "producer": "Charles Joguet", "cuvee": "Chinon",
                 "grapes": "Cabernet Franc", "region": "Loire Valley", "country": "FRA",
                 "btg_price": 30, "btl_price": 102},
            ]},
        ],
        "btb_sections": [
            {"heading": "Champagne", "wines": [
                {"vintage": "NV", "producer": "Lelarge-Peugot", "cuvee": "Tradition",
                 "grapes": "Chardonnay, Pinot Meunier +", "region": "Champagne", "country": "FRA", "btl_price": 176},
                {"vintage": "NV", "producer": "Emmanuel Brochet", "cuvee": "Extra Brut",
                 "grapes": "Pinot Meunier, Chardonnay", "region": "Champagne", "country": "FRA", "btl_price": 250},
                {"vintage": "NV", "producer": "Jérôme Blin", "cuvee": "Les Ports Zero Dosage",
                 "grapes": "Pinot Meunier, Pinot Blanc +", "region": "Champagne", "country": "FRA", "btl_price": 228},
                {"vintage": "20", "producer": "George Remy", "cuvee": "Grand Cru Blanc de Noirs",
                 "grapes": "Pinot Noir", "region": "Champagne", "country": "FRA", "btl_price": 233},
                {"vintage": "20", "producer": "Remi Leroy", "cuvee": "Les Crots Saignee",
                 "grapes": "Pinot Noir", "region": "Champagne", "country": "FRA", "btl_price": 233},
            ]},
            {"heading": "Sparkling & Pet Nat", "wines": [
                {"vintage": "22", "producer": "Bruno Dubois", "cuvee": "Bulle de BD",
                 "grapes": "Chenin Blanc", "region": "Loire Valley", "country": "FRA", "btl_price": 94},
                {"vintage": "22", "producer": "Strohmeier", "cuvee": "Blanc d'Orange",
                 "grapes": "Sauvignon Blanc, Pinot Blanc +", "region": "Weststeiermark", "country": "AUT", "btl_price": 120},
                {"vintage": "23", "producer": "Domaine Derain", "cuvee": "Chut... Derain",
                 "grapes": "Aligote", "region": "Burgundy", "country": "FRA", "btl_price": 140},
                {"vintage": "23", "producer": "Jean-Pierre Robinot", "cuvee": "Les Années Folles",
                 "grapes": "Pineau d'Aunis", "region": "Loire Valley", "country": "FRA", "btl_price": 125},
            ]},
            {"heading": "Crisp Fresh Whites", "wines": [
                {"vintage": "18", "producer": "Quinta do Ermizio", "cuvee": "Electrico",
                 "grapes": "Loueiro", "region": "Vinho Verde", "country": "PRT", "btl_price": 69},
                {"vintage": "22", "producer": "Les Cailloux du Paradis", "cuvee": "Quartz",
                 "grapes": "Sauvignon Blanc", "region": "Loire Valley", "country": "FRA", "btl_price": 130},
                {"vintage": "24", "producer": "Domaine Belargus", "cuvee": "Ronceray",
                 "grapes": "Chenin Blanc", "region": "Loire Valley", "country": "FRA", "btl_price": 194},
                {"vintage": "23", "producer": "Domaine de l'Ecu", "cuvee": "Muscadet Classic",
                 "grapes": "Melon de Bourgogne", "region": "Loire Valley", "country": "FRA", "btl_price": 79},
                {"vintage": "24", "producer": "Cosentino", "cuvee": "Vigna Don Paolo",
                 "grapes": "Carricante", "region": "Sicily", "country": "ITA", "btl_price": 149},
                {"vintage": "23", "producer": "Domaine des Ardoisieres", "cuvee": "Silice Blanc",
                 "grapes": "Jacquère", "region": "Savoie", "country": "FRA", "btl_price": 166, "note": "1500ml"},
            ]},
            {"heading": "Aromatic Whites", "wines": [
                {"vintage": "23", "producer": "Weiser Kunstler", "cuvee": "im Lowenbaum Feinherb",
                 "grapes": "Riesling", "region": "Mosel", "country": "DEU", "btl_price": 109},
                {"vintage": "23", "producer": "Domaine Guillaman", "cuvee": "Colombard",
                 "grapes": "Colombard, Sauvignon Blanc", "region": "Gascony", "country": "FRA", "btl_price": 68},
                {"vintage": "23", "producer": "Domaine Labije", "cuvee": "Mansengs",
                 "grapes": "Gros Manseng, Petit Manseng", "region": "Jurançon", "country": "FRA", "btl_price": 134},
                {"vintage": "20", "producer": "Ansitz Dolomytos Sacker", "cuvee": "Weisswein",
                 "grapes": "Pinot Gris, Sauvignon Blanc +", "region": "Alto Adige", "country": "ITA", "btl_price": 226},
            ]},
            {"heading": "Weighty & Textural Whites", "wines": [
                {"vintage": "21", "producer": "Terre de Elu", "cuvee": "Parfum d'Eden",
                 "grapes": "Chenin Blanc", "region": "Loire Valley", "country": "FRA", "btl_price": 181},
                {"vintage": "20", "producer": "Guillemot-Michel", "cuvee": "Retour a la Terre",
                 "grapes": "Chardonnay", "region": "Burgundy", "country": "FRA", "btl_price": 164},
                {"vintage": "24", "producer": "Stoney Rise", "cuvee": "Savagnin",
                 "grapes": "Savagnin", "region": "Tamar Valley", "country": "TAS", "btl_price": 80},
                {"vintage": "21", "producer": "Vignetti Massa", "cuvee": "Derthona Montecitorio",
                 "grapes": "Timorasso", "region": "Piedmont", "country": "ITA", "btl_price": 166},
                {"vintage": "21", "producer": "Valfaccenda", "cuvee": "Roero Arneis",
                 "grapes": "Arneis", "region": "Piedmont", "country": "ITA", "btl_price": 103},
            ]},
            {"heading": "Amber", "wines": [
                {"vintage": "20", "producer": "Farnea", "cuvee": "Birbo",
                 "grapes": "Friulano", "region": "Veneto", "country": "ITA", "btl_price": 85},
                {"vintage": "22", "producer": "Valdibella", "cuvee": "Ninfa",
                 "grapes": "Catarratto", "region": "Sicily", "country": "ITA", "btl_price": 72},
                {"vintage": "21", "producer": "Marko Fon", "cuvee": "Malvazija",
                 "grapes": "Malvasia", "region": "Kras", "country": "SVN", "btl_price": 117},
                {"vintage": "23", "producer": "Manon", "cuvee": "Juno",
                 "grapes": "Chardonnay, Sauvignon Blanc", "region": "Adelaide Hills", "country": "SA", "btl_price": 91},
                {"vintage": "23", "producer": "Serragghia", "cuvee": "Heritage Bianco Secco",
                 "grapes": "Zibibbo", "region": "Pantelleria", "country": "ITA", "btl_price": 361},
            ]},
            {"heading": "Rosé", "wines": [
                {"vintage": "24", "producer": "Castagna", "cuvee": "Allegro",
                 "grapes": "Shiraz", "region": "Beechworth", "country": "VIC", "btl_price": 71},
                {"vintage": "22", "producer": "Cascina Sot", "cuvee": "Rosato",
                 "grapes": "Nebbiolo, Barbera", "region": "Piemonte", "country": "ITA", "btl_price": 85},
                {"vintage": "24", "producer": "Passofonduto", "cuvee": "Occhio di Sale",
                 "grapes": "Nero d'Avola", "region": "Sicily", "country": "ITA", "btl_price": 100},
                {"vintage": "23", "producer": "Fiore San Biagio", "cuvee": "Briscola e Tressette",
                 "grapes": "Montepulciano", "region": "Abruzzo", "country": "ITA", "btl_price": 77},
            ]},
            {"heading": "Light & Chillable Reds", "wines": [
                {"vintage": "23", "producer": "Bendito Destino", "cuvee": "Clarete",
                 "grapes": "Tempranillo, Garnacha +", "region": "Ribera del Duero", "country": "ESP", "btl_price": 153},
                {"vintage": "23", "producer": "Michel Gahier", "cuvee": "Rouge du Max",
                 "grapes": "Trousseau", "region": "Jura", "country": "FRA", "btl_price": 127},
                {"vintage": "24", "producer": "Valli Unite Alessandrino", "cuvee": "",
                 "grapes": "Barbera, Dolcetto, Croatina", "region": "Piedmont", "country": "ITA", "btl_price": 80},
                {"vintage": "23", "producer": "Ranchelle", "cuvee": "Pergolacce",
                 "grapes": "Alicante, Ciliegiolo", "region": "Tuscany", "country": "ITA", "btl_price": 88},
            ]},
            {"heading": "Bright and Medium Bodied Reds", "wines": [
                {"vintage": "20", "producer": "Sylvain Martinez", "cuvee": "Corbeau",
                 "grapes": "Grolleau", "region": "Loire Valley", "country": "FRA", "btl_price": 102},
                {"vintage": "23", "producer": "Bonnet & Cotton", "cuvee": "100% Brouilly",
                 "grapes": "Gamay", "region": "Beaujolais", "country": "FRA", "btl_price": 115},
                {"vintage": "23", "producer": "Domaine Naudin-Ferrand", "cuvee": "Haute Cotes de Beaune",
                 "grapes": "Pinot Noir", "region": "Burgundy", "country": "FRA", "btl_price": 107},
                {"vintage": "24", "producer": "Domaine Thalie", "cuvee": "Balancin",
                 "grapes": "Pinot Noir", "region": "Burgundy", "country": "FRA", "btl_price": 112},
                {"vintage": "24", "producer": "Wilimee", "cuvee": "Granite",
                 "grapes": "Pinot Noir", "region": "Macedon Ranges", "country": "VIC", "btl_price": 117},
                {"vintage": "21", "producer": "Panduro Mianes", "cuvee": "Monastrell",
                 "grapes": "Monastrell", "region": "Mallorca", "country": "ESP", "btl_price": 96},
                {"vintage": "21", "producer": "Kamara Pure", "cuvee": "Shadow Play",
                 "grapes": "Xinomavro", "region": "Thessaloniki", "country": "GRE", "btl_price": 112},
                {"vintage": "23", "producer": "Domaine Mosse", "cuvee": "Cabernet Franc",
                 "grapes": "Cabernet Franc", "region": "Loire Valley", "country": "FRA", "btl_price": 110},
            ]},
            {"heading": "Powerful & Concentrated Reds", "wines": [
                {"vintage": "16", "producer": "Mount Mary", "cuvee": "Quintet",
                 "grapes": "Cabernet Sauvignon, Merlot +", "region": "Yarra Valley", "country": "VIC", "btl_price": 309},
                {"vintage": "24", "producer": "Hervé Souhaut", "cuvee": "Syrah",
                 "grapes": "Syrah", "region": "Rhone Valley", "country": "FRA", "btl_price": 122},
                {"vintage": "22", "producer": "Domaine Duseigneur", "cuvee": '"Caterina" Chateneuf du Pape',
                 "grapes": "Grenache, Syrah", "region": "Rhone Valley", "country": "FRA", "btl_price": 158},
                {"vintage": "21", "producer": "Giacomo Fenocchio", "cuvee": "Barolo",
                 "grapes": "Nebbiolo", "region": "Piemonte", "country": "ITA", "btl_price": 188},
            ]},
        ],
    }

    pdf_bytes = generate(sample)
    out = "/Users/feelypoo/Documents/Fountainhead/pdf-server/test_output.pdf"
    with open(out, "wb") as f:
        f.write(pdf_bytes)
    print(f"Written {len(pdf_bytes):,} bytes → {out}")
