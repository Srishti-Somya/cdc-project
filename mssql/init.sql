IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'vitComplianceSystem')
BEGIN
    CREATE DATABASE vitComplianceSystem;
END
GO

WHILE DB_ID('vitComplianceSystem') IS NULL
BEGIN
    WAITFOR DELAY '00:00:01';
END
GO

USE vitComplianceSystem;
GO

IF EXISTS (SELECT * FROM sys.databases WHERE name = 'vitComplianceSystem' AND is_cdc_enabled = 0)
BEGIN
    EXEC sys.sp_cdc_enable_db;
END
GO

IF OBJECT_ID('dbo.ComplianceScheduleOn', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ComplianceScheduleOn (
        ComplianceScheduleOnID BIGINT NOT NULL PRIMARY KEY,
        UNID INT NULL,
        ComplianceInstanceID BIGINT NULL,
        Performerid BIGINT NULL,
        Reviewerid BIGINT NULL,
        Approverid BIGINT NULL,
        ScheduleOn DATETIME NOT NULL,
        ForMonth VARCHAR(200) NULL,
        IsActive BIT NULL,
        IsUpcomingNotDeleted BIT NULL,
        IsChecklistWorkFlow BIT NULL,
        IsDocMan_NonMan BIT NULL,
        EventScheduledOnID BIGINT NULL,
        ParentEventD BIGINT NULL,
        InsertedOn DATETIME2 DEFAULT SYSDATETIME(),
        InsertedOnMS BIGINT DEFAULT DATEDIFF_BIG(MILLISECOND, '1970-01-01', SYSDATETIME())
    );
END
GO

IF OBJECT_ID('dbo.ComplianceTransaction', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ComplianceTransaction (
        ComplianceTransactionID BIGINT IDENTITY(1,1) PRIMARY KEY,
        UNID INT NULL,
        ComplianceInstanceID BIGINT NOT NULL,
        ComplianceScheduleOnID BIGINT NULL,
        StatusId INT NOT NULL,
        Remarks VARCHAR(MAX) NOT NULL,
        StatusChangedOn DATETIME NULL,
        Penalty DECIMAL(14,2) NULL,
        Interest DECIMAL(14,2) NULL,
        IsPenaltySave BIT NULL,
        PenaltySubmit VARCHAR(2) NULL,
        InsertedOn DATETIME2 DEFAULT SYSDATETIME(),
        InsertedOnMS BIGINT DEFAULT DATEDIFF_BIG(MILLISECOND, '1970-01-01', SYSDATETIME())
    );
END
GO

-- IF OBJECT_ID('[dbo].[5_dashboard_summary]', 'U') IS NULL
-- BEGIN
--     CREATE TABLE [dbo].[5_dashboard_summary] (
--         SummaryID BIGINT IDENTITY(1,1) PRIMARY KEY,
--         UNID INT NULL,
--         ComplianceInstanceID BIGINT NULL,
--         ComplianceScheduleOnID BIGINT NOT NULL,
--         Performerid BIGINT NULL,
--         Reviewerid BIGINT NULL,
--         Approverid BIGINT NULL,
--         ScheduleOn DATETIME NOT NULL,
--         ForMonth VARCHAR(200) NULL,
--         IsActive BIT NULL,
--         IsUpcomingNotDeleted BIT NULL,
--         IsChecklistWorkFlow BIT NULL,
--         IsDocMan_NonMan BIT NULL,
--         EventScheduledOnID BIGINT NULL,
--         ParentEventD BIGINT NULL,
--         StatusId INT NOT NULL,
--         Remarks VARCHAR(MAX) NOT NULL,
--         StatusChangedOn DATETIME NULL,
--         Penalty DECIMAL(14,2) NULL,
--         Interest DECIMAL(14,2) NULL,
--         IsPenaltySave BIT NULL,
--         PenaltySubmit VARCHAR(2) NULL,
--         InsertedOn DATETIME2 DEFAULT SYSDATETIME(),
--         InsertedOnMS BIGINT DEFAULT DATEDIFF_BIG(MILLISECOND, '1970-01-01', SYSDATETIME()),
--         TableSource VARCHAR(100),
--         ChangeType VARCHAR(10)
--     );
-- END
-- GO

IF NOT EXISTS (
    SELECT 1 FROM cdc.change_tables WHERE source_object_id = OBJECT_ID('dbo.ComplianceScheduleOn')
)
BEGIN
    EXEC sys.sp_cdc_enable_table
        @source_schema = N'dbo',
        @source_name   = N'ComplianceScheduleOn',
        @role_name     = NULL,
        @supports_net_changes = 0;
END
GO

IF NOT EXISTS (
    SELECT 1 FROM cdc.change_tables WHERE source_object_id = OBJECT_ID('dbo.ComplianceTransaction')
)
BEGIN
    EXEC sys.sp_cdc_enable_table
        @source_schema = N'dbo',
        @source_name   = N'ComplianceTransaction',
        @role_name     = NULL,
        @supports_net_changes = 0;
END
GO
