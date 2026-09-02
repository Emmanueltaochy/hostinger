# Conventions du dépôt

## Langue

Réponds **toujours en français**. Le mainteneur est francophone : les échanges,
les explications et les messages de commit se font en français.

Le code et les identifiants techniques ne se traduisent pas — noms d'outils MCP
(`hosting_listWebsitesV1`), noms de serveurs (`hostinger-vps`), clés JSON et
variables d'environnement restent tels quels.

## Documentation bilingue

`README.md` (français) et `README.en.md` (anglais) sont deux versions du même
document et doivent rester synchronisées : toute modification de fond apportée à
l'un se répercute dans l'autre, avec la même structure de sections et de
tableaux. Le français fait référence en cas de divergence.

## Token d'API

`HOSTINGER_API_TOKEN` donne un contrôle complet du compte Hostinger. Il ne doit
jamais être écrit en clair dans un fichier versionné :

- `.mcp.json` (portée projet) ne référence que `${HOSTINGER_API_TOKEN}`.
- Les fichiers de `examples/` conservent le marqueur `your-token-here`.

## Serveurs MCP par produit

La configuration déclare un serveur MCP par domaine produit
(`hostinger-hosting`, `hostinger-domains`, `hostinger-dns`, `hostinger-billing`,
`hostinger-reach`, `hostinger-mail`, `hostinger-vps`) plutôt que le serveur
agrégé `hostinger-api-mcp`, qui exposerait plusieurs centaines d'outils d'un
coup. Un nouveau besoin s'ajoute donc via le binaire par produit correspondant.

Trois fichiers déclarent les mêmes serveurs et doivent évoluer ensemble :
`.mcp.json`, `examples/claude.json.unix.example` (`npx`) et
`examples/claude.json.windows.example` (`npx.cmd`).

Avant de documenter un outil, vérifie qu'un serveur configuré l'expose
réellement : sa présence dans le serveur agrégé ne suffit pas.
