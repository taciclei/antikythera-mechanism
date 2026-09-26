# -*- coding: utf-8 -*-
"""Units de synthèse : texte original (sous-titres) et texte envoyé au TTS.
pause = silence après l'unité (s), à l'intérieur du chapitre."""
import json, pathlib

NARR = pathlib.Path('/Users/tsousa/antikythera/build/out/explainer/narration.txt')

U = [
 # chapitre 1
 [
  ("Il y a plus de deux mille ans, quelqu'un a enfermé le ciel dans une boîte : éclipses, phases de la Lune, planètes, et même les Jeux olympiques.",
   "Il y a plus de deux mille ans, quelqu'un a enfermé le ciel dans une boîte : éclipses, phases de la Lune, planètes, et même les Jeux olympiques.", 0.35),
  ("En 1900, des pêcheurs d'éponges découvrent l'épave d'Anticythère.",
   "En mille neuf cent, des pêcheurs d'éponges découvrent l'épave d'Anticythère.", 0.3),
  ("En 1902, sur un bloc de bronze rongé, apparaît une roue dentée.",
   "En mille neuf cent deux, sur un bloc de bronze rongé, apparaît une roue dentée.", 0.4),
  ("Apprenons à lire cette machine.",
   "Apprenons à lire cette machine.", 0.0),
 ],
 # chapitre 2
 [
  ("Voici notre reconstruction.", "Voici notre reconstruction.", 0.3),
  ("Sur le côté, une manivelle.", "Sur le côté, une manivelle.", 0.3),
  ("Tournez-la : toutes les aiguilles avancent ensemble.", "Tournez-la : toutes les aiguilles avancent ensemble.", 0.3),
  ("En avant, le temps passe ; en arrière, il remonte.", "En avant, le temps passe ; en arrière, il remonte.", 0.35),
  ("Un peu plus de quatre tours et demi : une année.", "Un peu plus de quatre tours et demi : une année.", 0.0),
 ],
 # chapitre 3
 [
  ("Devant, deux anneaux : le calendrier égyptien de trois cent soixante-cinq jours, et le zodiaque.",
   "Devant, deux anneaux : le calendrier égyptien de trois cent soixante-cinq jours, et le zodiaque.", 0.3),
  ("La sphère dorée, c'est le Soleil : il donne la date et son signe.",
   "La sphère dorée, c'est le Soleil : il donne la date et son signe.", 0.3),
  ("La Lune fait le tour en un mois, à vitesse variable, comme la vraie.",
   "La Lune fait le tour en un mois, à vitesse variable, comme la vraie.", 0.3),
  ("Sa petite boule montre la phase.", "Sa petite boule montre la phase.", 0.35),
  ("Aiguilles superposées : noire, nouvelle lune.", "Aiguilles superposées : noire, nouvelle lune.", 0.3),
  ("Opposées : blanche… pleine lune.", "Opposées : blanche… pleine lune.", 0.0),
 ],
 # chapitre 4
 [
  ("Autour du centre, cinq petites sphères : les planètes, lues sur le zodiaque.",
   "Autour du centre, cinq petites sphères : les planètes, lues sur le zodiaque.", 0.3),
  ("Leurs engrenages ont presque tous disparu : c'est une reconstruction, une hypothèse.",
   "Leurs engrenages ont presque tous disparu : c'est une reconstruction, une hypothèse.", 0.35),
  ("Regardez Mars : sa sphère s'arrête… puis recule, comme dans le ciel quand la Terre dépasse Mars.",
   "Regardez Mars : sa sphère s'arrête… puis recule, comme dans le ciel quand la Terre dépasse Mars.", 0.0),
 ],
 # chapitre 5
 [
  ("Retournons la machine.", "Retournons la machine.", 0.3),
  ("En haut, une spirale de deux cent trente-cinq mois : dix-neuf ans.",
   "En haut, une spirale de deux cent trente-cinq mois : dix-neuf ans.", 0.3),
  ("Chaque case, un mois, avec son nom.", "Chaque case, un mois, avec son nom.", 0.3),
  ("Dedans, un petit cadran fait un tour en quatre ans.", "Dedans, un petit cadran fait un tour en quatre ans.", 0.35),
  ("Tournons… Olympia !", "Tournons… Olympia !", 0.3),
  ("Cette année, les Jeux olympiques.", "Cette année, les Jeux olympiques.", 0.25),
  ("L'année, pas le jour.", "L'année, pas le jour.", 0.0),
 ],
 # chapitre 6
 [
  ("En bas, le Saros : deux cent vingt-trois mois, puis les éclipses reviennent.",
   "En bas, le Saros : deux cent vingt-trois mois, puis les éclipses reviennent.", 0.3),
  ("La plupart des cases sont vides.", "La plupart des cases sont vides.", 0.35),
  ("Tournons… Une case gravée !", "Tournons… Une case gravée !", 0.3),
  ("Sigma : éclipse de Lune.", "Sigma : éclipse de Lune.", 0.25),
  ("Êta : de Soleil.", "Êta : de Soleil.", 0.3),
  ("Puis l'heure ; ce cadran y ajoute zéro, huit ou seize heures.",
   "Puis l'heure ; ce cadran y ajoute zéro, huit ou seize heures.", 0.35),
  ("Devant, la pleine lune tombe sur l'aiguille du Dragon, hypothétique elle aussi : une éclipse est possible.",
   "Devant, la pleine lune tombe sur l'aiguille du Dragon, hypothétique elle aussi : une éclipse est possible.", 0.35),
  ("Attention : ces signes sont calculés par notre modèle.", "Attention : ces signes sont calculés par notre modèle.", 0.3),
  ("Et la machine ne disait pas où l'observer.", "Et la machine ne disait pas où l'observer.", 0.0),
 ],
 # chapitre 7
 [
  ("Servait-elle à naviguer ?", "Servait-elle à naviguer ?", 0.3),
  ("Non : ni viseur, ni latitude, ni longitude.", "Non : ni viseur, ni latitude, ni longitude.", 0.3),
  ("C'est un calculateur du ciel.", "C'est un calculateur du ciel.", 0.35),
  ("Mais regardez ces plaques : un calendrier des étoiles.", "Mais regardez ces plaques : un calendrier des étoiles.", 0.3),
  ("Quand le Soleil atteint la lettre ksi, on lit : « La Pléiade se lève le matin. »",
   "Quand le Soleil atteint la lettre Xi, on lit : La Pléiade se lève le matin.", 0.35),
  ("Bien plus tard, pour Végèce, la mer est sûre après ce lever.",
   "Bien plus tard, pour Végèce, la mer est sûre après ce lever.", 0.3),
  ("Déjà Hésiode avertissait : quand les Pléiades « tombent dans la noire mer », rentre tes navires.",
   "Déjà Hésiode avertissait : quand les Pléiades tombent dans la noire mer, rentre tes navires.", 0.35),
  ("La machine ne disait pas où aller, mais quand partir.", "La machine ne disait pas où aller, mais quand partir.", 0.4),
  ("La voici reconstruite, ses rapports prouvés mathématiquement, en accès libre.",
   "La voici reconstruite, ses rapports prouvés mathématiquement, en accès libre.", 0.4),
  ("Et vous, quelle date allez-vous lui demander ?", "Et vous, quelle date allez-vous lui demander ?", 0.0),
 ],
]


def chapters_from_narration():
    txt = NARR.read_text(encoding='utf-8')
    parts, cur = [], []
    for line in txt.splitlines():
        if line.strip() == '---':
            parts.append(' '.join(cur).strip()); cur = []
        else:
            cur.append(line.strip())
    parts.append(' '.join(cur).strip())
    return [p for p in parts if p]


def check():
    ch = chapters_from_narration()
    assert len(ch) == 7 == len(U), (len(ch), len(U))
    for i, (c, units) in enumerate(zip(ch, U), 1):
        joined = ' '.join(u[0] for u in units)
        assert joined == c, f"chapitre {i} différent:\n{joined}\n{c}"
    return True


def units():
    check()
    out = []
    for ci, units_ in enumerate(U, 1):
        for ui, (o, t, p) in enumerate(units_, 1):
            out.append(dict(ch=ci, u=ui, id=f"c{ci}u{ui:02d}", orig=o, tts=t, pause=p))
    return out


if __name__ == '__main__':
    check(); print('OK', len(units()), 'unités')
