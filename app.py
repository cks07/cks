import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import io
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Staff Scheduling App with Interactive Calendar")

uploaded_file = st.file_uploader("Upload staff availability CSV", type=["csv"])

def parse_time_range(tr):
    if pd.isna(tr) or tr.strip() == '':
        return None
    try:
        start_str, end_str = tr.split('-')
        return int(start_str), int(end_str)
    except:
        return None

def generate_events(df, year, month):
    events = []
    num_days = calendar.monthrange(year, month)[1]
    weekday_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri', 5:'Sat', 6:'Sun'}
    colors = [
        "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
        "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
        "#008080", "#e6beff", "#9a6324", "#fffac8", "#800000",
        "#aaffc3", "#808000", "#ffd8b1", "#000075", "#808080"
    ]

    weekly_hours = {row['Name']: {} for _, row in df.iterrows()}

    for idx, row in df.iterrows():
        color = colors[idx % len(colors)]
        name = row['Name']
        max_hours = row.get('MaxHoursPerWeek', 40)

        for day in range(1, num_days + 1):
            date = datetime.date(year, month, day)
            weekday = date.weekday()
            week_num = date.isocalendar()[1]
            day_col = weekday_map[weekday]
            time_range = row.get(day_col, '')
            tr = parse_time_range(time_range)
            if tr is None:
                continue

            start_hour, end_hour = tr
            shift_length = end_hour - start_hour
            staff_week_hours = weekly_hours[name].get(week_num, 0)

            if staff_week_hours >= max_hours:
                continue

            if staff_week_hours + shift_length > max_hours:
                allowed_hours = max_hours - staff_week_hours
                if allowed_hours <= 0:
                    continue
                end_hour = start_hour + allowed_hours
                shift_length = allowed_hours

            start_dt = datetime.datetime(year, month, day, start_hour).isoformat()
            end_dt = datetime.datetime(year, month, day, end_hour).isoformat()

            events.append({
                'id': f"{idx}-{day}",
                'title': name,
                'start': start_dt,
                'end': end_dt,
                'backgroundColor': color,
                'borderColor': color,
            })

            weekly_hours[name][week_num] = staff_week_hours + shift_length

    return events

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded staff availability:")
    st.dataframe(df)

    year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.datetime.now().year)
    month = st.number_input("Month", min_value=1, max_value=12, value=datetime.datetime.now().month)

    events = generate_events(df, year, month)

    st.markdown("### Staff Schedule Calendar")

    calendar_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.css' rel='stylesheet' />
      <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.8/index.global.min.js'></script>
      <style>
        #calendar {{
          max-width: 1000px;
          margin: 0 auto;
        }}
      </style>
    </head>
    <body>
      <div id='calendar'></div>
      <script>
        document.addEventListener('DOMContentLoaded', function() {{
          var calendarEl = document.getElementById('calendar');
          var calendar = new FullCalendar.Calendar(calendarEl, {{
            initialView: 'timeGridWeek',
            editable: true,
            selectable: true,
            events: {json.dumps(events)},
            headerToolbar: {{
              left: 'prev,next today',
              center: 'title',
              right: 'timeGridWeek,timeGridDay'
            }},
            eventDrop: function(info) {{
              const updatedEvent = {{
                id: info.event.id,
                title: info.event.title,
                start: info.event.start.toISOString(),
                end: info.event.end.toISOString()
              }};
              window.parent.postMessage({{type: 'eventUpdated', event: updatedEvent}}, '*');
              alert('Event moved! Update saving is not yet implemented.');
            }}
          }});
          calendar.render();
        }});
      </script>
    </body>
    </html>
    """

    components.html(calendar_html, height=650)

    # 📥 Download Schedule in Google Calendar-compatible format
    if events:
        st.markdown("### 📥 Download Schedule as CSV (Google Calendar Format)")

        output_rows = []
        for e in events:
            start_dt = datetime.datetime.fromisoformat(e['start'])
            end_dt = datetime.datetime.fromisoformat(e['end'])

            output_rows.append({
                "Subject": e['title'],
                "Start Date": start_dt.strftime("%Y-%m-%d"),
                "Start Time": start_dt.strftime("%H:%M"),
                "End Date": end_dt.strftime("%Y-%m-%d"),
                "End Time": end_dt.strftime("%H:%M"),
            })

        df_download = pd.DataFrame(output_rows)

        csv_buffer = io.StringIO()
        df_download.to_csv(csv_buffer, index=False)

        st.download_button(
            label="Download Schedule as CSV",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name="staff_schedule.csv",
            mime="text/csv"
        )

else:
    st.info("Please upload a staff availability CSV file to generate schedule.")
