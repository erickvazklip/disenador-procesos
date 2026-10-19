# 00 · Inventario de insumos (F0 Intake)

Proceso: **reembolso de gastos de viaje** · Organización: **Nubia SA** · Fecha del expediente: 2026-10-19

Fuente única: `../entrevista-reembolsos.md` (notas de entrevistas + extracto del manual de gastos). Se descompone en 4 insumos porque cada fragmento tiene distinto autor, rol y fiabilidad (Ch 5: conocimiento fragmentado).

| ID | Tipo | Fecha | Autor / rol | Fiabilidad (Ch 5) | Qué aporta |
|---|---|---|---|---|---|
| IN-01 | Nota de entrevista | s/f [A VALIDAR] | Ana, empleada del área comercial (cliente del proceso) | Percepción de un experto (cliente); cifras aproximadas ("más de una semana", "como al mes") | Disparador (regreso del viaje), formato Excel + tickets escaneados, envío por correo al jefe, devoluciones por ticket faltante con reenvío completo, cycle time percibido ≈ 1 mes |
| IN-02 | Nota de entrevista | s/f | Luis, jefe comercial (aprobador) | Percepción de un experto; volumen de su área | ~15 informes/semana en su área; revisión de montos y tickets; aprobación respondiendo el correo y reenvío a CxP; **revisión en bloque los viernes** |
| IN-03 | Nota de entrevista | s/f | Marta, Cuentas por Pagar | Percepción de un experto; contiene las cifras más concretas (60/semana, 10 min, 15 %, 2 días) | Volumen total ~60 informes/semana; captura manual en ERP de 10 min; topes de política (hospedaje 1,800 MXN/noche, comidas 600 MXN/día); autorización del director financiero si se excede; alta de cuenta de proveedor por TI (2 días); corrida de pagos quincenal; 15 % de informes incompletos devueltos |
| IN-04 | Documento normativo (extracto del manual de gastos v2019) | 2019 | Empresa (autor no indicado) | Documento normativo que **puede no reflejar la realidad** y puede estar desactualizado (7 años) | Plazo de entrega ≤ 30 días tras el viaje (si no, rechazo); aprobación automática por el jefe sin revisión para montos < 1,000 MXN |

## Cruce de fuentes y contradicciones detectadas

| # | Contradicción / hueco | Fuentes | Decisión de modelado |
|---|---|---|---|
| C1 | La política dice que < 1,000 MXN se aprueba "automáticamente por el jefe sin revisión", pero Luis describe que revisa todos los informes | IN-04 vs IN-02 | **Se modela lo real** (el jefe revisa todos) y se anota la desviación en el as-is (anotación A1) [A VALIDAR: ¿umbral por informe o por partida?] |
| C2 | Nadie menciona quién controla el plazo de 30 días | IN-04 | [SUPUESTO] CxP lo verifica en T07 junto con la política |
| C3 | Ana dice que la devuelve el jefe; Marta dice que CxP devuelve el 15 %. No se sabe a dónde vuelve el informe devuelto por CxP | IN-01, IN-03 | [SUPUESTO] ambos devuelven al empleado, que corrige y **reenvía todo al jefe** (Ana: "tengo que volver a mandar todo") |
| C4 | Qué pasa si el director financiero no autoriza el excedente | IN-03 | [SUPUESTO] se reembolsa hasta el tope (T11) |
| C5 | 15 informes/semana del área comercial vs 60 de toda la empresa | IN-02, IN-03 | Consistente: el comercial es ~25 % del volumen; [SUPUESTO] ~4 aprobadores equivalentes |
| C6 | El cycle time "como al mes" no está medido | IN-01 | Se usa como línea base percibida y se contrasta con el flow analysis (06) |
| C7 | No hay datos de tiempos de proceso del empleado, del jefe, del DF ni de TI (salvo duración de 2 días del alta) | — | Supuestos explícitos con análisis de sensibilidad (06) |
| C8 | No se mencionan comprobantes fiscales (CFDI) ni anticipos de viaje | — | Fuera del modelo; [A VALIDAR] relevancia fiscal en México |

## Limitaciones del discovery
- Solo hay entrevistas (una por rol) y un extracto normativo; **no hay evidencia objetiva** (event log, muestreo de informes, reportes del ERP). Las cifras son percepciones.
- No se entrevistó al director financiero, a TI ni a la tesorería.
- No hay validación del modelo con los expertos (se propone en 04-modelo-asis.md §Validación).
