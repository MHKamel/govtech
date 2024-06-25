from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go
import json
import plotly

app = Flask(__name__)

# Load the dataset
df = pd.read_csv('estat_nama_10_exi_en.csv')
# Extract unique values of Z column
default_country = df['geo'].iloc[0]

# Mapping function to group export p6 and import p7 items
def map_na_item(na_item):
    if na_item.startswith('P6'):
        return 'Export'
    elif na_item.startswith('P7'):
        return 'Import'
    return na_item

# Mohamed's task to map the country codes to the proper country names

# Apply the mapping function
df['na_item_group'] = df['na_item'].apply(map_na_item)

@app.route('/')
def index():
    # Extract unique values of Z column
    countries = df['geo'].unique()

    na_items = df['na_item_group'].unique()
    
    # Render the template with the multiselect options and default Z value
    return render_template('index.html', countries=countries, na_items=na_items, default_country=default_country)

@app.route('/update_graph', methods=['POST'])
def update_graph():
    # Get the selected Z values from the AJAX request
    countries = request.form.getlist('countries[]')
    na_items_selected = request.form.getlist('na_items[]')

    # Filter the dataset based on the selected countries and na_items_group
    df_filtered = df[(df['geo'].isin(countries)) & (df['na_item_group'].isin(na_items_selected))]

    data = []
    for na_item in na_items_selected:
        df_subset = df_filtered[df_filtered['na_item_group'] == na_item]
        trace = go.Bar(
            x=df_subset['TIME_PERIOD'],
            y=df_subset['OBS_VALUE'],
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

if __name__ == '__main__':
    app.run(debug=True)