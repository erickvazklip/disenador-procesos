# Expediente de proceso · Reembolso de gastos de viaje · Nubia SA

Fecha: 2026-10-19 · Método: *Fundamentals of BPM* (Dumas et al.), fases F0–F10 · Insumo: `../entrevista-reembolsos.md` (IN-01..IN-04)

## Resumen ejecutivo

**Problema.** Un empleado tarda cerca de **un mes** en recibir el reembolso de sus gastos de viaje (IN-01). El proceso circula por correo y Excel entre el empleado, su jefe, Cuentas por Pagar (CxP), el director financiero y TI.

**Hallazgos clave** (cifras modeladas; la mayoría de parámetros son [SUPUESTO], ver 06):
1. **Casi todo el tiempo es espera**: cycle time ≈ **18.5 días hábiles** frente a ≈ **78 min** de trabajo efectivo → **CTE ≈ 0.9 %**.
2. **Dos lotes de calendario** explican la mitad del cycle time: la revisión del jefe **solo los viernes** (≈ 4 d) y la **corrida de pagos quincenal** (≈ 5 d). Con la preparación tardía y la cola de CxP, 4 issues suman el **83 %** del tiempo (Pareto, 05).
3. **23.5 % de los informes se rehacen** al menos una vez (15 % devueltos por CxP [DATO] + devoluciones del jefe [SUPUESTO]), con reenvío completo: ≈ 880 reprocesos y ≈ 207,000 MXN al año.
4. **CxP es el cuello de botella** (ρ ≈ 0.93 con 5 h/día): recaptura en el ERP lo que el empleado ya escribió en Excel (10 min/informe [DATO], ≈ 565 h/año).
5. **La política v2019 no se aplica**: la aprobación sin revisión de informes < 1,000 MXN no se usa y nadie es responsable del control de plazo de 30 días.

**Recomendación.** Aplicar en 3 meses unos **quick wins sin tecnología** (S1: aprobación martes y viernes con 48 h, corrida semanal, plantilla validada, aplicar la regla < 1,000 MXN) y, de M3 a M12, implantar un **workflow digital con reglas** (S2: captura en origen con foto/CFDI, validación DMN, ruta automática para montos bajos, aprobación móvil con escalado a 48 h, contabilización automática en el ERP, auditoría por muestreo y corrida semanal).

**Beneficio esperado** [SUPUESTO]: cycle time **18.5 → 5.3 días hábiles** (≈ 7 días naturales, −71 %); coste de procesamiento **366 → 159 MXN/informe** (≈ −595,000 MXN/año); first-pass yield **76.5 % → ≈ 95 %**; CxP de 23 a 3 min por informe.

## Mapa de entregables

| Archivo | Fase | Propósito |
|---|---|---|
| [00-insumos.md](00-insumos.md) | F0 | Inventario de insumos, fiabilidad y contradicciones |
| [01-ficha-proceso.md](01-ficha-proceso.md) | F1 | Process Checklist, process profile, alcance, stakeholders |
| [03-kpis.md](03-kpis.md) | F2 | 10 KPIs con línea base, target con plazo y fuente |
| [04-asis.json](04-asis.json) · [04-asis.bpmn](04-asis.bpmn) · [04-modelo-asis.md](04-modelo-asis.md) | F3 | Modelo as-is validado, narrativa, catálogo de actividades, reglas, RACI |
| [05-analisis-cualitativo.md](05-analisis-cualitativo.md) | F4 | VA/BVA/NVA, 7 mudas, issue register, Pareto, PICK, Ishikawa, why-why |
| [06-analisis-cuantitativo.md](06-analisis-cuantitativo.md) · [06-calculos.py](06-calculos.py) | F5 | CT, TCT, CTE, CPM, coste, capacidad, M/M/1, Little, sensibilidad, spec de simulación |
| [07-rediseno.md](07-rediseno.md) | F6 | Devil's Quadrangle, heurísticas, 3 escenarios evaluados, trazabilidad |
| [08-tobe.json](08-tobe.json) · [08-tobe.bpmn](08-tobe.bpmn) · [08-modelo-tobe.md](08-modelo-tobe.md) | F7 | Modelo to-be validado y tabla de cambios |
| [09-implementacion.md](09-implementacion.md) | F8 | Tipos de tarea, completitud, datos, asignación, DMN (U + C verificadas), sistema, cambio, roadmap |
| [10-monitorizacion.md](10-monitorizacion.md) | F9 | Dashboards, event log, conformance, alertas, variantes |
| [visor.html](visor.html) | F10 | Visor BPMN con pestañas as-is / to-be |

No aplican: `02-arquitectura.md` (un solo proceso, no se pidió landscape) y `11-madurez.md` (alcance de un proceso, no organizacional).

## Trazabilidad resumida

| Issue | Causa raíz | Cambio to-be | KPI |
|---|---|---|---|
| I4 Corrida quincenal | Calendario de acreedores aplicado a empleados | Corrida semanal automática (IE2, T15) | K1 |
| I1 Revisión semanal del jefe | Sin SLA ni triage | Worklist + 48 h + escalado; ruta AUTO (T03, B1, T22, T21) | K2, K9 |
| I5 Preparación tardía | Formato tedioso, sin avisos | App con foto/CFDI y recordatorios (T20) | K1, K10 |
| I3 Captura manual en ERP | Sin integración | Contabilización por servicio (T06) | K3, K6 |
| I2 Rework por incompletos | Control lejos del origen | Validación DMN en línea (T20, T21) | K4 |
| I6, I7, I8, I9 | Ver 07 §7 | Tolerancia DMN, acreedor automático, política en DMN, estado visible | K5, K7, K8, K10 |

## Supuestos críticos
1. Esperas: jefe 4 d, CxP 3 d, empleado 3 d antes de preparar, DF 2 d (ninguna medida); el modelo da ≈ 26 días naturales frente al "como al mes" percibido.
2. 10 % de devoluciones por el jefe; 20 % de informes con excedente; 10 % sin cuenta de proveedor; 3 % fuera de plazo.
3. Tarifas cargadas por hora (empleado 250, jefe 450, CxP 200, DF 1,200, TI 250 MXN) → todos los importes en MXN son orientativos.
4. ≈ 35 % de los informes serían < 1,000 MXN sin excedente (ruta AUTO).
5. El ERP puede integrarse (API o RPA) y Tesorería acepta una corrida semanal.
6. El process owner es el director financiero.

## Preguntas abiertas (validar con el owner y los expertos)
1. ¿Cuántas horas al día dedica CxP a reembolsos y cuántas personas lo hacen?
2. ¿Cuál es la distribución real de montos por informe (para fijar el umbral AUTO)? ¿El umbral de 1,000 MXN es por informe o por partida?
3. ¿Quién controla hoy el plazo de 30 días y cuántos informes se rechazan por plazo?
4. ¿Qué pasa cuando el DF no autoriza un excedente: se paga hasta el tope o se rechaza la partida?
5. ¿A quién vuelve un informe devuelto por CxP: al empleado o al jefe? ¿Se re-aprueba?
6. ¿Se exige CFDI para la deducibilidad? ¿Hay anticipos de viaje o tarjetas corporativas?
7. ¿Tesorería puede pagar reembolsos semanalmente? ¿Existe un módulo de gastos en el ERP actual?
8. ¿Hay topes para transporte, taxis y otros conceptos? ¿El tope de hospedaje incluye impuestos?
9. ¿La política v2019 sigue vigente o hay una versión posterior?

## Próximos pasos
1. Validar la narrativa del as-is (04) con Ana, Luis, Marta, el DF y TI (60 min) y obtener la firma del owner.
2. Muestrear 30–50 informes recientes con sus fechas para sustituir los supuestos de espera y volver a correr `06-calculos.py`.
3. Decidir con el DF los quick wins de S1 y la actualización de la política (umbral, tolerancia, plazo).
4. Levantar con TI las opciones de herramienta e integración con el ERP (09 §6).

## Cómo ver los modelos
- `open "visor.html"` (requiere conexión: carga bpmn-js desde unpkg).
- Los `.bpmn` se pueden abrir y editar en **Camunda Modeler** o en **bpmn.io**; la fuente editable son los `.json` (`python3 ~/.agents/skills/disenar-procesos/tools/bpmn_tool.py build 04-asis.json -o 04-asis.bpmn`).
