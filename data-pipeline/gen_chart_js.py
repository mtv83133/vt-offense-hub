def chart_block(prefix, data_key, js_var):
    """prefix e.g. 'tm-eog' (canvas id suffix), data_key e.g. 'tmEog' (D.<data_key>FormationChart)."""
    front_colors = "['#75162A','#E87722','#4b5563','#9ca3af','#6b7280','#9333ea']"
    cov_colors = "['#75162A','#991b1b','#E87722','#cc6b1d','#4b5563','#6b7280','#374151','#9ca3af']"
    return f'''
  // {prefix.upper()} Formation chart -- team-scoped, driven by D.{data_key}FormationChart
  const {js_var}FormEl = document.getElementById('ch-{prefix}-form');
  if({js_var}FormEl) {{
    destroyChart('{prefix}-form');
    if (D.{data_key}FormationChart) {{
      const {js_var}f = D.{data_key}FormationChart;
      charts['{prefix}-form'] = new Chart({js_var}FormEl, {{
        type:'bar',
        data:{{
          labels: {js_var}f.labels,
          datasets:[
            {{label:'% of Snaps',data:{js_var}f.freq,backgroundColor:'#75162A',borderRadius:3,yAxisID:'y'}},
            {{label:'Blitz %',data:{js_var}f.blitz,type:'line',borderColor:'#E87722',backgroundColor:'rgba(232,119,34,.15)',pointBackgroundColor:'#E87722',pointRadius:5,yAxisID:'y1',tension:.3}}
          ]
        }},
        options:{{
          responsive:true,maintainAspectRatio:false,
          plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}}}}}}}},
          scales:{{
            y:{{title:{{display:true,text:'% of Snaps'}},max:40}},
            y1:{{position:'right',title:{{display:true,text:'Blitz %'}},max:100,grid:{{drawOnChartArea:false}}}}
          }}
        }}
      }});
    }}
  }}

  // {prefix.upper()} Fronts donut -- team-scoped, driven by D.{data_key}FrontsDonut
  const {js_var}FrontEl = document.getElementById('ch-{prefix}-fronts-donut');
  if({js_var}FrontEl) {{
    destroyChart('{prefix}-fronts-donut');
    _setDonutLegend({js_var}FrontEl, null);
    if (D.{data_key}FrontsDonut) {{
      const {js_var}FrontColors = {front_colors};
      charts['{prefix}-fronts-donut'] = new Chart({js_var}FrontEl, {{
        type:'doughnut',
        data:{{labels:D.{data_key}FrontsDonut.labels,datasets:[{{data:D.{data_key}FrontsDonut.data,backgroundColor:{js_var}FrontColors,borderWidth:2}}]}},
        options: forPrint
          ? {{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}}}}
          : {{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:11}}}}}}}}}}
      }});
      if (forPrint) _setDonutLegend({js_var}FrontEl, D.{data_key}FrontsDonut.labels, {js_var}FrontColors);
    }}
  }}

  // {prefix.upper()} Coverage donut -- team-scoped, driven by D.{data_key}CovDonut
  const {js_var}CovColors = {cov_colors};
  const {js_var}CovEl = document.getElementById('ch-{prefix}-cov-donut');
  if({js_var}CovEl) {{
    destroyChart('{prefix}-cov-donut');
    _setDonutLegend({js_var}CovEl, null);
    if (D.{data_key}CovDonut) {{
      charts['{prefix}-cov-donut'] = new Chart({js_var}CovEl, {{
        type:'doughnut',
        data:{{labels:D.{data_key}CovDonut.labels,datasets:[{{data:D.{data_key}CovDonut.data,backgroundColor:{js_var}CovColors,borderWidth:2}}]}},
        options: forPrint
          ? {{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}}}}}}
          : {{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{font:{{size:10}}}}}}}}}}
      }});
      if (forPrint) _setDonutLegend({js_var}CovEl, D.{data_key}CovDonut.labels, {js_var}CovColors);
    }}
  }}
'''

def all_blocks():
    return (
        chart_block('tm-eog', 'tmEog', 'tmEog') +
        chart_block('tm-eoh', 'tmEoh', 'tmEoh') +
        chart_block('fm', 'fm', 'fm')
    )

if __name__ == '__main__':
    print(all_blocks())
