#!/bin/bash

# Start Kafka Connect service first
echo "Starting Kafka Connect service..."
/docker-entrypoint.sh start &

# Wait for Kafka Connect REST API to be ready
echo "Waiting for Kafka Connect REST API..."
while ! curl -s -f http://localhost:8083/ > /dev/null
do
    echo "Waiting for Kafka Connect to start..."
    sleep 5
done

echo "Kafka Connect REST API is ready. Waiting additional 10 seconds for internal initialization..."
sleep 10

# Register Debezium SQL Server source connector
echo "Registering SQL Server CDC connector..."
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @/etc/kafka-connect/sqlserver-cdc.json

echo "Registering HTTP Sink connector..."
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d @/etc/kafka-connect/http-sink.json

# Keep the container running
wait
