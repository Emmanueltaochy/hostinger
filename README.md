# Configuration MCP Hostinger

*[English version](README.en.md)*

Configuration Claude Code pour le [serveur MCP de l'API Hostinger](https://github.com/hostinger/api-mcp-server)
(`hostinger-api-mcp` sur npm), découpée en un serveur MCP par domaine produit
afin de ne charger dans le contexte que les outils réellement nécessaires.

## Organisation des fichiers

| Fichier | Portée | À utiliser quand |
| --- | --- | --- |
| `.mcp.json` | Projet | Tu veux que ces serveurs soient disponibles pour toute personne travaillant dans ce dépôt. Le token est lu depuis la variable d'environnement `HOSTINGER_API_TOKEN`. |
| `examples/claude.json.windows.example` | Utilisateur (`%USERPROFILE%\.claude.json`) | Windows, serveurs disponibles dans tous les projets. |
| `examples/claude.json.unix.example` | Utilisateur (`~/.claude.json`) | macOS/Linux, serveurs disponibles dans tous les projets. |

La seule différence entre les deux exemples de portée utilisateur est `npx` face à
`npx.cmd` : sous Windows, c'est le shim `.cmd` qui est réellement exécutable, un
`npx` nu n'y démarre donc pas.

## Installation

1. Crée un token d'API dans le panneau Hostinger : **Compte → API → Générer un token**.
2. Choisis une portée :

   **Portée projet (recommandée pour ce dépôt)** — rien à copier, `.mcp.json` est
   déjà présent. Exporte le token avant de lancer Claude Code :

   ```bash
   export HOSTINGER_API_TOKEN='...'      # macOS / Linux
   ```
   ```powershell
   $env:HOSTINGER_API_TOKEN = '...'      # Windows PowerShell
   ```

   **Portée utilisateur** — fusionne le bloc `mcpServers` de l'exemple correspondant
   à ton système dans ton `.claude.json` (`%USERPROFILE%\.claude.json` sous Windows,
   `~/.claude.json` ailleurs) et remplace `your-token-here` par le vrai token.

3. Redémarre Claude Code et lance `/mcp` pour vérifier que les serveurs sont connectés.

Node.js 20 ou plus récent est requis (contrainte `engines` de `hostinger-api-mcp`).

## Gestion du token

Le token donne un contrôle complet sur l'hébergement, les domaines, le DNS, la
facturation, le mail et les VPS du compte. Garde-le hors du gestionnaire de versions :

- Privilégie le `.mcp.json` de portée projet, qui ne fait que référencer `${HOSTINGER_API_TOKEN}`.
- Avec la portée utilisateur, le token vit dans `.claude.json`, en dehors de ce dépôt.
- Le `.gitignore` couvre `.env`, `.env.local` et `*.token` ; les fichiers d'exemple
  sont livrés avec le marqueur `your-token-here` et doivent le rester.

## Serveurs configurés

| Serveur | Binaire | Périmètre |
| --- | --- | --- |
| `hostinger-hosting` | `hostinger-hosting-mcp` | Sites web, bases de données, tâches cron, réglages PHP/Node.js, accès aux fichiers |
| `hostinger-domains` | `hostinger-domains-mcp` | Achat de domaines, transferts, profils WHOIS, redirections, serveurs de noms |
| `hostinger-dns` | `hostinger-dns-mcp` | Enregistrements DNS, validation, instantanés et restaurations |
| `hostinger-billing` | `hostinger-billing-mcp` | Catalogue, abonnements, moyens de paiement, renouvellement automatique |
| `hostinger-reach` | `hostinger-reach-mcp` | Contacts, segments, tags, campagnes, automatisations, formulaires |
| `hostinger-mail` | `hostinger-mail-mcp` | Commandes mail, boîtes aux lettres, alias, redirections, réponses automatiques, journaux |
| `hostinger-vps` | `hostinger-vps-mcp` | Machines virtuelles, pare-feu, instantanés, sauvegardes, clés SSH, enregistrements PTR |

## Points d'entrée par section du panneau

Chaque section du panneau Hostinger a un outil qui en liste l'inventaire. Commence
par celui-ci, puis réutilise l'identifiant renvoyé (nom de domaine, `username`,
ID de commande, ID de machine virtuelle) pour les appels de détail du même serveur.

| Section du panneau | Outil d'entrée | Serveur MCP |
| --- | --- | --- |
| Hébergement | `hosting_listWebsitesV1` | `hostinger-hosting` |
| Domaines | `domains_getDomainListV1` | `hostinger-domains` |
| Facturation | `billing_getSubscriptionListV1` | `hostinger-billing` |
| VPS | `VPS_getVirtualMachinesV1` | `hostinger-vps` |
| Mail | `mail_listOrdersV1` | `hostinger-mail` |

Les noms d'outils sont ceux exposés par le serveur MCP ; dans Claude Code ils
apparaissent préfixés par le serveur, par exemple
`mcp__hostinger-hosting__hosting_listWebsitesV1`.

## Modifier le contenu d'un site WordPress

L'API Hostinger **ne modifie pas le contenu** des sites. Sur WordPress, textes et
images vivent dans la base de données : aucun outil des serveurs ci-dessus ne
sait éditer une page ou un article. Le contenu passe par l'**API REST de
WordPress**, avec un accès propre à un seul site.

`scripts/wp.py` s'appuie sur cette API (bibliothèque standard Python, aucune
dépendance à installer).

### Créer l'accès

1. Dans le site : **Utilisateurs → Ajouter**, rôle **Éditeur** (pas
   Administrateur : l'Éditeur modifie textes et images, sans pouvoir toucher aux
   extensions ni supprimer le site).
2. Se connecter avec ce compte, puis **Utilisateurs → Profil → Mots de passe
   d'application**. Nommer le mot de passe, le générer, le copier — il ne
   s'affiche qu'une fois. Les espaces qu'il contient font partie du mot de passe.
3. Renseigner les variables d'environnement :

   ```bash
   export WP_SITE_URL='https://monsite.fr'
   export WP_USER='mon-editeur'
   export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'
   ```

Un mot de passe d'application ne vaut que pour ce site, se révoque seul depuis la
même page, et n'ouvre que les droits du rôle choisi. Il ne donne accès ni à la
facturation, ni aux domaines, ni aux autres sites.

### Commandes

| Commande | Effet |
| --- | --- |
| `check` | Vérifier les identifiants et afficher le rôle |
| `detect-builder` | Repérer Elementor, Divi, WPBakery… avant toute écriture |
| `text ID` | Lister le texte lisible d'une page |
| `find ID "TEXTE"` | Localiser un texte et montrer l'extrait brut exact |
| `replace ID --old A --new B [--apply]` | Remplacer un texte sans toucher la mise en page |
| `list [--type pages] [--search TEXTE]` | Lister articles ou pages avec leur identifiant |
| `get ID` | Afficher le contenu brut |
| `update ID --title T --content-file F` | Modifier titre et/ou contenu |
| `upload IMAGE --alt TEXTE` | Envoyer une image dans la médiathèque |
| `set-image POST_ID MEDIA_ID` | Définir l'image mise en avant |

### Constructeurs de pages : deux cas très différents

Tous ne se valent pas, et `detect-builder` fait la distinction.

**Bloquants** — Elementor, Bricks, Beaver Builder rangent le texte dans des
métadonnées que l'API REST n'expose pas. Le champ `content` est vide ou
trompeur, et y écrire détruit la page. `detect-builder` renvoie le code 2.

**Éditables avec précaution** — Divi, WPBakery, Avada/Fusion gardent le texte
dans le champ `content`, entouré de leurs propres balises. L'édition est
possible via `replace`, qui ne touche qu'au texte visé.

Sur ces sites, n'utilise jamais `update` : elle réécrit tout le contenu et
emporterait la mise en page. `replace` sauvegarde le contenu original dans
`backup-<type>-<id>.html` avant d'écrire, et simule par défaut — il faut
`--apply` pour appliquer réellement.

### Retrouver le texte exact

Un constructeur coupe fréquemment une phrase par des balises : « Notre
Expertise » à l'écran peut être `Notre <span style="…">Expertise</span>` dans le
code. Le remplacement littéral échoue alors.

`find` fait le pont : il localise un texte lu à l'écran et affiche l'extrait
brut réel, en signalant s'il est d'un seul tenant.

```bash
python3 scripts/wp.py find 99641 "Notre Expertise"
```

Quand le texte est coupé, vise une portion sans balise — un mot seul plutôt que
la phrase entière — pour préserver la mise en forme.

Les sites en éditeur de blocs (Gutenberg) ou éditeur classique ne sont pas
concernés par ces précautions.

## Autres serveurs fournis par le paquet

Non activés ici — ajoute une entrée avec le binaire correspondant si tu en as besoin :

`hostinger-ecommerce-mcp`, `hostinger-wordpress-mcp`, `hostinger-horizons-mcp`,
`hostinger-agency-hosting-mcp`, ainsi que `hostinger-api-mcp` (tous les outils
dans un seul serveur).

Charger `hostinger-api-mcp` expose plusieurs centaines d'outils d'un coup : c'est
la raison pour laquelle cette configuration utilise les binaires par produit.
