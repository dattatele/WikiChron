#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   main.py

   Descp: Generate the main content of the webapp:
Title, plots and filter elements.

   Created on: 01-nov-2017

   Copyright 2017 Abel 'Akronix' Serrano Juste <akronix5@gmail.com>
"""

import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from dash.dependencies import Input, Output

# Local imports:
import lib.interface as lib

# get csv data location (data/ by default)
global data_dir;
data_dir = os.getenv('WIKICHRON_DATA_DIR', 'data')

wikis_df = []
global wikis, metrics
wikis = []
metrics = []

data = [] # matrix of panda series, being rows => metric and columns => wiki
graphs = []

use_relative_time = True
if use_relative_time:
    # TOREDESIGN ONE DAY:
    wikis_months_from_creation = []

def get_dataframe_from_csv(csv):
    """ Read and parse a csv and return the corresponding pandas dataframe"""
    print('Loading csv for ' + csv)
    df = pd.read_csv(os.path.join(data_dir, csv + '.csv'),
                    delimiter=';', quotechar='|',
                    index_col='revision_id')
    df['timestamp']=pd.to_datetime(df['timestamp'],format='%Y-%m-%dT%H:%M:%SZ')
    #~ df.set_index(df['timestamp'], inplace=True) # generate a datetime index
    #~ print(df.info())
    print('!!Loaded csv for ' + csv)
    return df


def load_data(dataframes, metrics):
    """ Load analyzed data by every metric for every dataframe and store it in data[] """

    metrics_by_wiki = []
    for df in dataframes:
        metrics_by_wiki.append(lib.compute_metrics_on_dataframe(metrics, df))

    # transposing matrix row=>wikis, column=>metrics to row=>metrics, column=>wikis
    wiki_by_metrics = []
    for metric_idx in range(len(metrics)):
        metric_row = [metrics_by_wiki[wiki_idx].pop(0) for wiki_idx in range(len(metrics_by_wiki))]
        wiki_by_metrics.append(metric_row)

    return wiki_by_metrics
    #~ old:
    #~ return [ lib.compute_metric_on_dataframes(metric, dataframes) for metric in metrics]

def generate_graphs(metrics, wikis):
    """ Turn over data[] into plotly graphs objects and store it in graphs[] """

    graphs_list = [[None for j in range(len(wikis))] for i in range(len(metrics))]

    #~ global metric_data
    for metric_idx in range(len(metrics)):
        for wiki_idx in range(len(wikis)):
            metric_data = data[metric_idx][wiki_idx]
            if use_relative_time:
                x_axis = len(metric_data.index) # relative to the age of the wiki in months
            else:
                x_axis = metric_data.index # natural months

            graphs_list[metric_idx][wiki_idx] = go.Scatter(
                                x=x_axis,
                                y=metric_data.data,
                                name=wikis[wiki_idx]
                                )

    return graphs_list


def generate_main_content(wikis_arg, metrics_arg):
    global wikis_df, data, graphs, wikis, metrics;
    wikis = wikis_arg;
    metrics = metrics_arg;

    wikis_df = [get_dataframe_from_csv(wiki) for wiki in wikis]

    data = load_data(wikis_df, metrics)
    graphs = generate_graphs(metrics, wikis)

    wikis_dropdown_options = []
    for index, wiki in enumerate(wikis):
        wikis_dropdown_options.append({'label': wiki, 'value': index})

    metrics_dropdown_options = []
    for index, metric in enumerate(metrics):
        metrics_dropdown_options.append({'label': metric.text, 'value': index})

    return html.Div(id='main',
        style={'width': '100%'},
        children=[
            html.H1(children='WIKI CHRON', className='container'),
            html.Hr(),

            html.Div(id='selection-div',
                className='container',
                children=[
                    html.Div(id='first-row',
                        className='row',
                        style={'marginBottom': '15px'},
                        children=[
                            html.Strong(
                            'You are comparing:',
                            className='three columns'
                            ),

                    html.Div(id='wikis-selection-div',
                        children=[
                            html.Strong('Wikis:', className='two columns'),

                            dcc.Dropdown(
                                id='wikis-selection-dropdown',
                                className='seven columns',
                                options=wikis_dropdown_options,
                                multi=True,
                                searchable=False,
                                value=[ option['value'] for option in wikis_dropdown_options ]
                             ),
                         ]),
                    ]),

                html.Div(id='metrics-selection-div',
                        className='row',
                        children=[
                            html.P(className='three columns'),
                            html.Strong('Metrics:', className='two columns', style={'marginLeft': '0'}),

                            dcc.Dropdown(
                                id='metrics-selection-dropdown',
                                className='seven columns',
                                options=metrics_dropdown_options,
                                multi=True,
                                searchable=False,
                                value=[ option['value'] for option in metrics_dropdown_options ]
                            ),
                         ])
             ]),

            html.Hr(),

            html.Div(id='date-slider-div',
                    className='container',
                    children=[

                        html.Strong(
                            'Select your temporary range:'),

                        dcc.RangeSlider(
                            id='dates-slider',
                            min=-5,
                            max=10,
                            step=None,
                            value=[0, 7],
                            disabled=True
                            #~ marks={str(year): str(year) for year in df['year'].unique()}
                        )
                   ]),

            html.Div(id='graphs')
        ]
    );

def bind_callbacks(app):
    @app.callback(
        Output('graphs', 'children'),
        [Input('wikis-selection-dropdown', 'value'),
        Input('metrics-selection-dropdown', 'value')])
    def update_graphs(selected_wikis, selected_metrics):

        for wiki_idx in range(len(wikis)):
            if wiki_idx in selected_wikis:
                for metric_idx in range(len(metrics)):
                    graphs[metric_idx][wiki_idx]['visible'] = True
            else:
                for metric_idx in range(len(metrics)):
                    graphs[metric_idx][wiki_idx]['visible'] = "legendonly"

        dash_graphs = []

        for i, metric in enumerate(metrics):
            if (i in selected_metrics):
                dash_graphs.append(
                    dcc.Graph(
                    id='graph-{}'.format(i),
                    figure={
                        'data': graphs[i],
                        'layout': {
                            'title': metric.text
                        }
                    }
                    )
                )

        return html.Div(
            id='graphs',
            children=dash_graphs
        )

    return

if __name__ == '__main__':

    data_dir = os.getenv('WIKICHRON_DATA_DIR', 'data')

    wikis = ['eslagunanegra_pages_full', 'cocktails']

    available_metrics = lib.get_available_metrics()
    metrics = []
    metrics.append(available_metrics[0])
    metrics.append(available_metrics[1])

    app = dash.Dash()
    app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
    app.css.append_css({"external_url": "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css"})

    app.layout = generate_main_content(wikis, metrics)

    bind_callbacks(app)

    app.run_server(debug=True, port=8053)
