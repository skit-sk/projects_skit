#!/bin/bash
# rescreenshot_full.sh — переснять все 8 скриншотов с --full

set -e

BASE="/home/user_aioc/workspace/projects/06_screenshots_project"

echo "=== Full-page screenshot reshoot ==="

# fundament_rf (:5000)
echo "[1/8] fundament_rf /"
agent-browser open "http://localhost:5000/"
agent-browser screenshot --full "$BASE/fundament_rf/index.png"

echo "[2/8] fundament_rf /dashboard/"
agent-browser open "http://localhost:5000/dashboard/"
agent-browser screenshot --full "$BASE/fundament_rf/dashboard.png"

echo "[3/8] fundament_rf /card/<id>"
agent-browser open "http://localhost:5000/card/38a5c68d-1570-47d7-8cf9-5c187001e29e"
agent-browser screenshot --full "$BASE/fundament_rf/card.png"

echo "[4/8] fundament_rf /graphics/all"
agent-browser open "http://localhost:5000/graphics/all"
agent-browser screenshot --full "$BASE/fundament_rf/graphics_all.png"

echo "[5/8] fundament_rf /range_variants_demo"
agent-browser open "http://localhost:5000/range_variants_demo"
agent-browser screenshot --full "$BASE/fundament_rf/range_variants.png"

# demo_charts_ascii (:5001)
echo "[6/8] demo_charts_ascii /"
agent-browser open "http://localhost:5001/"
agent-browser screenshot --full "$BASE/demo_charts_ascii/index.png"

# graphs_candle (:5002)
echo "[7/8] graphs_candle / (SVG)"
agent-browser open "http://localhost:5002/"
agent-browser screenshot --full "$BASE/graphs_candle/svg.png"

echo "[8/8] graphs_candle /plotly"
agent-browser open "http://localhost:5002/plotly"
agent-browser screenshot --full "$BASE/graphs_candle/plotly.png"

echo "=== Done ==="
ls -lh "$BASE"/*/
