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
facturation et les VPS du compte. Garde-le hors du gestionnaire de versions :

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
| `hostinger-vps` | `hostinger-vps-mcp` | Machines virtuelles, pare-feu, instantanés, sauvegardes, clés SSH, enregistrements PTR |

## Autres serveurs fournis par le paquet

Non activés ici — ajoute une entrée avec le binaire correspondant si tu en as besoin :

`hostinger-mail-mcp`, `hostinger-ecommerce-mcp`, `hostinger-wordpress-mcp`,
`hostinger-horizons-mcp`, `hostinger-agency-hosting-mcp`, ainsi que
`hostinger-api-mcp` (tous les outils dans un seul serveur).

Charger `hostinger-api-mcp` expose plusieurs centaines d'outils d'un coup : c'est
la raison pour laquelle cette configuration utilise les binaires par produit.
