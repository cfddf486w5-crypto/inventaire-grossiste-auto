# Deux jeux de données, deux usages

## Le jeu de démonstration — `demo_inventaire.csv` + `demo_commandes.csv`

240 articles, 3 000 commandes. C'est celui à montrer.

Ses adresses viennent du plan d'exemple de l'application, exportées par
l'application elle-même : rien n'y est écrit de mémoire. Résultat, dans
l'écran de réimplantation : **240 articles sur 240 rattachés, aucun orphelin,
aucun avertissement.**

Le rangement de départ est délibérément mauvais — les plus demandés au fond et
en hauteur, les dormants sur les meilleures places — pour que le plan de
réimplantation ait quelque chose à corriger. Un entrepôt déjà bien rangé ne
démontrerait rien.

Marche à suivre :

1. Ouvrir l'application, écran **Plan de réimplantation**.
2. Déposer `demo_inventaire.csv` dans *Inventaire*.
3. Déposer `demo_commandes.csv` dans *Historique des commandes*.

## Le jeu à l'échelle — `inventaire_grossiste_auto_50k.csv`, `inventaire_grossiste_auto_detaille.csv`, `journal_commandes.csv`

50 000 articles sur environ 18 000 adresses. C'est un volume de vrai grossiste,
et il sert à éprouver le lecteur — pas à démontrer.

L'application l'annonce d'ailleurs franchement : ces adresses ne suivent pas la
convention du site (`a1a/02/a/02`), et 50 000 articles ne tiennent pas dans un
plan de 240 alvéoles. Les deux avertissements sont exacts.

Note : `inventaire_grossiste_auto_50k.csv` ne porte ni poids, ni dimensions, ni
fréquence de prélèvement. La fréquence se retrouve en déposant
`journal_commandes.csv` par-dessus. Le poids et les dimensions ne sont que dans
`inventaire_grossiste_auto_detaille.csv`, dont les SKU appartiennent hélas à un
autre univers : les deux inventaires ne partagent aucune référence.

## Régénérer

```bash
python3 generate_orders.py          # journal du jeu à l'échelle + classes ABC
python3 generate_demo_entrepot.py   # jeu de démonstration
```

`generate_demo_entrepot.py` lit `adresses_plan_exemple.csv`. Ce fichier est
produit par l'application : écran **Plan de réimplantation**, lien
**« Adresses du plan »**. Si le plan d'exemple change, réexportez-le avant de
relancer le script, sinon les adresses du jeu de démonstration ne pointeront
plus nulle part.

Les deux scripts sont graînés : deux exécutions donnent le même résultat.
