import csv
import random
import time

print("Génération du référentiel d'emplacements (20 000 adresses)...")
start_time = time.time()

# 1. GÉNÉRATION PRÉCISE DES 20 000 LOCATIONS
locations = []

# Zones A1a, A1b, A1c (Allées 01-40, Niveaux a, b, c, Travées 01-12)
for zone in ["A1a", "A1b", "A1c"]:
    for aisle in range(1, 41):
        for level in ["a", "b", "c"]:
            for bay in range(1, 13):
                locations.append(f"{zone}-{aisle:02d}-{level}-{bay:02d}")

# Zone A1p (Palettes : 10 allées, 20 travées, 4 hauteurs)
for aisle in range(1, 11):
    for bay in range(1, 21):
        for h in range(1, 5):
            locations.append(f"A1p-{aisle:02d}-{bay:02d}-H{h}")

# Zone A2 (Petites pièces : 20 colonnes, 15 tiroirs, 8 casiers A-H)
for col in range(1, 21):
    for drawer in range(1, 16):
        for slot in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            locations.append(f"A2-C{col:02d}-T{drawer:02d}-{slot}")

# Zone A3 (Lisses multi-sections : 25 lisses, 5 hauteurs, 16 sections)
for rack in range(1, 26):
    for h in range(1, 6):
        for sec in range(1, 17):
            locations.append(f"A3-L{rack:02d}-H{h}-S{sec:02d}")

# Ajustement pour plafonner exactement au volume cible
locations = locations[:20000]

# 2. PROFILES PRODUITS AVEC VOLUMÉTRIE RÉELLE
families = {
    "Petite_Piece_A2": {
        "zone_pref": "A2",
        "types": [
            ("SEN", "Capteur ABS", 18.0, 45.0, (8, 15), (4, 8), (3, 6), (0.1, 0.4)),
            ("FUS", "Boîte fusibles relais", 4.0, 12.0, (5, 12), (3, 8), (2, 5), (0.05, 0.2)),
            ("SPK", "Bougie allumage iridium", 5.5, 16.0, (10, 14), (2, 4), (2, 4), (0.08, 0.15)),
            ("BLB", "Ampoule LED H7", 8.0, 24.0, (6, 10), (4, 6), (4, 6), (0.05, 0.12)),
        ],
    },
    "Moyenne_Standard_A1": {
        "zone_pref": ["A1a", "A1b", "A1c"],
        "types": [
            ("BRK", "Jeu plaquettes AV", 22.0, 65.0, (15, 25), (10, 18), (5, 10), (1.5, 3.8)),
            ("ROT", "Disque de frein ventilé", 35.0, 110.0, (26, 36), (26, 36), (4, 7), (6.0, 14.0)),
            ("ALT", "Alternateur 12V 140A", 120.0, 280.0, (20, 30), (18, 25), (18, 25), (5.5, 9.0)),
            ("FLT", "Filtre à air moteur", 6.0, 22.0, (20, 38), (14, 25), (4, 8), (0.2, 0.6)),
        ],
    },
    "Grande_Piece_A3_A1p": {
        "zone_pref": ["A3", "A1p"],
        "types": [
            ("EXH", "Silencieux échappement", 85.0, 240.0, (80, 140), (25, 45), (18, 30), (8.0, 18.0)),
            ("STR", "Jambe de force suspension", 55.0, 160.0, (55, 85), (15, 25), (15, 25), (4.5, 9.5)),
            ("RAD", "Radiateur refroidissement", 65.0, 195.0, (50, 85), (40, 65), (5, 12), (3.5, 8.0)),
            ("BMP", "Pare-chocs AV primaire", 110.0, 320.0, (150, 195), (45, 65), (35, 55), (6.0, 13.0)),
        ],
    },
}

# PRE-COMPUTE LOCATIONS PER FAMILY TO AVOID O(N*M) COMPLEXITY
valid_locations = {}
for fam_key, fam_data in families.items():
    target_zone = fam_data["zone_pref"]
    if isinstance(target_zone, list):
        valid_locs = [loc for loc in locations if any(loc.startswith(z) for z in target_zone)]
    else:
        valid_locs = [loc for loc in locations if loc.startswith(target_zone)]
    valid_locations[fam_key] = valid_locs if valid_locs else locations

# 3. GÉNÉRATION DES 50 000 ARTICLES
csv_filename = "inventaire_grossiste_auto_detaille.csv"
print("Génération des 50 000 articles en cours...")

with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "code_barre_128",
        "sku",
        "classe_produit",
        "designation",
        "emplacement_id",
        "prix_achat_cad",
        "prix_importation_cad",
        "prix_transport_cad",
        "cout_de_revient_total",
        "longueur_cm",
        "largeur_cm",
        "hauteur_cm",
        "poids_kg",
        "classe_abc",
    ])

    for i in range(1, 50001):
        # Rotation ABC
        r = random.random()
        classe_abc = "A" if r < 0.20 else ("B" if r < 0.50 else "C")

        # Choix famille & gabarit
        fam_key = random.choices(
            list(families.keys()), weights=[0.25, 0.55, 0.20], k=1
        )[0]
        fam = families[fam_key]
        prefix, name, min_p, max_p, l_r, w_r, h_r, wt_r = random.choice(fam["types"])

        # Identifiants
        sku = f"{prefix}-{i:06d}"
        barcode_128 = f"C128{random.randint(1000000000, 9999999999)}"

        assigned_loc = random.choice(valid_locations[fam_key])

        # Dimensions & Poids
        length = round(random.uniform(*l_r), 1)
        width = round(random.uniform(*w_r), 1)
        height = round(random.uniform(*h_r), 1)
        weight = round(random.uniform(*wt_r), 2)

        # Données Financières
        prix_achat = round(random.uniform(min_p, max_p), 2)
        # Importation : douanes 3.5% à 6.5% de la valeur usine
        prix_import = round(prix_achat * random.uniform(0.035, 0.065), 2)
        # Fret : proportionnel au volume/poids + variable
        prix_transport = round((weight * 1.85) + (prix_achat * 0.04) + random.uniform(1.0, 4.0), 2)
        cout_total = round(prix_achat + prix_import + prix_transport, 2)

        writer.writerow([
            barcode_128,
            sku,
            f"{prefix} - {fam_key.replace('_', ' ')}",
            name,
            assigned_loc,
            f"{prix_achat:.2f}",
            f"{prix_import:.2f}",
            f"{prix_transport:.2f}",
            f"{cout_total:.2f}",
            length,
            width,
            height,
            weight,
            classe_abc,
        ])

print(f"Export terminé en {round(time.time() - start_time, 2)}s -> Fichier : {csv_filename}")
