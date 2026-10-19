# 03 · KPIs (F2 Medición)

Método de 3 pasos (Ch 2): objetivo → medida (dimensión + función de agregación) → objetivo refinado → **target con plazo**. Plazos contados desde el arranque del proyecto (M0) [SUPUESTO: M0 = enero 2027].

| ID | Objetivo de alto nivel | Dimensión | Medida (agregación) | Línea base | Target con plazo | Fuente de medición |
|---|---|---|---|---|---|---|
| K1 | Pagar rápido al empleado | Tiempo | **Cycle time** *viaje concluido → reembolso pagado*, en días naturales: **mediana y P90** por mes | ≈ 30 días naturales [DATO percibido, IN-01]; modelo: 18.5 días hábiles ≈ 26 naturales [SUPUESTO calibrado, 06] | Mediana ≤ 14 d en M3 (quick wins); mediana ≤ 7 d y P90 ≤ 12 d en M12 | Fecha fin de viaje (campo del informe) y fecha de pago (ERP / archivo bancario) |
| K2 | Aprobar sin demoras | Tiempo | Tiempo *informe enviado → decisión del jefe*: **P90** en días hábiles | Hasta > 5 días hábiles ("más de una semana", IN-01); revisión solo los viernes (IN-02); media modelada 4 d [SUPUESTO] | P90 ≤ 2 días hábiles en M6 | Hoy: no medible (correo). To-be: timestamps del BPMS (T03 creado / completado) |
| K3 | Reducir el tiempo interno de Finanzas | Tiempo | Tiempo *aprobado → contabilizado*: media en días hábiles | ≈ 3 días [SUPUESTO] | ≤ 0.5 días en M9 (contabilización automática) | ERP / BPMS (T06) |
| K4 | Recibir informes correctos a la primera | Calidad | **First-pass yield** = % informes sin ninguna devolución (por mes) | ≈ 76.5 % = (1 − 0.10) × (1 − 0.15) [15 % DATO IN-03; 10 % del jefe SUPUESTO] | ≥ 90 % en M3; ≥ 97 % en M12 | Hoy: conteo manual de CxP; to-be: log del BPMS (repeticiones de T20) |
| K5 | Abaratar el trámite | Coste | **Coste de procesamiento por informe** (mano de obra, media mensual, MXN) | ≈ 366 MXN/informe ≈ 1.05 M MXN/año [SUPUESTO tarifas, 06] | ≤ 330 en M3; ≤ 180 en M12 | ABC con tiempos del log × tarifa por rol (Ch 11) |
| K6 | Liberar a CxP de la captura | Coste | Minutos de CxP por informe (media) | ≈ 23 min [10 min captura DATO IN-03 + SUPUESTOS] | ≤ 5 min en M12 | Log del BPMS + muestreo de tiempos |
| K7 | Cumplir la política de gastos | Calidad (interna) | % de informes auditados por muestreo **sin hallazgos**; % de informes con excedente autorizado | No medido [A MEDIR] | ≥ 98 % sin hallazgos en M12; excedentes ≤ 10 % de informes | Registro de auditoría (T23) |
| K8 | Adaptarse a cambios de política sin TI | Flexibilidad | **Tiempo para cambiar un tope o umbral** de la política en producción (días hábiles) | Política sin revisar desde 2019; cambio requeriría circular un manual [SUPUESTO] | ≤ 1 día hábil en M12 (DMN editable por Finanzas) | Bitácora de versiones de la tabla DMN |
| K9 | Automatizar lo de bajo riesgo | Flexibilidad / Coste | % de informes con **aprobación automática** (ruta AUTO) | 0 % (la regla < 1,000 MXN no se aplica, IN-02 vs IN-04) | ≥ 30 % en M12 [A VALIDAR distribución de montos] | Log del BPMS (salida de T21) |
| K10 | Empleado satisfecho con el trámite | Calidad (externa) | CSAT trimestral (1–5) de empleados que viajaron | Sin medir [A MEDIR en M0] | ≥ 4.0 en M12 | Encuesta breve tras el pago |

Notas
- K1 se reporta en días **naturales** (lo que percibe el empleado); los cálculos internos de 06 usan días hábiles de 8 h.
- Antes del to-be, K2–K4 solo pueden medirse con muestreo manual (por ejemplo, 30 informes al mes con fechas del correo): se recomienda levantarlo en M0 para sustituir los supuestos por datos.
