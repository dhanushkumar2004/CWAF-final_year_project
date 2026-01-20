#!/bin/bash

echo "========================================"
echo "   WAF Security Dashboard"
echo "========================================"
echo ""
echo "Starting services..."
echo ""

# Start proxy in background
mitmdump -s proxy.py &
PROXY_PID=$!

# Wait a bit
sleep 3

# Start dashboard in background
cd dashboard && python app.py &
DASHBOARD_PID=$!

echo ""
echo "========================================"
echo "Services started!"
echo ""
echo "Proxy:     http://127.0.0.1:8080"
echo "Dashboard: http://127.0.0.1:5000"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $PROXY_PID $DASHBOARD_PID; exit" INT
wait