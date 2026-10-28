CREATE DATASOURCE gridmind_scada_pg DESCRIBE BY "GridMind-synthetic-SCADA-PostgreSQL" OPTIONS (
  jdbcdriver "org.postgresql.Driver",
  jdbcurl "jdbc:postgresql://gridmind-demo-pg:5432/scada",
  username "gridmind",
  password "gridmind_demo_synthetic",
  fetchsize "1000"
);
REGISTER DATASOURCE TABLES FROM gridmind_scada_pg;
CREATE LIGHTNING DATABASE gridmind_files DESCRIBE BY "GridMind-synthetic-maintenance-and-tickets-CSV";
CREATE LIGHTNING FILESTORE TABLE maintenance_history FROM gridmind_files FORMAT CSV OPTIONS (
  path "/home/zetaris/customer-data/shared/gridmind/maintenance_history.csv",
  header "true",
  delimiter ","
);
CREATE LIGHTNING FILESTORE TABLE tickets_database FROM gridmind_files FORMAT CSV OPTIONS (
  path "/home/zetaris/customer-data/shared/gridmind/tickets_database.csv",
  header "true",
  delimiter ","
);
SHOW DATASOURCES;
SHOW LIGHTNING DATABASES;
SHOW LIGHTNING TABLES gridmind_files;
