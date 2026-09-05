"""
JEU DE DÉMONSTRATION CALÉ SUR LE PLAN

Les trois fichiers de ce dossier décrivent un grossiste de cinquante mille
références réparties sur dix-huit mille adresses. C'est un volume réaliste, et
c'est très bien pour éprouver le lecteur de l'application.

Ce n'est pas ce qu'il faut pour une démonstration. Deux raisons :

  LES ADRESSES NE SUIVAIENT PAS LA CONVENTION DU SITE. Écrites `A-01-07-L1-D`,
  elles ne se découpent pas selon `a1a/02/a/02` — zone, rangée, rack, hauteur,
  bin. Zéro adresse sur cinquante mille était comprise. L'application les
  gardait comme texte brut, donc sans jamais les rapprocher d'un emplacement du
  plan.

  L'ÉCHELLE NE CORRESPONDAIT À AUCUN PLAN OUVRABLE. Le plan d'exemple de
  l'application compte 240 alvéoles ; un inventaire de cinquante mille articles
  affichait donc « 49 760 articles n'ont trouvé aucun emplacement », ce qui est
  exact et illisible.

Ce script produit donc un second jeu, petit et cohérent :

  - 240 articles, pris dans le catalogue détaillé — vraies désignations, vrais
    poids, vraies dimensions, vrais coûts ;
  - une adresse par article, lue dans `adresses_plan_exemple.csv`, qui est
    exporté par l'application elle-même à partir de son plan. Aucune adresse
    n'est écrite à la main ici : c'est la seule façon d'obtenir zéro orphelin ;
  - un journal de commandes sur ces seuls articles, avec une demande concentrée
    et des familles d'achat, comme dans `generate_orders.py`.

ET SURTOUT : LE RANGEMENT DE DÉPART EST DÉLIBÉRÉMENT MAUVAIS.

Un entrepôt bien rangé ne démontre rien. Les articles les plus demandés sont
donc placés au plus loin du quai et au plus haut, et les dormants occupent les
meilleures places. C'est ce que le plan de réimplantation doit trouver et
corriger — s'il ne trouve rien, c'est qu'il ne sert à rien.

Régénérer `adresses_plan_exemple.csv` : l'application l'écrit depuis son plan
d'exemple. Si le plan change, réexportez-le avant de relancer ce script.
"""

import csv
import random
from collections import Counter

random.seed(20260905)

ADRESSES = "adresses_plan_exemple.csv"
CATALOGUE = "inventaire_grossiste_auto_detaille.csv"
SORTIE_INVENTAIRE = "demo_inventaire.csv"
SORTIE_COMMANDES = "demo_commandes.csv"

NB_COMMANDES = 3000
JOURS = 365
DATE_DEBUT = "2025-09-05"
ZIPF = 1.1
TAILLE_FAMILLE = 6
PROB_FAMILLE = 0.65

# 1. LES ADRESSES VIENNENT DU PLAN, JAMAIS D'ICI
with open(ADRESSES, encoding="utf-8") as f:
    adresses = list(csv.DictReader(f))
print(f"{len(adresses)} adresses lues dans le plan.")

# 2. LES ARTICLES VIENNENT DU CATALOGUE RÉEL
with open(CATALOGUE, encoding="utf-8") as f:
    catalogue = list(csv.DictReader(f))

# Un article ne peut occuper qu'une alvéole où il entre. On apparie donc les
# deux listes par volume : la plus petite alvéole reçoit le plus petit article.
# Sans ce tri, un alternateur se retrouverait dans un bin de bougies et
# l'optimiseur passerait son temps à signaler des impossibilités.
def volume_m3(article):
    return (
        float(article["longueur_cm"])
        * float(article["largeur_cm"])
        * float(article["hauteur_cm"])
    ) / 1_000_000.0

echantillon = random.sample(catalogue, len(adresses))
echantillon.sort(key=volume_m3)
adresses_par_volume = sorted(adresses, key=lambda a: float(a["volume_m3"]))

trop_gros = [
    (a["designation"], volume_m3(a))
    for a, adr in zip(echantillon, adresses_par_volume)
    if volume_m3(a) > float(adr["volume_m3"])
]
if trop_gros:
    print(f"  {len(trop_gros)} article(s) ne tiennent nulle part et sont écartés.")
    garder = [
        (a, adr)
        for a, adr in zip(echantillon, adresses_par_volume)
        if volume_m3(a) <= float(adr["volume_m3"])
    ]
    echantillon = [a for a, _ in garder]
    adresses_par_volume = [adr for _, adr in garder]

# 3. LA DEMANDE : CONCENTRÉE, ET AVEC DES FAMILLES D'ACHAT
#
# Même mécanique que generate_orders.py, et pour les mêmes raisons : une
# demande uniforme ne se classe pas en A, B et C, et un tirage indépendant
# interdit toute affinité par construction.
rangs = list(range(len(echantillon)))
random.shuffle(rangs)
poids = [0.0] * len(echantillon)
for rang, index in enumerate(rangs, start=1):
    poids[index] = 1.0 / (rang**ZIPF)

nb_familles = max(1, (len(rangs) + TAILLE_FAMILLE - 1) // TAILLE_FAMILLE)
familles = [[] for _ in range(nb_familles)]
for position, index in enumerate(rangs):
    familles[position % nb_familles].append(index)
famille_de = {i: n for n, fam in enumerate(familles) for i in fam}

from datetime import datetime, timedelta

debut = datetime.fromisoformat(DATE_DEBUT)
clients = [
    "Garage Tremblay", "Auto-Réparation ABC", "Carrosserie Moderne",
    "Mécanique Rapide Inc.", "Centre Auto Plus", "Garage du Centre",
    "Pneus & Mécanique Pro", "Atelier Mécanique 360", "Auto Clinic",
    "Garage Royal",
]

lignes_commandes = []
picks = Counter()

for numero in range(1, NB_COMMANDES + 1):
    commande = f"CMD-{numero:06d}"
    date = debut + timedelta(days=random.randint(0, JOURS))
    nb_lignes = random.randint(1, 5)

    if random.random() < PROB_FAMILLE:
        # L'article qui motive la commande y figure toujours. Tirer les lignes
        # uniformément dans sa famille le noyait parmi cinq compagnons plus
        # rares : la concentration tombait de 67 % à 48 %, sous le seuil à
        # partir duquel l'application refuse — à juste titre — de classer.
        ancre = random.choices(range(len(echantillon)), weights=poids, k=1)[0]
        famille = familles[famille_de[ancre]]
        autres = [i for i in famille if i != ancre]
        random.shuffle(autres)
        choisis = [ancre] + autres[: max(0, nb_lignes - 1)]
    else:
        choisis, vus = [], set()
        for _ in range(nb_lignes * 3):
            if len(choisis) >= nb_lignes:
                break
            i = random.choices(range(len(echantillon)), weights=poids, k=1)[0]
            if i not in vus:
                vus.add(i)
                choisis.append(i)

    for i in choisis:
        article = echantillon[i]
        qte = random.randint(1, 8)
        prix = float(article["cout_de_revient_total"]) * 1.45
        picks[article["sku"]] += 1
        lignes_commandes.append({
            "numero_commande": commande,
            "date_commande": date.strftime("%Y-%m-%d"),
            "client": random.choice(clients),
            "sku_produit": article["sku"],
            "produit_designation": article["designation"],
            "quantite": qte,
            "prix_unitaire_cad": round(prix, 2),
        })

# 4. LE RANGEMENT DE DÉPART EST MAUVAIS, ET C'EST VOULU
#
# Les plus demandés partent au plus loin du quai, les dormants occupent les
# meilleures places. Un entrepôt déjà bien rangé ne donnerait aucun
# déplacement à proposer, et la démonstration ne montrerait rien.
#
# Mais l'article doit toujours ENTRER dans son alvéole. Attribuer les adresses
# par la seule demande cassait l'appariement par volume établi plus haut, et un
# alternateur pouvait atterrir dans un bac à bougies : le moteur l'aurait à bon
# droit déclaré improbable, et la démonstration se serait couverte d'erreurs.
#
# Les articles sont donc traités du plus volumineux au plus petit — le plus
# contraint d'abord. Toute adresse qui convient au plus gros convient à tous
# les suivants, donc en réserver une ne peut jamais bloquer la suite. Parmi
# celles qui conviennent, le choix se fait sur la demande : au plus demandé la
# plus pénible, au dormant la meilleure.
rang_demande = {
    echantillon[i]["sku"]: position
    for position, i in enumerate(
        sorted(range(len(echantillon)), key=lambda i: picks[echantillon[i]["sku"]], reverse=True)
    )
}

# La pénibilité d'une alvéole : loin du quai d'abord, haut ensuite.
def penibilite(adresse):
    return (float(adresse["distance_quai_m"]), float(adresse["hauteur_sol_mm"]))

disponibles = sorted(adresses_par_volume, key=lambda a: float(a["volume_m3"]))
attribution = {}
mediane = len(echantillon) / 2

for index in sorted(range(len(echantillon)), key=lambda i: volume_m3(echantillon[i]), reverse=True):
    besoin = volume_m3(echantillon[index])
    candidates = [a for a in disponibles if float(a["volume_m3"]) >= besoin]
    if not candidates:
        raise SystemExit(
            f"Aucune alvéole assez grande pour {echantillon[index]['designation']} "
            f"({besoin:.4f} m³) — le plan a changé, réexportez les adresses."
        )
    tres_demande = rang_demande[echantillon[index]["sku"]] < mediane
    choix = max(candidates, key=penibilite) if tres_demande else min(candidates, key=penibilite)
    disponibles.remove(choix)
    attribution[index] = choix

# 5. LA CLASSE ABC SE DÉDUIT DE LA DEMANDE, JAMAIS DU HASARD
total = sum(picks.values())
classes, cumul = {}, 0
for sku, n in picks.most_common():
    classes[sku] = "A" if cumul / total < 0.80 else ("B" if cumul / total < 0.95 else "C")
    cumul += n

with open(SORTIE_INVENTAIRE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "sku", "code_barre_128", "designation", "emplacement_id",
        "poids_kg", "longueur_cm", "largeur_cm", "hauteur_cm",
        "cout_de_revient_total", "stock_systeme", "classe_abc",
    ])
    writer.writeheader()
    for index, article in enumerate(echantillon):
        writer.writerow({
            "sku": article["sku"],
            "code_barre_128": article["code_barre_128"],
            "designation": article["designation"],
            "emplacement_id": attribution[index]["adresse"],
            "poids_kg": article["poids_kg"],
            "longueur_cm": article["longueur_cm"],
            "largeur_cm": article["largeur_cm"],
            "hauteur_cm": article["hauteur_cm"],
            "cout_de_revient_total": article["cout_de_revient_total"],
            "stock_systeme": random.randint(0, 120),
            "classe_abc": classes.get(article["sku"], "C"),
        })

with open(SORTIE_COMMANDES, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(lignes_commandes[0].keys()))
    writer.writeheader()
    writer.writerows(lignes_commandes)

# 6. CE QUE LE JEU VAUT, MESURÉ ET NON SUPPOSÉ
compte = sorted(picks.values(), reverse=True)
tete = max(1, round(len(echantillon) * 0.2))
concentration = sum(compte[:tete]) / total if total else 0
repartition = Counter(classes.get(a["sku"], "C") for a in echantillon)

print(f"\n{len(echantillon)} articles écrits dans {SORTIE_INVENTAIRE}.")
print(f"{len(lignes_commandes)} lignes écrites dans {SORTIE_COMMANDES}.")
print(f"Articles commandés au moins une fois : {len(picks)} / {len(echantillon)}")
print(f"Prélèvements du plus demandé : {compte[0] if compte else 0}")
print(f"Concentration du premier cinquième : {concentration * 100:.1f} %")
print(f"Répartition ABC : A={repartition['A']} B={repartition['B']} C={repartition['C']}")
