import csv
import os
from datetime import datetime

import streamlit as st

# ---------------- Paramètres de la banque ----------------
SOLDE_INITIAL = 150_000          # FCFA
TAUX_INTERET = 3                 # % par an
CODE_PIN = "1234"                # code secret de la carte (pour le test)
NB_ESSAIS_PIN = 3
NUMERO_CARTE = "**** **** **** 4821"
BILLETS_DISTRIBUES = [10_000, 5_000]   # billets que le DAB peut donner
MULTIPLE_RETRAIT = 5_000
PLAFOND_RETRAIT = 500_000        # maximum par retrait
MULTIPLE_DEPOT = 1_000           # le DAB n'accepte que des billets
PLAFOND_DEPOT = 600_000          # maximum par dépôt
MONTANTS_PROPOSES = [50_000, 100_000, 150_000, 200_000]
FICHIER_CSV = "operations_dab.csv"   # registre de la banque (toutes les opérations clients)
CODE_BANQUE = "admin"            # accès à l'espace banque (pour le test)

MENU = ["1. Consulter le solde", "2. Déposer de l'argent", "3. Retirer de l'argent",
        "4. Afficher les intérêts", "5. Quitter"]


# ---------------- Fonctions utilitaires ----------------
def formater(montant):
    """150000 -> '150 000 FCFA'"""
    return f"{montant:,.0f}".replace(",", " ") + " FCFA"


def repartir_billets(montant):
    """Calcule les billets à distribuer : {10000: 3, 5000: 1}"""
    repartition = {}
    reste = montant
    for billet in BILLETS_DISTRIBUES:
        nombre = reste // billet
        if nombre > 0:
            repartition[billet] = nombre
            reste -= nombre * billet
    return repartition


def nouvelle_reference(compteur):
    return datetime.now().strftime("%Y%m%d%H%M%S") + f"{compteur:03d}"


# ---------------- Fiche d'opération (reçu du client) ----------------
def creer_fiche(operation, montant, solde, reference):
    """Construit le texte de la fiche : date, heure, opération, montant, solde."""
    maintenant = datetime.now()
    lignes = [
        "=" * 40,
        "        BANQUE - FICHE D'OPÉRATION",
        "=" * 40,
        f"Date        : {maintenant.strftime('%d/%m/%Y')}",
        f"Heure       : {maintenant.strftime('%H:%M:%S')}",
        f"Carte       : {NUMERO_CARTE}",
        f"Référence   : {reference}",
        "-" * 40,
        f"Opération   : {operation}",
        f"Montant     : {montant}",
        f"Solde       : {formater(solde)}",
        "=" * 40,
        "   Merci de votre confiance.",
        "=" * 40,
    ]
    return "\n".join(lignes)


def terminer_operation(operation, montant, solde, reference):
    """Garde la fiche en mémoire pour l'afficher et proposer son téléchargement."""
    st.session_state.fiche = {"texte": creer_fiche(operation, montant, solde, reference),
                              "reference": reference}


# ---------------- Enregistrement CSV (registre de la banque) ----------------
COLONNES_CSV = ["Date", "Heure", "Référence", "Carte", "Opération",
                "Montant (FCFA)", "Statut", "Solde (FCFA)"]


def enregistrer_operation_csv(reference, operation, montant, statut, solde):
    """Ajoute automatiquement l'opération à la fin du fichier CSV de la banque.
    Le fichier est créé (avec ses titres de colonnes) s'il n'existe pas encore."""
    nouveau_fichier = not os.path.exists(FICHIER_CSV) or os.path.getsize(FICHIER_CSV) == 0
    maintenant = datetime.now()
    with open(FICHIER_CSV, "a", newline="", encoding="utf-8-sig") as fichier:
        ecrivain = csv.writer(fichier, delimiter=";")
        if nouveau_fichier:
            ecrivain.writerow(COLONNES_CSV)
        ecrivain.writerow([
            maintenant.strftime("%d/%m/%Y"),
            maintenant.strftime("%H:%M:%S"),
            reference,
            NUMERO_CARTE,
            operation,
            montant,
            statut,
            solde,
        ])


# ---------------- Fonctions demandées par l'énoncé ----------------
def consulter_solde(solde):
    """Affiche le solde."""
    st.metric("💰 Solde disponible", formater(solde))


def deposer_argent(solde, montant):
    """Vérifie le dépôt et retourne le nouveau solde."""
    if montant <= 0:
        st.error("❌ Le montant du dépôt doit être strictement positif.")
        return solde
    if montant % MULTIPLE_DEPOT != 0:
        st.error(f"❌ Le DAB n'accepte que des billets : montant multiple de {formater(MULTIPLE_DEPOT)}.")
        return solde
    if montant > PLAFOND_DEPOT:
        st.error(f"❌ Dépôt limité à {formater(PLAFOND_DEPOT)} par opération.")
        return solde
    solde = solde + montant
    st.success(f"✅ Dépôt de {formater(montant)} effectué.")
    return solde


def retirer_argent(solde, montant):
    """Vérifie le retrait et retourne le solde actualisé."""
    if montant <= 0:
        st.error("❌ Le montant du retrait doit être strictement positif.")
        return solde
    if montant % MULTIPLE_RETRAIT != 0:
        st.error(f"❌ Le DAB distribue des billets de 10 000 et 5 000 : "
                 f"montant multiple de {formater(MULTIPLE_RETRAIT)}.")
        return solde
    if montant > PLAFOND_RETRAIT:
        st.error(f"❌ Retrait limité à {formater(PLAFOND_RETRAIT)} par opération.")
        return solde
    if montant > solde:
        st.error(f"❌ Solde insuffisant. Solde disponible : {formater(solde)}.")
        return solde

    solde = solde - montant
    billets = ", ".join(f"{nombre} billet(s) de {formater(billet)}"
                        for billet, nombre in repartir_billets(montant).items())
    st.success(f"✅ Veuillez retirer vos billets : {formater(montant)}  \n💵 {billets}")
    return solde


def calculer_interets(solde, taux):
    """Retourne les intérêts annuels théoriques."""
    return solde * taux / 100


def afficher_historique(historique):
    """Affiche les opérations enregistrées."""
    st.markdown("**========== HISTORIQUE ==========**")
    if len(historique) == 0:
        st.write("Aucune opération effectuée.")
    for operation in historique:
        st.text(operation)


# =========================================================
#  ÉTAT DE LA SESSION (remplace les variables du programme console)
# =========================================================
def nouvelle_session():
    st.session_state.etape = "pin"          # pin -> menu -> fin   (ou carte_retenue)
    st.session_state.essais_restants = NB_ESSAIS_PIN
    st.session_state.solde = SOLDE_INITIAL
    st.session_state.historique = []
    st.session_state.nb_operations = 0
    st.session_state.fiche = None


if "etape" not in st.session_state:
    nouvelle_session()


def choisir_montant_propose(cle, montant):
    """Bouton de montant proposé : remplit le champ, que le client peut ensuite modifier."""
    st.session_state[cle] = montant


def saisie_montant(type_operation, cle):
    """Affiche les montants proposés + le champ modifiable. Retourne le montant saisi."""
    st.write(f"Montants proposés pour le {type_operation} :")
    colonnes = st.columns(len(MONTANTS_PROPOSES))
    for colonne, montant in zip(colonnes, MONTANTS_PROPOSES):
        colonne.button(formater(montant), key=f"{cle}_{montant}", width="stretch",
                       on_click=choisir_montant_propose, args=(cle, montant))
    return st.number_input("Montant (modifiable)", min_value=0, step=1_000,
                           value=None, placeholder="Choisissez ou saisissez un montant", key=cle)


# =========================================================
#  INTERFACE
# =========================================================
st.set_page_config(page_title="DAB - Distributeur automatique", page_icon="🏧")
st.title("🏧 Distributeur automatique de billets")

# ---------- Écran 1 : carte et code PIN ----------
if st.session_state.etape == "pin":
    st.info("💳 Carte détectée. Veuillez saisir votre code secret.")
    with st.form("form_pin", clear_on_submit=True):
        pin = st.text_input("Code secret (4 chiffres)", type="password", max_chars=4)
        valider = st.form_submit_button("Valider", type="primary")
    if valider:
        if pin == CODE_PIN:
            st.session_state.etape = "menu"
            st.rerun()
        else:
            st.session_state.essais_restants -= 1
            if st.session_state.essais_restants > 0:
                st.error(f"❌ Code incorrect. Il vous reste {st.session_state.essais_restants} essai(s).")
            else:
                enregistrer_operation_csv(nouvelle_reference(0), "Carte retenue (code PIN erroné 3 fois)",
                                          0, "Refusé", "")
                st.session_state.etape = "carte_retenue"
                st.rerun()
    st.caption("Code de test : 1234")

# ---------- Carte retenue ----------
elif st.session_state.etape == "carte_retenue":
    st.error("⛔ Code incorrect 3 fois. Votre carte est retenue par le distributeur.  \n"
             "Veuillez contacter votre agence.")
    st.button("Insérer une autre carte", on_click=nouvelle_session)

# ---------- Écran 2 : menu ----------
elif st.session_state.etape == "menu":
    choix = st.radio("========== DISTRIBUTEUR AUTOMATIQUE ==========", MENU,
                     key="choix_menu", on_change=lambda: st.session_state.update(fiche=None))
    st.divider()
    solde = st.session_state.solde
    heure = datetime.now().strftime("%H:%M:%S")

    if choix == MENU[0]:
        if st.button("Afficher le solde", type="primary"):
            consulter_solde(solde)
            st.session_state.historique.append(f"[{heure}] Consultation du solde")
            st.session_state.nb_operations += 1
            reference = nouvelle_reference(st.session_state.nb_operations)
            enregistrer_operation_csv(reference, "Consultation du solde", 0, "Effectué", solde)
            terminer_operation("Consultation du solde", "-", solde, reference)

    elif choix == MENU[1]:
        montant = saisie_montant("dépôt", "montant_depot")
        st.caption(f"Billets uniquement (multiple de {formater(MULTIPLE_DEPOT)}) — "
                   f"plafond : {formater(PLAFOND_DEPOT)}")
        if st.button("Valider le dépôt", type="primary"):
            if montant is None:
                st.error("❌ Choisissez ou saisissez un montant.")
            else:
                nouveau_solde = deposer_argent(solde, montant)
                st.session_state.nb_operations += 1
                reference = nouvelle_reference(st.session_state.nb_operations)
                if nouveau_solde != solde:
                    st.session_state.solde = nouveau_solde
                    st.session_state.historique.append(f"[{heure}] Dépôt : +{formater(montant)}")
                    enregistrer_operation_csv(reference, "Dépôt", montant, "Effectué", nouveau_solde)
                    terminer_operation("Dépôt", f"+{formater(montant)}", nouveau_solde, reference)
                else:
                    st.session_state.historique.append(f"[{heure}] Dépôt refusé : {formater(montant)}")
                    enregistrer_operation_csv(reference, "Dépôt", montant, "Refusé", solde)

    elif choix == MENU[2]:
        montant = saisie_montant("retrait", "montant_retrait")
        st.caption(f"Billets de 10 000 et 5 000 (multiple de {formater(MULTIPLE_RETRAIT)}) — "
                   f"plafond : {formater(PLAFOND_RETRAIT)}")
        if st.button("Valider le retrait", type="primary"):
            if montant is None:
                st.error("❌ Choisissez ou saisissez un montant.")
            else:
                nouveau_solde = retirer_argent(solde, montant)
                st.session_state.nb_operations += 1
                reference = nouvelle_reference(st.session_state.nb_operations)
                if nouveau_solde != solde:
                    st.session_state.solde = nouveau_solde
                    st.session_state.historique.append(f"[{heure}] Retrait : -{formater(montant)}")
                    enregistrer_operation_csv(reference, "Retrait", -montant, "Effectué", nouveau_solde)
                    terminer_operation("Retrait", f"-{formater(montant)}", nouveau_solde, reference)
                else:
                    st.session_state.historique.append(f"[{heure}] Retrait refusé : {formater(montant)}")
                    enregistrer_operation_csv(reference, "Retrait", -montant, "Refusé", solde)

    elif choix == MENU[3]:
        if st.button("Calculer les intérêts", type="primary"):
            interets = calculer_interets(solde, TAUX_INTERET)
            st.metric(f"📈 Intérêts annuels théoriques ({TAUX_INTERET} %)", formater(interets))
            st.caption(f"Calculés sur un solde de {formater(solde)}")
            st.session_state.historique.append(f"[{heure}] Intérêts calculés : {formater(interets)}")
            st.session_state.nb_operations += 1
            reference = nouvelle_reference(st.session_state.nb_operations)
            enregistrer_operation_csv(reference, f"Intérêts calculés ({TAUX_INTERET} %)",
                                      round(interets), "Effectué", solde)
            terminer_operation(f"Intérêts annuels ({TAUX_INTERET} %)", formater(interets), solde, reference)

    elif choix == MENU[4]:
        st.write("Voulez-vous terminer et reprendre votre carte ?")
        if st.button("Quitter", type="primary"):
            st.session_state.etape = "fin"
            st.session_state.fiche = None
            st.rerun()

    # Fiche de la dernière opération réussie
    if st.session_state.fiche is not None:
        st.subheader("🧾 Fiche d'opération")
        st.code(st.session_state.fiche["texte"], language=None)
        st.download_button("📥 Télécharger la fiche", st.session_state.fiche["texte"],
                           file_name=f"fiche_{st.session_state.fiche['reference']}.txt",
                           mime="text/plain")

# ---------- Écran 3 : fin de session ----------
elif st.session_state.etape == "fin":
    afficher_historique(st.session_state.historique)
    st.markdown(f"**Solde final : {formater(st.session_state.solde)}**")
    st.success("💳 Veuillez reprendre votre carte. Merci de votre visite. À bientôt !")
    st.button("Nouveau client (insérer une carte)", on_click=nouvelle_session, type="primary")

# =========================================================
#  ESPACE BANQUE (registre CSV) - accès protégé
# =========================================================
with st.sidebar:
    st.header("🏦 Espace banque")
    code = st.text_input("Code d'accès banque", type="password", key="code_banque")
    if code == CODE_BANQUE:
        if os.path.exists(FICHIER_CSV):
            with open(FICHIER_CSV, encoding="utf-8-sig") as fichier:
                lignes = list(csv.DictReader(fichier, delimiter=";"))
            st.caption(f"{len(lignes)} opération(s) enregistrée(s)")
            st.dataframe(lignes, hide_index=True)
            with open(FICHIER_CSV, "rb") as fichier:
                st.download_button("📥 Télécharger le registre CSV", fichier.read(),
                                   file_name=FICHIER_CSV, mime="text/csv")
        else:
            st.info("Aucune opération enregistrée pour le moment.")
    elif code:
        st.error("Code incorrect.")
    st.caption("Code de test : admin")