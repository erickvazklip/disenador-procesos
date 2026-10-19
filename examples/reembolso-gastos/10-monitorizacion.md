# 10 · Plan de monitorización y process mining (F9)

## 1. Dashboards

| Nivel | Audiencia | Medida | Visual | Frecuencia |
|---|---|---|---|---|
| **Operativo** | CxP, jefes, DF | WIP por estado (`PEND_APROBACION`, `PEND_DF`, `EN_AUDITORIA`, `PROGRAMADO`) con semáforo a tiempo / en riesgo (> 36 h) / vencido (> 48 h) | Tablero kanban por estado + contador | Tiempo real |
| Operativo | Cada jefe | Mis aprobaciones pendientes y su antigüedad | Lista en la worklist | Tiempo real |
| Operativo | CxP / Tesorería | Informes que entran en la próxima corrida (número e importe) | Tarjeta numérica | Diario |
| **Táctico** | DF (owner), gerente de CxP | K1 CT mediana y P90 (días naturales); K2 P90 aprobación; K3; espera por tarea (T03, T10, IE2) | Línea mensual (longitudinal) + histograma del CT | Mensual |
| Táctico | DF, gerente de CxP | K4 first-pass yield; motivos de INCOMPLETO; K9 % AUTO; % excedentes y % autorizados | Barras apiladas por área (transversal) | Mensual |
| Táctico | DF | K5 coste por informe (ABC) y K6 min de CxP | Línea mensual | Trimestral |
| **Estratégico** | Dirección general | Índice de servicio a empleados (K1 + K10) y coste anual del proceso dentro del grupo de procesos financieros | Scorecard (semáforo frente a target) | Trimestral |

Regla: los dashboards por persona se usan para **gestionar colas**, no para evaluar desempeño individual (riesgo "Gran Hermano", Ch 11).

## 2. Especificación del event log

| Atributo | Contenido | Origen |
|---|---|---|
| **case_id** | ID del InformeGasto (correlación única; las correcciones conservan el mismo ID) | BPMS |
| **activity** | Nombre de la actividad/evento del modelo to-be (tabla abajo) | BPMS |
| **ts_start / ts_end** | Timestamps de inicio (check-out) y fin (check-in) en ISO 8601 con zona `America/Mexico_City` | BPMS |
| **resource** | Usuario o `SYS` (rol en atributo aparte) | BPMS |
| role | Empleado / Jefe / Gerente / DF / CxP / SYS | BPMS |
| Atributos del caso | área, centroCosto, montoSolicitado, montoAprobado, ruta, excedeTope, requiereDF, seleccionAuditoria, fechaFinViaje, versionPolitica | BPMS / DMN |
| Atributos de evento | resultado (decisión), motivo de devolución, escalado (sí/no) | BPMS |

Hitos que **deben existir** en el modelo ejecutable (todos están en `08-tobe.bpmn`): S1 *Viaje concluido* (= fechaFinViaje), T20, T21 (con su salida `ruta`), T03, B1/T22 (escalado), T10, T06, T23, IE2, T15, E1/E2/E3.
Retos (Ch 11): **correlación** (las correcciones no crean caso nuevo), **timestamps** (el viaje concluido viene del dato capturado, no del sistema), **longevidad** (ventana ≥ 3 meses ≫ CT; excluir casos abiertos al calcular CT), **granularidad** (agrupar eventos técnicos del ERP en T06).

Análisis con la herramienta del skill (una vez exportado el CSV):
```bash
python3 ~/.agents/skills/disenar-procesos/tools/bpmn_tool.py eventlog log.csv \
  --case case_id --activity activity --timestamp ts_end --resource resource --mermaid -o informe-log.md
```

## 3. Reglas de conformance

| Tipo | Regla | Severidad |
|---|---|---|
| Obligatoriedad | Todo caso pagado (T15) tiene T21 con ruta AUTO o JEFE | Alta |
| Obligatoriedad | Todo caso con ruta JEFE pagado tiene T03 con resultado *aprobado* | Alta |
| Obligatoriedad | Todo caso con `requiereDF = true` pagado tiene T10 | Alta |
| Exclusividad | Un caso no termina a la vez en E1 y en E2/E3 | Alta |
| Exclusividad | Ruta AUTO y T03 no aparecen ambos (salvo corrección) | Media |
| Orden | T21 precede a T03; T03 precede a T10; T06 precede a T15 | Alta |
| Datos | No se paga ningún caso con diasDesdeFinViaje > 30 | Alta |
| Datos | montoAprobado ≤ topes de D2 salvo T10 = AUTORIZADO | Alta |
| Datos | montoTotal ≥ 1,000 MXN o excedeTope = true ⇒ ruta JEFE | Alta |
| Recursos / **separation of duties** | resource(T03) ≠ empleado; resource(T10) ≠ empleado; resource(T23) ≠ empleado | Alta |
| Recursos | T10 lo ejecuta solo el rol DF o su delegado | Alta |

## 4. Alertas online

| Disparador | Destinatario | Acción |
|---|---|---|
| T03 abierta > 36 h | Jefe | Recordatorio (antes del escalado a 48 h) |
| T10 abierta > 2 días hábiles | DF y delegado | Recordatorio |
| Caso con fechaFinViaje a 25 días y sin enviar | Empleado | Aviso de plazo |
| Fallo de T06 o T15 tras 3 reintentos | TI y CxP | Incidente |
| % INCOMPLETO semanal > 10 % | Owner | Revisar UX del portal / reglas |
| Violación de una regla de conformance de severidad alta | Owner y auditoría interna | Investigar el caso |

## 5. Análisis de variantes previsto
- **Rápidos frente a lentos**: casos con CT ≤ 5 d hábiles frente a > 10 d; comparar sus DFG para localizar dónde se pierde el tiempo (esperado: escalados, PEND_DF, correcciones).
- **Por ruta**: AUTO frente a JEFE frente a JEFE + DF (CT, % hallazgos en auditoría → calibrar el umbral de 1,000 MXN y la tolerancia TOL).
- **Por área**: comparar jefes/áreas (transversal) para detectar prácticas de lote que persisten.
- **Rework**: r = 1 − T/CT por actividad (T20) y motivos de INCOMPLETO.
- Proyecto guiado por preguntas a los 6 meses del go-live (5 fases del Ch 11): *¿por qué el P90 sigue por encima de 12 días?*
