from flask import Flask, request, jsonify
import pymssql
import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DB_CONFIG = {
    "server": "sqlserver-dev",
    "user": "sa",
    "password": "Srishti!sqlw0rd",
    "database": "vitComplianceSystem"
}

DEST_COLUMNS = [
    "UNID", "ComplianceInstanceID", "ComplianceScheduleOnID",
    "Performerid", "Reviewerid", "Approverid", "ScheduleOn", "ForMonth",
    "IsActive", "IsUpcomingNotDeleted", "IsChecklistWorkFlow", "IsDocMan_NonMan",
    "EventScheduledOnID", "ParentEventD",

    "ComplianceTransactionID", "StatusId", "Remarks", "StatusChangedOn",
    "Penalty", "Interest", "IsPenaltySave", "PenaltySubmit",

    "InsertedOn", "InsertedOnMS",
    "TableSource", "ChangeType"
]

DATETIME_COLUMNS = ["ScheduleOn", "StatusChangedOn", "InsertedOn"]

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

@app.route('/ingest', methods=['POST'])
def ingest():
    app.logger.info(">>> /ingest endpoint hit")

    try:
        records = request.get_json(force=True)
        if not isinstance(records, list):
            return jsonify({"error": "Expected a JSON array of records"}), 400

        results = []
        for i, record in enumerate(records):
            try:
                result = handle_single_record(record)
                app.logger.info(f"Record {i} result: {result}")
                results.append({"index": i, **result})
            except Exception as e:
                app.logger.exception(f"Error processing record {i}")
                results.append({"index": i, "error": str(e)})

        return jsonify(results), 200

    except Exception as e:
        app.logger.exception("Bulk ingest failed")
        return jsonify({"error": "Invalid request", "details": str(e)}), 500

def handle_single_record(payload):
    conn = cursor = None
    try:
        value = payload.get("payload")
        if not value:
            return {"status": "skipped", "reason": "Missing 'payload' in record"}

        op = value.get("op")
        source_table = value.get("source", {}).get("table")
        data = value.get("after") if op != "d" else value.get("before")

        if not data:
            return {"status": "skipped", "reason": "No data in 'after' or 'before'"}

        unid = data.get("UNID")
        schedule_id = data.get("ComplianceScheduleOnID")
        if not unid or not schedule_id:
            return {"status": "skipped", "reason": "UNID or ComplianceScheduleOnID missing"}

        destination_table = f"[dbo].[{unid}_dashboard_summary]"

        enriched = enrich_data_from_both_sources(data, source_table)
        enriched["TableSource"] = source_table
        enriched["ChangeType"] = op
        enriched.setdefault("InsertedOn", datetime.datetime.now())
        enriched.setdefault("InsertedOnMS", int(datetime.datetime.utcnow().timestamp() * 1000))

        for col in DEST_COLUMNS:
            enriched.setdefault(col, None)

        for field in DATETIME_COLUMNS:
            val = enriched.get(field)
            if isinstance(val, int):  # from Debezium timestamp
                try:
                    enriched[field] = datetime.datetime.fromtimestamp(val / 1000.0)
                except:
                    enriched[field] = None

        conn = pymssql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create table with composite primary key
        create_sql = f"""
            IF OBJECT_ID(N'{destination_table}', N'U') IS NULL
            BEGIN
                EXEC('
                    CREATE TABLE {destination_table} (
                        UNID INT NOT NULL,
                        ComplianceScheduleOnID BIGINT NOT NULL,

                        ComplianceInstanceID BIGINT NULL,
                        Performerid BIGINT NULL,
                        Reviewerid BIGINT NULL,
                        Approverid BIGINT NULL,
                        ScheduleOn DATETIME NULL,
                        ForMonth VARCHAR(200) NULL,
                        IsActive BIT NULL,
                        IsUpcomingNotDeleted BIT NULL,
                        IsChecklistWorkFlow BIT NULL,
                        IsDocMan_NonMan BIT NULL,
                        EventScheduledOnID BIGINT NULL,
                        ParentEventD BIGINT NULL,

                        ComplianceTransactionID BIGINT NULL,
                        StatusId INT NULL,
                        Remarks VARCHAR(MAX) NULL,
                        StatusChangedOn DATETIME NULL,
                        Penalty DECIMAL(14,2) NULL,
                        Interest DECIMAL(14,2) NULL,
                        IsPenaltySave BIT NULL,
                        PenaltySubmit VARCHAR(2) NULL,

                        InsertedOn DATETIME2,
                        InsertedOnMS BIGINT,

                        TableSource VARCHAR(100),
                        ChangeType VARCHAR(10),

                        CONSTRAINT PK_{unid}_Dashboard PRIMARY KEY (UNID, ComplianceScheduleOnID)
                    )
                ')
            END
        """
        cursor.execute(create_sql)
        conn.commit()

        # UPSERT logic
        cursor.execute(f"""
            SELECT 1 FROM {destination_table}
            WHERE UNID = %s AND ComplianceScheduleOnID = %s
        """, (unid, schedule_id))
        exists = cursor.fetchone()

        if op == "d":
            cursor.execute(f"""
                DELETE FROM {destination_table}
                WHERE UNID = %s AND ComplianceScheduleOnID = %s
            """, (unid, schedule_id))

        elif exists:
            update_fields = ", ".join([
                f"{col} = %({col})s" for col in DEST_COLUMNS
                if col not in ["UNID", "ComplianceScheduleOnID"]
            ])
            cursor.execute(f"""
                UPDATE {destination_table}
                SET {update_fields}
                WHERE UNID = %(UNID)s AND ComplianceScheduleOnID = %(ComplianceScheduleOnID)s
            """, enriched)

        else:
            cursor.execute(f"""
                INSERT INTO {destination_table} (
                    {', '.join(DEST_COLUMNS)}
                ) VALUES (
                    {', '.join([f'%({col})s' for col in DEST_COLUMNS])}
                )
            """, enriched)

        conn.commit()
        return {"status": "success", "op": op}

    except Exception as e:
        app.logger.exception("Exception in handle_single_record")
        raise

    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def enrich_data_from_both_sources(data, source_table):
    d = dict(data)
    compliance_schedule_id = d.get("ComplianceScheduleOnID")

    try:
        conn = pymssql.connect(**DB_CONFIG)
        cursor = conn.cursor(as_dict=True)

        if source_table == "ComplianceTransaction" and compliance_schedule_id:
            cursor.execute("""
                SELECT Performerid, Reviewerid, Approverid, ScheduleOn, ForMonth,
                       IsActive, IsUpcomingNotDeleted, IsChecklistWorkFlow, IsDocMan_NonMan,
                       EventScheduledOnID, ParentEventD
                FROM ComplianceScheduleOn
                WHERE ComplianceScheduleOnID = %s
            """, (compliance_schedule_id,))
        elif source_table == "ComplianceScheduleOn" and compliance_schedule_id:
            cursor.execute("""
                SELECT ComplianceTransactionID, StatusId, Remarks, StatusChangedOn,
                       Penalty, Interest, IsPenaltySave, PenaltySubmit
                FROM ComplianceTransaction
                WHERE ComplianceScheduleOnID = %s
            """, (compliance_schedule_id,))
        else:
            return d

        row = cursor.fetchone()
        if row:
            d.update(row)
    except Exception as e:
        app.logger.warning(f"Error enriching data: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    return d

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)
