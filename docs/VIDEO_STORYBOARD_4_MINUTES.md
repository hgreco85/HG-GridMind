# HG GridMind — Video Demo Storyboard (4 Minutos)

**Competencia:** Open Agent Hackathon 2026  
**Track:** Challenge 02 — *The Agent That Can Explain Why*  
**Duración Total:** Exactamente 3 minutos y 50 segundos.  

---

### [00:00 – 00:25] Bloque 1: El Problema Operativo y el Costo del Error
- **Pantalla:** Terminal / Tablero SCADA ficticio mostrando alarmas de sobrecorriente repetidas en el transformador TR-404.
- **Narración:**  
  *"En la operación de infraestructura eléctrica, una alarma de sobrecorriente suele inducir a sospechas inmediatas de falla interna en transformadores, provocando cortes preventivos costosos o reemplazos innecesarios. ¿Qué pasaría si tuviéramos un agente de operaciones que no solo diagnostica, sino que demuestra rigurosamente por qué su diagnóstico es correcto y falsa activamente las explicaciones erróneas? Presentamos HG GridMind."*

---

### [00:25 – 01:00] Bloque 2: Integración de Datos Fragmentados con Zetaris
- **Pantalla:** Diagrama de silos de datos conectándose a la consulta federada de Zetaris. Ejecución de `execute_federated_query("INCIDENT_AUDIT")`.
- **Narración:**  
  *"Las organizaciones operan con datos fragmentados: los tickets de usuarios viven en una base de atención, los ensayos de laboratorio de aceite viven en registros de mantenimiento, y las corrientes instantáneas fluyen por SCADA. Con Zetaris, GridMind consulta estos tres silos en una única pasada lógica unificada, extrayendo las filas de evidencia exactas sin requerir duplicación ni migraciones de datos."*

---

### [01:00 – 02:05] Bloque 3: Razonamiento Causal con Nemotron y Falsación de Hipótesis
- **Pantalla:** Ejecución en vivo de `commander.investigate_incident()`. Aparición en pantalla de la hipótesis inicial y su proceso de descarte.
- **Narración:**  
  *"El operador sospechaba daño en la cuba de aceite. Pero GridMind invoca el razonamiento de NVIDIA Nemotron junto a un validador determinístico. Al inspeccionar el ensayo cromatográfico DGA con identificador MAINT-ROW-99182, observa concentraciones normales de hidrógeno y acetileno: esto descarta tajantemente la falla dieléctrica interna.  
  Inmediatamente, GridMind cruza la telemetría SCADA (SCADA-ROW-55102), descubriendo un desbalance severo: Fase B absorbe 445 Amperes, drenando 268 Amperes hacia el neutro. Al verificar la última termografía (MAINT-ROW-99204), encuentra que el borne de neutro tenía una conexión floja con 42°C de sobretemperatura. El agente une las piezas: no es una falla interna; es un borne de neutro sobrecargado por desbalance de cargas."*

---

### [02:05 – 02:50] Bloque 4: Explicación del "Por Qué" y Puerta de Aprobación Humana
- **Pantalla:** Muestra en pantalla de la `IncidentDiagnosis` con la explicación narrativa y el intento de despacho de maniobra interceptado por el `HumanApprovalGate`.
- **Narración:**  
  *"GridMind no es una caja negra: emite una narrativa causal completa y fundamentada en citas a nivel de fila. Pero ningún agente autónomo debe conmutar alimentadores de energía sin control. Basado en la arquitectura HG Operator, GridMind incorpora un Human Approval Gate fail-closed: el plan de maniobra —transferir carga a alimentador de reserva y reapretar el borne— queda suspendido de forma segura hasta recibir la aprobación criptográfica del operador humano."*

---

### [03:00 – 03:30] Bloque 5: Resiliencia ante Información Faltante
- **Pantalla:** Ejecución con un caso sintético con datos faltantes. El agente emite abstención explícita.
- **Narración:**  
  *"La explicabilidad también exige honestidad epistemológica: ante una pérdida de telemetría, GridMind no alucina causas; emite una abstención segura indicando qué datos faltan para alcanzar una conclusión válida."*

---

### [03:30 – 03:50] Bloque 6: Tecnologías Sponsor, Licencia y Conclusiones
- **Pantalla:** Logotipos y menciones técnicas: Zetaris, NVIDIA Nemotron, Cursor. Repositorio GitHub con licencia MIT.
- **Narración:**  
  *"HG GridMind fue desarrollado en Cursor utilizando Zetaris y Nemotron bajo un presupuesto estricto de cero dólares. Código abierto bajo licencia MIT, demostrando que la explicabilidad operativa rigurosa y auditable es hoy una realidad."*
