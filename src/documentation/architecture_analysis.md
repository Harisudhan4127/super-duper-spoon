# Architecture Analysis — Brihadisvara Temple

## 1. Sources used

| Source | What it is used for |
|---|---|
| Wikipedia, "Brihadisvara Temple" (en.wikipedia.org, retrieved 2026-10-20) | overall dimensions, component names, the elevations and storey counts quoted below |
| R. Balasubrahmanyam, *Middle Chola Temples* (1975), cited by Wikipedia | the 240.79 × 121.92 m compound, the ~63.4 m vimana, the 450 m prakara perimeter, the plan sequence |
| UNESCO World Heritage nomination 250bis-001, "Great Living Chola Temples" | the 18.07 ha protected area, the official description of the complex as a "perunkoil" |
| Archaeological Survey of India material (via Wikipedia's ASI citations) | the monolithic linga, the plinth thicknesses, the 13th-century fresco programme |
| Wikimedia Commons photographs (44 files, `src/references/`) | silhouette, storey rhythm, roof profiles, gopuram massing, the Nandi and the prakara corridors |
| The Chola temple at Gangaikonda Cholapuram (comparison) | the contrast between a straight-tapering and a curvilinear vimana |

Photographs were used as **evidence of proportion and profile only**. No
dimension in this project was measured off a photograph; where a measurement
was needed and no published figure exists, the value is an interpretation and is
listed in `historical_assumptions.md`.

## 2. The building as a whole

The temple is a *perunkoil* — a large temple standing on a raised platform —
organised on a strict east–west axis. The temple faces **east**; a worshipper
approaching the shrine walks west along the axis.

The published plan (Balasubrahmanyam, via Wikipedia) gives the compound as a
rectangle of **240.79 m (E–W) × 121.92 m (N–S)**, "almost two stacked
squares", and divides it into five axial elements:

1. the sanctum with the *sri vimana*,
2. the *antrala* (vestibule) linking it to the great hall,
3. the *maha-mandapam* (great gathering hall),
4. the *mukha-mandapam* (community hall),
5. the *Nandi-mandapam* (hall of the bull), and, outside the sanctum block,
   the courtyard (*kuttu vannam*), the pillared *prakara* veranda, the inner
   gateway (*Rajarajan tiruvasal*), the outer gateway (*Keralantakan
   tiruvasal*) and the enclosure walls.

The temple block itself is therefore **not** the whole complex. Modelling the
complete compound at a small scale produces a model in which the shrine is a
minor element inside a large walled court; that is historically correct and is
why the project also produces a 1:320 core model.

## 3. The vimana (the tower over the sanctum)

This is the defining element of the monument.

* Height: the Wikipedia infobox gives an elevation of **65.83 m (216 ft)**;
  Balasubrahmanyam is quoted as **63.4 m (208 ft)**; a third figure of
  59.82 m is used for the height of the tower above the shrine. The model
  reproduces the **65.83 m** figure, the most widely reproduced one, and the
  difference between the published figures is recorded in
  `historical_assumptions.md`.
* Plan: the tower stands on a **30.18 m sided square** — the *aditala* — and
  the published description counts **16 storeys of which 13 are tapering
  squares**.
* Structure of the crown: above the 13 tapering storeys stands the single
  granite block of **7.77 m side** (weight given as 80 tons), with a pair of
  Nandi at each corner (each about 1.98 m × 1.68 m); above that the *griva*,
  the cupola-shaped *sikhara* (25 tons) and the *stupi* finial, **3.81 m**
  high, originally gilded.
* Each storey is articulated with *kutas* and *salas* — the miniature
  shrine motifs that give Dravidian towers their texture — and with rhythmic
  pilasters and attached columns.
* The profile is **straight, not curvilinear**; the Wikipedia article
  explicitly contrasts it with the tower of Gangaikonda Cholapuram, which
  curves. The model therefore uses a straight (slightly convex) taper, never
  a North-Indian curvilinear *shikhara*.
* The upper storey wall of the *aditala* corridor carries the 81 *karana*
  dance postures of the Natya Sastra.

**Modelling consequence.** The tower is modelled as 13 truncated square
storeys, each with a projecting *kapota* cornice, a pilaster rhythm and
simplified *kuta* motifs; a stepped *griva* block, a 16-sided ribbed cupola
and a turned finial complete it.

## 4. The halls

* The *maha-mandapam* and *mukha-mandapam* are **square in plan** and
  axially aligned between the sanctum and the Nandi hall; the *maha-mandapam*
  has **six pillars on each side** and is flanked by two giant stone
  *dvarapala* figures. The *mukha-mandapam* contains eight small shrines of
  the *dikpalas* (installed under Rajendra I).
* Both halls are linked by flights of steps and by the *antrala*, which
  connects the great hall to the *pradakshina* patha — the circumambulatory
  passage that runs around the sanctum between the inner and outer walls of
  the sanctuary.
* The cella (*garbhagriha*) is square, stands on a moulded plinth 0.5 m thick
  (*upapitham* 140 cm, *adhishthanam* 360 cm) and contains the monolithic
  **linga 8.7 m (29 ft)** high, which occupies two storeys of the sanctum.

## 5. The Nandi

The Nandi mandapa contains a **monolithic seated bull facing the sanctum**,
about **5.94 m long, 2.59 m broad and 3.65 m high** and estimated at 25
tons. It is one of the largest monolithic Nandi sculptures in India. In the
model it is a simplified, solid, printable stylisation placed on the axis
inside the Nandi hall.

## 6. The gopurams

* The main entrance gopuram is **30 m high** — "less than half the size of the
  main temple's vimana" — and is entered through a **barrel-vaulted** passage.
* The outermost eastern gateway is the *Keralantakan tiruvasal*, "the sacred
  gate of Keralantakan" (the title of Rajaraja); roughly 100 m further in
  stands the **inner courtyard gopuram**, the *Rajarajan tiruvasal*, which is
  the more richly decorated of the two and is described as a five-storey
  gopuram. The model places the inner gateway on the axis, with five storeys,
  and the outer gateway in the east enclosure wall.
* The gopurams of the Chola period are stepped, with each storey set back from
  the one below and crowned by a small *sikhara*; this is the silhouette the
  model reproduces (never the tall, curvilinear, later Chola gopuram).

## 7. The enclosure, the prakara and the courtyard

* A **pillared and covered veranda** (*prakara*) frames the courtyard; the
  published circumambulation perimeter is about **450 m**.
* Outside it stand **two enclosure walls**: the inner one of the temple, and
  an outer, **defensive wall added in 1777 by the French**, with gun-holes,
  which used the temple as an arsenal. A moat once separated the complex from
  the fortification.
* The courtyard contained the main shrine plus later (Nayaka-period) shrines
  of Parvati (*Amman*), Murugan, Ganesha and others, plus the *Nandi* shrine.
  Two of these subsidiary shrines are modelled in the courtyard.

## 8. Materials and the surface language

* The base and tower are **granite**; the superstructure of the halls is
  **sandstone**, which is why the tower reads darker and the halls warmer in
  the photographs. The model is rendered in a single neutral stone material,
  because the printable object cannot carry material information.
* The surface language is: stepped *talas* (storeys) separated by projecting
  cornices, *kuta* and *sala* motifs, rhythmically placed pilasters and
  columns, and a continuous moulded base (*adhisthana* / *upapitham*).

## 9. What the photographs add

The 44 reference photographs in `src/references/images/` were reviewed as
contact sheets (`src/scripts/inspect_references.py`). They were used to:

* confirm the convex-then-straight taper of the vimana and the strength of its
  horizontal cornice bands;
* confirm that the crown of the tower is a **ribbed cupola** on a square
  *griva* block and not a curvilinear *shikhara*;
* confirm the blocky, stepped profile of the gopurams and their small crowning
  *shikhara*;
* confirm the proportions of the prakara colonnade and of the low subsidiary
  shrines in the courtyard;
* confirm the position of the Nandi on the axis, facing the sanctum.
