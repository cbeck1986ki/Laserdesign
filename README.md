# Weihnachtsdeko für den xTool D1 Pro 10W

Fünf Entwürfe als laserfertige SVG-Dateien (Maßstab 1:1 in mm) mit Mockup und Laservorschau.

![Übersicht](entwuerfe/uebersicht_mockups.jpg)

| # | Entwurf | Teile | Fläche (mm) | Datei |
|---|---------|-------|-------------|-------|
| 1 | Schneeflocken-Anhänger (3 Varianten, eine mit „2026“) | 3 | 216 × 90 | `entwuerfe/01_schneeflocken/01_schneeflocken.svg` |
| 2 | 3D-Steck-Tannenbaum, 180 mm hoch, plus Passungstest | 3 | 256 × 215 | `entwuerfe/02_steck-tannenbaum/02_steck-tannenbaum.svg` |
| 3 | Weihnachtssterne: Gruß-Stern + Filigran-Stern, 100 mm | 2 | 193 × 94 | `entwuerfe/03_sterne/03_sterne.svg` |
| 4 | Teelicht-Laterne „Winterdorf“, 90 × 90 × 110 mm, Fingerzinken | 5 | 292 × 236 | `entwuerfe/04_teelicht-laterne/04_teelicht-laterne.svg` |
| 5 | Geschenkanhänger-Set (Kugel, Baum, klassisch) | 6 | 248 × 163 | `entwuerfe/05_geschenkanhaenger/05_geschenkanhaenger.svg` |

Alle Entwürfe passen auf die Arbeitsfläche des D1 Pro (432 × 406 mm). Ausgelegt sind sie für **3 mm Pappel- oder Lindensperrholz**.

## Farben = Bearbeitungsart (in xTool Creative Space)

| Farbe | Ebene | Bearbeitung in XCS |
|-------|-------|--------------------|
| 🔴 Rot `#FF0000` | Schneiden | **Schneiden** (Kontur) |
| 🔵 Blau `#0000FF` | Gravieren | **Gravieren** (Flächenfüllung) |
| ⚫ Schwarz `#000000` | Linie | **Gravieren**, Modus *Linie/Ritzen* (Score) |

Die Dateien enthalten keine Schrift-Objekte: Alle Texte sind bereits in Pfade umgewandelt.

## Startwerte für den D1 Pro 10W

| Vorgang | Leistung | Geschwindigkeit | Durchgänge | Hinweis |
|---------|----------|-----------------|------------|---------|
| Schneiden 3 mm Linde | 100 % | 8–12 mm/s | 1 | Air Assist an |
| Schneiden 3 mm Pappelsperrholz | 100 % | 6–10 mm/s | 1–2 | Leimschicht kann einen 2. Durchgang brauchen |
| Gravieren (Fläche) | 25–40 % | 150–250 mm/s | 1 | ca. 100 Linien/cm |
| Linie (Score) | 20–30 % | 50–80 mm/s | 1 | |

Holz fällt sehr unterschiedlich aus. Mach deshalb vorher ein **Materialtest-Raster** in XCS und stell den Fokus genau ein.

**Reihenfolge:** zuerst gravieren, dann Linien, **zuletzt schneiden**. In der SVG ist das so vorsortiert, und innere Ausschnitte werden vor der Außenkontur geschnitten. Ein Abdeckband (Malerkrepp) auf dem Holz verhindert Rauchspuren.

## Tipps zu den einzelnen Entwürfen

1. **Schneeflocken:** Die Stege sind 3 mm breit. Für Bänder und Garn hat jede Flocke eine Öse mit Ø 4 mm.
2. **Steck-Tannenbaum:** Teil A wird von unten, Teil B von oben zusammengesteckt. Der Schlitz ist auf **2,9 mm** ausgelegt. Schneide zuerst den **Passungstest-Streifen** mit Schlitzen von 2,7 bis 3,2 mm und prüf, welcher Schlitz stramm sitzt. Weicht dein Wert ab, ändere `SLOT` in `tools/designs.py` und erzeuge die Dateien neu.
3. **Sterne:** Den Text („Frohe Weihnachten 2026“) kannst du in XCS löschen und durch einen Namen ersetzen.
4. **Laterne:** Die Teile sind Vorderwand (mit Gravur), Rückwand, zwei Seitenwände und der Boden mit Ø-22-mm-Loch für den Schalter des LED-Teelichts. Die Zinken stecken sich zusammen, ein Tropfen Holzleim macht die Laterne stabil. Wenn du Transparentpapier von innen einklebst, wird das Licht weicher. ⚠️ **Nur LED-Teelichter verwenden, keine echten Kerzen!**
5. **Geschenkanhänger:** Auf „Für:“ und „Von:“ kannst du mit Bleistift oder Fineliner schreiben. Für Kordel oder Garn gibt es Löcher mit Ø 4–5 mm.

## Dateien neu erzeugen und anpassen

```bash
pip install shapely fonttools cairosvg pillow numpy
python3 tools/build.py
```

- `tools/designs.py`: Formen, Texte, Materialstärke (`MAT`) und Schlitzbreite (`SLOT`)
- `tools/lasergeo.py`: Geometrie, Text-zu-Pfad und SVG-Export
- `tools/render.py` und `tools/build.py`: Mockups und Vorschauen

Die Schriften *Great Vibes* und *Berkshire Swash* stehen unter der SIL Open Font License (siehe `tools/fonts/`).

---

# Saaletal-Serie: Hammelburg, Bad Kissingen und die Fränkische Saale

Zehn weitere Entwürfe mit regionalem Bezug, ebenfalls für den **xTool D1 Pro 10W** und **3 mm Pappel- oder Lindensperrholz**. Farben, Laserwerte und Schneidreihenfolge wie oben.

![Übersicht Saaletal](entwuerfe/saaletal/uebersicht_saaletal.jpg)

| # | Entwurf | Teile | Maße (mm) | Datei |
|---|---------|-------|-----------|-------|
| 1 | Wandschild „Skyline Saaletal“: Hohntor, Kurstadt-Kirchen, Arkaden, Trimburg, Hammelburg, Schloss Saaleck mit Weinberg | 1 | 380 × 100 | `entwuerfe/saaletal/01_skyline-saaletal/` |
| 2 | Flusskarte „Fränkische Saale“: 11 Orte von der Quelle bis Gemünden, Rhön, Main, Kompass | 1 | 300 × 215 | `entwuerfe/saaletal/02_flusskarte-saale/` |
| 3 | Wanduhr „Saaletal-Zeit“: 12 Saale-Orte statt Ziffern, Mini-Skyline | 1 | Ø 260 | `entwuerfe/saaletal/03_wanduhr-saaletal/` |
| 4 | Untersetzer-Set: Hammelburg, Bad Kissingen, Schloss Saaleck, Fränkische Saale | 4 | je Ø 95 | `entwuerfe/saaletal/04_untersetzer-saaletal/` |
| 5 | Bocksbeutel-Flaschenanhänger: „Hammelburg“, „Zum Wohl!“, „Schloss Saaleck“ | 3 | 60 × 129 | `entwuerfe/saaletal/05_bocksbeutel-anhaenger/` |
| 6 | Schlüsselanhänger im Ortstafel-Stil (6 Orte) | 6 | 72 × 30 | `entwuerfe/saaletal/06_ortsschild-anhaenger/` |
| 7 | Lesezeichen: Weinrebe, Arkaden, Kanu auf der Saale | 3 | 40 × 150 | `entwuerfe/saaletal/07_lesezeichen/` |
| 8 | Christbaumanhänger mit Durchbruch: Hammelburg, Bad Kissingen, Saaleck, Trimburg | 4 | Ø 80 | `entwuerfe/saaletal/08_christbaumanhaenger/` |
| 9 | Steckfigur „Hammelburger Rhönschaf“ mit Bodenplatte | 2 | 114 × 80 / 132 × 58 | `entwuerfe/saaletal/09_steckfigur-rhoenschaf/` |
| 10 | Teelicht-Laterne „Kurstadt“: Arkaden, Zwiebelkuppel, Doppeltürme, Gradierbau-Seiten | 5 | 90 × 90 × 110 | `entwuerfe/saaletal/10_laterne-kurstadt/` |

Jeder Ordner enthält die laserfertige SVG, eine Laservorschau (PNG) und ein Mockup (JPG). Alle Arbeitsflächen passen auf den D1 Pro.

Die Gebäude sind **stilisierte Silhouetten**, keine maßstabsgetreuen Ansichten. Wappen und Logos der Städte sind bewusst nicht verwendet.

## Tipps zur Saaletal-Serie

1. **Skyline:** Zwei Löcher mit Ø 5 mm zum Aufhängen. Mit einem LED-Streifen hinter dem Schild entsteht ein schöner Lichtsaum an der Wand.
2. **Flusskarte:** Die Orte sind nach echten Koordinaten platziert. Der Fluss ist eine Flächengravur und wird zur Mündung hin breiter. Auf großen Flächen lohnt sich Malerkrepp gegen Rauchspuren.
3. **Wanduhr:** Das Mittelloch hat Ø 8 mm, passend für gängige Quarzuhrwerke mit Gewindehals für 3–5 mm Zifferblattstärke.
4. **Untersetzer:** Nach dem Gravieren mit Hartwachsöl oder Klarlack versiegeln, sonst ziehen Ränder von Gläsern ein.
5. **Bocksbeutel-Anhänger:** Der Ring (Ø 34 mm) rutscht über den Hals einer 0,75-l-Flasche. Auf der Rückseite ist Platz für einen Gruß.
6. **Ortsschild-Anhänger:** Wer möchte, lackiert das Schild gelb und lässt die Gravur dunkel, dann sieht es aus wie eine echte Ortstafel. Das Loch hat Ø 5,4 mm für Schlüsselringe. Weitere Orte lassen sich in `KEY_TOWNS` in `tools/saaletal.py` eintragen.
7. **Lesezeichen:** Das Loch oben ist für eine Quaste gedacht. Die feinen Durchbrüche nicht zu stark biegen.
8. **Christbaumanhänger:** Die Szenen sind Durchbrüche. Vor einem Licht oder Fenster wirken sie wie Scherenschnitte.
9. **Rhönschaf:** Die Zapfen unter den Beinen stecken in den Schlitzen der Bodenplatte (2,9 mm). Mit dem **Passungstest** aus Entwurf 2 der Weihnachtsserie lässt sich die Schlitzbreite vorher prüfen. Bei zu lockerem Sitz hilft ein Tropfen Leim. Den Kopf schwärzt die Flächengravur, genau wie beim echten Rhönschaf.
10. **Laterne:** Gleiche Fingerzinken wie die „Winterdorf“-Laterne, Boden mit Ø-22-mm-Loch. ⚠️ **Nur LED-Teelichter verwenden!**

## Saaletal-Dateien neu erzeugen

```bash
python3 tools/build_saaletal.py            # alle zehn
python3 tools/build_saaletal.py 03 07      # nur einzelne Entwürfe
```

`tools/saaletal.py` enthält Formen, Texte und Ortslisten, `tools/build_saaletal.py` die Mockups. Die Ortsnamen sind mit *Inter Bold* gesetzt (SIL Open Font License, siehe `tools/fonts/OFL-Inter.txt`).
