from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go
import json
import plotly

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('estat_nama_10_exi_en.csv')
df = df[df['unit'] == 'CP_MEUR']  # always filter the data by the current millions EUR price

# Filter the dataset to only include 'P6' and 'P7' items
df = df[df['na_item'].isin(['P6', 'P7'])]

# Define the mapping function
def map_na_item(na_item):
    if na_item == 'P6':
        return 'Export'
    elif na_item == 'P7':
        return 'Import'
    else:
        return na_item

# Apply the mapping function
df['na_item_group'] = df['na_item'].apply(map_na_item)

# Extract unique values of Z column
default_country = df['geo'].iloc[0]

@app.route('/')
def index():
    # Extract unique values of Z column
    countries = df['geo'].unique()
    na_items = df['na_item_group'].unique().tolist()
    
    # Render the template with the multiselect options and default Z value
    return render_template('index.html', countries=countries, na_items=na_items, default_country=default_country)

@app.route('/update_graph', methods=['POST'])
def update_graph():
    # Get the selected country and na_items from the AJAX request
    country = request.form.get('country')
    na_items_selected = request.form.getlist('na_items[]')

    # Filter the dataset based on the selected country and na_items_group
    df_filtered = df[(df['geo'] == country) & (df['na_item'].isin(['P6', 'P7']))]

    data = []
    for na_item in na_items_selected:
        df_subset = df_filtered[df_filtered['na_item_group'] == na_item]
        trace = go.Scatter(
            x=df_subset['TIME_PERIOD'],
            y=df_subset['OBS_VALUE'],
            mode='lines+markers',
            name=na_item
        )
        data.append(trace)

    # Create a Plotly layout
    layout = go.Layout(
        title='Chart from Dataset',
        xaxis=dict(title='TIME_PERIOD'),
        yaxis=dict(title='OBS_VALUE'),
        barmode='group'
    )

    # Create a Plotly figure
    fig = go.Figure(data=data, layout=layout)

    # Convert the Plotly figure to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Return the JSON data to update the graph
    return jsonify(graphJSON=graphJSON)


@app.route('/year_filter')
def year_filter():
    years = sorted(df['TIME_PERIOD'].unique().tolist(), reverse=True)  # Convert to Python list
    na_items = df['na_item_group'].unique().tolist()  # Convert to Python list
    return render_template('year_filter.html', years=years, na_items=na_items)

@app.route('/update_year_graph', methods=['POST'])
def update_year_graph():
    # Get the selected year and na_item from the AJAX request
    selected_year = int(request.form.get('year'))  # Convert to integer
    na_items_selected = request.form.getlist('na_items[]')

    # Filter the dataset based on the selected year, na_items_group, and unit
    df_filtered = df[(df['TIME_PERIOD'] == selected_year) & 
                     (df['na_item'].isin(['P6', 'P7']))]

    data = []
    for na_item in na_items_selected:
        df_subset = df_filtered[df_filtered['na_item_group'] == na_item]
        trace = go.Bar(
            x=df_subset['geo'],
            y=df_subset['OBS_VALUE'],
            name=na_item
        )
        data.append(trace)

    # Create a Plotly layout
    layout = go.Layout(
        title=f'Chart for {selected_year}',
        xaxis=dict(title='Countries'),
        yaxis=dict(title='OBS_VALUE'),
        barmode='group'
    )

    # Create a Plotly figure
    fig = go.Figure(data=data, layout=layout)

    # Convert the Plotly figure to JSON using Plotly's encoder
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Return the JSON data to update the graph
    return jsonify(graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(debug=True)
