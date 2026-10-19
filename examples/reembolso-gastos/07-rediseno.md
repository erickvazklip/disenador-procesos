# 07 · Rediseño (F6)

## 1. Objetivos sobre el Devil's Quadrangle

| Vértice | Objetivo | Prioridad | Restricción |
|---|---|---|---|
| **Tiempo** | Reducir el cycle time de ≈ 18.5 d hábiles a ≤ 5 d (K1, K2) | 1 | — |
| **Coste** | Reducir el coste de procesamiento ≥ 50 % (K5, K6) | 2 | La inversión en herramienta debe recuperarse en ≤ 2 años [SUPUESTO] |
| **Calidad** | First-pass yield ≥ 97 % (K4) y cumplimiento de política medible (K7) | 2 | **No** reducir el control del gasto (los BVA de control se reubican, no se eliminan) |
| **Flexibilidad** | Cambiar topes y umbrales en ≤ 1 día sin TI (K8) | 3 | — |

Trade-offs previstos: la automatización mejora tiempo, coste y calidad, pero **reduce flexibilidad en tiempo de ejecución** (casos atípicos) y añade coste fijo (licencias); la aprobación automática < 1,000 MXN ahorra tiempo pero **aumenta el riesgo** de gasto indebido → se compensa con auditoría por muestreo.

## 2. Método (Redesign Orbit)
**Transaccional + analítico + inward-looking → Heuristic Process Redesign** (Ch 8). Motivos: el problema es incremental (las actividades necesarias ya existen, sobran esperas y controles duplicados), hay un modelo as-is y un análisis cuantificado, y no hay mandato de transformación radical. Se toma de **BPR** el principio de *capturar el dato una vez, en origen*. El escenario S3 explora una mirada outward (tarjeta corporativa/terceros) como referencia.

## 3. Heurísticas candidatas (de las 29)

| Dimensión | Heurística | Aplicación concreta | Issues | Estado |
|---|---|---|---|---|
| Tiempo | **Case-based work** | Quitar los lotes: aprobación continua con SLA (no "los viernes"); corrida **semanal** | I1, I4 | ✔ S1, S2 |
| Tiempo | **Activity elimination** | Eliminar la recaptura en ERP (T06 manual), la revisión de tickets por el jefe (la hace el sistema) y la verificación manual de cuenta de proveedor (T12) | I3, I2 | ✔ S2 |
| Tiempo | **Resequencing / Knock-out** | Verificar plazo y completitud **antes** de que trabaje cualquier aprobador (knock-out barato primero) | I2, overproduction | ✔ S1 (checklist), S2 (DMN) |
| Tiempo | Parallelism | Validación de política en paralelo a la aprobación del jefe | — | ✘ innecesaria: la validación automática es instantánea y actúa como knock-out (choca con *knock-out*) |
| Tiempo | **Contact reduction** | Corrección en línea de la partida faltante, sin reenviar todo | I2 | ✔ S2 |
| Tiempo/Coste | **Activity automation** | Validación DMN (T21), contabilización (T06 service), pago (T15 service), escalado (T22) | I3, I1 | ✔ S2 |
| Coste | **Empower** | Jefe aprueba excedentes ≤ 10 % sin DF; DF solo por encima | I6 | ✔ S1; en S2 vía DMN [A VALIDAR con DF] |
| Coste | **Triage** | Ruta AUTO (< 1,000 MXN y dentro de tope) frente a ruta JEFE | I1, I8 | ✔ S1 (manual), S2 (DMN) |
| Calidad | **Control relocation** | Mover el control de completitud y topes al empleado, en el momento de capturar | I2 | ✔ S1, S2 |
| Calidad | **Control addition** | Auditoría por muestreo en CxP (≈ 10 % aleatorio + todos los excedentes) | riesgo de AUTO | ✔ S2 |
| Calidad | Case manager | Un analista de CxP como punto único de contacto por informe | I9 | ✘ en S2 la transparencia la da el portal (estado visible); útil solo en S1 como "buzón único" |
| Calidad | Case assignment | Una persona hace todos los pasos de CxP | — | ✘ excluyente con *activity automation* (ya no quedan pasos manuales que agrupar) |
| Flexibilidad | **Integral technology / Centralization** | BPMS/portal como registro único con worklist para jefes, DF y CxP | I9, I3 | ✔ S2 |
| Flexibilidad | **Interfacing** | Integración estándar (REST) portal ↔ ERP ↔ banca | I3 | ✔ S2 |
| Coste | Extra resources | Más personal en CxP | I3 | ✘ trata el síntoma (Kill en PICK) |
| Coste | **Trusted party / Outsourcing** | Tarjeta corporativa y proveedor de gestión de gastos | I4, I5 | ◐ S3 |
| Tiempo | Resequencing | Alta del acreedor-empleado en el onboarding (antes del primer viaje) | I7 | ✔ S1, S2 |

## 4. Escenarios

### S1 — Quick wins sin nueva tecnología (M0–M3)
- Jefes aprueban **martes y viernes** con compromiso de 48 h; CxP envía recordatorio (case-based work parcial).
- **Corrida semanal** para reembolsos de empleados [A VALIDAR con Tesorería].
- Plantilla Excel con validaciones (campos obligatorios, topes 1,800/600 calculados, fecha del viaje → aviso de plazo) y checklist de comprobantes (control relocation, knock-out).
- Aplicar la política: < 1,000 MXN y dentro de tope → el jefe solo da visto bueno sin revisión detallada (triage).
- Excedentes ≤ 10 % los aprueba el jefe (empower) [A VALIDAR].
- Alta de acreedor en el onboarding (resequencing).

### S2 — Workflow digital con reglas (recomendado, M3–M12)
Todo lo de S1 más: portal/app donde el empleado **registra los gastos con foto o CFDI** (T20); **validación automática** DMN (T21) con ruta INCOMPLETO / FUERA_DE_PLAZO / AUTO / JEFE; aprobación del jefe en worklist o móvil con **timer de 48 h y escalado** (T03, T22); DF solo para excedentes (T10); **contabilización automática** en ERP con creación del acreedor (T06 service); **auditoría por muestreo** en CxP (T23); corrida semanal automática (T15) y notificación al empleado. Modelo: `08-tobe.bpmn`.

### S3 — Tarjeta corporativa + plataforma externa (evaluar en 12–24 meses)
Los viajeros frecuentes pagan con tarjeta corporativa (trusted party/outsourcing); el reembolso queda solo para gastos de bolsillo. El proceso se convierte en **conciliación de tarjeta**. Requiere política de tarjetas, banco emisor y un proceso nuevo; fuera del alcance de este expediente.

## 5. Evaluación (cifras de `06-calculos.py`, todas [SUPUESTO])

| Criterio | As-is | S1 Quick wins | S2 Workflow digital | S3 Tarjeta |
|---|---|---|---|---|
| CT medio (días hábiles) | 18.5 | **12.1** (−35 %) | **5.3** (−71 %) ≈ 7.4 d naturales | ≈ 0 para el empleado en gastos con tarjeta; conciliación aparte |
| TCT (min) / CTE | 77.7 / 0.9 % | 69.7 / 1.2 % | 34.3 / 1.4 % | n. d. |
| Coste de procesamiento/informe | 366 MXN | 330 MXN (−10 %) | **159 MXN (−56 %)** ≈ −595,000 MXN/año | n. d. (comisiones de tarjeta) |
| Minutos de CxP/informe | 23.2 | 21.6 | **2.8** (−88 %) → CxP sale de saturación | — |
| First-pass yield | 76.5 % | ≈ 87 % (p_j 0.05, p_c 0.08 [SUPUESTO]) | ≈ 95 % (3 % incompletos detectados en línea + 3 % correcciones del jefe) | — |
| Flexibilidad (cambio de reglas) | manual | manual | **DMN editable** | según proveedor |
| Esfuerzo / riesgo de implantación | — | Bajo / bajo | Medio-alto / medio (integración ERP, adopción) | Alto / alto (cambio de política y banco) |
| Efectos negativos | — | Disciplina de los jefes difícil de sostener sin herramienta | Coste de licencias; casos atípicos que la regla no cubre; miedo a "Gran Hermano" en la worklist; riesgo de gasto indebido en AUTO (mitigado con auditoría) | Riesgo de mal uso de la tarjeta; dependencia del banco |

Sensibilidad S2: si el jefe tarda 2 d en vez de 1 d → CT 5.9 d; si la corrida siguiera quincenal → 7.7 d; si el empleado tarda 3 d en registrar → 7.3 d; si solo el 20 % es AUTO → 5.5 d. **El escenario resiste**: en todos los casos el CT queda < 8 d hábiles.

## 6. Recomendación
**Implantar S1 de inmediato (M0–M3) y S2 de forma gradual (M3–M12)**; revisar S3 tras 12 meses de datos del BPMS. S1 aporta credibilidad (*quick wins*, DICE) y genera los datos para dimensionar S2; S2 ataca las causas raíz (control lejos del origen, lotes, doble captura).

## 7. Matriz de trazabilidad

| Issue | Causa raíz | Cambio en el to-be | Actividad to-be | KPI |
|---|---|---|---|---|
| I1 Revisión semanal del jefe | Sin canal con SLA/escalado; control manual sin triage | Aprobación continua en worklist, SLA 48 h, escalado; ruta AUTO | T03, B1, T22, T21 | K2, K1, K9 |
| I2 Rework por incompletos | Control lejos del origen; sin registro único | Validación en línea al capturar; corrección parcial | T20, T21 | K4, K5 |
| I3 Captura manual en ERP | Sin integración Excel/correo ↔ ERP | Contabilización automática vía servicio | T06 (service) | K3, K6, K5 |
| I4 Corrida quincenal | Calendario de acreedores aplicado al empleado | Corrida semanal automática para empleados | IE2, T15 | K1 |
| I5 Preparación tardía | Formato tedioso; sin recordatorios | App con foto/CFDI; recordatorios a 7 y 20 días [SUPUESTO] | T20 | K1, K10 |
| I6 Excedentes al DF | Sin tolerancia ni delegación | DF solo para excedentes > tolerancia (DMN) | T10, G3b | K1, K5 |
| I7 Alta reactiva de proveedor | Requisito del ERP resuelto al final | Acreedor creado en onboarding o automáticamente en T06 | T06 | K1 |
| I8 Política no aplicada | Política 2019 sin dueño ni control | Política codificada en DMN, con versión y owner | T21 | K7, K8, K9 |
| I9 Sin visibilidad | Correo como workflow | Estado del informe visible en el portal y notificaciones | T20, T15 | K10 |
