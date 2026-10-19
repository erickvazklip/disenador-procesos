# 08 · Modelo to-be (F7) — escenario S2 "Workflow digital con reglas"

Archivos: `08-tobe.json` → `08-tobe.bpmn`. Pool **Nubia SA** (lanes: Empleado, Sistema de gastos (BPMS), Jefe inmediato, Director financiero, Cuentas por Pagar) + pool black box **Banco**. 22 flow objects + 1 boundary event (≤ 30).

## Narrativa
1. Al **concluir el viaje**, el empleado registra sus gastos en el portal o app, con foto o CFDI de cada comprobante (T20).
2. El sistema **valida el informe contra la política** (T21, DMN): si falta un comprobante o un dato, se lo indica en el momento y el empleado corrige solo esa partida (vuelta a T20); si se entregó más de 30 días después del viaje, se rechaza (E2).
3. Si es válido y es **< 1,000 MXN dentro de tope**, se aprueba automáticamente (ruta AUTO). Si no, va al **jefe inmediato**, que lo aprueba en su worklist o móvil (T03). Si en **48 h hábiles** no decide, el sistema **escala** el work item a su gerente (B1 → T22) y vuelve a quedar pendiente de aprobación.
4. El jefe puede pedir corrección (vuelta a T20), rechazar (E3) o aprobar. Si lo aprobado **excede un tope**, el **director financiero** decide el excedente (T10): lo autoriza o lo limita al tope; el sistema aplica el monto.
5. El sistema **contabiliza el informe en el ERP** (T06), creando el acreedor-empleado si no existe. Una muestra (≈ 10 % aleatorio + todos los excedentes) pasa a **auditoría** de CxP (T23).
6. En la **corrida semanal**, el sistema paga los reembolsos (T15), envía el archivo al banco y notifica al empleado: **reembolso pagado** (E1).

## Cambios frente al as-is

| Tipo | As-is | To-be | Motivo (issue / heurística) |
|---|---|---|---|
| Eliminado | T01 Preparar informe de gastos (Excel + escaneo) | — (sustituido por T20) | I2, I5 · BPR dato en origen |
| Eliminado | T02 Enviar informe al jefe | Enrutado automático del BPMS | Handoff NVA |
| Eliminado | IE1 Viernes de revisión alcanzado | — | I1 · case-based work |
| Eliminado | T04 Devolver informe con observaciones / T08 Devolver informe incompleto | Ruta "requiere corrección" / INCOMPLETO con corrección parcial | I2 · contact reduction |
| Eliminado | T05 Aprobar informe por correo | Integrado en T03 (worklist) | Handoff NVA |
| Eliminado | T07 Verificar política de gastos (manual) | T21 automática | I2, I8 · activity automation, control relocation |
| Eliminado | T09 Solicitar autorización de excedente | Enrutado automático | Handoff NVA |
| Eliminado | T11 Ajustar monto al tope | Aplicado por el sistema según la decisión de T10 | Automation |
| Eliminado | T12, T13, T14 (verificar / solicitar / dar de alta proveedor) | Acreedor creado en onboarding o por T06 | I7 · resequencing, automation |
| **Nuevo** | — | T20 Registrar gastos en portal (user) | I2, I5, I9 |
| **Nuevo** | — | T21 Validar informe contra política (business rule, DMN) | I2, I8 · knock-out, triage |
| **Nuevo** | — | B1 timer 48 h + T22 Escalar aprobación al gerente | I1 |
| **Nuevo** | — | T23 Auditar informe por muestreo (CxP) | Control addition (compensa la ruta AUTO) |
| **Nuevo** | — | E3 Informe rechazado por jefe | Outcome negativo explícito (antes implícito en el correo) |
| Modificado | T03 Revisar informe de gastos | T03 Aprobar informe de gastos (worklist, SLA) — ya no revisa tickets, solo razonabilidad | I1 · empower, activity elimination |
| Modificado | T10 Decidir gasto excedente | Solo excedentes por encima de la tolerancia [A VALIDAR] | I6 · empower |
| **Automatizado** | T06 Capturar informe en ERP | T06 Contabilizar informe en ERP (service) | I3 |
| **Automatizado** | T15 Pagar reembolsos en corrida (quincenal, manual) | T15 (service), **semanal** | I4 |

## Impacto esperado en los KPIs (estimado, [SUPUESTO])

| KPI | Base | To-be estimado | Target |
|---|---|---|---|
| K1 CT viaje → pago | 18.5 d hábiles (≈ 26 naturales; percibido ≈ 30) | 5.3 d hábiles (≈ 7.4 naturales) | mediana ≤ 7 d naturales (M12) |
| K2 P90 aprobación del jefe | > 5 d hábiles | ≤ 2 d por diseño (timer + escalado) | ≤ 2 d |
| K4 First-pass yield | 76.5 % | ≈ 95 % | ≥ 97 % (requiere buena UX del portal) |
| K5 Coste por informe | 366 MXN | 159 MXN (−56 %) | ≤ 180 MXN |
| K6 Min. de CxP por informe | 23.2 | 2.8 | ≤ 5 |
| K9 % AUTO | 0 % | 35 % [SUPUESTO distribución de montos] | ≥ 30 % |

## Supuestos del to-be
- La distribución de montos permite ≈ 35 % de informes < 1,000 MXN sin excedentes [A VALIDAR con datos del ERP].
- El ERP expone (o puede exponer) servicios para registrar el gasto, crear acreedores y generar el archivo de pagos [A VALIDAR con TI].
- Tesorería acepta una corrida **semanal** para empleados [A VALIDAR].
- Los hallazgos de auditoría (T23) se resuelven fuera del flujo (descuento en el siguiente reembolso o vía nómina) [SUPUESTO; requiere política].
- El escalado reasigna al gerente del jefe; el organigrama está disponible en el BPMS [SUPUESTO].

## Validación
`bpmn_tool.py validate 08-tobe.bpmn`: **0 errores, 0 advertencias**; soundness correcta. 1 start y 3 ends (pagado, rechazado por plazo, rechazado por jefe: uno por outcome).
Ajustes durante el modelado: (1) el escalado se modeló primero como **boundary timer non-interrupting** que terminaba en su propio end event; la herramienta lo marcó como falta de sincronización porque el timer puede dispararse varias veces → se cambió a **timer interrumpiente con reasignación** (T22 → vuelve a T03), que además es más fiel al patrón de escalado del Ch 10. (2) Los gateways G1 y G3 tenían 5 caminos (7PMG G2) → se separaron en G1/G1b y G3/G3b.
