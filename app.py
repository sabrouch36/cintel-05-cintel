from shiny import reactive, render
from shiny.express import ui, input
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats
from faicons import icon_svg

UPDATE_INTERVAL_SECS = 3
DEQUE_SIZE = 5
data_store = reactive.value(deque(maxlen=DEQUE_SIZE))

@reactive.calc()
def live_data():
    if input.update_on():
        reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    use_fahrenheit = input.use_fahrenheit()
    temp_c = round(random.uniform(-10, 10), 1)
    temp = round(temp_c * 9 / 5 + 32, 1) if use_fahrenheit else temp_c
    unit = "F" if use_fahrenheit else "C"
    timestamp = datetime.now().strftime("%H:%M:%S")
    new_row = {"temp": temp, "timestamp": timestamp, "unit": unit}

    if input.update_on():
        data_store.get().append(new_row)

    df = pd.DataFrame(data_store.get())
    return data_store.get(), df, new_row

ui.page_opts(title="🌡️ Sabri Temp Tracker", fillable=True)

with ui.sidebar(open="open"):
    ui.h2("🔥 Temp Monitor")
    ui.p("Track simulated temperature every 3 seconds.")
    ui.input_checkbox("use_fahrenheit", "Use Fahrenheit (°F)", False)
    ui.input_switch("update_on", "Live Updates", True)
    ui.hr()
    ui.h6("Resources:")
    ui.a("📁 GitHub Repo", href="https://github.com/sabrouch36/cintel-05-cintel", target="_blank")

with ui.layout_columns():
    with ui.value_box(showcase=icon_svg("temperature-high"), theme="bg-gradient-orange-red"):
        ui.h4("Current Temp")

        @render.text
        def show_temp():
            _, _, row = live_data()
            return f"{row['temp']} °{row['unit']}"

    with ui.card():
        ui.card_header("Current Time")

        @render.text
        def show_time():
            _, _, row = live_data()
            return row["timestamp"]

with ui.card():
    ui.card_header("Recent Readings")

    @render.data_frame
    def show_table():
        _, df, _ = live_data()
        return render.DataGrid(df)

with ui.card():
    ui.card_header("Temperature Chart + Trend")

    @render_plotly
    def show_plot():
        _, df, row = live_data()
        if not df.empty:
            unit = row["unit"]
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            fig = px.scatter(
                df,
                x="timestamp",
                y="temp",
                title=f"Temp ({unit}) with Trend Line",
                labels={"temp": f"Temp (°{unit})"},
                color_discrete_sequence=["blue"]
            )
            x = list(range(len(df)))
            slope, intercept, *_ = stats.linregress(x, df["temp"])
            df["trend"] = [slope * i + intercept for i in x]
            fig.add_scatter(
                x=df["timestamp"],
                y=df["trend"],
                mode="lines",
                name="Trend",
                line=dict(color="red")
            )
            fig.update_layout(xaxis_title="Time", yaxis_title=f"Temp (°{unit})")
            return fig
        return px.scatter()
