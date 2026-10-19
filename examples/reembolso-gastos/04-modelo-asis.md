# 04 · Modelo as-is (F3 Discovery)

Archivos: `04-asis.json` (fuente) → `04-asis.bpmn` (BPMN 2.0 con diagrama). Propósito: **modelo conceptual** para análisis y validación con los expertos (sin detalles de TI).

Estructura: pool **Nubia SA** (lanes: Empleado, Jefe inmediato, Cuentas por Pagar, Director financiero, TI) + pool black box **Banco**. 28 flow objects (≤ 30, 7PMG G7).

## Narrativa (para validar con los expertos, Ch 5)
1. Cuando el empleado **concluye su viaje**, llena el formato de gastos en Excel y escanea los tickets (T01), y lo envía por correo a su jefe (T02). (IN-01)
2. El informe espera en el correo del jefe **hasta el viernes**, día en que revisa en bloque (evento timer IE1). (IN-02)
3. El jefe revisa que los montos tengan sentido y que estén los tickets (T03). Si falta algo, lo devuelve con observaciones (T04) y el empleado tiene que **volver a preparar y mandar todo** (vuelta a T01). Si está bien, lo aprueba respondiendo el correo y lo reenvía a Cuentas por Pagar (T05). (IN-01, IN-02)
4. Cuentas por Pagar captura el informe en el ERP, unos 10 minutos (T06), y verifica la política (T07): completitud, plazo de 30 días y topes (hospedaje 1,800 MXN/noche, comidas 600 MXN/día). (IN-03, IN-04)
5. Si está **incompleto** (~15 %), CxP lo devuelve al empleado (T08), que vuelve al paso 1. Si se entregó **más de 30 días** después del viaje, se rechaza y el proceso termina (E2) [SUPUESTO sobre quién lo controla]. (IN-03, IN-04)
6. Si está completo y en plazo pero **excede un tope**, CxP pide autorización al director financiero (T09), que decide (T10). Si no lo autoriza, CxP ajusta el monto al tope (T11) [SUPUESTO]. (IN-03)
7. CxP verifica si el empleado tiene **cuenta de proveedor** en el ERP (T12). Si no, solicita el alta (T13) y TI la da de alta, lo que tarda unos 2 días (T14). (IN-03)
8. El informe espera a la **corrida quincenal** (IE2) y CxP paga los reembolsos en la corrida (T15), enviando el archivo de pagos al banco. El proceso termina con el **reembolso pagado** (E1). (IN-03, IN-01)

## Catálogo de actividades

| ID | Actividad | Rol (lane) | Tipo | Entradas | Salidas | Sistema | Tiempo de proceso | Fuente |
|---|---|---|---|---|---|---|---|---|
| T01 | Preparar informe de gastos | Empleado | Manual | Tickets, gastos del viaje | Informe [Excel], tickets escaneados | Excel, escáner | 30 min [SUPUESTO] | IN-01 |
| T02 | Enviar informe al jefe | Empleado | Envío | Informe + escaneos | Correo al jefe | Correo | 2 min [SUPUESTO] | IN-01 |
| T03 | Revisar informe de gastos | Jefe inmediato | Usuario | Correo con informe | Decisión (completo/razonable o no) | Correo | 5 min [SUPUESTO] | IN-02 |
| T04 | Devolver informe con observaciones | Jefe inmediato | Envío | Decisión negativa | Correo de devolución | Correo | 3 min [SUPUESTO] | IN-01 |
| T05 | Aprobar informe por correo | Jefe inmediato | Envío | Decisión positiva | Correo reenviado a CxP | Correo | 2 min [SUPUESTO] | IN-02 |
| T06 | Capturar informe en ERP | Cuentas por Pagar | Usuario | Correo aprobado | Registro en ERP | ERP | **10 min [DATO]** | IN-03 |
| T07 | Verificar política de gastos | Cuentas por Pagar | Usuario | Registro, manual v2019 | Resultado de verificación | ERP, manual | 5 min [SUPUESTO] | IN-03, IN-04 |
| T08 | Devolver informe incompleto | Cuentas por Pagar | Envío | Resultado "incompleto" | Correo al empleado | Correo | 3 min [SUPUESTO] | IN-03 |
| T09 | Solicitar autorización de excedente | Cuentas por Pagar | Envío | Partidas excedidas | Correo al DF | Correo | 3 min [SUPUESTO] | IN-03 |
| T10 | Decidir gasto excedente | Director financiero | Usuario | Solicitud | Autorización / negativa | Correo | 10 min [SUPUESTO] | IN-03 |
| T11 | Ajustar monto al tope | Cuentas por Pagar | Usuario | Negativa del DF | Monto ajustado | ERP | 5 min [SUPUESTO] | C4 |
| T12 | Verificar cuenta de proveedor | Cuentas por Pagar | Usuario | Registro | Existe / no existe | ERP | 2 min [SUPUESTO] | IN-03 |
| T13 | Solicitar alta de proveedor | Cuentas por Pagar | Envío | Datos del empleado | Solicitud a TI | Correo/ticket | 3 min [SUPUESTO] | IN-03 |
| T14 | Dar de alta proveedor | TI | Usuario | Solicitud | Cuenta de proveedor | ERP | 15 min de proceso [SUPUESTO]; **2 días de duración [DATO]** | IN-03 |
| T15 | Pagar reembolsos en corrida | Cuentas por Pagar | Usuario | Informes listos | Archivo de pagos al banco | ERP, banca | 2 min/informe [SUPUESTO] | IN-03 |

Eventos: S1 *Viaje concluido* · IE1 *Viernes de revisión alcanzado* (timer) · IE2 *Corrida quincenal alcanzada* (timer) · E1 *Reembolso pagado* · E2 *Informe rechazado por plazo*.
Gateways: G1 ¿Informe completo y razonable? · G2 ¿Informe completo y en plazo? · G2b ¿Excede tope de política? · G3 ¿Excedente autorizado? · G4 ¿Empleado tiene cuenta de proveedor? · M1, M3, M4 (joins XOR).
Datos: D1 Informe de gastos [Excel] · D2 Tickets escaneados · D3 ERP (data store) · mensaje *Archivo de pagos* al Banco.

## Reglas de negocio

| ID | Regla | Fuente | Observación |
|---|---|---|---|
| RN1 | El informe debe entregarse ≤ 30 días después del viaje; si no, se rechaza | IN-04 | Control no descrito por nadie [A VALIDAR] |
| RN2 | Hospedaje máximo 1,800 MXN por noche | IN-03 | ¿Incluye impuestos? [A VALIDAR] |
| RN3 | Comidas máximo 600 MXN por día | IN-03 | ¿Por día de viaje o por día con comprobante? [A VALIDAR] |
| RN4 | Excedente de tope → autorización del director financiero | IN-03 | Sin umbral de tolerancia |
| RN5 | Informes < 1,000 MXN se aprueban sin revisión del jefe | IN-04 | **No se aplica en la práctica** (C1) |
| RN6 | Sin cuenta de proveedor en el ERP no se puede pagar | IN-03 | El alta es reactiva, en el momento del pago |
| RN7 | Los pagos se hacen en la corrida quincenal | IN-03 | — |

## Excepciones (rainy-days modelados)
- Informe devuelto por el jefe (T04) o por CxP (T08) → rework completo desde T01.
- Informe fuera de plazo → E2 (outcome negativo).
- Excedente no autorizado → reembolso parcial (T11).
- Empleado sin cuenta de proveedor → alta por TI (T13–T14).
- **No modelados por falta de evidencia** [A VALIDAR]: correo perdido o informe olvidado (no existe timeout ni recordatorio en el as-is), ausencia del jefe (vacaciones), pago rechazado por el banco (cuenta bancaria errónea), duplicidad de informes.

## Matriz RACI

| Actividad | Empleado | Jefe inmediato | CxP | DF | TI |
|---|---|---|---|---|---|
| T01 Preparar informe de gastos | **R/A** | | | | |
| T02 Enviar informe al jefe | **R/A** | I | | | |
| T03 Revisar informe de gastos | | **R/A** | | | |
| T04 Devolver informe con observaciones | I | **R/A** | | | |
| T05 Aprobar informe por correo | | **R/A** | I | | |
| T06 Capturar informe en ERP | | | **R/A** | | |
| T07 Verificar política de gastos | | | **R** | A | |
| T08 Devolver informe incompleto | I | I | **R/A** | | |
| T09 Solicitar autorización de excedente | | | **R** | I | |
| T10 Decidir gasto excedente | I | C | I | **R/A** | |
| T11 Ajustar monto al tope | I | | **R** | A | |
| T12 Verificar cuenta de proveedor | | | **R/A** | | |
| T13 Solicitar alta de proveedor | | | **R/A** | | I |
| T14 Dar de alta proveedor | | | I | | **R/A** |
| T15 Pagar reembolsos en corrida | I | | **R** | A | |

## Validación
- **Sintáctica** (`bpmn_tool.py validate 04-asis.bpmn`): **0 errores, 0 advertencias**; soundness correcta (sin deadlocks, sin falta de sincronización, sin actividades muertas). 1 start, 2 ends (un end por outcome).
- Advertencias resueltas durante el modelado: el gateway de verificación tenía 5 caminos (7PMG G2) → se dividió en G2 (completitud/plazo) y G2b (tope); "Ejecutar corrida de pagos" usaba un verbo genérico (G6) → "Pagar reembolsos en corrida".
- **Semántica** (validez y completitud): **pendiente**. Validar la narrativa anterior con Ana, Luis, Marta, el DF y TI en una sesión de 60 min; obtener la firma del process owner.
