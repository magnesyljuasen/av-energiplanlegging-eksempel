import plotly.graph_objects as go
import datetime
import numpy as np
from .utilities import hour_to_month
from PIL import Image
from plotly.subplots import make_subplots

def plot_hourly_series(
    *args,
    colors=("#1d3c34", "#4d4b32", "#4d4b32"),
    xlabel=None,
    ylabel=None,
    ymin=None,
    ymax=None,
    height=200,
    showlegend=True,
    linemode=False,
    xtick_datemode=True,
    yticksuffix=' kW',
    unit='kW',
    export_name = None,
    elprice_legend = False
):
    if unit == 'kW':
        unit_sum = 'kWh/år'
    elif unit == 'kr':
        unit_sum = 'kr/år'
    elif unit == '°C':
        unit_sum = '°C'
    elif unit == '-':
        unit_sum = '-'
        
    num_series = len(args) // 2
    colors = colors[:num_series]  # Ensure colors match the number of series
    y_arrays = [arg for arg in args[::2]]
    if xtick_datemode:
        start = datetime.datetime(2023, 1, 1, 0)  # Start from January 1, 2023, 00:00
        end = start + datetime.timedelta(hours=len(y_arrays[0]))
        hours = int((end - start).total_seconds() / 3600) + 1
        x_arr = np.array([start + datetime.timedelta(hours=i) for i in range(hours)])
        ticksuffix = None
    else:
        x_arr = np.arange(0, 8760, 1)
        start = 0
        end = 8760
        ticksuffix = ' t'
    fig = go.Figure()
    if linemode == False:
        stackgroup='one'
        fill='tonexty'
        width=0
        barmode='stack'
    else:
        stackgroup, fill, width, barmode = None, None, 1, None
    for i in range(num_series):
        if elprice_legend == True:
            legend_text = f"{args[i*2+1]}:<br>{round(np.mean(y_arrays[i]), 2):,} kr/kWh".replace(",", " ").replace(".", ",")
        else:
            legend_text = f"{args[i*2+1]}:<br>{int(round(np.sum(y_arrays[i]),-3)):,} {unit_sum}<br>{int(round(np.max(y_arrays[i]),-1)):,} {unit}".replace(",", " ").replace(".", ",")
        if sum(y_arrays[i]) != 0:
            fig.add_trace(
                go.Scatter(
                    x=x_arr,
                    y=y_arrays[i],
                    stackgroup=stackgroup,
                    fill=fill,
                    line=dict(width=width, color=colors[i]),
                    name=legend_text
                    )
                )
            
    fig.update_layout(
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(size=16), orientation="h"),
        height=height,
        xaxis_title=xlabel, 
        yaxis_title=ylabel,
        barmode=barmode, 
        margin=dict(l=20, r=20, t=20, b=20, pad=0),
        showlegend=showlegend,
        xaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
        yaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
    )
    fig.update_xaxes(
        ticksuffix=ticksuffix,
        tickformat="%d.%m",
        range=[start, end],
        mirror=True,
        ticks="outside",
        showline=True,
        #linecolor="black",
        #gridcolor="lightgrey",
    )
    fig.update_yaxes(
        ticksuffix=yticksuffix,
        range=[ymin, ymax],
        mirror=True,
        ticks="outside",
        showline=True,
        #linecolor="black",
        #gridcolor="lightgrey",
    )
    if export_name != None:
        fig.write_image(f"src/plots/{export_name}.svg")
    return fig



#--
def plot_monthly_series(
    *args,
    colors=("#1d3c34", "#4d4b32", "#4d4b32"),
    xlabel=None,
    ylabel=None,
    ymin=None,
    ymax=None,
    height=300,
    showlegend=True,
    yticksuffix='',
    unit='kW',
    title=None,
    aggregation = 'sum'
):
    if unit == 'kW':
        unit_sum = 'kWh/år'
    elif unit == 'kr':
        unit_sum = 'kr/år'
    elif unit == '°C':
        unit_sum = '°C'
    elif unit == '-':
        unit_sum = '-'
        
    num_series = len(args) // 2
    colors = colors[:num_series]  # Ensure colors match the number of series
    fig = go.Figure()
    y_array = [hour_to_month(arg, aggregation) for arg in args[::2]]

    x_arr = ['1. jan', '1. feb', '1. mar', '1. apr', '1. mai', '1. jun', '1. jul', '1. aug', '1. sep', '1. okt', '1. nov', '1. des']
    
    for i in range(num_series):
        fig.add_trace(
            go.Bar(
                x=x_arr,
                y=y_array[i],
                #stackgroup='group',
                #fill=fill,
                #line=dict(width=width, color=colors[i]),
                name=f"{args[i*2+1]}".replace(",", " ").replace(".", ",")
                )
            )
            
    
    fig.update_layout(
        title='',
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(size=16), orientation="h"),
        height=height,
        xaxis_title=xlabel, 
        yaxis_title=ylabel,
        #barmode=barmode, 
        margin=dict(l=20, r=20, t=40, b=20, pad=0),
        showlegend=showlegend,
        xaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
        yaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
    )
    fig.update_xaxes(
        ticksuffix=None,
        tickformat="%d.%m",
        mirror=True,
        ticks="outside",
        showline=True,
        #linecolor="black",
        #gridcolor="lightgrey",
    )
    fig.update_yaxes(
        ticksuffix=yticksuffix,
        range=[ymin, ymax],
        mirror=True,
        ticks="outside",
        showline=True,
        tickformat=','
        #linecolor="black",
        #gridcolor="lightgrey",
    )
    return fig


def double_axis_monthly_plot(
    *args,
    colors=("#1d3c34", "#4d4b32", "#4d4b32"),
    xlabel=None,
    ylabel=[None, None],
    ymin=[None, None],
    ymax=[None, None],
    height=300,
    showlegend=True,
    yticksuffix=[' kWh', ' kW'],
    unit='kW',
    title=None,
    double_axis=True,
    export_name=None,
    aggregation_list = ['sum', 'max']
):
    if unit == 'kW':
        unit_sum = 'kWh/år'
    elif unit == 'kr':
        unit_sum = 'kr/år'
    elif unit == '°C':
        unit_sum = '°C'
    elif unit == '-':
        unit_sum = '-'
        
    num_series = len(args) // 2
    colors = colors[:num_series]  # Ensure colors match the number of series
    if double_axis == True:
        stackgroup, fill, width, barmode = None, None, 1, 'stack'
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        y_array_1 = [hour_to_month(arg, aggregation_list[0]) for arg in args[::2]]
        y_array_2 = [hour_to_month(arg, aggregation_list[1]) for arg in args[::2]]
    else:
        ylabel = ylabel[0]
        stackgroup, fill, width, barmode = None, None, 1, None
        fig = go.Figure()
        ymin = ymin[0]
        ymax = ymax[0]
        yticksuffix = yticksuffix[0]
        y_array = [hour_to_month(arg, aggregation_list[0]) for arg in args[::2]]

    x_arr = ['jan', 'feb', 'mar', 'apr', 'mai', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'des']
    
    if double_axis == False:
        for i in range(num_series):
            if y_array[i].sum() != 0:
                fig.add_trace(
                    go.Scatter(
                        x=x_arr,
                        y=y_array[i],
                        stackgroup=stackgroup,
                        fill=fill,
                        line=dict(width=width, color=colors[i]),
                        name=f"{args[i*2+1]}".replace(",", " "))
                    )
            
    else:
        for i in range(num_series):
            if np.sum(y_array_1[i]) != 0:
                fig.add_trace(
                    go.Bar(
                        x=x_arr,
                        y=y_array_1[i],
                        marker=dict(color=colors[i], line=dict(width=width)),
                        showlegend=True,
                        name= f"{args[i*2+1]}: {int(round(np.sum(y_array_1[i]), -2)):,} {unit_sum} | {int(round(np.max(y_array_2[i]))):,} {unit}".replace(",", " ")
                        #name= f"{args[i*2+1]} (maks): {round(np.sum(y_array_1[i])):,} {unit_sum}".replace(",", " ").replace(".", ",")
                        #name=f"{args[i*2+1]}"
                        ),secondary_y=False)
        
        for i in range(num_series):
            if np.sum(y_array_2[i]) != 0:
                fig.add_trace(
                    go.Scatter(
                        x=x_arr,
                        y=y_array_2[i],
                        fill=fill,
                        line=dict(width=width, color='black', dash='dash'),
                        marker=dict(
                            symbol='circle',
                            color=colors[i],  # Customize the fill color of the marker
                            size=10,
                            line=dict(color='black', width=2)  # Customize the border color and width of the marker
                        ),
                        showlegend=False,
                        name= f"{args[i*2+1]}: {int(round(np.sum(y_array_1[i]),-2)):,} {unit_sum} | {int(round(np.max(y_array_2[i]),-2)):,} {unit}".replace(",", " ")
                        # | {round(np.max(y_array_1[i])):,} {unit}
                        ),secondary_y=True)
    if double_axis == True:
        fig.update_layout(
            title=title,
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(size=16), orientation="h"),
            height=height,
            xaxis_title=xlabel, 
            barmode=barmode, 
            margin=dict(l=20, r=20, t=40, b=20, pad=0),
            showlegend=showlegend,
            xaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
            yaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
        )
        fig.update_xaxes(
            ticksuffix=None,
            tickformat="%d.%m",
            mirror=True,
            ticks="outside",
            showline=True,
            #linecolor="black",
            #gridcolor="lightgrey",
        )
        fig.update_yaxes(
            title_text=ylabel[0],
            ticksuffix=yticksuffix[0],
            range=[ymin[0], ymax[0]],
            mirror=True,
            ticks="outside",
            showline=True,
            secondary_y=False,
            tickformat=','
            #linecolor="black",
            #gridcolor="lightgrey",
        )
        fig.update_yaxes(
            title_text=ylabel[1],
            ticksuffix=yticksuffix[1],
            range=[ymin[1], ymax[1]],
            mirror=True,
            ticks="outside",
            showline=True,
            secondary_y=True,
            tickformat=','
            #linecolor="black",
            #gridcolor="lightgrey",
        )
    else:
        fig.update_layout(
            title=title,
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(size=16), orientation="h"),
            height=height,
            xaxis_title=xlabel, 
            yaxis_title=ylabel,
            barmode=barmode, 
            margin=dict(l=20, r=20, t=40, b=20, pad=0),
            showlegend=showlegend,
            xaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
            yaxis=dict(tickfont=dict(size=16), gridwidth=0.1),
        )
        fig.update_xaxes(
            ticksuffix=None,
            tickformat="%d.%m",
            mirror=True,
            ticks="outside",
            showline=True,
            #linecolor="black",
            #gridcolor="lightgrey",
        )
        fig.update_yaxes(
            ticksuffix=yticksuffix,
            range=[ymin, ymax],
            mirror=True,
            ticks="outside",
            showline=True,
            tickformat=','
            #linecolor="black",
            #gridcolor="lightgrey",
        )
    return fig


def plot_npv(df, title='', height=300):
    df['period'] = df.index

    #y_max = df['incomes'].max() * 3
    #y_min = df['expenses'].min() * 1.1
    y_max = 2500000
    y_min = -25000000

    fig = go.Figure()

    fig.update_layout(
        shapes=[
        # Add shape for incomes (above zero)
        dict(
            type='rect',
            x0=-0.5,
            x1=len(df) - 0.5,
            y0=0,
            y1=y_max,
            fillcolor='rgba(72, 162, 63, 0.2)',  # Light green background for incomes
            line=dict(width=0)
        ),
        # Add shape for expenses (below zero)
        dict(
            type='rect',
            x0=-0.5,
            x1=len(df) - 0.5,
            y0=y_min,
            y1=0,
            fillcolor='rgba(255, 127, 127, 0.2)',  # Light red background for expenses
            line=dict(width=0)
        ),
        dict(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,
            line=dict(color="black", width=1)  # Border color and thickness
        )
    ])

    # Add income and expenses traces
    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['incomes'],
        name='Inntekt',
        marker_color='#1d3c34'  # Custom color for incomes
    ))

    fig.add_trace(go.Bar(
        x=df['period'],
        y=df['expenses'],
        name='Kostnad',
        marker_color='#1d3c34'  # Custom color for expenses
    ))

    # Update layout
    fig.update_layout(
        yaxis=dict(range=[y_min, y_max]),
        title={
            'text': title,  # Title text
            'font': {
                'size': 20  # Set the font size here
            }},
        xaxis_title='År',
        showlegend=False,
        yaxis_title='Kroner',
        barmode='stack',  # Group bars
        margin=dict(l=20, r=20, t=40, b=20),
        height=height
    )

    fig.update_layout(
         xaxis=dict(
            title_font=dict(size=20),  # Set x-axis label font size
            tickfont=dict(size=18)  # Set x-tick font size
        ),
        yaxis=dict(
            title_font=dict(size=20),  # Set y-axis label font size
            tickfont=dict(size=18)  # Set y-tick font size
        ),
    )

    return fig

def plot_borefield(df, well_color='#1d3c34'):
    fig = go.Figure()

    for i in range(len(df)):
        x_start, y_start, z_start = df['x_top'][i], df['y_top'][i], df['z_top'][i]
        x_end, y_end, z_end = df['x_bottom'][i], df['y_bottom'][i], df['z_bottom'][i]
        
        fig.add_trace(go.Scatter3d(
            x=[x_start, x_end],
            y=[y_start, y_end],
            z=[z_start, z_end],
            mode='lines',
            line=dict(color=well_color, width=1),
            name=f'Line {i+1}'
        ))

        fig.add_trace(go.Scatter3d(
            x=[df['x_top'][i]], y=[df['y_top'][i]], z=[df['z_top'][i]],
            mode='markers',
            marker=dict(size=3, color=well_color),
            name='Top Point'
        ))

    camera = dict(eye=dict(x=0., y=0., z=2.5))
    # Update layout
    fig.update_layout(
        scene_camera=camera,
        scene=dict(
            aspectmode='data',
            xaxis_title='',
            yaxis_title='',
            zaxis=dict(
                title='', 
                #showticklabels=False
                )
        ),
        showlegend=False,
        height=600,
        margin=dict(
            l=0,   # left margin
            r=0,   # right margin
            b=20,   # bottom margin
            t=20    # top margin
        )
    )
    return fig