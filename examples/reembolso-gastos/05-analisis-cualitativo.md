# 05 · Análisis cualitativo (F4)

Cliente: **empleado que viajó**; outcome positivo: *reembolso correcto pagado*. Las cifras de impacto salen del flow analysis de `06-analisis-cuantitativo.md`.

## 1. Value-added analysis (VA / BVA / NVA)

| Paso | Actividad | Rol | Clase | Justificación |
|---|---|---|---|---|
| Registrar los gastos y adjuntar comprobantes | T01 | Empleado | BVA | Documentación exigida por Finanzas y fiscal; el cliente no la "pagaría" |
| Escanear tickets uno a uno | T01 | Empleado | NVA | Motion: se digitaliza un papel que luego se recaptura |
| Enviar el correo al jefe | T02 | Empleado | NVA | Handoff |
| Esperar al viernes | IE1 | — | NVA | Espera por batching |
| Revisar razonabilidad y tickets | T03 | Jefe | BVA | Control de gasto (riesgo de abuso) |
| Devolver con observaciones / reenviar todo | T04, T01–T02 | Jefe, Empleado | NVA | Defecto + rework + handoffs |
| Aprobar y reenviar a CxP | T05 | Jefe | BVA (aprobar) / NVA (reenviar) | Autorización requerida; el reenvío es handoff |
| Capturar el informe en el ERP | T06 | CxP | NVA | Doble captura de datos que ya existen en Excel (BPR: dato único en origen) |
| Verificar completitud, plazo y topes | T07 | CxP | BVA | Control de política; **duplica parcialmente** el control del jefe sobre tickets |
| Devolver informe incompleto | T08 | CxP | NVA | Defecto detectado tarde |
| Solicitar y decidir excedente | T09, T10 | CxP, DF | BVA (decidir) / NVA (solicitar) | Control de excepción; la solicitud es handoff |
| Ajustar monto al tope | T11 | CxP | BVA | Cumplimiento de política |
| Verificar / solicitar / dar de alta proveedor | T12–T14 | CxP, TI | NVA (verificar, solicitar) / BVA (alta) | Requisito técnico del ERP resuelto de forma reactiva |
| Esperar la corrida quincenal | IE2 | — | NVA | Espera por batching |
| Pagar el reembolso | T15 | CxP | **VA** | Lo que el cliente quiere |

Resultado: de ~16 pasos, **1 VA**, 7 BVA y 8 NVA (incluidas 2 esperas por lote). Los BVA se conservan pero se buscará su **mínimo** (p. ej., que el control del jefe y el de CxP no revisen lo mismo).

## 2. Las 7 mudas sobre el modelo

| Grupo | Muda | Dónde en el as-is | Evidencia |
|---|---|---|---|
| Move | **Transporte** (handoffs) | 8 cruces de lane en el camino feliz y en las ramas: Empleado→Jefe (T02), Jefe→Empleado (T04), Jefe→CxP (T05), CxP→Empleado (T08), CxP→DF (T09), DF→CxP (G3), CxP→TI (T13), TI→CxP (T14) + message flow al banco | Modelo 04 |
| Move | Motion | Excel → escáner → correo → ERP: el mismo dato pasa por 4 herramientas; CxP cambia entre correo y ERP | IN-01, IN-03 |
| Hold | **Inventario (WIP)** | ≈ 222 informes abiertos en promedio (Little: 12/día × 18.5 días) = dinero adelantado por empleados | 06 |
| Hold | **Espera** | Viernes de revisión (≈ 4 d), cola de CxP (≈ 3 d), corrida quincenal (≈ 5 d), DF (≈ 2 d), TI (2 d) | IN-02, IN-03, 06 |
| Overdo | **Defectos** | 15 % devueltos por CxP + devoluciones del jefe (≈ 10 % [SUPUESTO]) → 23.5 % de casos con al menos un rework, y reenvío completo | IN-01, IN-03 |
| Overdo | Overprocessing | Jefe y CxP revisan ambos la presencia de tickets; informes < 1,000 MXN revisados aunque la política los exime; CxP recaptura todo | IN-02, IN-04 |
| Overdo | Overproduction | Informes entregados fuera de plazo que recorren jefe y captura antes de rechazarse (el rechazo era **previsible** con la fecha) | IN-04 |

## 3. Issue register (solo issues de primer nivel)

| ID | Nombre | Descripción | Prioridad | Datos y supuestos | Impacto cualitativo | Impacto cuantitativo |
|---|---|---|---|---|---|---|
| I1 | Revisión semanal del jefe | El jefe revisa los informes solo los viernes, en bloque | Alta | IN-02 (viernes), IN-01 (> 1 semana); espera media 4 d hábiles [SUPUESTO: 2.5 d por el lote + 30 % de casos que se saltan un viernes] | Empleado sin dinero; sin visibilidad | **4.0 días hábiles/caso** (22.9 % del CT atribuible a issues) |
| I2 | Rework por informes incompletos | Informes devueltos por falta de tickets o datos, con reenvío completo | Alta | 15 % en CxP [DATO IN-03], 10 % en jefe [SUPUESTO]; 1.31 intentos por caso | Frustración, doble trabajo de 3 roles | **2.37 d/caso**; ≈ 0.31 intentos extra × 60 × 48 ≈ 880 reprocesos/año ≈ 207,000 MXN/año |
| I3 | Captura manual en ERP | CxP recaptura en el ERP lo que el empleado ya registró en Excel, y forma una cola | Alta | 10 min/informe [DATO IN-03]; cola ≈ 3 d [SUPUESTO]; CxP cerca de saturación (ρ ≥ 0.93, 06) | Errores de transcripción [SUPUESTO], CxP sin tiempo para control | **2.7 d/caso**; ≈ 565 h/año de captura (incl. recapturas) ≈ 113,000 MXN/año [SUPUESTO tarifa 200 MXN/h] |
| I4 | Corrida de pagos quincenal | Los informes listos esperan a la siguiente corrida quincenal | Alta | IN-03; espera media = ½ periodo = 5 d hábiles | Retraso al final, cuando todo está aprobado | **4.85 d/caso** (27.7 %) |
| I5 | Preparación tardía del informe | El empleado tarda en preparar el informe tras el viaje | Media | [SUPUESTO] 3 d hábiles; formato Excel + escaneo es tedioso (IN-01) | Riesgo de exceder los 30 días y perder el reembolso | **3.0 d/caso** (17.1 %) |
| I6 | Excedentes escalan al DF | Cualquier excedente, por pequeño que sea, requiere autorización del DF por correo | Media | IN-03; 20 % de informes con excedente [SUPUESTO]; espera del DF 2 d [SUPUESTO] | Carga de la alta dirección en decisiones menores | 0.39 d/caso; ≈ 93 h/año del DF [SUPUESTO] |
| I7 | Alta reactiva de proveedor | La cuenta de proveedor del empleado se crea en el momento de pagar | Baja | IN-03 (2 días); 10 % de casos [SUPUESTO] | Retraso de primeros viajeros | 0.19 d/caso |
| I8 | Política desactualizada y no aplicada | La política v2019 no se aplica (< 1,000 MXN) y su control de plazo no tiene responsable | Media | IN-04 vs IN-02 | Riesgo de cumplimiento y de auditoría; trato desigual entre áreas | No cuantificable sin datos [A MEDIR] |
| I9 | Sin visibilidad del estado | El empleado no sabe en qué paso está su informe | Media | IN-01 ("me depositan como al mes") | Consultas por correo, desconfianza | No cuantificado [A MEDIR: consultas/semana a CxP] |

## 4. Pareto (efecto = días hábiles de cycle time por caso atribuibles a cada issue)

| Rank | Issue | Días/caso | % | % acumulado |
|---|---|---|---|---|
| 1 | I4 Corrida de pagos quincenal | 4.85 | 27.7 % | 27.7 % |
| 2 | I1 Revisión semanal del jefe | 4.00 | 22.9 % | 50.6 % |
| 3 | I5 Preparación tardía del informe | 3.00 | 17.1 % | 67.7 % |
| 4 | I3 Captura manual en ERP (cola de CxP) | 2.70 | 15.4 % | **83.1 %** |
| 5 | I2 Rework por informes incompletos | 2.37 | 13.5 % | 96.6 % |
| 6 | I6 Excedentes escalan al DF | 0.39 | 2.2 % | 98.8 % |
| 7 | I7 Alta reactiva de proveedor | 0.19 | 1.1 % | 100 % |
| | *Total atribuible (excluye 0.97 d de liquidación bancaria)* | *17.5* | | |

→ 4 issues (I4, I1, I5, I3) explican el **83 %** del cycle time; **todos son esperas o colas**, no tiempo de trabajo (CTE ≈ 0.9 %, ver 06). Si el efecto se mide en **coste**, I3 (captura) e I2 (rework) pasan al frente: ambos se tratan juntos.

## 5. PICK chart

| Cuadrante | Acciones |
|---|---|
| **Implement** (mucho payoff, fácil) | Revisión del jefe 2 veces por semana con SLA de 48 h (I1); corrida de pagos **semanal** (I4) [A VALIDAR con Tesorería]; checklist/plantilla Excel con validaciones de topes y campos obligatorios (I2); aplicar la regla < 1,000 MXN (I8) |
| **Possible** (poco payoff, fácil) | Alta de la cuenta de proveedor en el onboarding del empleado (I7); recordatorio al empleado a los 7 y 20 días del viaje (I5); tolerancia de excedente ≤ 10 % sin DF (I6) |
| **Challenge** (mucho payoff, difícil — elegir uno) | **Portal/app de gastos con BPMS, reglas DMN e integración con el ERP** (I2, I3, I5, I9, y habilita I1/I4) |
| **Kill** (poco payoff, difícil) | Contratar más personal en CxP para absorber la captura (trata el síntoma); reescribir toda la política antes de mejorar el flujo |

## 6. Causa raíz

### Ishikawa (6M) — efecto: *cycle time ≈ 1 mes* (I1 + I4 + I3)
- **Machine**: no hay sistema de flujo; correo como "workflow"; Excel y ERP sin integración; el ERP exige cuenta de proveedor.
- **Method**: revisión del jefe y pagos en **lotes** (viernes, quincena); dos controles secuenciales que revisan lo mismo; alta de proveedor reactiva; sin SLA ni escalado.
- **Material**: informes incompletos o con tickets ilegibles; formato Excel sin validaciones.
- **Man**: jefes sin tiempo entre semana (IN-02); CxP dedicado a captura en lugar de control.
- **Measurement**: no se mide el cycle time ni el tiempo por etapa; nadie ve el WIP.
- **Milieu**: calendario de pagos de Tesorería; banco (liquidación ~1 d).

### Why-why — I1 Revisión semanal del jefe
1. ¿Por qué tarda el jefe? → Porque revisa solo los viernes.
2. ¿Por qué solo los viernes? → Porque entre semana no tiene tiempo y el correo no le recuerda nada (IN-02).
3. ¿Por qué no tiene tiempo? → Porque revisa **cada** informe a detalle, incluso los de bajo monto que la política exime (I8), y porque revisar un Excel + escaneos es lento.
4. ¿Por qué revisa todo? → Porque no hay reglas automáticas que filtren lo conforme, ni un compromiso de tiempo (SLA) ni visibilidad de la espera.
- **Causas raíz**: (a) ausencia de un canal de aprobación con SLA y escalado; (b) control manual sin triage por riesgo.

### Why-why — I4 Corrida de pagos quincenal
1. ¿Por qué se espera hasta 10 días hábiles para pagar? → Porque los reembolsos se pagan en la corrida quincenal de proveedores.
2. ¿Por qué en esa corrida? → Porque el empleado se trata como **proveedor** en el ERP y hereda su calendario.
3. ¿Por qué ese calendario? → Optimización de tesorería para pagos a terceros [SUPUESTO], no pensada para empleados.
- **Causa raíz**: calendario de pagos diseñado para acreedores externos aplicado a un cliente interno.

### Why-why — I2 Rework por informes incompletos
1. ¿Por qué se devuelven informes? → Faltan tickets o datos.
2. ¿Por qué faltan? → El formato Excel no obliga a adjuntar comprobante por partida y el empleado descubre el error días después.
3. ¿Por qué tan tarde? → El control ocurre **al final** (jefe el viernes, CxP días después), no en el momento de capturar.
4. ¿Por qué se reenvía todo? → El correo no permite corregir solo la partida faltante.
- **Causas raíz**: (a) control ubicado lejos del origen del dato (heurística *control relocation*); (b) ausencia de un registro único del informe que admita correcciones parciales.
