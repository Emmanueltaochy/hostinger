#!/usr/bin/env python3
"""Édition de contenu WordPress (textes, images) via l'API REST.

L'API Hostinger ne donne pas accès au contenu des pages : sur WordPress il vit
dans la base de données, pas dans des fichiers. On passe donc par l'API REST de
WordPress, authentifiée par un mot de passe d'application.

Identifiants attendus dans l'environnement (jamais dans un fichier versionné) :

    WP_SITE_URL       https://monsite.fr
    WP_USER           identifiant WordPress
    WP_APP_PASSWORD   mot de passe d'application (24 caractères, espaces inclus)

Usage :
    python3 scripts/wp.py check
    python3 scripts/wp.py list [--type posts|pages] [--search TEXTE]
    python3 scripts/wp.py get ID [--type posts|pages]
    python3 scripts/wp.py update ID [--title T] [--content-file F] [--type ...]
    python3 scripts/wp.py upload FICHIER [--alt TEXTE]
    python3 scripts/wp.py set-image POST_ID MEDIA_ID [--type posts|pages]
    python3 scripts/wp.py detect-builder
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30

# Marqueurs laissés dans le HTML public par les constructeurs de pages. Quand
# l'un d'eux est présent, le contenu réel n'est pas dans le champ « content »
# de l'API mais dans des métadonnées propres au constructeur : l'écraser via
# l'API REST casse la mise en page.
BUILDERS = {
    "Elementor": r"elementor-(?:page|widget|element)",
    "Divi": r"\bet_pb_",
    "WPBakery": r"\bvc_row\b",
    "Avada/Fusion": r"\bfusion-(?:builder|row)\b",
    "Bricks": r"\bbrxe-",
    "Beaver Builder": r"\bfl-builder",
}


class WPError(Exception):
    pass


def config():
    missing = [v for v in ("WP_SITE_URL", "WP_USER", "WP_APP_PASSWORD") if not os.environ.get(v)]
    if missing:
        raise WPError(
            "Variables d'environnement manquantes : " + ", ".join(missing) + "\n"
            "Renseigne-les avant de lancer le script (voir l'en-tête du fichier)."
        )
    site = os.environ["WP_SITE_URL"].rstrip("/")
    if not site.startswith("https://"):
        raise WPError(
            f"WP_SITE_URL doit commencer par https:// (reçu : {site}).\n"
            "Les mots de passe d'application transitent en clair sans HTTPS."
        )
    token = base64.b64encode(
        f"{os.environ['WP_USER']}:{os.environ['WP_APP_PASSWORD']}".encode()
    ).decode()
    return site, token


def request(method, path, data=None, headers=None, raw=None):
    site, token = config()
    url = path if path.startswith("http") else f"{site}/wp-json/wp/v2{path}"
    body = raw if raw is not None else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Accept", "application/json")
    if raw is None and data:
        req.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        if exc.code == 401:
            raise WPError(
                "401 — identifiants refusés. Vérifie WP_USER et WP_APP_PASSWORD "
                "(le mot de passe d'application contient des espaces : garde-les).\n"
                f"Réponse : {detail}"
            ) from None
        if exc.code == 403:
            raise WPError(
                "403 — authentifié mais sans les droits nécessaires. Le compte doit "
                f"avoir au moins le rôle Éditeur.\nRéponse : {detail}"
            ) from None
        if exc.code == 404:
            raise WPError(
                f"404 — introuvable. Soit l'identifiant n'existe pas, soit l'API REST "
                f"est désactivée sur ce site.\nURL : {url}\nRéponse : {detail}"
            ) from None
        raise WPError(f"HTTP {exc.code} sur {url}\n{detail}") from None
    except urllib.error.URLError as exc:
        raise WPError(f"Connexion impossible à {url} : {exc.reason}") from None


def strip_html(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def cmd_check(args):
    me = request("GET", "/users/me?context=edit")
    roles = me.get("roles", [])
    print(f"Connecté   : {me.get('name')} ({me.get('slug')})")
    print(f"Rôle       : {', '.join(roles) or 'inconnu'}")
    caps = me.get("capabilities", {})
    can_edit = caps.get("edit_others_posts") or "administrator" in roles or "editor" in roles
    print(f"Peut éditer les contenus : {'oui' if can_edit else 'NON'}")
    if "administrator" in roles:
        print(
            "\nAttention : ce compte est administrateur. Pour de la simple édition "
            "de textes et d'images, un compte au rôle Éditeur suffit et limite les "
            "dégâts possibles."
        )
    if not can_edit:
        print("\nCe compte ne peut pas modifier les contenus des autres auteurs.")
        return 1
    return 0


def cmd_list(args):
    query = f"/{args.type}?per_page={args.limit}&status=any&orderby=modified"
    if args.search:
        query += f"&search={urllib.parse.quote(args.search)}"
    items = request("GET", query)
    if not items:
        print("Aucun résultat.")
        return 0
    for item in items:
        title = strip_html(item.get("title", {}).get("rendered", "")) or "(sans titre)"
        print(f"{item['id']:>6}  [{item.get('status','?'):<7}]  {title[:70]}")
    return 0


def cmd_get(args):
    item = request("GET", f"/{args.type}/{args.id}?context=edit")
    title = strip_html(item.get("title", {}).get("raw") or item.get("title", {}).get("rendered", ""))
    content = item.get("content", {}).get("raw") or item.get("content", {}).get("rendered", "")
    print(f"# {title}\n")
    print(f"Statut : {item.get('status')}   Lien : {item.get('link')}\n")
    print(content)
    return 0


def cmd_update(args):
    if not args.title and not args.content_file:
        raise WPError("Rien à modifier : passe --title et/ou --content-file.")
    payload = {}
    if args.title:
        payload["title"] = args.title
    if args.content_file:
        with open(args.content_file, encoding="utf-8") as handle:
            payload["content"] = handle.read()
    item = request("POST", f"/{args.type}/{args.id}", data=payload)
    print(f"Mis à jour : {item.get('link')}")
    print("Champs modifiés : " + ", ".join(payload))
    return 0


def cmd_upload(args):
    path = args.file
    if not os.path.isfile(path):
        raise WPError(f"Fichier introuvable : {path}")
    mime = mimetypes.guess_type(path)[0]
    if not mime or not mime.startswith("image/"):
        raise WPError(f"Type de fichier non reconnu comme image : {mime or 'inconnu'}")
    with open(path, "rb") as handle:
        blob = handle.read()
    name = os.path.basename(path)
    media = request(
        "POST",
        "/media",
        raw=blob,
        headers={
            "Content-Type": mime,
            "Content-Disposition": f'attachment; filename="{name}"',
        },
    )
    print(f"Image envoyée — id {media['id']}")
    print(f"URL : {media.get('source_url')}")
    if args.alt:
        request("POST", f"/media/{media['id']}", data={"alt_text": args.alt})
        print(f"Texte alternatif : {args.alt}")
    return 0


def cmd_set_image(args):
    request("POST", f"/{args.type}/{args.post_id}", data={"featured_media": args.media_id})
    print(f"Image {args.media_id} définie comme image mise en avant de {args.post_id}.")
    return 0


def cmd_detect_builder(args):
    site, _ = config()
    req = urllib.request.Request(site, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read().decode(errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise WPError(f"Page d'accueil illisible ({exc}).") from None
    found = [name for name, pattern in BUILDERS.items() if re.search(pattern, html)]
    if found:
        print("Constructeur de pages détecté : " + ", ".join(found))
        print(
            "\nLe contenu visible n'est alors PAS dans le champ « content » de l'API.\n"
            "Modifier une page via ce script écraserait la mise en page.\n"
            "Sur ces pages, passe par l'éditeur du constructeur."
        )
        return 2
    print("Aucun constructeur de pages détecté : édition par l'API REST possible.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="vérifier les identifiants et le rôle").set_defaults(func=cmd_check)

    p = sub.add_parser("list", help="lister articles ou pages")
    p.add_argument("--type", choices=("posts", "pages"), default="posts")
    p.add_argument("--search")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("get", help="afficher le contenu brut")
    p.add_argument("id", type=int)
    p.add_argument("--type", choices=("posts", "pages"), default="posts")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("update", help="modifier titre et/ou contenu")
    p.add_argument("id", type=int)
    p.add_argument("--type", choices=("posts", "pages"), default="posts")
    p.add_argument("--title")
    p.add_argument("--content-file", help="fichier contenant le nouveau contenu")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("upload", help="envoyer une image dans la médiathèque")
    p.add_argument("file")
    p.add_argument("--alt", help="texte alternatif")
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser("set-image", help="définir l'image mise en avant")
    p.add_argument("post_id", type=int)
    p.add_argument("media_id", type=int)
    p.add_argument("--type", choices=("posts", "pages"), default="posts")
    p.set_defaults(func=cmd_set_image)

    sub.add_parser("detect-builder", help="repérer Elementor, Divi, etc.").set_defaults(func=cmd_detect_builder)

    args = parser.parse_args()
    try:
        return args.func(args)
    except WPError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
