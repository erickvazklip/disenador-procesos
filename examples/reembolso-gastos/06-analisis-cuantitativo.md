# 06 · Análisis cuantitativo (F5)

"Mejor aproximadamente correcto que precisamente equivocado" (Ch 7). **No hay event log**: salvo 4 datos de IN-03 (60 informes/semana, 10 min de captura, 15 % incompletos, 2 días de alta), todos los parámetros son **[SUPUESTO]** y se someten a sensibilidad. Cálculos reproducibles en `06-calculos.py`.

Unidades: día hábil = 8 h = 480 min; 48 semanas laborables/año; **λ = 60 informes/semana = 12/día** [DATO IN-03].

## 1. Parámetros

| Parámetro | Valor | Tipo |
|---|---|---|
| Espera del empleado antes de preparar (1.er intento / reintento) | 3 d / 1 d | SUPUESTO |
| Espera hasta la revisión del jefe | 4 d (2.5 d del lote semanal + 30 % de casos que se saltan un viernes × 5 d) | SUPUESTO (IN-02: viernes; IN-01: "> 1 semana") |
| Devolución por el jefe p_j | 0.10 | SUPUESTO |
| Espera en cola de CxP | 3 d | SUPUESTO |
| Devolución por CxP p_c | 0.15 | **DATO IN-03** |
| Fuera de plazo | 0.03 | SUPUESTO |
| Excede tope / DF no autoriza | 0.20 / 0.30 | SUPUESTO |
| Espera del DF | 2 d | SUPUESTO |
| Sin cuenta de proveedor / duración del alta | 0.10 / 2 d | SUPUESTO / **DATO IN-03** |
| Espera a la corrida quincenal | 5 d (½ de 10 d hábiles) | Derivado de IN-03 |
| Liquidación bancaria | 1 d | SUPUESTO |
| Tiempos de proceso | ver catálogo en 04 (T06 = 10 min DATO) | SUPUESTO salvo T06 |
| Tarifas (MXN/h) | Empleado 250 · Jefe 450 · CxP 200 · DF 1,200 · TI 250 | SUPUESTO (coste laboral cargado; regla Ch 11: salario × 1.2 / (240 × 8 × 60) por minuto) |

## 2. Flow analysis (cycle time)

El bucle de rework tiene **dos salidas** de devolución (jefe y CxP) que vuelven a T01. Probabilidad de pasar ambos filtros en un intento: (1 − 0.10)(1 − 0.15) = **0.765** → intentos esperados **n = 1/0.765 = 1.307** (equivale a r = 0.235 en la fórmula x/(1−r)).

CT de un intento (sin preparación) = espera jefe + (1 − p_j) × espera CxP = 4 + 0.9 × 3 = **6.7 d**

CT del bucle = prep. inicial + (n − 1) × prep. reintento + n × 6.7 = 3 + 0.307 × 1 + 1.307 × 6.7 = **12.07 d**

CT posterior (solo el 97 % en plazo): 0.97 × [0.20 × 2 (DF) + 0.10 × 2 (TI) + 5 (corrida) + 1 (banco)] = 0.97 × 6.6 = **6.40 d**

**CT ≈ 12.07 + 6.40 = 18.5 días hábiles ≈ 26 días naturales.** Contraste: Ana percibe "como al mes" (≈ 21–22 hábiles, IN-01). La diferencia (≈ 3 d) sugiere que alguna espera está subestimada (probablemente la del jefe o la del empleado) → priorizar su medición.

## 3. TCT y CTE

TCT (solo tiempo de proceso):
- Bucle: n × [T01 30 + T02 2 + T03 5 + 0.1 × T04 3 + 0.9 × (T05 2 + T06 10 + T07 5 + 0.15 × T08 3)] = 1.307 × 52.7 ≈ 68.9 min
- Posterior: 0.97 × [0.2 × (T09 3 + T10 10 + 0.3 × T11 5) + T12 2 + 0.1 × (T13 3 + T14 15) + T15 2] = 0.97 × 9.1 ≈ 8.8 min
- **TCT ≈ 77.7 min**

**CTE = TCT / CT = 77.7 / (18.47 × 480) = 0.88 %** → por debajo del 5 % típico de procesos administrativos (Blackburn): **el margen está en las esperas y los lotes, no en acelerar tareas.**

## 4. Ruta crítica (CPM)
El modelo no tiene AND-splits: todas las actividades del camino feliz (sin rework, sin DF, con cuenta) están en serie, así que **la ruta crítica es el camino completo** y ninguna tarea tiene holgura.
Camino feliz: S1 → T01 → T02 → IE1 → T03 → T05 → T06 → T07 → T12 → IE2 → T15 → E1 · CT = 3 + 4 + 3 + 5 + 1 = **16 d**; TCT = 58 min.
Implicación: solo se acorta el CT **eliminando esperas** o **paralelizando** (p. ej., validación de política en paralelo a la aprobación del jefe; ver 07).

## 5. Coste por caso (mano de obra)

| Rol | Unit load (min/caso) | Cálculo | Coste/caso (MXN) |
|---|---|---|---|
| Empleado | 41.8 | 1.307 × (30 + 2) | 174.3 |
| Jefe | 9.3 | 1.307 × (5 + 0.1 × 3 + 0.9 × 2) | 69.6 |
| CxP | 23.2 | 1.307 × 0.9 × (10 + 5 + 0.15 × 3) + 0.97 × (0.2 × (3 + 0.3 × 5) + 2 + 0.1 × 3 + 2) | 77.4 |
| DF | 1.9 | 0.97 × 0.2 × 10 | 38.8 |
| TI | 1.5 | 0.97 × 0.1 × 15 | 6.1 |
| **Total** | **77.7** | | **366 MXN/informe ≈ 1.05 M MXN/año** (60 × 48) |

El rework (0.307 intentos extra) cuesta ≈ 0.307 × (32 × 250 + 7.1 × 450 + 0.9 × 15.45 × 200)/60 ≈ **72 MXN/informe ≈ 207,000 MXN/año**. La captura manual (T06) cuesta 10 × 1.307 × 0.9 × 200/60 ≈ 39 MXN/informe ≈ **113,000 MXN/año** (≈ 565 h/año incluyendo recapturas).

## 6. Capacidad, cuello de botella y utilización

Carga diaria = λ × ul:

| Pool | ul (min) | Carga (min/día) | Capacidad disponible [SUPUESTO] | μ = uc/ul (informes/día) | ρ = λ/μ |
|---|---|---|---|---|---|
| CxP | 23.2 | 278.6 (= 4.6 h) | 5 h/día dedicadas a reembolsos | 12.9 | **0.93** |
| Jefes (≈ 4; λ = 3/día cada uno) | 9.3 | 27.8 por jefe | 1 h/día | 6.5 | 0.46 |
| DF | 1.9 | 23.3 | 1 h/día | 30.9 | 0.39 |
| TI (altas) | 1.5 | 17.5 | 1 h/día | 41 | 0.29 |

→ **Cuello de botella: CxP** (menor μ). Con ρ = 0.93 la cola es muy sensible: con 4 h/día dedicadas, ρ = 1.16 → **sistema inestable** (la cola crece sin límite). Los jefes **no** tienen un problema de capacidad, sino de **batching** (su espera nace del calendario, no de la carga).

Cola de CxP como M/M/1 (aproximación; un equipo que trabaja en bloque = 1 servidor; exponencialidad [SUPUESTO no verificado]): λ = 12, μ = 12.9 → ρ = 0.93, **Lq = ρ²/(1 − ρ) = 12.1 informes**, **Wq = Lq/λ = 1.0 d**, W = Wq + 1/μ ≈ 1.1 d. El supuesto de 3 d de espera en CxP implicaría una dedicación menor o trabajo por lotes adicional [A VALIDAR: horas reales de CxP en reembolsos].

## 7. Little

**WIP = λ × CT = 12 × 18.5 ≈ 222 informes abiertos** en promedio. Con un importe medio de X MXN por informe [A VALIDAR], los empleados financian ≈ 222·X MXN (p. ej., con X = 5,000, ≈ 1.1 M MXN). Comprobación sugerida: contar los informes abiertos un día cualquiera; si son ≈ 260–280, el CT real ronda los 22–23 d hábiles (consistente con IN-01).

## 8. Sensibilidad (CT en días hábiles; base 18.5)

| Variación | CT | Δ |
|---|---|---|
| Espera del jefe 2.5 d (sin saltos de viernes) | 16.5 | −2.0 |
| Espera del jefe 6 d | 21.1 | +2.6 |
| Espera en CxP 1 d | 16.1 | −2.4 |
| Espera en CxP 5 d | 20.8 | +2.4 |
| p_j = 0.05 | 18.1 | −0.3 |
| p_j = 0.20 | 19.3 | +0.8 |
| Corrida **semanal** | 16.0 | −2.4 |
| Preparación inicial 1 d | 16.5 | −2.0 |
| Preparación inicial 5 d | 20.5 | +2.0 |

Las palancas de mayor efecto son **esperas** (jefe, CxP, corrida, preparación); las probabilidades de rework afectan poco al CT pero mucho al coste.

## 9. Especificación para simulación (BIMP o similar)

| Elemento | Especificación |
|---|---|
| Llegadas | Exponencial, media 40 min entre informes en horario 9:00–17:00, L–V (12/día); [A VALIDAR] picos a fin de mes y tras temporadas de viaje |
| T01 | Normal (30 min, σ 20 %); pool Empleados (ilimitado); inicio retrasado: exponencial media 3 d |
| T03 | Normal (5 min, σ 20 %); pool Jefes (4) con **calendario: solo viernes 9–13 h** |
| T06, T07 | Fija 10 min (T06) / normal (5, σ 20 %); pool CxP (1 recurso, 5 h/día) |
| T10 | Exponencial media 10 min; pool DF (1) con calendario 1 h/día |
| T14 | Duración fija 2 d (cola de TI) |
| T15 | Timer: cada 2 semanas (día 15 y último) |
| Gateways | G1 0.9/0.1 · G2 0.15 incompleto / 0.03 plazo / 0.82 sigue · G2b 0.2/0.8 · G3 0.7/0.3 · G4 0.9/0.1 |
| Corridas | ≥ 10 réplicas de 3 meses (≈ 720 casos); aceptar si la variación entre réplicas ≤ ±10 % |
| Salidas | CT medio y P90, espera por tarea, utilización de CxP, WIP; sensibilidad ±1 recurso en CxP y ±10 % de tiempos |

## 10. Event log
No aplica: no se entregó event log. Se especifica cuál capturar en `10-monitorizacion.md`; mientras tanto se recomienda un **muestreo manual de 30–50 informes** (fechas de viaje, envío, aprobación por correo, captura en ERP y pago) para sustituir los supuestos de espera.
