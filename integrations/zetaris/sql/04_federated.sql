-- Q1: three-way federation (PostgreSQL datasource + 2 CSV filestore tables) for incident asset TR-102
SELECT s.row_id AS scada_row_id, s.ts, s.current_phase_b_amps, s.neutral_current_amps,
       m.row_id AS maint_row_id, m.verdict AS dga_verdict, m.acetylene_ppm,
       t.row_id AS ticket_row_id, t.ticket_type, t.reported_at
FROM gridmind_scada_pg.scada_telemetry s
JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id AND m.verdict <> 'NORMAL'
JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
WHERE s.asset_id = 'TR-102' AND s.neutral_current_amps > 15
ORDER BY s.ts DESC, t.row_id;
-- Q2: fleet summary across all three sources
SELECT s.asset_id, MAX(s.neutral_current_amps) AS max_neutral_a, COUNT(DISTINCT t.row_id) AS open_tickets,
       MAX(m.acetylene_ppm) AS max_acetylene_ppm
FROM gridmind_scada_pg.scada_telemetry s
LEFT JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id
LEFT JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
GROUP BY s.asset_id
ORDER BY s.asset_id;
