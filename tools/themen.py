"""Sechs Themenserien mit je zehn Entwuerfen: Vater, Mutter, Oma, Opa, Versicherung, Finanzen.

Jeder Eintrag: (slug, Titel, Geometrie-Funktion, max. Zeilenbreite, Mockup-Spezifikation)
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

import geschenke as G
from designs import DECO, MAT, SCRIPT
from geschenke import SANS, SPORT, T, icons, scene, texts
from lasergeo import Part, circle, polys
from motive import engraved, ell, icon, rr


# ====================================================================== VATER
def vater():
    def schild():
        return [G.plaque("Papas Werkstatt", 300, 150, "rect",
                         txt=[("Papas", SCRIPT, 150, 46, 30, 110), ("WERKSTATT", DECO, 150, 86, 30, 150),
                              ("Hier wird repariert, was andere wegwerfen", SANS, 150, 120, 6.5, 200)],
                         ico=[("werkzeug", 40, 76, 44), ("werkzeug", 260, 76, 44)])]

    def uhr():
        return [G.clock("Papa-Zeit", numbers="arabic", font=DECO, rim_icons={5: "bier", 7: "grill"},
                        txt=[("Papa", SCRIPT, 0, 40, 34, 100), ("ZEIT FÜR FEIERABEND", SANS, 0, 64, 7, 100)],
                        ico=[("bart", 0, -42, 40)])]

    def untersetzer():
        return [G.coaster("Grillmeister", "DER CHEF AM ROST", "grill"),
                G.coaster("Prost Papa", "AUF DEN BESTEN", "bier"),
                G.coaster("Petri Heil", "PAPAS ANGELZEIT", "fisch"),
                G.coaster("Macher", "KANN ALLES REPARIEREN", "werkzeug")]

    def anhaenger():
        return [G.tag_icon("Anhaenger Werkzeug", "werkzeug", 40), G.tag_rect("Anhaenger Bart", "bart", "Bester Papa", "DER WELT"),
                G.tag_heart("Anhaenger Herz Papa", "Papa"), G.tag_icon("Anhaenger Pokal", "pokal", 40),
                G.tag_round("Anhaenger Krawatte", "krawatte", "No. 1"), G.tag_rect("Anhaenger Taxi", "auto", "Papas Taxi", "IMMER IM EINSATZ")]

    def medaille():
        return [G.medal("Medaille Bester Papa", "OFFIZIELL", "krone", "Bester Papa")]

    def rahmen():
        return G.photo_frame("Bilderrahmen Papa", "Papa & ich", "MEIN HELD SEIT DEM ERSTEN TAG")

    def pokal():
        return G.trophy3d("Pokal Papa", "Bester", "PAPA DER WELT")

    def halter():
        eng = unary_union([engraved("bart", 0, 26, 30), T("Papas", SCRIPT, 0, 48, 16, 56),
                           T("SOFA-KOMMANDO", SANS, 0, 64, 6, 60)])
        return G.stand("Handyhalter Papa", eng_a=eng)

    def kiste():
        W, D, H = 150.0, 90.0, 64.0
        front = unary_union([T("Papas Kram", DECO, W / 2, 24, 15, 100), engraved("hammer", 20, 26, 22),
                             engraved("schluessel_werkzeug", W - 20, 26, 22),
                             T("SCHRAUBEN · DÜBEL · KRIMSKRAMS", SANS, W / 2, 43, 4.6, 110)])
        side = engraved("werkzeug", D / 2, 28, 30)
        return G.box_set("Kiste Papa", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                  "right": (None, side, [])})

    def flaschen():
        return [G.bottle_tag("Flasche Prost", "Prost Papa", "AUF DICH!", "bier"),
                G.bottle_tag("Flasche Feierabend", "Feierabend", "HAST DU DIR VERDIENT", "sonne"),
                G.bottle_tag("Flasche Danke", "Danke Papa", "FÜR ALLES", "herz")]

    return "vater", "Vatertag & Papa", [
        ("01_wandschild-werkstatt", "Wandschild Papas Werkstatt", schild, 320, ("wall", dict(bg="dark", sub="300 × 150 mm · Hammer & Schraubenschlüssel"))),
        ("02_wanduhr-papa-zeit", "Wanduhr Papa-Zeit", uhr, 280, ("clock", dict(bg="dark", sub="Ø 260 mm · Bier um fünf, Grill um sieben"))),
        ("03_untersetzer-papa", "Untersetzer-Set Papa", untersetzer, 210, ("table", dict(bg="wood_dark", sub="4 Stück · Ø 95 mm · Grill, Bier, Angeln, Werkzeug", glasses=True))),
        ("04_schluesselanhaenger-papa", "Schlüsselanhänger Papa", anhaenger, 200, ("table", dict(bg="wood_dark", sub="6 Motive · Werkzeug, Bart, Herz, Pokal, Krawatte, Papas Taxi", ring=True))),
        ("05_medaille-bester-papa", "Medaille Bester Papa", medaille, 200, ("hanging", dict(bg="dark_bokeh", sub="Ø 72 mm · Schlitz für ein Ordensband", ribbon=True))),
        ("06_bilderrahmen-papa", "Bilderrahmen Papa & ich", rahmen, 360, ("frame", dict(bg="dark_table", sub="für Fotos 10 × 15 cm · mit Aufsteller"))),
        ("07_pokal-bester-papa", "3D-Pokal Bester Papa", pokal, 260, ("trophy", dict(bg="dark_table", sub="2 Steckteile · 150 mm hoch · ohne Kleber"))),
        ("08_handyhalter-papa", "Handyhalter Sofa-Kommando", halter, 230, ("stand", dict(bg="dark_table", sub="2 Steckteile · 68° Neigung"))),
        ("09_kiste-papas-kram", "Kiste Papas Kram", kiste, 420, ("box", dict(bg="dark_table", sub="150 × 90 × 64 mm · Fingerzinken"))),
        ("10_flaschenanhaenger-papa", "Flaschenanhänger Papa", flaschen, 200, ("bottles", dict(bg="dark_table", sub="3 Motive · Ring Ø 30 mm für Bierflaschen"))),
    ]


# ====================================================================== MUTTER
def mutter():
    def herzschild():
        W, H = 260.0, 240.0
        return [G.plaque("Herzschild Mama", W, H, "heart", holes=[(70, 40), (190, 40)],
                         txt=[("Mama", SCRIPT, W / 2, 104, 48, 150), ("DU BIST UNSER ZUHAUSE", SANS, W / 2, 146, 7, 120)],
                         ico=[("blume", 80, 70, 22), ("blume", 180, 70, 22), ("herz", W / 2, 176, 18)])]

    def puzzle():
        return G.heart_puzzle("Herz-Puzzle", ["Mama", "Papa", "Lena", "Tom", "Mia", "Ben", "Oma", "Opa", "Max"],
                              "Wir gehören zusammen")

    def untersetzer():
        return [G.coaster("Mama-Zeit", "KAFFEE IN RUHE", "kaffee", font=SCRIPT),
                G.coaster("Lieblingsmensch", "FÜR IMMER", "herz", font=SCRIPT),
                G.coaster("Danke", "FÜR ALLES, WAS DU TUST", "blume", font=SCRIPT),
                G.coaster("Sonnenschein", "DU MACHST JEDEN TAG HELL", "sonne", font=SCRIPT)]

    def anhaenger():
        return [G.tag_heart("Anhaenger Herz Mama", "Mama"), G.tag_icon("Anhaenger Schmetterling", "schmetterling", 40),
                G.tag_icon("Anhaenger Blume", "blume", 38), G.tag_round("Anhaenger Kleeblatt", "kleeblatt", "Glück"),
                G.tag_rect("Anhaenger Beste Mama", "herz", "Beste Mama", "DER WELT", font=SCRIPT),
                G.tag_heart("Anhaenger Herz Liebe", "Liebe", ic="sonne")]

    def rahmen():
        return G.photo_frame("Bilderrahmen Mama", "Mama & ich", "DIE SCHÖNSTEN MOMENTE")

    def laterne():
        f = scene([("blume_stiel", 14, 22), ("blume_stiel", 76, 26), ("blume_stiel", 30, 16), ("blume_stiel", 62, 18)],
                  balloons=[("herz", 45, 38, 22), ("herz", 28, 50, 12), ("herz", 62, 48, 13)])
        b = scene([("haus", 45, 40), ("baum", 15, 30), ("baum", 76, 26)])
        s = scene([("blume_stiel", 20, 20), ("blume_stiel", 70, 22)], balloons=[("schmetterling", 45, 44, 22)])
        return G.lantern("Laterne Mama", f, b, s, "Danke Mama", "Zuhause", "Liebe", "Für Mama")

    def schmuck():
        W, D, H = 130.0, 90.0, 48.0
        front = unary_union([T("Mamas Schätze", SCRIPT, W / 2, 22, 16, 96), engraved("blume", 14, 22, 14),
                             engraved("blume", W - 14, 22, 14)])
        lid = unary_union([T("Für Mama", SCRIPT, (W + 2) / 2, (D + 2) / 2 + 22, 14, 80),
                           engraved("herz", (W + 2) / 2 - 30, 20, 12), engraved("herz", (W + 2) / 2 + 30, 20, 12)])
        side = engraved("schmetterling", D / 2, 22, 22)
        return G.box_set("Schmuckkiste Mama", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                        "right": (None, side, [])}, lid="knob", lid_eng=lid)

    def lesezeichen():
        sc1 = G.bm_scene([("blume_stiel", 13, 34), ("blume_stiel", 28, 26)])
        sc2 = G.bm_scene([], balloons=[("herz", 14, 30, 14), ("herz", 27, 44, 11), ("herz", 20, 58, 9)])
        sc3 = G.bm_scene([("blume_stiel", 30, 20)], balloons=[("schmetterling", 16, 34, 18)])
        return [G.bookmark("LZ Mama", sc1, "Mama"), G.bookmark("LZ Herzen", sc2, "Lieblingsmensch"),
                G.bookmark("LZ Danke", sc3, "Danke")]

    def kueche():
        eng = unary_union([engraved("schneebesen", -40, 40, 34), engraved("herz", 40, 40, 26),
                           T("Mamas Küche", SCRIPT, 0, 84, 24, 130), T("MIT LIEBE GEKOCHT", SANS, 0, 106, 7, 100)])
        return G.stand("Rezeptstaender Mama", A_W=160.0, A_LEN=190.0, NOTCH=62.0, eng_a=eng, scale=1.55)

    def karte():
        return G.wood_card("Holzkarte Mama", "Danke Mama", "ALLES LIEBE ZUM MUTTERTAG",
                           ico=[("blume", 18, 18, 16), ("blume", 130, 18, 16), ("herz", 74, 72, 10)])

    return "mutter", "Muttertag & Mama", [
        ("01_herzschild-mama", "Herzschild Mama", herzschild, 280, ("wall", dict(bg="rose", sub="260 × 240 mm · Herzform mit Blumen"))),
        ("02_herz-puzzle-familie", "Familien-Herz-Puzzle", puzzle, 260, ("puzzle", dict(bg="wood_light", sub="9 Teile · 220 mm · mit Namen der Familie"))),
        ("03_untersetzer-mama", "Untersetzer-Set Mama", untersetzer, 210, ("table", dict(bg="wood_light", sub="4 Stück · Ø 95 mm · Kaffee, Herz, Blume, Sonne", glasses=True))),
        ("04_schluesselanhaenger-mama", "Schlüsselanhänger Mama", anhaenger, 200, ("table", dict(bg="wood_light", sub="6 Motive · Herz, Schmetterling, Blume, Kleeblatt", ring=True))),
        ("05_bilderrahmen-mama", "Bilderrahmen Mama & ich", rahmen, 360, ("frame", dict(bg="rose_table", sub="für Fotos 10 × 15 cm · mit Aufsteller"))),
        ("06_laterne-danke-mama", "Laterne Danke Mama", laterne, 300, ("lantern", dict(sub="90 × 90 × 110 mm · Blumen & Herz-Luftballons · nur LED-Teelichter"))),
        ("07_schmuckkiste-mama", "Schmuckkiste Mamas Schätze", schmuck, 420, ("box", dict(bg="rose_table", sub="130 × 90 × 48 mm · Deckel mit Griffloch", lid=True))),
        ("08_lesezeichen-mama", "Lesezeichen Mama", lesezeichen, 160, ("book", dict(bg="wood_light", sub="3 Stück · 40 × 160 mm · Blumen, Herzen, Schmetterling"))),
        ("09_rezeptstaender-mama", "Rezeptständer Mamas Küche", kueche, 330, ("stand", dict(bg="rose_table", sub="für Kochbuch oder Tablet · 2 Steckteile"))),
        ("10_holzkarte-danke-mama", "Holzkarte Danke Mama", karte, 200, ("wall", dict(bg="rose", sub="148 × 105 mm (A6) · Schrift ausgeschnitten"))),
    ]


# ====================================================================== OMA
NAMEN = ["Lena", "Tom", "Mia", "Ben", "Max", "Emma", "Paul", "Lea", "Noah", "Anna", "Finn", "Ida"]


def oma():
    def schild():
        return [G.plaque("Omas Kueche", 300, 160, "arch",
                         txt=[("Omas Küche", SCRIPT, 150, 92, 40, 220),
                              ("HIER WIRD MIT LIEBE GEKOCHT & GEBACKEN", SANS, 150, 128, 6.4, 220)],
                         ico=[("nudelholz", 100, 40, 34), ("kuchen", 150, 40, 30), ("schneebesen", 200, 40, 30)],
                         holes=[(30, 120), (270, 120)])]

    def rezepte():
        eng = unary_union([engraved("kuchen", 0, 40, 40), T("Omas Rezepte", SCRIPT, 0, 86, 24, 130),
                           T("GEHEIM & KÖSTLICH", SANS, 0, 108, 7, 100)])
        return G.stand("Rezeptstaender Oma", A_W=160.0, A_LEN=190.0, NOTCH=62.0, eng_a=eng, scale=1.55)

    def untersetzer():
        return [G.coaster("Kaffeeklatsch", "JEDEN TAG UM DREI", "kaffee"),
                G.coaster("Omas Kuchen", "DER BESTE DER WELT", "kuchen"),
                G.coaster("Handarbeit", "MIT LIEBE GESTRICKT", "wolle"),
                G.coaster("Gartenglück", "OMAS GRÜNER DAUMEN", "giesskanne")]

    def stecker():
        return [G.garden_stake("Gartenstecker Omas Garten", "Omas Garten", "giesskanne"),
                G.garden_stake("Gartenstecker Kraeuter", "Kräuter", "blatt", shape="rect"),
                G.garden_stake("Gartenstecker Blumen", "Blütenzauber", "blume_stiel")]

    def rahmen():
        return G.photo_frame("Bilderrahmen Oma", "Oma & ich", "BEI DIR IST ES AM SCHÖNSTEN")

    def stammbaum():
        return G.family_tree("Stammbaum Oma", "Omas Enkel", NAMEN)

    def anhaenger():
        return [G.tag_heart("Anhaenger Herz Oma", "Oma"), G.tag_icon("Anhaenger Kaffee", "kaffee", 38),
                G.tag_icon("Anhaenger Wolle", "wolle", 40), G.tag_icon("Anhaenger Kuchen", "kuchen", 38),
                G.tag_rect("Anhaenger Beste Oma", "brille", "Beste Oma", "DER WELT", font=SCRIPT),
                G.tag_round("Anhaenger Blume Oma", "blume", "Oma")]

    def laterne():
        f = scene([("haus", 45, 42), ("baum", 13, 28), ("baum", 78, 24)])
        b = scene([("giesskanne", 26, 20), ("blume_stiel", 54, 24), ("blume_stiel", 70, 18)])
        s = scene([("baum", 22, 26), ("baum", 68, 30)], balloons=[("herz", 45, 40, 16)])
        return G.lantern("Laterne Oma", f, b, s, "Beste Oma", "Omas Garten", "Liebe", "Für Oma")

    def naehkasten():
        W, D, H = 160.0, 100.0, 70.0
        front = unary_union([T("Omas Nähkästchen", SCRIPT, W / 2, 26, 18, 120), engraved("wolle", 16, 26, 18),
                             engraved("wolle", W - 16, 26, 18)])
        lid = unary_union([engraved("wolle", (W + 2) / 2 - 40, (D + 2) / 2, 30), engraved("herz", (W + 2) / 2 + 40, (D + 2) / 2, 22)])
        side = engraved("blume", D / 2, 30, 26)
        return G.box_set("Naehkaestchen", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                    "right": (None, side, [])}, lid="knob", lid_eng=lid,
                         dividers=["Knöpfe"])

    def uhr():
        return [G.clock("Kaffeezeit Oma", numbers="arabic", font=SCRIPT, rim_icons={3: "kaffee"},
                        txt=[("Bei Oma", SCRIPT, 0, 40, 30, 100), ("IST IMMER KAFFEEZEIT", SANS, 0, 62, 7, 100)],
                        ico=[("kuchen", 0, -44, 36)])]

    return "oma", "Für Oma", [
        ("01_wandschild-omas-kueche", "Wandschild Omas Küche", schild, 320, ("wall", dict(bg="cream", sub="300 × 160 mm · Nudelholz, Kuchen, Schneebesen"))),
        ("02_rezeptstaender-oma", "Rezeptständer Omas Rezepte", rezepte, 330, ("stand", dict(bg="cream_table", sub="für Kochbuch oder Tablet · 2 Steckteile"))),
        ("03_untersetzer-oma", "Untersetzer-Set Oma", untersetzer, 210, ("table", dict(bg="wood_light", sub="4 Stück · Ø 95 mm · Kaffee, Kuchen, Wolle, Garten", glasses=True))),
        ("04_gartenstecker-oma", "Gartenstecker Omas Garten", stecker, 220, ("garden", dict(sub="3 Stück · 90 × 175 mm · für Beet und Blumentopf"))),
        ("05_bilderrahmen-oma", "Bilderrahmen Oma & ich", rahmen, 360, ("frame", dict(bg="cream_table", sub="für Fotos 10 × 15 cm · mit Aufsteller"))),
        ("06_stammbaum-omas-enkel", "Stammbaum Omas Enkel", stammbaum, 320, ("wall", dict(bg="cream", sub="300 × 260 mm · 12 Herzen für die Namen der Enkel"))),
        ("07_schluesselanhaenger-oma", "Schlüsselanhänger Oma", anhaenger, 200, ("table", dict(bg="wood_light", sub="6 Motive · Herz, Kaffee, Wolle, Kuchen, Brille, Blume", ring=True))),
        ("08_laterne-beste-oma", "Laterne Beste Oma", laterne, 300, ("lantern", dict(sub="90 × 90 × 110 mm · Häuschen mit Garten · nur LED-Teelichter"))),
        ("09_naehkaestchen-oma", "Omas Nähkästchen", naehkasten, 420, ("box", dict(bg="cream_table", sub="160 × 100 × 70 mm · Deckel & Trennwand", lid=True))),
        ("10_wanduhr-kaffeezeit", "Wanduhr Kaffeezeit", uhr, 280, ("clock", dict(bg="cream", sub="Ø 260 mm · um drei Uhr ist Kaffeezeit"))),
    ]


# ====================================================================== OPA
def opa():
    def schild():
        return [G.plaque("Opa Legende", 300, 170, "rect",
                         txt=[("OPA", DECO, 150, 72, 60, 160), ("DER MANN · DER MYTHOS · DIE LEGENDE", SANS, 150, 128, 7, 230)],
                         ico=[("hut", 50, 72, 50), ("brille", 250, 72, 50)])]

    def uhr():
        return [G.clock("Opa-Zeit", numbers="roman", font=DECO, rim_icons=None,
                        txt=[("Opa-Zeit", SCRIPT, 0, 40, 30, 96), ("MITTAGSSCHLAF NICHT STÖREN", SANS, 0, 64, 6.4, 110)],
                        ico=[("brille", 0, -44, 40)])]

    def untersetzer():
        return [G.coaster("Petri Heil", "OPAS ANGELGLÜCK", "fisch"),
                G.coaster("Schachmatt", "OPA GEWINNT IMMER", "springer"),
                G.coaster("Prost Opa", "AUF VIELE JAHRE", "bier"),
                G.coaster("Werkstatt", "OPA REPARIERT'S", "werkzeug")]

    def spiel():
        return G.muehle("Muehle Opa", "Opas Mühle")

    def rahmen():
        return G.photo_frame("Bilderrahmen Opa", "Opa & ich", "MEIN HELD MIT HERZ")

    def brille():
        return G.glasses_stand("Brillenstaender Opa", "Opas Brille")

    def anhaenger():
        return [G.tag_heart("Anhaenger Herz Opa", "Opa"), G.tag_icon("Anhaenger Hut", "hut", 42),
                G.tag_icon("Anhaenger Fisch", "fisch", 42), G.tag_icon("Anhaenger Springer", "springer", 40),
                G.tag_rect("Anhaenger Bester Opa", "brille", "Bester Opa", "DER WELT"),
                G.tag_round("Anhaenger Anker", "anker", "Kapitän")]

    def medaille():
        return [G.medal("Medaille Bester Opa", "OFFIZIELL", "krone", "Bester Opa")]

    def kiste():
        W, D, H = 170.0, 70.0, 60.0
        front = unary_union([T("Opas Kommandozentrale", DECO, W / 2, 24, 13, 130),
                             T("FERNBEDIENUNG · BRILLE · ZEITUNG", SANS, W / 2, 41, 4.6, 120)])
        side = engraved("brille", D / 2, 26, 30)
        return G.box_set("Fernbedienungsbox Opa", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                            "right": (None, side, [])}, dividers=["Brille"])

    def lesezeichen():
        sc1 = G.bm_scene([("baum", 12, 30), ("baum", 28, 24)])
        sc2 = G.bm_scene([("haus", 20, 28)], balloons=[("sonne", 20, 28, 14)])
        sc3 = G.bm_scene([("springer", 20, 32)])
        return [G.bookmark("LZ Opa", sc1, "Opa"), G.bookmark("LZ Lesezeit", sc2, "Lesezeit"),
                G.bookmark("LZ Schach", sc3, "Schachmatt")]

    return "opa", "Für Opa", [
        ("01_wandschild-opa-legende", "Wandschild Opa Legende", schild, 320, ("wall", dict(bg="green", sub="300 × 170 mm · Der Mann, der Mythos, die Legende"))),
        ("02_wanduhr-opa-zeit", "Wanduhr Opa-Zeit", uhr, 280, ("clock", dict(bg="green", sub="Ø 260 mm · römische Ziffern"))),
        ("03_untersetzer-opa", "Untersetzer-Set Opa", untersetzer, 210, ("table", dict(bg="wood_dark", sub="4 Stück · Ø 95 mm · Angeln, Schach, Bier, Werkstatt", glasses=True))),
        ("04_muehle-spiel-opa", "Mühle-Spiel Opa", spiel, 400, ("game", dict(bg="wood_dark", sub="Spielbrett 240 × 240 mm · 18 Spielsteine Ø 22 mm"))),
        ("05_bilderrahmen-opa", "Bilderrahmen Opa & ich", rahmen, 360, ("frame", dict(bg="green_table", sub="für Fotos 10 × 15 cm · mit Aufsteller"))),
        ("06_brillenstaender-opa", "Brillenständer Opa", brille, 200, ("glasses", dict(bg="green_table", sub="2 Steckteile · Profil mit Nase"))),
        ("07_schluesselanhaenger-opa", "Schlüsselanhänger Opa", anhaenger, 200, ("table", dict(bg="wood_dark", sub="6 Motive · Herz, Hut, Fisch, Springer, Brille, Anker", ring=True))),
        ("08_medaille-bester-opa", "Medaille Bester Opa", medaille, 200, ("hanging", dict(bg="green_bokeh", sub="Ø 72 mm · Schlitz für ein Ordensband", ribbon=True))),
        ("09_fernbedienungsbox-opa", "Fernbedienungsbox Opa", kiste, 420, ("box", dict(bg="green_table", sub="170 × 70 × 60 mm · mit Trennwand"))),
        ("10_lesezeichen-opa", "Lesezeichen Opa", lesezeichen, 160, ("book", dict(bg="wood_dark", sub="3 Stück · 40 × 160 mm · Bäume, Häuschen, Springer"))),
    ]


# ====================================================================== VERSICHERUNG
def versicherung():
    def tischschild():
        eng = unary_union([engraved("schild", -72, -36, 40), T("IHR ANSPRECHPARTNER", SANS, 14, -56, 6, 140),
                           T("Max Mustermann", DECO, 14, -38, 16, 150), T("VERSICHERUNGEN & VORSORGE", SANS, 14, -20, 5.4, 140)])
        return G.desk_sign("Tischschild", 200, 70, eng)

    def karten():
        eng = unary_union([engraved("schirm", 0, -38, 30), T("PERSÖNLICH FÜR SIE DA", SANS, 0, -14, 5, 80)])
        return G.card_holder("Visitenkartenhalter", eng, T("Visitenkarten", SCRIPT, 0, -11, 9, 60))

    def stifte():
        S, H = 72.0, 100.0

        def face(ic, lab):
            return (None, unary_union([engraved(ic, S / 2, 38, 34), T(lab, SANS, S / 2, 66, 6, 56)]), [])
        return G.box_set("Stiftehalter", S, S, H, {"front": face("haus", "WOHNEN"), "back": face("auto", "MOBILITÄT"),
                                                   "left": face("schirm", "SCHUTZ"), "right": face("familie", "FAMILIE")})

    def untersetzer():
        return [G.coaster("Wohnen", "HAUS & HAUSRAT", "haus", font=SANS),
                G.coaster("Mobilität", "AUTO & UNTERWEGS", "auto", font=SANS),
                G.coaster("Familie", "VORSORGE FÜR DIE LIEBSTEN", "familie", font=SANS),
                G.coaster("Gesundheit", "KRANKEN & PFLEGE", "puls", font=SANS)]

    def anhaenger():
        return [G.tag_icon("Anhaenger Haus", "haus", 40), G.tag_icon("Anhaenger Schirm", "schirm", 42),
                G.tag_icon("Anhaenger Schild", "schild", 40),
                G.tag_rect("Anhaenger Auto", "auto", "Gute Fahrt", "KOMM GUT ANS ZIEL", font=SANS),
                G.tag_heart("Anhaenger Gesund", "Gesund bleiben", ic="puls", font=SCRIPT),
                G.tag_round("Anhaenger Zuhause", "schluessel", "Zuhause")]

    def schild():
        W, H = 300.0, 180.0
        return [G.plaque("Wandschild Gut abgesichert", W, H, "arch", holes=[(30, 140), (270, 140)],
                         txt=[("Gut abgesichert", SCRIPT, W / 2, 132, 30, 220),
                              ("FÜR ALLES, WAS IHNEN WICHTIG IST", SANS, W / 2, 160, 6.4, 200)],
                         ico=[("schirm", W / 2, 50, 64), ("haus", W / 2 - 52, 90, 34), ("familie", W / 2 + 52, 90, 34)])]

    def uhr():
        return [G.clock("Uhr Vorsorge", numbers="arabic", font=SANS, rim_icons={0: "haus", 3: "auto", 6: "familie", 9: "schirm"},
                        txt=[("Zeit für Vorsorge", SCRIPT, 0, 40, 26, 100)], ico=[("schild", 0, -44, 36)])]

    def notfall():
        W, H = 200.0, 280.0
        rows = [("Polizei", "110"), ("Feuerwehr & Rettungsdienst", "112"), ("Ärztlicher Bereitschaftsdienst", "116 117"),
                ("Giftnotruf", None), ("Hausarzt", None), ("Versicherung / Schadenmeldung", None), ("Nachbarn", None)]
        txt = [("Wichtige Nummern", SCRIPT, W / 2, 34, 24, 124)]
        sc = []
        for i, (lab, num) in enumerate(rows):
            y = 70 + i * 28
            txt.append((lab.upper(), SANS, W / 2, y, 6.6, 176))
            if num:
                txt.append((num, SPORT, W / 2, y + 13, 14, 120))
            else:
                sc.append(LineString([(30, y + 15), (W - 30, y + 15)]))
        return [G.plaque("Notfall-Tafel", W, H, "rect", txt=txt, ico=[("puls", 20, 34, 18), ("schild", W - 20, 34, 18)],
                         extra_score=sc)]

    def kartei():
        W, D, H = 160.0, 120.0, 80.0
        front = unary_union([T("Wichtige Unterlagen", SCRIPT, W / 2, 30, 18, 130),
                             T("POLICEN · VERTRÄGE · BELEGE", SANS, W / 2, 50, 5, 110)])
        side = engraved("schild", D / 2, 34, 32)
        return G.box_set("Karteibox", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                "right": (None, side, [])},
                         dividers=["Policen", "Verträge", "Belege", "Notizen"])

    def laterne():
        f = scene([("haus", 45, 40), ("baum", 15, 26), ("baum", 76, 22)], balloons=[])
        b = scene([("blume_stiel", 20, 20), ("blume_stiel", 70, 22), ("baum", 45, 30)], balloons=[("herz", 24, 40, 14)])
        s = scene([("baum", 22, 26), ("blume_stiel", 60, 16)], balloons=[("herz", 45, 42, 16)])
        return G.lantern("Laterne Zuhause", f, b, s, "Sicher zuhause", "Familie", "Geborgen", "Zuhause")

    return "versicherung", "Versicherung & Vorsorge", [
        ("01_tischschild-ansprechpartner", "Tischschild Ansprechpartner", tischschild, 230, ("desk", dict(bg="office_table", sub="200 × 70 mm · Name frei änderbar · gesteckt"))),
        ("02_visitenkartenhalter", "Visitenkartenhalter", karten, 200, ("cards", dict(bg="office_table", sub="3 Steckteile · für Standard-Visitenkarten"))),
        ("03_stiftehalter-vorsorge", "Stiftehalter Vorsorge", stifte, 420, ("box", dict(bg="office_table", sub="72 × 72 × 100 mm · Wohnen, Mobilität, Schutz, Familie"))),
        ("04_untersetzer-vorsorge", "Untersetzer-Set Vorsorge", untersetzer, 210, ("table", dict(bg="office_desk", sub="4 Stück · Ø 95 mm · Wohnen, Mobilität, Familie, Gesundheit", glasses=True))),
        ("05_schluesselanhaenger-kunden", "Schlüsselanhänger Kundengeschenk", anhaenger, 200, ("table", dict(bg="office_desk", sub="6 Motive · Haus, Schirm, Schild, Auto, Herz, Schlüssel", ring=True))),
        ("06_wandschild-gut-abgesichert", "Wandschild Gut abgesichert", schild, 320, ("wall", dict(bg="office", sub="300 × 180 mm · Schirm über Haus und Familie"))),
        ("07_wanduhr-vorsorge", "Wanduhr Zeit für Vorsorge", uhr, 280, ("clock", dict(bg="office", sub="Ø 260 mm · Haus, Auto, Familie, Schirm"))),
        ("08_notfall-tafel", "Notfall-Tafel Wichtige Nummern", notfall, 220, ("wall", dict(bg="office", sub="200 × 280 mm · 110 · 112 · 116 117 · Felder zum Ausfüllen"))),
        ("09_karteibox-unterlagen", "Karteibox Wichtige Unterlagen", kartei, 420, ("box", dict(bg="office_table", sub="160 × 120 × 80 mm · für A6-Karten · 4 Trennwände"))),
        ("10_laterne-sicher-zuhause", "Laterne Sicher zuhause", laterne, 300, ("lantern", dict(sub="90 × 90 × 110 mm · Haus, Familie, Herz · nur LED-Teelichter"))),
    ]


# ====================================================================== FINANZEN
def finanzen():
    def spardose():
        W, D, H = 120.0, 90.0, 90.0
        front = unary_union([engraved("sparschwein", W / 2, 36, 40), T("Urlaubskasse", SCRIPT, W / 2, 70, 16, 100)])
        back = unary_union([T("MEIN SPARZIEL", SANS, W / 2, 30, 6, 80), T("€", SANS, W - 26, 50, 10)])
        side = engraved("muenzen", D / 2, 40, 34)
        lid = T("Sparen macht Spaß", SCRIPT, (W + 2) / 2, (D + 2) / 2 + 22, 12, 90)
        return G.box_set("Spardose", W, D, H, {"front": (None, front, []), "back": (None, back, [LineString([(24, 50), (W - 34, 50)])]),
                                               "left": (None, side, []), "right": (None, side, [])}, lid="slot", lid_eng=lid)

    def challenge():
        return G.challenge52("Spar-Challenge")

    def schwein():
        body = ell(0, -52, 52, 34)
        snout = rr(46, -66, 64, -42, 7)
        ear = Polygon([(18, -80), (30, -102), (40, -78)])
        tail = LineString([(-52, -60), (-60, -64), (-62, -72), (-56, -76), (-52, -70)]).buffer(2.2)
        legs = unary_union([rr(x - 6, -30, x + 6, 0, 3) for x in (-28, 26)])
        side = unary_union([body, snout, ear, tail, legs])
        side = side.difference(rr(-14, -86 + 4, 14, -80 + 4, 2))         # Muenzschlitz (Deko)
        eng = unary_union([circle(30, -62, 3.2), circle(58, -58, 1.8), circle(58, -50, 1.8),
                           T("Sparschwein", SCRIPT, -2, -46, 16, 70)])
        sc = [LineString([(40, -70), (44, -56), (40, -42)])]
        return G.steck_figure("Sparschwein", side, [-28, 26], 30, 60, eng, sc)

    def untersetzer():
        return [G.coaster("Sparen", "KLEINVIEH MACHT AUCH MIST", "sparschwein"),
                G.coaster("Planen", "ZIELE SETZEN", "chart"),
                G.coaster("Sichern", "GUT VERWAHRT", "tresor"),
                G.coaster("Glück", "AUF EIN GUTES JAHR", "kleeblatt")]

    def anhaenger():
        return [G.tag_icon("Anhaenger Sparschwein", "sparschwein", 42), G.tag_icon("Anhaenger Geldboerse", "geldboerse", 40),
                G.tag_icon("Anhaenger Tresor", "tresor", 38), G.tag_round("Anhaenger Gluecksklee", "kleeblatt", "Glückstaler"),
                G.tag_rect("Anhaenger Sparziel", "chart", "Mein Sparziel", "SCHRITT FÜR SCHRITT"),
                G.tag_round("Anhaenger Gluecks-Euro", "muenze", "Glücks-Euro")]

    def uhr():
        return [G.clock("Uhr Zeit ist Geld", numbers="arabic", font=SANS, rim_icons={0: "muenze"},
                        txt=[("Zeit ist Geld", SCRIPT, 0, 40, 28, 100)], ico=[("muenzen", 0, -44, 40)])]

    def budget():
        W, D, H = 190.0, 110.0, 80.0
        front = unary_union([T("Budget-Box", DECO, W / 2, 28, 18, 120), T("DIE UMSCHLAG-METHODE", SANS, W / 2, 48, 6, 120),
                             engraved("geldboerse", 22, 30, 22), engraved("brief", W - 22, 30, 22)])
        side = engraved("muenzen", D / 2, 34, 30)
        return G.box_set("Budget-Box", W, D, H, {"front": (None, front, []), "left": (None, side, []),
                                                 "right": (None, side, [])},
                         dividers=["Miete", "Lebensmittel", "Freizeit", "Sparen", "Rücklagen"])

    def geldbaum():
        return G.money_tree("Geldbaum", "Für deine Wünsche")

    def schild():
        return [G.plaque("Wandschild Kleinvieh", 300, 140, "banner",
                         txt=[("Kleinvieh", SCRIPT, 158, 52, 34, 130), ("MACHT AUCH MIST", DECO, 158, 92, 18, 124)],
                         ico=[("sparschwein", 58, 70, 60), ("muenzen", 254, 74, 32)], holes=[(40, 20), (260, 20)])]

    def lesezeichen():
        sc1 = G.bm_scene([("sparschwein", 20, 22)], balloons=[("muenze", 14, 32, 10), ("muenze", 27, 42, 9)])
        sc2 = G.bm_scene([("chart", 20, 26)])
        sc3 = G.bm_scene([], balloons=[("kleeblatt", 20, 40, 22)])
        return [G.bookmark("LZ Sparen", sc1, "Sparen"), G.bookmark("LZ Planen", sc2, "Planen"),
                G.bookmark("LZ Glueck", sc3, "Glück")]

    return "finanzen", "Finanzen & Sparen", [
        ("01_spardose-urlaubskasse", "Spardose Urlaubskasse", spardose, 420, ("box", dict(bg="money_table", sub="120 × 90 × 90 mm · Deckel mit Münzschlitz", lid=True, coins=True))),
        ("02_spar-challenge-52-wochen", "52-Wochen-Spar-Challenge", challenge, 320, ("wall", dict(bg="money_wall", sub="300 × 215 mm · 52 Felder zum Abhaken · 1.378 € nach einem Jahr"))),
        ("03_steckfigur-sparschwein", "Steckfigur Sparschwein", schwein, 260, ("steck", dict(bg="money_table", sub="3 Steckteile · 128 × 104 mm"))),
        ("04_untersetzer-finanzen", "Untersetzer-Set Finanzen", untersetzer, 210, ("table", dict(bg="wood_dark", sub="4 Stück · Ø 95 mm · Sparen, Planen, Sichern, Glück", glasses=True))),
        ("05_schluesselanhaenger-finanzen", "Schlüsselanhänger Finanzen", anhaenger, 200, ("table", dict(bg="wood_dark", sub="6 Motive · Sparschwein, Geldbörse, Tresor, Klee, Sparziel, Euro", ring=True))),
        ("06_wanduhr-zeit-ist-geld", "Wanduhr Zeit ist Geld", uhr, 280, ("clock", dict(bg="money_wall", sub="Ø 260 mm · Münzen statt der Zwölf"))),
        ("07_budget-box", "Budget-Box Umschlag-Methode", budget, 420, ("box", dict(bg="money_table", sub="190 × 110 × 80 mm · 5 beschriftete Trennwände"))),
        ("08_geldbaum", "Geldbaum Geldgeschenk", geldbaum, 260, ("tree", dict(bg="money_table", sub="Schlitze für gefaltete Geldscheine · Standfuß gesteckt"))),
        ("09_wandschild-kleinvieh", "Wandschild Kleinvieh macht auch Mist", schild, 320, ("wall", dict(bg="money_wall", sub="300 × 140 mm · Sparschwein & Münzen"))),
        ("10_lesezeichen-finanzen", "Lesezeichen Finanzen", lesezeichen, 160, ("book", dict(bg="wood_dark", sub="3 Stück · 40 × 160 mm · Sparschwein, Chart, Kleeblatt"))),
    ]


THEMEN = {"vater": vater, "mutter": mutter, "oma": oma, "opa": opa, "versicherung": versicherung, "finanzen": finanzen}
