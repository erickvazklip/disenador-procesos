# 01 · Ficha del proceso (F1 Identificación)

## Process Checklist (Ch 2)

| # | Pregunta | Veredicto | Evidencia |
|---|---|---|---|
| 1 | ¿Es un proceso? (acción principal sobre una categoría de casos) | **Sí**. Acción: *reembolsar gastos de viaje*; outcome: *gastos reembolsados* | IN-01..IN-03 |
| 2 | ¿Se puede controlar? (noción de caso y repetición) | **Sí**. Caso = un informe de gastos de un viaje; ~60 casos por semana | IN-03 |
| 3 | ¿Es lo bastante importante? | **Sí**. Lo exige el control interno y fiscal (comprobación de gastos), se podría externalizar (proveedores de *expense management*) y afecta al empleado que adelanta su dinero | IN-01, IN-04 |
| 4 | ¿El alcance no es demasiado grande? (relación 1:1 con el disparador) | **Sí**. Todas las actividades se ejecutan una vez por informe (salvo rework). La solicitud del viaje y la compra de boletos quedan fuera | — |
| 5 | ¿El alcance no es demasiado pequeño? (≥ 3 actores además del cliente) | **Sí**. Jefe inmediato, Cuentas por Pagar, Director financiero, TI (+ banco) | IN-02, IN-03 |

## Nombre
- Proceso: **reembolso de gastos de viaje** (expense-to-reimbursement).
- Acción principal: **Reembolsar gastos de viaje**.

## Process profile

| Campo | Contenido |
|---|---|
| Visión | Que todo empleado reciba el reembolso correcto de sus gastos de viaje en pocos días, con un esfuerzo mínimo y en cumplimiento de la política de gastos |
| Process owner | Director financiero [SUPUESTO] (quien hoy autoriza excepciones y controla CxP) |
| Cliente y expectativas | **Empleado que viajó** (cliente interno): rapidez del depósito, pocas idas y vueltas, transparencia del estado. Cliente secundario: **Finanzas/Contabilidad** (gasto correcto, comprobado y registrado) |
| Outcome positivo | Reembolso pagado (por el monto conforme a la política) |
| Outcomes negativos | Informe rechazado por plazo (> 30 días); excedente no autorizado (reembolso parcial); informe devuelto (outcome intermedio) |
| Disparador | Viaje concluido (el empleado regresa con comprobantes) |
| Primera actividad | T01 Preparar informe de gastos |
| Última actividad | T15 Pagar reembolsos en corrida |
| Interfaces de entrada | Proceso de **solicitud/organización de viajes** (upstream, no descrito) [A VALIDAR]; alta de empleados (cuenta de proveedor) |
| Interfaces de salida | **Tesorería / corrida de pagos** (pago bancario); **cierre contable** (gasto registrado en el ERP) |
| Recursos | Empleados viajeros, jefes inmediatos (~4 equivalentes), analista(s) de CxP, Director financiero, TI; Excel, correo, escáner, ERP, banca electrónica; manual de gastos v2019 |
| KPIs | Cycle time viaje→pago, tiempo de aprobación del jefe, first-pass yield, coste de procesamiento por informe, % aprobación automática, cumplimiento de política (ver 03-kpis.md) |

## Alcance
- **Dentro**: desde que el empleado concluye el viaje hasta que el reembolso se paga; incluye revisión, aprobación, verificación de política, autorización de excedentes, alta de la cuenta de proveedor del empleado y la corrida de pagos.
- **Fuera**: solicitud y autorización del viaje, compra de boletos y hospedaje, anticipos de viaje, tarjetas corporativas, conciliación bancaria, cierre contable, deducibilidad fiscal (CFDI) [A VALIDAR si debe incluirse].

## Categoría y relaciones
- **Categoría**: proceso de **soporte** (finanzas). Referencia APQC PCF: categoría 9 *Gestionar recursos financieros* → grupo de cuentas por pagar y reembolso de gastos (código exacto [A VALIDAR] contra la versión PCF vigente).
- **Secuencia**: upstream *organizar viaje de negocio* → **reembolsar gastos de viaje** → downstream *pagar a acreedores (corrida)* y *cerrar periodo contable*.
- **Descomposición**: subproceso del macroproceso *procure-to-pay / cuentas por pagar*.
- **Especialización**: variantes posibles por tipo de gasto (viaje nacional, internacional, gastos menores no ligados a viaje) [A VALIDAR]; este expediente modela el viaje nacional en MXN.

## Stakeholders (5 categorías del Ch 6)

| Categoría | Quién | Interés principal | Issues percibidos |
|---|---|---|---|
| Clientes | Empleados que viajan (p. ej. Ana) | Recibir el dinero pronto y sin rework | Espera > 1 semana del jefe; reenvíos completos; pago "como al mes" (IN-01) |
| Participantes | Jefes inmediatos (Luis), CxP (Marta), DF, TI | Carga de trabajo razonable, entradas completas | Falta de tiempo entre semana (IN-02); captura manual y 15 % incompletos (IN-03); altas de proveedor urgentes (IN-03) |
| Partes externas | Banco (pagos); SAT/auditor externo [A VALIDAR] | Archivos de pago correctos; comprobación fiscal | — (no entrevistados) |
| Process owner y gestores | Director financiero [SUPUESTO], gerente de CxP | Cumplimiento de política, coste de procesamiento, control | Excepciones que llegan sin contexto; política v2019 sin actualizar |
| Sponsor y alta dirección | Dirección general | Productividad comercial, satisfacción del personal | Tiempo comercial invertido en trámites (no medido) |

## Arquitectura de procesos
No aplica `02-arquitectura.md`: el insumo describe un único proceso y no se pidió landscape.
