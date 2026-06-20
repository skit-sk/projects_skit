"""Standalone demo: Plotly bar chart."""

from bar_chart import create_bar_chart

if __name__ == "__main__":
    categories = ["BTC", "ETH", "SOL", "AVAX", "LINK"]
    values = [45200, 3200, 185, 38, 22]

    html = create_bar_chart(categories, values, title="Portfolio Value by Asset")

    with open("bar_chart.html", "w") as f:
        f.write(html)

    print("-> bar_chart.html saved. Open in browser.")
