# CDC Project - Under TeamLease Regtech Pvt. Ltd.

## Prerequisites

1. **Docker Desktop**
   - 8GB RAM allocated to Docker
   - Ports used: 1433, 5050, 9092, 8083

2. **SQL Client** (one of these)
   - Azure Data Studio
   - SQL Server Management Studio

## Running the Project

1. **Start Services**
   ```bash
   # Start all containers
   docker-compose up -d

   # Wait for about 60 seconds for all services to initialize
   ```

2. **Verify Services**

   a. **Check Container Status**
   ```bash
   docker ps
   ```
   Should show all containers running:
   - sqlserver-dev
   - redpanda
   - kafka-connect
   - api-server

   b. **Check API Server**
   ```bash
   curl http://localhost:5050/ping
   ```
   Should return: `pong`

   c. **Check Kafka Connect**
   ```bash
   # List connectors
   curl -s http://localhost:8083/connectors | jq

   # Should show:
   # [
   #   "sqlserver-cdc",
   #   "http-sink"
   # ]

   # Check connector status
   curl -s http://localhost:8083/connectors/sqlserver-cdc/status | jq
   curl -s http://localhost:8083/connectors/http-sink/status | jq

   # Both should show "state": "RUNNING"
   ```

## Testing the Pipeline

1. **Connect to SQL Server**
   ```
   Host: localhost
   Port: 1433
   Database: vitComplianceSystem
   Username: sa
   Password: Srishti!sqlw0rd
   ```

2. **View Existing Data**
   ```sql
   -- Check current data in source tables
   SELECT * FROM ComplianceScheduleOn;
   SELECT * FROM ComplianceTransaction;

   -- List all tables (including dashboard tables)
   SELECT TABLE_NAME 
   FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_TYPE = 'BASE TABLE';
   ```

3. **Test Data Operations**

   a. **Insert Schedule Data**
   ```sql
   -- Insert into ComplianceScheduleOn with all fields
   INSERT INTO dbo.ComplianceScheduleOn (
     ComplianceScheduleOnID, UNID, ComplianceInstanceID, Performerid,
     Reviewerid, Approverid, ScheduleOn, ForMonth,
     IsActive, IsUpcomingNotDeleted, IsChecklistWorkFlow, IsDocMan_NonMan,
     EventScheduledOnID, ParentEventD
   ) VALUES (
     400, 125, 6004, 1004,
     2006, 3006, '2025-07-22 10:00:00', 'Jul-2025',
     1, 1, 1, 1, 7006, 0
   );

   -- Verify dashboard table creation and data
   SELECT * FROM [dbo].[125_dashboard_summary];
   ```

   b. **Insert Transaction Data**
   ```sql
   -- Insert corresponding transaction
   INSERT INTO dbo.ComplianceTransaction (
     UNID,
     ComplianceInstanceID,
     ComplianceScheduleOnID,
     StatusId,
     Remarks,
     StatusChangedOn,
     Penalty,
     Interest,
     IsPenaltySave,
     PenaltySubmit
   )
   VALUES (
     125,                 
     6002,                
     400,                  
     1,                   
     'Initial submission',
     '2025-07-22 15:00:00',
     250.00,              
     20.50,              
     1,                   
     'Y'                  
   );

   -- Verify data in dashboard
   SELECT * FROM [dbo].[125_dashboard_summary];
   ```

   c. **Update Data**
   ```sql
   -- Update transaction details
   UPDATE dbo.ComplianceTransaction
   SET
     StatusId = 2,
     Remarks = 'Updated after review',
     StatusChangedOn = '2025-07-22 17:30:00',
     Penalty = 300.00,
     Interest = 25.75,
     IsPenaltySave = 0,
     PenaltySubmit = 'N'
   WHERE
     UNID = 125 AND
     ComplianceScheduleOnID = 400;

   -- Verify changes in dashboard
   SELECT * FROM [dbo].[125_dashboard_summary];
   ```

   d. **Delete Data**
   ```sql
   -- Delete specific transaction
   DELETE FROM dbo.ComplianceTransaction
   WHERE UNID = 90 AND ComplianceScheduleOnID = 100;

   -- Verify deletion reflected in dashboard
   SELECT * FROM [dbo].[90_dashboard_summary];
   ```

4. **Monitor Changes**

   a. **Check Kafka Topics**
   ```bash
   # View redpanda topics:
   docker exec -it redpanda rpk topic list

   # View changes in ComplianceScheduleOn topic
   docker exec -it redpanda rpk topic consume sqlserver.vitComplianceSystem.dbo.ComplianceScheduleOn -o start

   # View changes in ComplianceTransaction topic
   docker exec -it redpanda rpk topic consume sqlserver.vitComplianceSystem.dbo.ComplianceTransaction -o start
   ```

   b. **Check Dashboard Tables**
   ```sql
   -- List all dashboard tables
   SELECT TABLE_NAME 
   FROM INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME LIKE '%dashboard_summary';

   -- Check specific dashboard table
   SELECT * FROM [125_dashboard_summary]
   ORDER BY InsertedOn DESC;
   ```

   c. **View Change History**
   ```sql
   -- Check CDC change tables
   SELECT * FROM cdc.dbo_ComplianceScheduleOn_CT;
   SELECT * FROM cdc.dbo_ComplianceTransaction_CT;
   ```

5. **Expected Results**

   After running the test queries:
   - A new dashboard table `125_dashboard_summary` should be created
   - The dashboard table should show:
     - Initial schedule data (UNID=125, ComplianceScheduleOnID=400)
     - Transaction data with initial values
     - Updated transaction values after the UPDATE
   - Kafka topics should contain:
     - Insert events for schedule and transaction
     - Update event for transaction
     - Delete event for UNID=90 transaction

## Troubleshooting

1. **If Connectors are Not Running**
   ```bash
   # Check connector logs
   docker logs kafka-connect

   # Restart connector if needed
   curl -X POST http://localhost:8083/connectors/sqlserver-cdc/restart
   curl -X POST http://localhost:8083/connectors/http-sink/restart
   ```

2. **If SQL Server is Not Accessible**
   ```bash
   # Check SQL Server logs
   docker logs sqlserver-dev

   # Verify CDC is enabled
   SELECT is_cdc_enabled FROM sys.databases WHERE name = 'vitComplianceSystem';
   SELECT * FROM cdc.change_tables;
   ```

3. **If Dashboard Tables are Not Created**
   ```bash
   # Check API server logs
   docker logs api-server

   # List all tables
   SELECT TABLE_NAME 
   FROM vitComplianceSystem.INFORMATION_SCHEMA.TABLES 
   WHERE TABLE_NAME LIKE '%dashboard_summary';
   ```

## Stopping the Project

```bash
# Stop all services
docker-compose down

# To completely clean up (including volumes)
docker-compose down -v
```

## Expected Behavior

1. When you insert/update/delete in source tables:
   - Changes appear in Redpanda topics
   - API server processes the changes
   - Dashboard summary tables are updated

2. Dashboard tables:
   - Created automatically based on UNID
   - Combine data from both source tables
   - Track all changes (insert/update/delete)

3. CDC Pipeline:
   - Captures all changes in real-time
   - Maintains data consistency
   - Handles transaction boundaries properly 
