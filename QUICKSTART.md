# 🚀 Guide de démarrage rapide

## Étape 1 : Installation des dépendances (2 minutes)

Ouvrez un terminal dans le dossier contenant les fichiers et exécutez :

```bash
pip install -r requirements.txt
```

Vous devriez voir :
```
Successfully installed mcp-1.x.x httpx-0.27.x
```

## Étape 2 : Configuration de Claude Desktop (3 minutes)

### Trouver le fichier de configuration

**Sur macOS** :
```bash
open ~/Library/Application\ Support/Claude/
```

**Sur Windows** :
```
%APPDATA%\Claude\
```

**Sur Linux** :
```bash
~/.config/Claude/
```

### Éditer claude_desktop_config.json

Si le fichier n'existe pas, créez-le. Ajoutez cette configuration :

```json
{
  "mcpServers": {
    "french-opendata": {
      "command": "python",
      "args": [
        "/REMPLACER/PAR/CHEMIN/ABSOLU/french_opendata_complete_mcp.py"
      ]
    }
  }
}
```

**🔴 IMPORTANT** : Remplacez `/REMPLACER/PAR/CHEMIN/ABSOLU/` par le vrai chemin !

### Exemples de chemins corrects

**macOS** :
```json
"/Users/votrenom/Documents/mcp-datagouv-ign/french_opendata_complete_mcp.py"
```

**Windows** :
```json
"C:\\Users\\VotreNom\\Documents\\mcp-datagouv-ign\\french_opendata_complete_mcp.py"
```

**Linux** :
```json
"/home/votrenom/mcp-datagouv-ign/french_opendata_complete_mcp.py"
```

## Étape 3 : Redémarrer Claude Desktop

1. **Fermez complètement** Claude Desktop (ne le laissez pas en arrière-plan)
2. **Relancez** Claude Desktop
3. **Attendez** quelques secondes que le serveur démarre

## Étape 4 : Vérifier que ça fonctionne

Dans Claude, essayez ces commandes :

### Test 1 : Data.gouv.fr
```
Recherche les datasets sur les vélos en France
```

### Test 2 : IGN Cartographie
```
Liste les couches de cartes IGN disponibles sur les orthophotos
```

### Test 3 : Géocodage
```
Donne-moi les coordonnées GPS de la Tour Eiffel
```

### Test 4 : API Geo
```
Quelle est la population de Lyon ?
```

## ✅ Ça marche !

Si Claude répond avec des données, félicitations ! Le serveur MCP est opérationnel.

## ❌ Problèmes courants

### "Command not found" ou "python: not found"

**Solution** : Utilisez `python3` au lieu de `python` dans la config :
```json
"command": "python3"
```

### "No module named 'mcp'"

**Solution** : Réinstallez les dépendances :
```bash
pip install --upgrade mcp httpx
```

### Les outils n'apparaissent pas

**Solutions** :
1. Vérifiez que le chemin dans la config est **absolu** (commence par `/` ou `C:\`)
2. Redémarrez **complètement** Claude Desktop
3. Vérifiez les logs : Menu → Settings → Developer

### "Permission denied"

**Solution** : Rendez le script exécutable :
```bash
chmod +x french_opendata_complete_mcp.py
```

## 📊 Voir les logs

Pour déboguer, vérifiez les logs de Claude Desktop :

**macOS/Linux** :
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows** :
Ouvrez l'Observateur d'événements Windows

## 🎯 Prochaines étapes

Maintenant que le serveur fonctionne, essayez :

1. **Recherche de données** : "Trouve des datasets sur l'environnement publiés par le ministère"
2. **Cartographie** : "Génère une URL de carte IGN centrée sur Paris"
3. **Géocodage** : "Convertis cette adresse en coordonnées GPS"
4. **Analyse territoriale** : "Liste toutes les communes du département 75"

## 📚 Documentation complète

Pour plus d'informations, consultez :
- `README.md` - Documentation détaillée
- `EXEMPLES.md` - Exemples d'utilisation avancés

---

Besoin d'aide ? Vérifiez d'abord que :
1. Python 3.8+ est installé
2. Les dépendances sont installées
3. Le chemin dans la config est correct et absolu
4. Claude Desktop a été complètement redémarré
