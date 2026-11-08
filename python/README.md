# Original desktop version (archived)

GeoQuiz started as a Python/Tkinter desktop app. It is no longer maintained:
the game now lives in [`web/`](../web/) and is played at
[amrutha-b-nair.github.io/geoquiz](https://amrutha-b-nair.github.io/geoquiz/).

This folder is kept for reference and as the source of the quiz data:

- `geoquiz/quiz.py`: the original desktop app
- `geoquiz/csv/selected_names.csv`: country names, alternative names and difficulty order
- `geojson files/`: map data the web app's country shapes are drawn from
- the other scripts: one-off tools used to prepare the data

`tools/build_web_data.py` reads the CSV and GeoJSON from here to generate the web app's data.
