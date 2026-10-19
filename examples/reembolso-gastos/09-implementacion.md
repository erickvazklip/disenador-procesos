# 09 · Paquete de implementación (F8)

Base: `08-tobe.bpmn` (sound, 0 errores). Método de 5 pasos de Ch 10: fronteras de automatización → tareas manuales → completar → granularidad → propiedades de ejecución.

## 1. Fronteras de automatización

| ID | Tarea | Tipo de ejecución | Cómo se conecta / quién | Notas |
|---|---|---|---|---|
| T20 | Registrar gastos en portal | **User** (formulario web/app) | Inicio **explícito** del caso por el empleado (untyped start) | Foto u XML CFDI por partida; validación de campos en el formulario |
| T21 | Validar informe contra política | **Business rule** (DMN) | Motor de reglas del BPMS | Tablas D1–D3 (§5) |
| T03 | Aprobar informe de gastos | **User** (worklist + móvil) | Jefe del empleado | Formulario con resumen, partidas y comprobantes |
| B1 | 48 h hábiles sin decisión | Timer boundary (interrumpiente) | Calendario laboral del BPMS | Duración `PT48H` en calendario hábil |
| T22 | Escalar aprobación al gerente | **Send** (notificación) + reasignación | Motor | Patrón *escalado* |
| T10 | Decidir gasto excedente | **User** | Director financiero (o delegado) | Salida: `AUTORIZADO` / `LIMITAR_AL_TOPE` |
| T06 | Contabilizar informe en ERP | **Service** (REST o conector del ERP; **RPA** si el ERP no expone API) | Integración | Crea el acreedor-empleado si no existe |
| T23 | Auditar informe por muestreo | **User** | Analista de CxP | Salida: `SIN_HALLAZGOS` / `CON_HALLAZGOS` |
| IE2 | Corrida semanal alcanzada | Timer intermedio | Ciclo `R/P1W` (jueves 10:00) [SUPUESTO] | Agrupa los informes listos |
| T15 | Pagar reembolsos en corrida | **Service** | ERP / banca electrónica (archivo de layout bancario) | Notifica al empleado al confirmar |

No quedan **tareas manuales** invisibles para el BPMS: el escaneo y el envío por correo desaparecen; la auditoría se registra como user task.

## 2. Completitud ejecutable (excepciones y datos que faltan en el modelo conceptual)

| Hueco | Tratamiento propuesto en el modelo ejecutable |
|---|---|
| El ERP no responde en T06 o T15 | Boundary **error** + reintento automático (3 veces, backoff) → incidente a TI |
| El banco rechaza un pago (CLABE inválida) | Mensaje de rechazo del banco → user task "Corregir datos bancarios" (empleado) → siguiente corrida |
| El empleado cancela su informe antes de aprobarse | Boundary message non-interrupting en el tramo T20–T03 → fin "Informe cancelado" |
| Comprobante duplicado (mismo UUID CFDI o foto) | Regla adicional en T21 → ruta INCOMPLETO con motivo "duplicado" [A VALIDAR] |
| Jefe ausente | Delegación configurada en la worklist (§4) |
| Aprobador = solicitante (el jefe viaja) | Asignación al jefe del jefe (separación de funciones) |
| Hallazgo en auditoría (T23) | Fuera del flujo: caso de recuperación (descuento o vía nómina) [SUPUESTO; requiere política] |
| G4 necesita el dato `seleccionAuditoria` | Añadir en el ejecutable una **script task** "Seleccionar muestra de auditoría" tras T06 (o un listener) — "sin datos no hay decisiones" |
| G3b necesita `requiereDF` | Lo produce la tabla D3 al terminar T03 (o se recalcula en T21) |

## 3. Ajustes de granularidad
- Se **agregan** en T20 los pasos consecutivos del empleado (capturar partidas, adjuntar comprobantes, enviar): mismo recurso, sin handoff.
- Se **mantienen separadas** T21 (regla) y T06 (contabilización) porque son hitos medibles distintos y tienen manejadores de error diferentes.
- T03 y T10 se mantienen separadas (distintos recursos; **separación de funciones**).
- No hay fragmentos ad hoc: **CMMN no aplica** (la gestión de hallazgos de auditoría podría modelarse como caso si su volumen lo justifica).

## 4. Modelo de datos y asignación

### Objetos y campos clave

| Objeto | Campos clave |
|---|---|
| **InformeGasto** | id, empleadoId, centroCosto, fechaInicioViaje, **fechaFinViaje**, fechaEnvio, montoSolicitado, montoAprobado, **ruta** (INCOMPLETO / FUERA_DE_PLAZO / AUTO / JEFE), excedeTope, requiereDF, seleccionAuditoria, **estado**, versionPolitica |
| Partida | id, informeId, **categoria** (HOSPEDAJE / COMIDA / OTRO), fecha, importe, unidades (noches o días), importePorUnidad, comprobanteId, excede, excedentePct |
| Comprobante | id, tipo (FOTO / CFDI), uuidCFDI, archivo, legible |
| Empleado / Acreedor | id, jefeId, gerenteId, CLABE, acreedorERP |
| Decision | informeId, tarea (T03 / T10 / T23), actor, fecha, resultado, comentario |
| Pago | id, corridaId, fechaPago, importe, referenciaBancaria, estado |

### Estados de InformeGasto
`BORRADOR` → `ENVIADO` → (`EN_CORRECCION` ↺ `ENVIADO`) → `PEND_APROBACION` → [`PEND_DF`] → `APROBADO` → `CONTABILIZADO` → [`EN_AUDITORIA`] → `PROGRAMADO` → `PAGADO`. Finales negativos: `RECHAZADO_PLAZO`, `RECHAZADO_JEFE`, `CANCELADO`. (El estado reemplaza las etiquetas "[aprobado]" de los data objects.)

### Asignación de tareas (workflow resource patterns)

| Tarea | Resource class | Patrón de creación | Patrón de push | Delegación / escalado |
|---|---|---|---|---|
| T20 | Empleado (iniciador) | Direct (el iniciador) | — | Recordatorio a los 7 y 20 días del fin de viaje [SUPUESTO] |
| T03 | Jefe inmediato | **Organizational** (jefeId del empleado) + **separation of duties** (≠ solicitante) | Offer | Delegación en vacaciones; **escalado** a gerenteId a las 48 h (B1/T22) |
| T10 | Director financiero | **Role-based** + separation of duties (si el solicitante es el DF → Dirección general) | Offer | Delegado: contralor [SUPUESTO] |
| T23 | Analista CxP | Role-based + separation of duties (≠ solicitante) | **Shortest queue** | Escalado al gerente de CxP a los 5 días |

## 5. Tablas DMN

### D1 · Ruta del informe (hit **U**, completitud **C**) — invocada por T21

| # | comprobantesCompletos | diasDesdeFinViaje | excedeTope | montoTotal (MXN) | → ruta |
|---|---|---|---|---|---|
| 1 | false | [0..30] | – | – | INCOMPLETO |
| 2 | – | > 30 | – | – | FUERA_DE_PLAZO |
| 3 | true | [0..30] | false | < 1000 | AUTO |
| 4 | true | [0..30] | false | ≥ 1000 | JEFE |
| 5 | true | [0..30] | true | – | JEFE |

**Verificación explícita**
- Dominio: comprobantesCompletos ∈ {true, false}; diasDesdeFinViaje ∈ ℕ (0..∞), partido en [0..30] y > 30; excedeTope ∈ {true, false}; montoTotal ≥ 0, partido en < 1000 y ≥ 1000.
- **Sin solapamientos**: R2 es la única con días > 30; R1 (false) frente a R3–R5 (true) son disjuntas por el primer input; R3 frente a R4 por el monto; R3/R4 (false) frente a R5 (true) por excedeTope.
- **Sin huecos**: días > 30 → R2 (cualquier combinación). Días ≤ 30: completos = false → R1; completos = true y excede = true → R5; completos = true, excede = false → monto < 1000 → R3, ≥ 1000 → R4. Las 2 × 2 × 2 × 2 = 16 combinaciones de particiones quedan cubiertas exactamente una vez.
- Decisión de diseño: el plazo se evalúa sobre cualquier informe (un informe fuera de plazo se rechaza aunque esté incompleto: no tiene sentido pedir que lo complete).
- [A VALIDAR] el umbral < 1,000 MXN es por **informe** (supuesto) y no por partida.

### D2 · Tope por partida (hit **U**, completitud **C**) — excedeTope = OR sobre las partidas

| # | categoria | importePorUnidad (MXN) | → excede | → tope |
|---|---|---|---|---|
| 1 | HOSPEDAJE | ≤ 1800 | false | 1800/noche |
| 2 | HOSPEDAJE | > 1800 | true | 1800/noche |
| 3 | COMIDA | ≤ 600 | false | 600/día |
| 4 | COMIDA | > 600 | true | 600/día |
| 5 | OTRO | – | false | sin tope |

Verificación: categoria es una enumeración cerrada de 3 valores; para HOSPEDAJE y COMIDA el importe ≥ 0 se parte en ≤ tope y > tope (disjuntos y exhaustivos); OTRO tiene una única regla. **Sin solapamientos ni huecos.** [A VALIDAR] topes para transporte, taxis, casetas y otros conceptos; ¿hospedaje con o sin impuestos?

### D3 · Requiere director financiero (hit **U**, completitud **C**) — empower con tolerancia

| # | excedeTope | excedenteMaxPct (máx. sobre partidas) | → requiereDF |
|---|---|---|---|
| 1 | false | – | false |
| 2 | true | (0 .. TOL] | false |
| 3 | true | > TOL | true |

TOL = **0 %** al arrancar (equivale a la política actual: todo excedente va al DF); propuesta de **10 %** tras 3 meses de datos [A VALIDAR con el DF]. Verificación: excedeTope = true implica excedenteMaxPct > 0, por lo que (0..TOL] y > TOL particionan el dominio; con TOL = 0 la regla 2 queda vacía pero no deja huecos. **Sin solapamientos ni huecos.**

## 6. Tipo de sistema e integraciones
- **Tipo**: proceso estructurado y repetitivo → **production workflow administrativo** (no case management).
- **Opciones, por orden de preferencia** [A VALIDAR con TI]: (1) módulo de gastos del ERP actual, si existe (ERP-driven, menor integración); (2) SaaS de gestión de gastos con integración al ERP; (3) BPMS con DMN nativo (p. ej., Camunda o Bizagi) + portal propio. Criterios: DMN editable por Finanzas, worklist móvil, timers con calendario hábil, API REST, lectura de CFDI.
- **Integraciones**: ERP (alta de acreedor, póliza de gasto, archivo de pagos) vía REST o conector; si el ERP es legacy sin API, **RPA** como puente temporal en T06; banca electrónica (layout de pagos y respuesta de rechazos); directorio/organigrama (jefeId, gerenteId); validación de CFDI ante el SAT [A VALIDAR alcance fiscal]; correo y notificaciones push.

## 7. Gestión del cambio
- **DICE**: *Duration*: fases de 6–8 semanas con revisión al cierre de cada una · *Integrity*: equipo con el DF (owner y sponsor), Marta (CxP), un líder de TI, Luis como jefe piloto y Ana como usuaria piloto · *Commitment*: el DF comunica el "por qué" (pagar en una semana) y la Dirección general respalda el SLA de 48 h · *Effort*: formación ≤ 1 h por rol y guía de una página.
- **Quick wins** (S1) visibles en el primer mes: corrida semanal y aprobación dos veces por semana; publicar el cycle time medido.
- Riesgos de resistencia: jefes que pierden "control" con la ruta AUTO → mostrar auditoría por muestreo; CxP que pasa de capturar a auditar → re-perfilar el puesto (heurística *specialize*), sin recorte de plantilla; miedo a "Gran Hermano" → los dashboards no se usan para evaluar personas.
- Evitar la **victoria prematura**: mantener al equipo hasta M12 y medir K1–K10 cada mes.

## 8. Roadmap de implantación gradual

| Fase | Plazo | Entregables | KPIs de salida |
|---|---|---|---|
| 0 · Línea base | M0–M1 | Muestreo de 30–50 informes; validación del as-is con expertos; política actualizada (umbral, topes, plazo, tolerancia) aprobada por el DF | Supuestos de 06 sustituidos por datos |
| 1 · Quick wins (S1) | M1–M3 | Aprobación martes/viernes con 48 h; corrida semanal; plantilla Excel validada; alta de acreedor en onboarding | K1 mediana ≤ 14 d; K4 ≥ 90 % |
| 2 · Selección y diseño | M2–M4 | Elección de herramienta; DMN D1–D3 configuradas y probadas con casos históricos; contrato de integración ERP | DMN sin solapamientos/huecos en pruebas |
| 3 · Piloto S2 | M4–M6 | Área comercial (≈ 25 % del volumen) en el portal; T06 vía servicio o RPA | K2 P90 ≤ 2 d en el piloto |
| 4 · Despliegue | M6–M9 | Resto de áreas; T15 automatizada; auditoría por muestreo | K6 ≤ 5 min |
| 5 · Estabilización | M9–M12 | Dashboards (10-monitorizacion.md); revisión de TOL; evaluación de S3 | K1 mediana ≤ 7 d naturales; K5 ≤ 180 MXN |
