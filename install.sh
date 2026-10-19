#!/usr/bin/env bash
# Instala el agente disenador-procesos y su herramienta bpmn_tool.py
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
AGENTS="$HOME/.claude/agents"
TOOLS="$HOME/.agents/skills/disenar-procesos/tools"
mkdir -p "$AGENTS" "$TOOLS"
if [ -f "$AGENTS/disenador-procesos.md" ] && ! cmp -s "$HERE/agents/disenador-procesos.md" "$AGENTS/disenador-procesos.md"; then
  cp "$AGENTS/disenador-procesos.md" "$AGENTS/disenador-procesos.md.bak"
  echo "Copia de seguridad del agente anterior: $AGENTS/disenador-procesos.md.bak"
fi
cp "$HERE/agents/disenador-procesos.md" "$AGENTS/"
cp "$HERE/tools/bpmn_tool.py" "$TOOLS/"
chmod +x "$TOOLS/bpmn_tool.py"
echo "✓ Agente:      $AGENTS/disenador-procesos.md"
echo "✓ Herramienta: $TOOLS/bpmn_tool.py"
if [ ! -f "$HOME/.agents/skills/disenar-procesos/SKILL.md" ] && [ ! -f "$HOME/.claude/skills/disenar-procesos/SKILL.md" ]; then
  echo "⚠ No se encontró el skill 'disenar-procesos'. Consulta el README (sección Requisitos) para generarlo."
fi
echo "Reinicia Claude Code para cargar el agente."
