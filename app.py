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

@app.route('/')
def index():
    # Extract unique values of Z column
    countries = df['geo'].unique()

    # Render the template with the multiselect options and default Z value
    return render_template('index.html', countries=countries, default_country=default_country)

@app.route('/update_graph', methods=['POST'])
def update_graph():
    # Get the selected Z values from the AJAX request
    countries = request.form.getlist('countries[]')

    # Filter the dataset based on the selected Z values
    df_filtered = df[df['geo'].isin(countries)]

    # Extract x and y data from the filtered dataset
    x_data = df_filtered['TIME_PERIOD']
    y_data = df_filtered['OBS_VALUE']
    
    # Create a Plotly trace
    trace = go.Scatter(x=x_data, y=y_data, mode='markers', name='Data from CSV')

    # Create a Plotly layout
    layout = go.Layout(title='Chart from Dataset', xaxis=dict(title='TIME_PERIOD'), yaxis=dict(title='OBS_VALUE'))

    # Create a Plotly figure
    fig = go.Figure(data=[trace], layout=layout)

    # Convert the Plotly figure to JSON
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Return the JSON data to update the graph
    return jsonify(graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(debug=True)