# disenador-procesos

Agente para **Claude Code** que diseña y documenta procesos de negocio de punta a punta. A partir de cualquier insumo (narrativas, transcripciones de entrevistas o talleres, manuales y políticas en PDF o DOCX, hojas de cálculo, fotos de pizarras, modelos BPMN existentes o event logs) genera un **expediente de proceso** completo que sigue el BPM lifecycle: identificación → discovery → análisis → rediseño → implementación → monitorización.

Incluye `bpmn_tool.py`, una herramienta en Python (sin dependencias) que genera **BPMN 2.0 con diagrama**, valida la estructura, la *soundness* y las 7 guías de modelado (7PMG), crea un visor HTML, analiza event logs, calcula el flow analysis y verifica tablas DMN.

## Qué genera

| Archivo | Contenido |
|---|---|
| `00-README.md` | Resumen ejecutivo, mapa de entregables, trazabilidad, supuestos y preguntas abiertas |
| `00-insumos.md` | Inventario de fuentes, su fiabilidad y las contradicciones entre ellas |
| `01-ficha-proceso.md` · `02-arquitectura.md` | Process checklist, process profile, alcance, stakeholders; landscape y portafolio |
| `03-kpis.md` | Objetivo → medida → target con plazo, línea base y fuente de datos |
| `04-asis.bpmn` + `.md` | Modelo actual validado, narrativa, catálogo de actividades, RACI, reglas y excepciones |
| `05-analisis-cualitativo.md` | VA/BVA/NVA, 7 mudas, issue register, Pareto, PICK, Ishikawa 6M y why-why |
| `06-analisis-cuantitativo.md` | Cycle time y CTE, coste, capacidad, cuello de botella, Little, colas, simulación |
| `07-rediseno.md` | Devil's Quadrangle, heurísticas de rediseño, escenarios, trazabilidad issue → cambio → KPI |
| `08-tobe.bpmn` + `.md` | Modelo propuesto validado y tabla de cambios |
| `09-implementacion.md` | Tareas ejecutables, datos, asignación de trabajo, tablas DMN verificadas, BPMS, gestión del cambio |
| `10-monitorizacion.md` | Dashboards en 3 niveles, especificación del event log, reglas de conformance, alertas |
| `visor.html` | Visor bpmn-js con pestañas, descarga y exportación SVG |

En [`examples/reembolso-gastos/`](examples/reembolso-gastos/00-README.md) hay un expediente completo generado a partir de una [entrevista ficticia](examples/reembolso-gastos/insumo-entrevista-reembolsos.md).

## Requisitos

- [Claude Code](https://claude.com/claude-code) y Python 3.8 o superior.
- **El skill `disenar-procesos`**: el agente toma de él el método (plantillas, técnicas, umbrales). Ese skill **no se incluye en este repositorio** porque deriva de un libro con derechos de autor (*Fundamentals of Business Process Management*, 2.ª ed., Dumas, La Rosa, Mendling y Reijers, Springer 2018). Si tienes tu propia copia del libro, puedes generarlo con [book-to-skill](https://github.com/virgiliojr94/book-to-skill):

  ```bash
  npx skills add virgiliojr94/book-to-skill -g -a claude-code -y
  ```
  Y después, en Claude Code:
  ```
  /book-to-skill /ruta/a/Fundamentals-of-BPM.pdf disenar-procesos
  ```
  Sin el skill, el agente sigue funcionando con las instrucciones y la herramienta, pero con menos profundidad de método.

## Instalación

```bash
git clone https://github.com/erickvazklip/disenador-procesos.git
cd disenador-procesos
./install.sh
```

El script copia el agente a `~/.claude/agents/` y la herramienta a `~/.agents/skills/disenar-procesos/tools/`, que es la ruta que usa el agente. Reinicia Claude Code después de instalar.

## Uso

En Claude Code:

```
Usa disenador-procesos para documentar el proceso de compras con estos archivos: ./entrevistas/*.md ./manual-compras.pdf
```

Modos parciales: *solo as-is*, *diagnóstico* (hasta el análisis), *to-be*, *implementación*, *monitorización/mining* o *arquitectura* (varios procesos).

## Herramienta `bpmn_tool.py`

```bash
python3 tools/bpmn_tool.py build --help-spec                 # formato JSON del modelo
python3 tools/bpmn_tool.py build modelo.json -o modelo.bpmn --strict
python3 tools/bpmn_tool.py validate modelo.bpmn              # estructura + soundness + 7PMG
python3 tools/bpmn_tool.py viewer asis.bpmn tobe.bpmn -o visor.html --title "Mi proceso"
python3 tools/bpmn_tool.py eventlog log.csv --case caso --activity actividad --timestamp fin --start inicio --resource recurso --mermaid
python3 tools/bpmn_tool.py flow modelo.json                  # CT, TCT, CTE, coste, utilización, cuello de botella
python3 tools/bpmn_tool.py dmn tabla.json                    # solapes y huecos en tablas DMN
```

- **Validación**: reglas estructurales de BPMN, *soundness* mediante exploración de estados (deadlock, livelock, falta de sincronización, actividades muertas) y advertencias de las 7PMG (tamaño, OR-gateways, etiquetas verbo-objeto, gateways sin actividad de decisión).
- **Diagrama**: maquetación automática por capas con pools, lanes, message flows, data objects y anotaciones. Se abre y edita en [Camunda Modeler](https://camunda.com/download/modeler/) o en [demo.bpmn.io](https://demo.bpmn.io).
- El visor HTML carga bpmn-js desde unpkg, así que necesita conexión a internet.

## Licencia

[MIT](LICENSE) para el agente, la herramienta y los ejemplos. Los conceptos de BPM que se citan (BPM lifecycle, 7PMG, heurísticas de rediseño, etc.) pertenecen a la literatura publicada sobre BPM; este repositorio no reproduce texto de ningún libro.
