"""
JOURNAL DE COMMANDES — AVEC UNE DEMANDE QUI RESSEMBLE À UN ENTREPÔT

La version précédente tirait les articles d'une commande avec
`random.sample(products, n)` : uniformément, sur les cinquante mille
références. Le journal produit était statistiquement plat.

Conséquences, mesurées sur le fichier produit :

  - Le plus demandé des cinquante mille articles sortait six fois en un an.
    Dix-sept mille quatre cents en sortaient une seule.
  - Le premier cinquième du catalogue faisait 34,8 % des prélèvements. Un
    entrepôt réel tourne autour de 80 %.
  - Aucune paire d'articles ne se croisait plus d'une fois. Il n'existait donc
    aucune affinité à trouver — le tirage uniforme l'interdit par construction.

Un tel journal ne peut pas nourrir un classement ABC, une distance de pige, ni
une recommandation d'affinité : découper cette demande plate en A, B et C ne
classe rien, ça met une étiquette sur du bruit.

Ce que cette version change, et rien d'autre :

  LA POPULARITÉ SUIT UNE LOI DE PUISSANCE. Dans la pièce d'auto comme ailleurs,
  quelques centaines de références — filtres, plaquettes, ampoules — font
  l'essentiel des trajets, et la queue du catalogue dort. Chaque article reçoit
  donc un poids de tirage, et les commandes se tirent selon ce poids.

  LES ARTICLES SORTENT PAR GROUPES. Un client qui achète des plaquettes prend
  souvent les disques avec. Les références sont réparties en familles d'achat,
  et une commande pioche le plus souvent dans une seule d'entre elles. C'est
  cette régularité, et elle seule, qui rend une affinité mesurable.

  LA CLASSE ABC EST DÉDUITE DE LA DEMANDE OBSERVÉE. Elle valait
  `random.random()` : une lettre sans rapport avec quoi que ce soit, y compris
  avec le journal du même dossier. Elle est maintenant recalculée à la fin, sur
  les prélèvements réellement générés, selon la règle usuelle : 80 % des
  trajets font les A, les 15 % suivants les B, le reste les C. C'est la
  définition d'un classement ABC.
"""

import csv
import random
import time
from collections import Counter
from datetime import datetime, timedelta

random.seed(20260905)  # Journal reproductible : deux exécutions se comparent.

print("Génération du journal de commandes...")
start_time = time.time()

INVENTORY_FILE = "inventaire_grossiste_auto_50k.csv"
OUTPUT_FILE = "journal_commandes.csv"

NUM_ORDERS = 10000
START_DATE = datetime(2023, 1, 1)
DAYS = 365

# Loi de puissance de la popularité, calibrée et non devinée : 0,9 place le
# premier cinquième du catalogue autour de 80 % des prélèvements, ce qu'on
# mesure en entrepôt. Plus haut concentre encore, plus bas aplatit.
ZIPF_EXPONENT = 0.9

# Taille moyenne d'une famille d'achat, et probabilité qu'une commande reste
# dans une seule famille. Le reste des commandes pioche au hasard : un client
# achète aussi des choses sans rapport.
FAMILY_SIZE = 6
FAMILY_ORDER_PROB = 0.65

# 1. CHARGEMENT DES PRODUITS
products = []
fieldnames = []
try:
    with open(INVENTORY_FILE, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            products.append(row)
except FileNotFoundError:
    print(f"Erreur : le fichier {INVENTORY_FILE} est introuvable. Générez-le d'abord.")
    raise SystemExit(1)

print(f"{len(products)} produits chargés.")

# 2. POPULARITÉ ET FAMILLES D'ACHAT
#
# Le rang décide du poids, et l'ordre des rangs est tiré au hasard : rien dans
# le SKU ne doit prédire la popularité, sans quoi le classement ABC se lirait
# dans le numéro de référence au lieu de se calculer.
order_of_popularity = list(range(len(products)))
random.shuffle(order_of_popularity)

weights = [0.0] * len(products)
for rank, index in enumerate(order_of_popularity, start=1):
    weights[index] = 1.0 / (rank**ZIPF_EXPONENT)

# Les familles mélangent les niveaux de popularité, en distribuant les rangs à
# tour de rôle. Regrouper des rangs voisins ferait des familles entièrement
# populaires, tirées sans cesse : la concentration montait alors à 91 % au lieu
# des 80 % d'un entrepôt. Une vraie famille d'achat ressemble davantage à ça —
# des plaquettes qui sortent tous les jours, et le capteur d'usure qui va avec
# et qu'on remplace rarement.
nombre_familles = (len(order_of_popularity) + FAMILY_SIZE - 1) // FAMILY_SIZE
families = [[] for _ in range(nombre_familles)]
for rang, index in enumerate(order_of_popularity):
    families[rang % nombre_familles].append(index)
family_of = {}
for numero, fam in enumerate(families):
    for index in fam:
        family_of[index] = numero

clients = [
    "Garage Tremblay", "Auto-Réparation ABC", "Carrosserie Moderne",
    "Mécanique Rapide Inc.", "Centre Auto Plus", "Garage du Centre",
    "Pneus & Mécanique Pro", "Services Automobiles Express",
    "Atelier Mécanique 360", "Concessionnaire XYZ", "Pièces Auto Dépôt",
    "Garage Les Experts", "Moteurs & Cie", "Auto Clinic", "Garage Royal",
]

# 3. GÉNÉRATION DES COMMANDES
print(f"Génération de {NUM_ORDERS} commandes...")

orders_data = []
picks = Counter()

for order_id in range(1, NUM_ORDERS + 1):
    num_cmd = f"CMD-{order_id:07d}"
    client = random.choice(clients)
    order_date = START_DATE + timedelta(days=random.randint(0, DAYS))
    num_lines = random.randint(1, 6)

    if random.random() < FAMILY_ORDER_PROB:
        # Une commande de famille : le client remplace un ensemble. La famille
        # se choisit par l'article qui motive la commande, non par le poids
        # cumulé de ses membres — sinon la famille la plus populaire raflerait
        # presque tout, et la concentration monterait à 99 %.
        ancre = random.choices(range(len(products)), weights=weights, k=1)[0]
        famille = families[family_of[ancre]]
        selected = random.sample(famille, min(num_lines, len(famille)))
    else:
        # Une commande de dépannage : ce qui manque, sans rapport entre les
        # lignes, mais toujours pondéré par la popularité.
        selected = []
        vus = set()
        for _ in range(num_lines * 3):
            if len(selected) >= num_lines:
                break
            index = random.choices(range(len(products)), weights=weights, k=1)[0]
            if index in vus:
                continue
            vus.add(index)
            selected.append(index)

    lines = []
    total = 0.0
    for index in selected:
        prod = products[index]
        prix = float(prod["prix_vente_cad"])
        qty = random.randint(1, 12)
        ligne_total = qty * prix
        total += ligne_total
        picks[prod["sku"]] += 1
        lines.append((prod, qty, prix, round(ligne_total, 2)))

    total = round(total, 2)
    for prod, qty, prix, ligne_total in lines:
        orders_data.append({
            "numero_commande": num_cmd,
            "date_commande": order_date.strftime("%Y-%m-%d"),
            "client": client,
            "montant_total_commande": total,
            "sku_produit": prod["sku"],
            "produit_designation": prod["designation"],
            "quantite": qty,
            "prix_unitaire_cad": prix,
            "sous_total_ligne_cad": ligne_total,
        })

with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(orders_data[0].keys()))
    writer.writeheader()
    writer.writerows(orders_data)

print(f"{len(orders_data)} lignes écrites dans {OUTPUT_FILE}.")

# 4. CLASSE ABC DÉDUITE DE LA DEMANDE
#
# 80 % des prélèvements font les A, les 15 % suivants les B, le reste les C.
# Un article jamais commandé est un C : il occupe de la place sans faire de
# trajet, ce qui est précisément ce que la lettre doit dire.
total_picks = sum(picks.values())
classes = {}
if total_picks:
    cumul = 0
    for sku, n in picks.most_common():
        part = cumul / total_picks
        classes[sku] = "A" if part < 0.80 else ("B" if part < 0.95 else "C")
        cumul += n

repartition = Counter()
for prod in products:
    prod["classe_abc"] = classes.get(prod["sku"], "C")
    repartition[prod["classe_abc"]] += 1

with open(INVENTORY_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(products)

# 5. CE QUE LE JOURNAL VAUT, DIT PLUTÔT QUE SUPPOSÉ
rangs = sorted(picks.values(), reverse=True)
tete = max(1, round(len(products) * 0.2))
concentration = sum(rangs[:tete]) / total_picks if total_picks else 0

print(f"\nArticles commandés au moins une fois : {len(picks)} / {len(products)}")
print(f"Prélèvements du plus demandé : {rangs[0] if rangs else 0}")
print(f"Concentration du premier cinquième : {concentration * 100:.1f} %")
print(f"Répartition ABC : A={repartition['A']} B={repartition['B']} C={repartition['C']}")
print(f"Terminé en {time.time() - start_time:.1f} s.")
