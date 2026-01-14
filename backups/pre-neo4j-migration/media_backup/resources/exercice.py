""" 
exercice: on veut calculer la prime d'un employé, pour cela il faut
respecter les régles métiers suivantes:
-regle1: l'employé peut avoir une prime s'il a depassé 6 ans 
d'ancienneté et son rendement est  de 80%, sa prime est de 12000
-regle2: il a droit à une prime de 5000 si l'une des conditions
précédentes est respectée
regle3: les cadres ont une prime supplémentair de 2500 

"""
nbranc=int(input("Entrez nbr année:"))
rendement=int(input("Entrez le rendement:"))
cadre=input("Cadre oui/non:")
prime=0
if nbranc>6 and rendement==80:
    prime+=12000
elif nbranc>6 or rendement==80:
    prime+=5000

if cadre=="oui":
    prime+=2500

print("La prime est:",prime)