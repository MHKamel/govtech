from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.graph_objs as go
import json
import plotly

# Initialize Flask app
app = Flask(__name__)

# Function to load and preprocess data
def load_data():
    df = pd.read_csv('estat_nama_10_exi_en.csv')
    df = df[df['unit'] == 'CP_MEUR']  
    df = df[df['TIME_PERIOD'] >= 2008] 
    df['na_item_group'] = df['na_item'].apply(map_na_item)
    return df

# Mapping function
def map_na_item(na_item):
    if na_item == 'P6':
        return 'Export'
    elif na_item == 'P6_S2111':
        return 'Export To EU Monetary Union'
    elif na_item == 'P6_S2112':
        return 'Export To EU None Monetary Union'
    elif na_item == 'P6_S212':
        return 'Export to EU institutions'
    elif na_item == 'P6_S22':
        return 'Exports 3rd countries and international orgs'
    elif na_item == 'P7':
        return 'Import'
    elif na_item == 'P7_S2111':
        return 'Import From EU Monetary Union'
    elif na_item == 'P7_S2112':
        return 'Import From EU None Monetary Union'
    elif na_item == 'P7_S212':
        return 'Import From EU institutions'
    elif na_item == 'P7_S22':
        return 'Import From 3rd countries and international orgs'
    else:
        return na_item

# Default variables
default_country = "DE"

# Load dataset
df = load_data()



@app.route('/')
def load_bar_chart():
    years = sorted(df['TIME_PERIOD'].unique().tolist(), reverse=True)
    na_items = ['Export', 'Import']
    return render_template('bar_chart.html', years=years, na_items=na_items)

@app.route('/update_year_graph', methods=['POST'])
def update_year_graph():
    selected_year = int(request.form.get('year'))
    na_items_selected = request.form.getlist('na_items[]')
    df_filtered = df[(df['TIME_PERIOD'] == selected_year) & (df['na_item'].isin(['P6', 'P7']))]
    graphJSON = create_chart(df_filtered, na_items_selected, f'Chart for {selected_year}', 'geo', 'OBS_VALUE', 'group')
    return jsonify(graphJSON=graphJSON)

# Routes
@app.route('/country')
def load_line_chart():
    countries = df['geo'].unique()
    na_items = ['Export', 'Import']
    return render_template('line_chart.html', countries=countries, na_items=na_items, default_country=default_country)

@app.route('/update_graph', methods=['POST'])
def update_graph():
    country = request.form.get('country')
    na_items_selected = request.form.getlist('na_items[]')
    df_filtered = df[(df['geo'] == country) & (df['na_item'].isin(['P6', 'P7']))]
    graphJSON = create_chart(df_filtered, na_items_selected, f'Chart from {country}', 'TIME_PERIOD', 'OBS_VALUE', 'lines+markers')
    table_data = calculate_import_export(df_filtered)
    return jsonify(graphJSON=graphJSON, tableData=table_data)

# Calculate Import/Export difference across years
def calculate_import_export(df):
    table_data = []
    years = sorted(df['TIME_PERIOD'].unique())

    for i in range(1, len(years)):
        prev_year = years[i-1]
        curr_year = years[i]
        prev_data = df[df['TIME_PERIOD'] == prev_year]
        curr_data = df[df['TIME_PERIOD'] == curr_year]
        
        prev_export = prev_data[prev_data['na_item'] == 'P6']['OBS_VALUE'].sum()
        curr_export = curr_data[curr_data['na_item'] == 'P6']['OBS_VALUE'].sum()
        export_change = curr_export - prev_export
        export_percent_change = (export_change / prev_export * 100) if prev_export != 0 else 0
        
        prev_import = prev_data[prev_data['na_item'] == 'P7']['OBS_VALUE'].sum()
        curr_import = curr_data[curr_data['na_item'] == 'P7']['OBS_VALUE'].sum()
        import_change = curr_import - prev_import
        import_percent_change = (import_change / prev_import * 100) if prev_import != 0 else 0
        
        table_data.append({
            'year': int(curr_year), 
            'exportChange': export_change, 
            'exportPercentChange': export_percent_change, 
            'importChange': import_change, 
            'importPercentChange': import_percent_change
        })
    
    return table_data

# Group the logic to create line or bar chart based on mode
def create_chart(df, na_items_selected, title, x_title, y_title, mode):
    data = []
    if mode == 'lines+markers':
        for na_item in na_items_selected:
            data.append(go.Scatter(
                x=df[df['na_item_group'] == na_item][x_title],
                y=df[df['na_item_group'] == na_item][y_title],
                mode=mode,
                name=na_item
            ))
    elif mode == 'group':
        for na_item in na_items_selected:
            data.append(go.Bar(
                x=df[df['na_item_group'] == na_item][x_title],
                y=df[df['na_item_group'] == na_item][y_title],
                name=na_item
            ))

    layout = go.Layout(
        title=title,
        xaxis=dict(title=x_title),
        yaxis=dict(title=y_title)
    )
    
    if mode == 'group':
        layout.barmode = 'group'

    fig = go.Figure(data=data, layout=layout)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graphJSON

@app.route('/country_detailed')
def load_pie_charts():
    countries = df['geo'].unique().tolist()
    years = sorted(df['TIME_PERIOD'].unique().tolist(), reverse=True)
    return render_template('pie_charts.html', countries=countries, years=years, default_country=default_country)

@app.route('/update_pie_charts', methods=['POST'])
def update_pie_charts():
    selected_year = int(request.form.get('year'))
    selected_country = request.form.get('country')
    
    # Filter the dataset for the selected year, country, and excluding 'P6' and 'P7'
    df_filtered = df[(df['geo'] == selected_country) & 
                     (df['TIME_PERIOD'] == selected_year) & 
                     (~df['na_item'].isin(['P6', 'P7','P6_S21','P7_S21']))]

    # Group by na_item and sum OBS_VALUE
    data = df_filtered.groupby('na_item')['OBS_VALUE'].sum().reset_index()
    
    # Map na_item to readable categories
    data['na_item_group'] = data['na_item'].apply(map_na_item)
    
    # Prepare Pie chart traces
    pie_traces = []
    for index, row in data.iterrows():
        pie_trace = {
            'labels': [row['na_item_group']],
            'values': [row['OBS_VALUE']],
            'type': 'pie',
            'name': row['na_item_group']
        }
        pie_traces.append(pie_trace)
    
    return jsonify(pieTracesJSON=pie_traces)

@app.route('/country_combined')
def load_combined_pie_charts():
    countries = df['geo'].unique().tolist()
    return render_template('combined_pie_charts.html', countries=countries, default_country=default_country)

@app.route('/update_combined_pie_charts', methods=['POST'])
def update_combined_pie_charts():
    selected_country = request.json.get('country')
    
    # Filter the dataset for the selected country, and excluding 'P6' and 'P7'
    df_filtered = df[(df['geo'] == selected_country) & (~df['na_item'].isin(['P6', 'P7', 'P6_S21', 'P7_S21']))]

    # Group by na_item and sum OBS_VALUE
    data = df_filtered.groupby('na_item')['OBS_VALUE'].sum().reset_index()
    
    # Map na_item to readable categories
    data['na_item_group'] = data['na_item'].apply(map_na_item)
    
    # Separate export and import data
    export_data = data[data['na_item_group'].str.contains('Export')]
    import_data = data[data['na_item_group'].str.contains('Import')]
    
    # Create Pie chart traces for export and import categories
    export_trace = {
        'labels': export_data['na_item_group'].tolist(),
        'values': export_data['OBS_VALUE'].tolist(),
        'type': 'pie',
        'name': 'Export'
    }
    
    import_trace = {
        'labels': import_data['na_item_group'].tolist(),
        'values': import_data['OBS_VALUE'].tolist(),
        'type': 'pie',
        'name': 'Import'
    }
    
    combined_pie_traces_json = json.dumps([export_trace, import_trace], cls=plotly.utils.PlotlyJSONEncoder)
    
    return jsonify(combinedPieTracesJSON=combined_pie_traces_json)


if __name__ == '__main__':
    app.run(debug=True)
