#!/bin/sh

# Start SQL Server in background
/opt/mssql/bin/sqlservr &

# Wait for SQL Server to be ready
sleep 15

# Write mssql.conf dynamically inside mounted volume
cat <<EOF > /var/opt/mssql/mssql.conf
[sqlagent]
enabled = true
EOF

# Run initialization SQL
/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'Srishti!sqlw0rd' -d master -i /init.sql

# Keep the container running
wait
