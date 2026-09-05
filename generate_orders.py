import csv
import random
import time
from datetime import datetime, timedelta

print("Génération du journal de commandes...")
start_time = time.time()

# 1. CHARGEMENT DES PRODUITS (à partir du premier inventaire qui contient les prix de vente)
inventory_file = "inventaire_grossiste_auto_50k.csv"
products = []
try:
    with open(inventory_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append({
                "sku": row["sku"],
                "designation": row["designation"],
                "prix_vente": float(row["prix_vente_cad"])
            })
except FileNotFoundError:
    print(f"Erreur : le fichier {inventory_file} est introuvable. Veuillez le générer d'abord.")
    exit(1)

print(f"{len(products)} produits chargés.")

# 2. LISTE DE CLIENTS FICTIFS
clients = [
    "Garage Tremblay", "Auto-Réparation ABC", "Carrosserie Moderne",
    "Mécanique Rapide Inc.", "Centre Auto Plus", "Garage du Centre",
    "Pneus & Mécanique Pro", "Services Automobiles Express",
    "Atelier Mécanique 360", "Concessionnaire XYZ", "Pièces Auto Dépôt",
    "Garage Les Experts", "Moteurs & Cie", "Auto Clinic", "Garage Royal"
]

# 3. GÉNÉRATION DES COMMANDES
output_file = "journal_commandes.csv"
num_orders = 10000  # On va générer 10 000 commandes
start_date = datetime(2023, 1, 1)

print(f"Génération de {num_orders} commandes...")

orders_data = []

for order_id in range(1, num_orders + 1):
    num_cmd = f"CMD-{order_id:07d}"
    client = random.choice(clients)
    
    # Date aléatoire dans les 365 derniers jours
    days_offset = random.randint(0, 365)
    order_date = start_date + timedelta(days=days_offset)
    
    # Nombre de lignes pour cette commande (1 à 6 produits)
    num_lines = random.randint(1, 6)
    order_lines = []
    total_order_amount = 0.0
    
    # Sélection des produits pour cette commande
    selected_products = random.sample(products, num_lines)
    
    for prod in selected_products:
        qty = random.randint(1, 12)
        line_total = qty * prod["prix_vente"]
        total_order_amount += line_total
        
        order_lines.append({
            "sku": prod["sku"],
            "designation": prod["designation"],
            "qty": qty,
            "prix_unitaire": prod["prix_vente"],
            "total_ligne": round(line_total, 2)
        })
        
    # Arrondir le total de la commande
    total_order_amount = round(total_order_amount, 2)
    
    # Ajouter toutes les lignes à la liste globale
    for line in order_lines:
        orders_data.append({
            "numero_commande": num_cmd,
            "date_commande": order_date.strftime("%Y-%m-%d"),
            "client": client,
            "montant_total_commande": total_order_amount,
            "sku_produit": line["sku"],
            "produit_designation": line["designation"],
            "quantite": line["qty"],
            "prix_unitaire_cad": line["prix_unitaire"],
            "sous_total_ligne_cad": line["total_ligne"]
        })

# 4. EXPORTATION EN CSV
orders_data.sort(key=lambda x: x["numero_commande"])

with open(output_file, mode="w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "numero_commande", "date_commande", "client", 
        "montant_total_commande", "sku_produit", "produit_designation", 
        "quantite", "prix_unitaire_cad", "sous_total_ligne_cad"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in orders_data:
        writer.writerow(row)

print(f"Export terminé en {round(time.time() - start_time, 2)}s ! Fichier : {output_file}")
