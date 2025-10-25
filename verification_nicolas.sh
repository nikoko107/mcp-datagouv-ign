#!/bin/bash

echo "🔍 VÉRIFICATION DE L'INSTALLATION MCP - Nicolas"
echo "================================================"
echo ""

# Vérifier Python
echo "1️⃣ Version Python :"
python3 --version
echo ""

# Vérifier les modules
echo "2️⃣ Modules Python :"
python3 -c "import mcp; print('✓ MCP installé')" 2>&1
python3 -c "import httpx; print('✓ httpx installé')" 2>&1
echo ""

# Vérifier les fichiers
echo "3️⃣ Fichiers dans /Users/nicolasdunand/Documents/nicolas/mcp-datagouv-ign/ :"
ls -la /Users/nicolasdunand/Documents/nicolas/mcp-datagouv-ign/*.py 2>&1
echo ""

# Vérifier la syntaxe
echo "4️⃣ Test de syntaxe Python :"
python3 -m py_compile /Users/nicolasdunand/Documents/nicolas/mcp-datagouv-ign/french_opendata_complete_mcp.py && echo "✓ Syntaxe correcte" || echo "✗ Erreur de syntaxe"
python3 -m py_compile /Users/nicolasdunand/Documents/nicolas/mcp-datagouv-ign/ign_geo_services.py && echo "✓ Module IGN OK" || echo "✗ Erreur module IGN"
echo ""

# Vérifier le fichier de config Claude
echo "5️⃣ Configuration Claude Desktop :"
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CONFIG_PATH" ]; then
    echo "✓ Fichier de config trouvé"
    echo "Contenu :"
    cat "$CONFIG_PATH"
else
    echo "✗ Fichier de config non trouvé à : $CONFIG_PATH"
fi
echo ""

echo "================================================"
echo "✅ Si tout est ✓, redémarrez Claude Desktop"
echo "❌ Si des ✗ apparaissent, corrigez-les d'abord"
