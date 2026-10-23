# HG GridMind — Slide Deck Outline (6 Slides)

**Competition:** Open Agent Hackathon 2026  
**Track:** Challenge 02 — *The Agent That Can Explain Why*  
**Author:** Horacio Greco (@hgreco85) | Team: HG Stack Operations  

---

### Slide 1: El Desafío Operativo: La Falacia de Correlación
- **Título:** Diagnósticos Operativos en Infraestructura Crítica: Por qué fallan los tableros tradicionales.
- **Puntos Clave:**
  - Ante una alarma en subestación (disparo térmico en transformador TR-404), la sospecha inicial suele culpar a la falla más destructiva (daño interno en cuba de aceite).
  - La sobre-reacción genera costos masivos: desconexión de clientes, cuadrillas de emergencia y reemplazos prematuros de activos de alto costo.
  - Los modelos LLM convencionales alucinan causas al carecer de anclaje probatorio determinístico.

---

### Slide 2: La Fragmentación de Datos Operativos
- **Título:** Datos Rotos: La realidad de los silos en empresas de servicios públicos.
- **Puntos Clave:**
  - Silo 1: Sistema de gestión de tickets (reportes de usuarios y alarmas de sala de control).
  - Silo 2: Base de datos de mantenimiento (ensayos de cromatografía DGA y termografía infrarroja).
  - Silo 3: Telemetría SCADA en tiempo real (voltajes, corrientes por fase y neutro).
  - Ninguna fuente por sí sola tiene la verdad completa.

---

### Slide 3: Arquitectura HG GridMind: Causalidad Explicable
- **Título:** Arquitectura Multicapa con Federación Zetaris y Razonamiento Nemotron.
- **Puntos Clave:**
  - **Capa de Datos:** Zetaris Virtual Query Engine consulta simultáneamente tickets, mantenimiento y SCADA con costo marginal cero.
  - **Capa de Razonamiento:** NVIDIA Nemotron formula hipótesis en competencia y realiza análisis causal deductivo.
  - **Capa de Control:** Validador determinístico de evidencia a nivel de fila (`row_id`) y cola de ejecución transaccional inspirada en HG Operator con ACK durable.

---

### Slide 4: Demostración en Vivo: Falsación y Explicación del "Por Qué"
- **Título:** Caso de Estudio INC-2026-UTIL-8812: Falsando la Hipótesis Errónea.
- **Puntos Clave:**
  - *Hipótesis Inicial:* Falla interna en cuba de transformador.
  - *Falsación Concluyente:* El análisis DGA (`MAINT-ROW-99182`) certifica concentraciones normales de H2 y C2H2; no existe degradación térmica interna.
  - *Causa Raíz Verificada:* Desbalance severo en Fase B (445.8 A vs 210 A, `SCADA-ROW-55102`) que descarga 268 A sobre borne flojo advertido en termografía (`MAINT-ROW-99204`).
  - *Resultado:* El transformador no requiere reemplazo; requiere rebalanceo de alimentador y reapriete programado.

---

### Slide 5: Métricas de Precisión y Evaluación Cuantitativa
- **Título:** Rendimiento Cuantitativo y Seguridad Operativa.
- **Puntos Clave:**
  - Precisión de Citas (`Row-level Citation Precision`): 100% sobre fixtures sintéticos (cero citas alucinadas).
  - Tasa de Falsación Correcta: 100% en casos control con prueba de contraejemplo.
  - Tasa de Abstención Segura: 100% ante datos incompletos (el agente se abstiene en vez de inventar).
  - Latencia de Ejecución: < 10 ms en validación local determinística.
  - Gasto de Inferencia: $0.00 (desarrollado bajo créditos y capas gratuitas de patrocinadores).

---

### Slide 6: Tecnologías Patrocinadoras, Gobernanza y Futuro
- **Título:** Stack Patrocinador y Despliegue con Human-in-the-Loop.
- **Puntos Clave:**
  - *Sponsors Integrados:* Zetaris (datos federados), NVIDIA Nemotron (razonamiento), Cursor (desarrollo).
  - *Gobernanza Estricta:* `HumanApprovalGate` bloquea cualquier maniobra física sobre la red hasta contar con autorización humana explícita.
  - *Licencia y Apertura:* 100% código abierto bajo licencia MIT en repositorio público independiente.
