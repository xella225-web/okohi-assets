import shutil, py_compile, os
from datetime import datetime

def backup(path):
    b = path + ".bak." + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(path, b)
    return b

# ══════════════════════════════════════════════
# 1. QUESTIONNAIRE — Question poids haltères
# ══════════════════════════════════════════════
Q = "/home/ubuntu/okohi_system/questionnaire/questionnaire.py"
with open(Q) as f:
    content = f.read()
b = backup(Q)
original = content

old1 = '("materiel_dispo","materiel","Quel equipement tu as ? (tape OK quand fini)",["Salle de sport complete","Halteres / Barres","Bandes de resistance","Poids du corps uniquement","Corde a sauter"]),'
new1 = old1 + '\n    ("poids_halteres","halteres_poids","Quel(s) poids tu as pour tes halteres ? (ex: 2x5kg, 2x8kg - ou tape AUCUN)",None),'
if old1 in content:
    content = content.replace(old1, new1)
    print("OK1 questionnaire - question halteres ajoutee")
else:
    print("ERR1 questionnaire - pattern materiel non trouve")

old2 = '        if qtype == "blessure":\n            if texte.lower() in ["aucune"'
new2 = '''        if qtype == "halteres_poids":
            import json as _jh
            mat = s["reponses"].get("materiel_dispo", "[]")
            if isinstance(mat, str):
                try: mat = _jh.loads(mat)
                except: mat = []
            a_halteres = any("halt" in m.lower() or "barre" in m.lower() for m in mat)
            if not a_halteres:
                s["reponses"]["poids_halteres"] = "Aucun"
                s["etape"] += 1
                return self._next(tid)
            t = texte.strip().lower()
            s["reponses"]["poids_halteres"] = "Aucun" if t in ["aucun","non","pas","0"] else texte.strip()
            s["etape"] += 1
            return self._next(tid)

        if qtype == "blessure":
            if texte.lower() in ["aucune"'''

if old2 in content:
    content = content.replace(old2, new2)
    print("OK2 questionnaire - handler halteres ajoute")
else:
    print("ERR2 questionnaire - pattern blessure non trouve")
    idx = content.find('if qtype == "blessure"')
    print("Contexte:", repr(content[idx:idx+60]))

old3 = '        return texte_q, None, False\n\n    def _generer_recap'
new3 = '''        if qtype == "halteres_poids":
            import json as _jh2
            mat = s["reponses"].get("materiel_dispo", "[]")
            if isinstance(mat, str):
                try: mat = _jh2.loads(mat)
                except: mat = []
            if not any("halt" in m.lower() or "barre" in m.lower() for m in mat):
                s["reponses"]["poids_halteres"] = "Aucun"
                s["etape"] += 1
                return self._next(tid)
            return texte_q, [["2x2kg","2x4kg","2x6kg"],["2x8kg","2x10kg","2x12kg"],["2x15kg","2x20kg","Autre"]], False
        return texte_q, None, False

    def _generer_recap'''

if old3 in content:
    content = content.replace(old3, new3)
    print("OK3 questionnaire - _next() mis a jour")
else:
    print("ERR3 questionnaire - pattern _next non trouve")

old4 = '"Materiel : " + mat_str,'
new4 = '"Materiel : " + mat_str,\n            "Halteres : " + r.get("poids_halteres", "Non specifie"),'
if old4 in content:
    content = content.replace(old4, new4)
    print("OK4 questionnaire - recap mis a jour")
else:
    print("ERR4 questionnaire - pattern recap non trouve")

if content != original:
    with open(Q, "w") as f:
        f.write(content)
    try:
        py_compile.compile(Q, doraise=True)
        print("OK questionnaire.py syntaxe valide")
    except py_compile.PyCompileError as e:
        print("ERR syntaxe:", e)
        shutil.copy(b, Q)
        print("Backup restaure")
else:
    print("WARN questionnaire - aucune modif")

# ══════════════════════════════════════════════
# 2. IA_NUTRITION — TMB/TDEE correct + halal strict
# ══════════════════════════════════════════════
N = "/home/ubuntu/okohi_system/generator/ia_nutrition.py"
with open(N) as f:
    ncontent = f.read()
nb = backup(N)
noriginal = ncontent

old_n1 = "    prompt = (\n        \"Tu es un nutritionniste expert. Genere un plan alimentaire hebdomadaire complet et personnalise.\\n\\n\""
new_n1 = '''    # Calcul TMB Harris-Benedict revise
    try:
        p = float(poids); t2 = float(taille); a = float(age)
        if sexe == "femme":
            tmb = 10*p + 6.25*t2 - 5*a - 161
        else:
            tmb = 10*p + 6.25*t2 - 5*a + 5
        seances_tot = int(client.get("seances_semaine", 3))
        if seances_tot <= 1: mult = 1.2
        elif seances_tot <= 2: mult = 1.375
        elif seances_tot <= 4: mult = 1.55
        else: mult = 1.725
        tdee = tmb * mult
        if programme == "perte_poids": kcal_cible = round(tdee - 400)
        elif programme == "seche": kcal_cible = round(tdee - 500)
        elif programme == "masse": kcal_cible = round(tdee + 300)
        else: kcal_cible = round(tdee)
        prot_g = round(float(poids) * 1.8)
        lip_g = round(kcal_cible * 0.25 / 9)
        gluc_g = round((kcal_cible - prot_g*4 - lip_g*9) / 4)
        macros_calcules = {"calories": kcal_cible, "proteines": prot_g, "glucides": gluc_g, "lipides": lip_g}
        print(f"TMB={round(tmb)} TDEE={round(tdee)} Cible={kcal_cible}kcal")
    except Exception as e:
        print(f"Erreur calcul TMB: {e}")
        macros_calcules = None

    # Mots interdits selon restriction
    mots_interdits = []
    restr_low = str(restrictions).lower()
    if "halal" in restr_low:
        mots_interdits = ["porc","jambon","lard","bacon","chorizo","saucisson","alcool","vin","biere","gelatine","rillettes","andouille"]
    if "vegetarien" in restr_low or "vegan" in restr_low:
        mots_interdits += ["poulet","boeuf","agneau","dinde","poisson","crevettes","saumon","thon"]
    if "lactose" in restr_low:
        mots_interdits += ["lait de vache","fromage","yaourt classique","beurre","creme fraiche"]

    interdits_str = ""
    if mots_interdits:
        interdits_str = "MOTS ABSOLUMENT INTERDITS dans toute la nutrition (meme avec halal ou autre qualificatif) : " + ", ".join(mots_interdits) + ". Si tu veux du jambon utilise UNIQUEMENT blanc de dinde ou escalope de poulet. JAMAIS le mot jambon meme avec halal.\\n\\n"

    macros_str = ""
    if macros_calcules:
        macros_str = (f"MACROS OBLIGATOIRES (calcules Harris-Benedict) : {macros_calcules['calories']} kcal, "
                     f"{macros_calcules['proteines']}g proteines, {macros_calcules['glucides']}g glucides, "
                     f"{macros_calcules['lipides']}g lipides. Respecte EXACTEMENT ces valeurs.\\n\\n")

    prompt = (
        "Tu es un nutritionniste expert. Genere un plan alimentaire hebdomadaire complet et personnalise.\\n\\n"'''

if old_n1 in ncontent:
    ncontent = ncontent.replace(old_n1, new_n1)
    print("OK5 ia_nutrition - calcul TMB ajoute")
else:
    print("ERR5 ia_nutrition - pattern prompt non trouve")

old_n2 = '        "REGLES ABSOLUES :\\n"'
new_n2 = ('        + macros_str\n'
          '        + interdits_str\n'
          '        + "REGLES ABSOLUES :\\n"')
if old_n2 in ncontent:
    ncontent = ncontent.replace(old_n2, new_n2)
    print("OK6 ia_nutrition - macros et interdits injectes dans prompt")
else:
    print("ERR6 ia_nutrition - pattern REGLES non trouve")

old_n3 = '    from generator.nutrition import generer_nutrition as gen_fallback\n    fallback = gen_fallback(client)\n    macros = fallback.get("macros", {"calories":1850,"proteines":130,"glucides":180,"lipides":55})'
new_n3 = ('    from generator.nutrition import generer_nutrition as gen_fallback\n'
          '    fallback = gen_fallback(client)\n'
          '    macros = macros_calcules if macros_calcules else fallback.get("macros", {"calories":1850,"proteines":130,"glucides":180,"lipides":55})')
if old_n3 in ncontent:
    ncontent = ncontent.replace(old_n3, new_n3)
    print("OK7 ia_nutrition - macros calcules utilises en priorite")
else:
    print("ERR7 ia_nutrition - pattern fallback macros non trouve")

if ncontent != noriginal:
    with open(N, "w") as f:
        f.write(ncontent)
    try:
        py_compile.compile(N, doraise=True)
        print("OK ia_nutrition.py syntaxe valide")
    except py_compile.PyCompileError as e:
        print("ERR syntaxe:", e)
        shutil.copy(nb, N)
        print("Backup restaure")
else:
    print("WARN ia_nutrition - aucune modif")

# ══════════════════════════════════════════════
# 3. IA_PROGRAMME — Table materiel + regresssions debutants
# ══════════════════════════════════════════════
P = "/home/ubuntu/okohi_system/generator/ia_programme.py"
with open(P) as f:
    pcontent = f.read()
pb = backup(P)
poriginal = pcontent

table_materiel = '''
# Table OKOHI : poids minimum efficace et alternatives
MATERIEL_TABLE = {
    # exercice : (poids_min_femme_kg, poids_min_homme_kg, alternative_sans_poids)
    "romanian-deadlift":    (8,  12, "Good morning poids du corps"),
    "hip-thrust":           (10, 15, "Glute bridge poids du corps"),
    "fentes-bulgares":      (6,  8,  "Fentes classiques poids du corps"),
    "goblet-squat":         (6,  10, "Squat poids du corps"),
    "developpe-militaire":  (4,  6,  "Pike push-up"),
    "rowing-halteres":      (4,  8,  "Rowing bandes de resistance"),
    "curl-biceps":          (4,  6,  "Curl bandes de resistance"),
    "extension-triceps":    (4,  6,  "Dips sur chaise"),
    "souleve-de-terre":     (10, 15, "Romanian deadlift poids du corps"),
    "developpe-couche":     (6,  10, "Pompes sur genoux"),
    "kettlebell-swing":     (8,  12, "Hip hinge poids du corps"),
}

REGRESSIONS_DEBUTANT = {
    "pompes":            "Pompes sur les genoux (meme mouvement, moins de charge)",
    "pompes-declinees":  "Pompes classiques sur les genoux",
    "pompes-diamant":    "Pompes serrees sur les genoux",
    "fentes-bulgares":   "Fentes classiques poids du corps",
    "squat-jump":        "Squat poids du corps (sans saut)",
    "burpees":           "Burpee sans saut (monter lentement)",
    "plank":             "Plank sur les genoux (30 sec)",
    "mountain-climbers": "Mountain climbers lents (1 sec par genou)",
    "dead-bug":          "Dead bug avec jambes posees au sol",
    "hip-thrust":        "Glute bridge poids du corps",
    "romanian-deadlift": "Good morning poids du corps",
    "box-jump":          "Step-up sur marche",
    "fentes-halteres":   "Fentes poids du corps",
}

SEUILS_PROGRESSION = {
    "pompes sur les genoux": "Quand tu fais 3x12 sans effort -> pompes classiques le mois prochain",
    "squat poids du corps":  "Quand tu fais 3x15 fluide -> squat avec halteres le mois prochain",
    "glute bridge":          "Quand tu fais 3x20 en contractant fort -> hip thrust avec haltere le mois prochain",
    "plank sur les genoux":  "Quand tu tiens 45 sec sans trembler -> plank classique le mois prochain",
    "fentes classiques":     "Quand tu fais 3x10/jambe stable -> fentes bulgares le mois prochain",
}

'''

if "MATERIEL_TABLE" not in pcontent:
    insert_after = "CLAUDE_URL = "
    idx = pcontent.find(insert_after)
    if idx > 0:
        end_line = pcontent.find("\n", idx) + 1
        pcontent = pcontent[:end_line] + table_materiel + pcontent[end_line:]
        print("OK8 ia_programme - table materiel + regressions ajoutees")
    else:
        print("ERR8 ia_programme - point insertion non trouve")
else:
    print("INFO8 ia_programme - table deja presente")

old_p1 = '    prompt = construire_prompt_programme(client, exos_dispo, semaine, nb_seances_solo=nb_seances_solo)'
new_p1 = '''    # Construire contexte materiel et regressions
    import json as _jmat
    poids_halt = client.get("poids_halteres", "Aucun") or "Aucun"
    sexe_mat = str(client.get("sexe","homme")).lower()
    mat_list = client.get("materiel_dispo", "[]")
    if isinstance(mat_list, str):
        try: mat_list = _jmat.loads(mat_list)
        except: mat_list = []
    a_salle = any("salle" in m.lower() for m in mat_list)
    a_halteres = any("halt" in m.lower() or "barre" in m.lower() for m in mat_list)
    a_bandes = any("band" in m.lower() or "resistance" in m.lower() for m in mat_list)
    niv_client = str(client.get("niveau","debutant")).lower()
    is_debutant = niv_client in ["debutant","tres_debutant"]

    # Calculer poids halteres disponible
    poids_halt_kg = 0
    if poids_halt and poids_halt != "Aucun":
        import re as _re
        nums = _re.findall(r"\\d+", poids_halt)
        if nums: poids_halt_kg = int(nums[-1])

    # Construire instructions materiel pour le prompt
    mat_instructions = []
    if not a_salle:
        mat_instructions.append("PAS de salle de sport - INTERDIT: presse a cuisses, cable, machines, barre olympique")
    if a_halteres and poids_halt_kg > 0:
        mat_instructions.append(f"Halteres disponibles: {poids_halt}. Verifie que chaque exercice est efficace avec ce poids.")
        for exo, (pmin_f, pmin_h, alt) in MATERIEL_TABLE.items():
            pmin = pmin_f if sexe_mat == "femme" else pmin_h
            if poids_halt_kg < pmin:
                mat_instructions.append(f"- {exo}: poids insuffisant ({poids_halt_kg}kg < {pmin}kg min) -> utilise '{alt}' a la place")
    if not a_halteres:
        mat_instructions.append("PAS d halteres - utiliser uniquement poids du corps et bandes de resistance")
    if a_bandes:
        mat_instructions.append("Bandes de resistance disponibles - peut remplacer certains exercices halteres")

    # Instructions debutant
    regr_instructions = []
    if is_debutant:
        regr_instructions.append("CLIENT DEBUTANT - REGLES STRICTES:")
        regr_instructions.append("- Semaines 1-2: version REGRESSION de chaque exercice (voir liste)")
        regr_instructions.append("- Semaines 3-4: version STANDARD avec indication du seuil de progression")
        regr_instructions.append("- JAMAIS de variante difficile pour un debutant")
        regr_instructions.append("- Ajoute un seuil de progression chiffre pour chaque exercice principal")
        for exo, regr in REGRESSIONS_DEBUTANT.items():
            regr_instructions.append(f"  {exo} -> {regr}")

    client["_mat_instructions"] = "\\n".join(mat_instructions)
    client["_regr_instructions"] = "\\n".join(regr_instructions)

    prompt = construire_prompt_programme(client, exos_dispo, semaine, nb_seances_solo=nb_seances_solo)'''

if old_p1 in pcontent:
    pcontent = pcontent.replace(old_p1, new_p1)
    print("OK9 ia_programme - contexte materiel et regressions injectes")
else:
    print("ERR9 ia_programme - pattern prompt non trouve")

old_p2 = '    prompt = "Tu es un coach sportif expert. Genere un programme de " + str(nb_seances_solo) + " seances en AUTONOMIE pour ce client. Ces seances sont uniquement pour le travail solo sans coach.\\n\\n"'
new_p2 = ('    prompt = "Tu es un coach sportif expert. Genere un programme de " + str(nb_seances_solo) + " seances en AUTONOMIE pour ce client. Ces seances sont uniquement pour le travail solo sans coach.\\n\\n"\n'
          '    mat_inst = client.get("_mat_instructions","")\n'
          '    regr_inst = client.get("_regr_instructions","")\n'
          '    if mat_inst: prompt += "CONTRAINTES MATERIEL STRICTES:\\n" + mat_inst + "\\n\\n"\n'
          '    if regr_inst: prompt += regr_inst + "\\n\\n"')

if old_p2 in pcontent:
    pcontent = pcontent.replace(old_p2, new_p2)
    print("OK10 ia_programme - instructions injectees dans prompt Claude")
else:
    print("ERR10 ia_programme - pattern prompt Claude non trouve")

if pcontent != poriginal:
    with open(P, "w") as f:
        f.write(pcontent)
    try:
        py_compile.compile(P, doraise=True)
        print("OK ia_programme.py syntaxe valide")
    except py_compile.PyCompileError as e:
        print("ERR syntaxe:", e)
        shutil.copy(pb, P)
        print("Backup restaure")
else:
    print("WARN ia_programme - aucune modif")

# ══════════════════════════════════════════════
# 4. GENERATOR/__init__.py — Analyse post-generation + rapport Telegram + historique
# ══════════════════════════════════════════════
G = "/home/ubuntu/okohi_system/generator/__init__.py"
with open(G) as f:
    gcontent = f.read()
gb = backup(G)
goriginal = gcontent

analyse_code = '''
def _analyser_site(html: str, client: dict, url: str) -> dict:
    """Analyse le site genere et retourne un rapport."""
    import re, requests as _req
    rapport = {"score": 100, "ok": [], "warns": [], "errors": []}
    prenom = client.get("prenom","?")

    # 1. Verifier restrictions alimentaires
    restrictions = str(client.get("restrictions_alim","")).lower()
    mots_interdits_map = {
        "halal": ["porc","jambon","lard","bacon","chorizo","saucisson"],
        "vegetarien": ["poulet","boeuf","agneau"],
        "sans lactose": ["lait de vache","fromage rape"],
    }
    for restr, mots in mots_interdits_map.items():
        if restr in restrictions:
            for mot in mots:
                if mot in html.lower():
                    rapport["errors"].append(f"Aliment interdit detecte: '{mot}' (restriction: {restr})")
                    rapport["score"] -= 15

    if not rapport["errors"]:
        rapport["ok"].append("Restrictions alimentaires respectees")

    # 2. Verifier images
    imgs = re.findall(r'data-img="([^"]+)"', html)
    broken = []
    for img_url in imgs[:15]:
        try:
            r = _req.head(img_url, timeout=4)
            if r.status_code != 200:
                broken.append(img_url.split("/")[-1])
        except:
            broken.append(img_url.split("/")[-1])
    if broken:
        rapport["warns"].append(f"{len(broken)} image(s) cassee(s): {', '.join(broken[:5])}")
        rapport["score"] -= len(broken) * 3
    else:
        rapport["ok"].append(f"Toutes les images OK ({len(imgs)} exercices)")

    # 3. Verifier planning
    jours_coach = client.get("jours_coach","[]")
    jours_solo = client.get("jours_solo","[]")
    import json as _j
    if isinstance(jours_coach, str):
        try: jours_coach = _j.loads(jours_coach)
        except: jours_coach = []
    if isinstance(jours_solo, str):
        try: jours_solo = _j.loads(jours_solo)
        except: jours_solo = []
    for jour in jours_solo:
        if jour not in html.lower():
            rapport["warns"].append(f"Jour solo '{jour}' absent du planning")
            rapport["score"] -= 10
    if not rapport["warns"] or all("image" in w for w in rapport["warns"]):
        rapport["ok"].append("Planning coherent")

    # 4. Verifier exercices salle sans salle
    mat_list = client.get("materiel_dispo","[]")
    if isinstance(mat_list, str):
        try: mat_list = _j.loads(mat_list)
        except: mat_list = []
    a_salle = any("salle" in m.lower() for m in mat_list)
    if not a_salle and "presse" in html.lower():
        rapport["errors"].append("Exercice salle detecte (presse) mais client sans salle")
        rapport["score"] -= 20
    elif not a_salle:
        rapport["ok"].append("Exercices compatibles avec materiel")

    rapport["score"] = max(0, rapport["score"])
    return rapport


def _envoyer_rapport_telegram(client: dict, url: str, rapport: dict):
    """Envoie le rapport de generation sur Telegram."""
    import os as _os, requests as _req
    token = _os.getenv("BOT_TOKEN_PRIVE","")
    alex_id = _os.getenv("ALEX_TELEGRAM_ID","5966402999")
    if not token: return

    prenom = client.get("prenom","?")
    score = rapport["score"]
    emoji_score = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"

    lines = [f"📊 *Site {prenom} genere* — Score {emoji_score} {score}/100", ""]
    for ok in rapport["ok"]:
        lines.append(f"✅ {ok}")
    for w in rapport["warns"]:
        lines.append(f"⚠️ {w}")
    for e in rapport["errors"]:
        lines.append(f"❌ {e}")
    lines += ["", f"🔗 {url}"]

    msg = "\\n".join(lines)
    keyboard = {
        "inline_keyboard": [[
            {"text": "🔄 Regenerer", "callback_data": f"regen_{prenom.lower()}"},
            {"text": "✅ Valider", "callback_data": f"valider_{prenom.lower()}"}
        ]]
    }
    try:
        _req.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": int(alex_id), "text": msg, "parse_mode": "Markdown",
                  "reply_markup": keyboard, "disable_web_page_preview": True},
            timeout=10
        )
    except Exception as e:
        print(f"Erreur envoi rapport Telegram: {e}")


def _sauvegarder_version(client: dict, html: str, url: str):
    """Garde l ancienne version pendant 7 jours."""
    import json as _j
    from datetime import datetime, timedelta
    prenom = client.get("prenom","client").lower()
    hist_dir = SITES_DIR / "historique"
    hist_dir.mkdir(exist_ok=True)

    # Nettoyer versions > 7 jours
    for old_file in hist_dir.glob("*.html"):
        try:
            ts = float(old_file.stem.split("_")[-1])
            if datetime.now().timestamp() - ts > 7 * 86400:
                old_file.unlink()
        except: pass

    # Sauvegarder version actuelle
    ts = str(int(datetime.now().timestamp()))
    version_path = hist_dir / f"{prenom}_{ts}.html"
    version_path.write_text(html, encoding="utf-8")

    # Mettre a jour index
    index_path = hist_dir / "index.json"
    try:
        index = _j.loads(index_path.read_text()) if index_path.exists() else {}
    except: index = {}
    if prenom not in index: index[prenom] = []
    index[prenom].append({"ts": ts, "url": url, "file": str(version_path)})
    index[prenom] = index[prenom][-5:]  # garder 5 versions max
    index_path.write_text(_j.dumps(index, ensure_ascii=False, indent=2))

'''

if "_analyser_site" not in gcontent:
    old_g = "def generer_et_deployer"
    if old_g in gcontent:
        gcontent = gcontent.replace(old_g, analyse_code + "\ndef generer_et_deployer", 1)
        print("OK11 generator - fonctions analyse + rapport + historique ajoutees")
    else:
        print("ERR11 generator - point insertion non trouve")
else:
    print("INFO11 generator - fonctions deja presentes")

old_g2 = "    if url:\n        from database.init_db import upsert_client"
new_g2 = '''    if url:
        # Sauvegarder version avant mise a jour
        try:
            _sauvegarder_version(client, html, url)
        except Exception as e:
            print(f"Warn historique: {e}")

        # Analyser le site genere
        try:
            rapport = _analyser_site(html, client, url)
            _envoyer_rapport_telegram(client, url, rapport)
            print(f"Score qualite: {rapport['score']}/100")
        except Exception as e:
            print(f"Warn analyse: {e}")

        from database.init_db import upsert_client'''

if old_g2 in gcontent:
    gcontent = gcontent.replace(old_g2, new_g2)
    print("OK12 generator - analyse + rapport integres dans generer_et_deployer")
else:
    print("ERR12 generator - pattern if url non trouve")

if gcontent != goriginal:
    with open(G, "w") as f:
        f.write(gcontent)
    try:
        py_compile.compile(G, doraise=True)
        print("OK generator/__init__.py syntaxe valide")
    except py_compile.PyCompileError as e:
        print("ERR syntaxe:", e)
        shutil.copy(gb, G)
        print("Backup restaure")
else:
    print("WARN generator - aucune modif")

print("")
print("=== PATCH V4 TERMINE ===")
