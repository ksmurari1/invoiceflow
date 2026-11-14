-- Runs once, on first initialization of the Postgres data volume.
-- Creates the database used by the backend test suite.
CREATE DATABASE invoiceflow_test OWNER invoiceflow;
