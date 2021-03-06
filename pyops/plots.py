import pandas as pd
from bokeh.plotting import figure, show, output_notebook, gridplot
from bokeh.palettes import brewer
from collections import OrderedDict
from bokeh.models import HoverTool
import numpy as np
from bokeh.models import ColumnDataSource, Range1d, FactorRange
from datetime import datetime


# BREWER_PLOT
def brewer_plot(defata, instruments_all, instruments=None):
    """
    This function shows two bokeh brewer plots into the ipython notebook using
    the data given as a parameter. In the second one only the instruments
    given in the third parameter are plotted. In the first one all of them
    are plotted.

    :param data: power_avg table
    :type data: pandas DataFrame
    :param instruments_all: All the instruments in the power_avg file
    :type instruments_all: List of strings
    :param instruments: Instruments to be plotted in the second plot
    :type instruments: List of strings
    :returns: Nothing
    """
    # Hidding anoying warnings on the top of the plot
    output_notebook(hide_banner=True)

    # Creating both figures
    big_figure = create_plot(data, instruments_all)
    small_figure = create_plot(data, instruments, big_figure.x_range)

    # Plotting them together
    p = gridplot([[big_figure], [small_figure]])

    show(p)


def create_plot(data, instruments, x_range=None):
    """
    This function creates a plot given a power_avg table and the instruments
    to be plotted. Optionally an x_range to be linked to another plot can be
    passed as a parameter.

    :param data: module_states or modes table
    :type data: pandas DataFrame
    :param instruments: Instruments to be plotted
    :type instruments: List of strings
    :param x_range: x_range to be linked with
    :type x_range: figure x_range
    :returns: bokeh figure
    """
    # Create a set of tools to use
    tools = "resize,hover,save,pan,box_zoom,wheel_zoom,reset"

    # Creating the areas to be plotted
    areas = stacked(data, instruments)

    # Selecting the colors for the calculated areas
    colors = palette(len(areas))

    # Stacking the values of each instrument
    x2 = np.hstack((data.index.values[::-1], data.index.values))

    # Creating the figure
    if x_range is None:
        f = figure(x_axis_label=data.index.name, y_axis_label='Watts',
                   x_axis_type="datetime", tools=tools, logo=None,
                   x_range=Range1d(min(data.index.values),
                                   max(data.index.values)))
    else:
        f = figure(x_axis_label=data.index.name, y_axis_label='Watts',
                   x_axis_type="datetime", x_range=x_range, tools=tools,
                   logo=None)
    for pos in range(len(colors)):
        f.patch(x2, list(areas.values())[pos], color=colors[pos],
                legend=instruments[pos], line_color=None, alpha=0.8)

    # Setting the color of the line of the background
    f.grid.minor_grid_line_color = '#eeeeee'

    return f


def palette(number):
    """
    This function returns a palette of hex colors of size number.

    :param number: Amount of different colors needed
    :type number: integer
    :returns: list of strings
    """
    if number > 40:
        print ("Ooops, too many parameters, not enough colors...")

    # Selecting the colors from different bokeh palettes
    palette = brewer["Spectral"][11]
    palette += list(reversed(brewer["RdBu"][11]))
    palette += brewer["YlGnBu"][9]
    palette += list(reversed(brewer["YlGn"][9]))
    palette += brewer["PiYG"][11]

    return palette[:number]


def stacked(df, categories):
    """
    This function stacks all the power information for each instrument.

    :param df: power_avg pandas DataFrame
    :type df: pandas DataFrame
    :param categories: categories in which the plot is going to be divided
    :type categories: list of values
    :returns: pandas DataFrame
    """
    areas = OrderedDict()
    last = np.zeros(len(df[categories[0]]))
    for cat in categories:
        next = last + df[cat]
        areas[cat] = np.hstack((last[::-1], next))
        last = next
    return areas


# MODES_SCHEDULE
def modes_schedule(data):
    # Hidding anoying warnings on the top of the plot
    output_notebook(hide_banner=True)

    show(get_modes_schedule(data))


def get_modes_schedule(data, x_range=None):
    """
    This function create a time line plot based on the data form modes or
    module_states files.

    :param data: module_states or modes table
    :type data: pandas DataFrame
    :returns: Nothing
    """
    # Adding new column to see which instruments are changing in each entry
    data = add_difference_column(data)

    # Building a new table to make the data plotable by bokeh
    start_end_table = build_start_end_table(data)
    source = ColumnDataSource(start_end_table)

    # Selecting the instruments detected in the data
    instruments = [colum for colum in data if colum.upper() == colum]
    instruments.sort(reverse=True)

    # Creating the figure
    if x_range is None:
        p = figure(x_axis_type="datetime", logo=None,
                   x_range=Range1d(min(start_end_table['Start_time']),
                                   max(start_end_table['End_time'])),
                   y_range=FactorRange(factors=instruments),
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")
    else:
        p = figure(x_axis_type="datetime", logo=None,
                   x_range=x_range,
                   y_range=FactorRange(factors=instruments),
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")

    p.quad(left='Start_time', right='End_time', top='Instrument_top',
           bottom='Instrument_bottom', color='Color', source=source)

    # Adding the hover tool to see info when putting the mouse over the plot
    hover = p.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ('Mode', '@Mode'),
        ('Time', '@Time')
    ])

    return p


def add_difference_column(data):
    """
    This function returns the same pandas DataFrame that it receives as a
    parameter but with a new column, which contains which instrument has
    changed since the last recorded state in the table.

    :param data: module_states or modes table
    :type data: pandas DataFrame
    :returns: pandas DataFrame
    """
    # We create a list of lists, which will be the new column to add to to data
    difference = [[]]

    # We take the first row of the table to have the starting values
    data_aux = data.transpose()
    prev_row = data_aux[data_aux.columns.values[0]]
    difference[0] = [element for element in prev_row.index
                     if prev_row[element] is not None]

    # For each entry in the table we detect which instruments are changig
    # since the previous row
    pos = 0
    for row in data_aux:
        for element in data_aux.index:
            if not prev_row[element] == data_aux[row][element]:
                if not len(difference) == pos + 1:
                    difference.append([element])
                else:
                    difference[pos].append(element)
        if not len(difference) == pos + 1:
            difference.append([])
        prev_row = data_aux[row]
        pos += 1

    # Finally we add the calculated column
    data["Change"] = difference

    return data


def build_start_end_table(data):
    """
    This function returns a pandas DataFrame which will be used to make a Bokeh
    directly from it. This DataFrame will be created from the data received as
    a parameter.

    :param data: module_states or modes table
    :type data: pandas DataFrame
    :returns: pandas DataFrame
    """
    # Creating the DataFrame manually
    di = {"End_time": [], "Instrument": [],
          "Mode": [], "Start_time": [], "Time": []}

    # Filling the new DataFrame with the instrument, mode and start time
    data_aux = data.transpose()
    for row in data_aux:
        row_t = data_aux[row].transpose()
        for instrument in row_t["Change"]:
            di["End_time"].append(None)
            di["Instrument"].append(instrument)
            di["Mode"].append(row_t[instrument])
            di["Start_time"].append(row)
    di["Time"] = [str(x) for x in di["Start_time"]]
    df = pd.DataFrame(di)
    df = df.sort(["Start_time"], ascending=True)

    instruments = [colum for colum in data if colum.upper() == colum]

    # Calculating and adding the end time for each task
    for ins in instruments:
        shift = df.loc[df["Instrument"] == ins].shift(-1)
        if len(shift) > 1:
            for i in range(len(shift.index.values)):
                di["End_time"][shift.index.values[i]] = \
                    shift["Start_time"][shift.index.values[i]]
    df = pd.DataFrame(di)

    # Calculating and adding the end time for tasks without unespecified end
    for pos in range(len(df["End_time"])):
        if not type(df["End_time"][pos]) is pd.tslib.Timestamp:
            df.loc[pos, "End_time"] = df["Start_time"].max()

    # Deleting OFF states, we don't want to plot it
    df = df[df.Mode != "OFF"]
    df[["End_time", "Start_time"]] = \
        df[["End_time", "Start_time"]].astype(datetime)

    # Creating new rows needed for making the bars wider in the plot
    df["Instrument_bottom"] = [row + ":0.25" if " " in row else row + ":0.1"
                               for row in df["Instrument"].values]
    df["Instrument_top"] = [row + ":0.75" if " " in row else row + ":0.9" for
                            row in df["Instrument"].values]

    # Setting different colors for each different mode in the DataFrame
    modes = df["Mode"].unique()
    colors = dict(zip(modes, palette(len(modes))))
    df["Color"] = [colors[row] for row in df["Mode"].values]

    return df


# DATA_PLOT
def data_plot(data, instruments):
    """
    This function shows a data plot in the ipython notebook using the given
    data for the given instruments.

    :param data: data_rate pandas DataFrame
    :type data: pandas DataFrame
    :param instruments: list of the instruments to plot
    :type instruments: list of strings
    :returns: nothing
    """
    # Hidding anoying warnings on the top of the plot
    output_notebook(hide_banner=True)

    show(get_data_plot(data, instruments))


def get_data_plot(data, instruments, x_range=None):
    """
    This function returns a data rate plot bokeh figure using the given
    data for the given instruments.

    :param data: data_rate pandas DataFrame
    :type data: pandas DataFrame
    :param instruments: list of the instruments to plot
    :type instruments: list of strings
    :param x_range: x_range from another figure to link with
    :type x_range: x_range bokeh format
    :returns: bokeh figure
    """
    # Creating the figure depending if we want to link it to another figure
    if x_range is None:
        r = figure(x_axis_type="datetime", logo=None,
                   x_range=Range1d(min(data.index.values),
                                   max(data.index.values)),
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")
    else:
        r = figure(x_axis_type="datetime", x_range=x_range, logo=None,
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")

    # Getting the appropiate list of colors
    colors = palette(len(instruments))
    i = 0
    # Transforming the multiindex dataframe into a normal one to use hover tool
    d = transform_multiindex_df(data, instruments)
    # Inserting the lines in the plot
    for ins in instruments:
        r.line(d['index'], d[ins[0] + "_" + ins[1]], color=colors[i],
               legend=ins[0] + " - " + ins[1], line_width=3)
        # I don't know why, but if this source is not rebuilt every single
        # time, it doesn't plot correctly
        source = ColumnDataSource(d)
        # WARNING: THIS IS A HACK
        # Hover tool doesn't work over lines show I have created points
        r.scatter(d['index'], d[ins[0] + "_" + ins[1]], color=colors[i],
                  source=source, fill_color=None, size=8)
        i += 1

    r.title = "Data Rate"
    r.grid.grid_line_alpha = 0.3

    # Adding the hover tool to see info when putting the mouse over the plot
    hover = r.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([("Time", "@Time")] +
                                 [(ins[0] + " - " + ins[1], "@" + ins[0] + "_"
                                   + ins[1]) for ins in instruments])

    return r


def transform_multiindex_df(data, instruments):
    """
    This function returns a pandas DataFrame without a multiindex and prepared
    to be plotted and used by the hover tool when converted to the proper
    format.

    :param data: power usage pandas DataFrame
    :type data: pandas DataFrame
    :param instruments: list of the instruments to plot
    :type instruments: list of strings
    :returns: pandas DataFrame
    """
    d = {}
    d['Time'] = [str(x) for x in pd.to_datetime(data.index.values)]
    d['index'] = data.index.values
    for ins in instruments:
        d[ins[0] + "_" + ins[1]] = \
            [x[0] for x in data[ins[0], ins[1]].values.tolist()]

    df = pd.DataFrame(d)
    return df


# POWER_PLOT
def power_plot(data, instruments):
    """
    This function shows a power plot in the ipython notebook using the given
    data for the given instruments.

    :param data: power usage pandas DataFrame
    :type data: pandas DataFrame
    :param instruments: list of the instruments to plot
    :type instruments: list of strings
    :returns: nothing
    """
    # Hidding anoying warnings on the top of the plot
    output_notebook(hide_banner=True)

    show(get_power_plot(data, instruments))


def get_power_plot(data, instruments, x_range=None):
    """
    This function returns a power plot bokeh figure using the given
    data for the given instruments.

    :param data: data_rate pandas DataFrame
    :type data: pandas DataFrame
    :param instruments: list of the instruments to plot
    :type instruments: list of strings
    :param x_range: x_range from another figure to link with
    :type x_range: x_range bokeh format
    :returns: bokeh figure
    """
    # Creating the figure depending if we want to link it to another figure
    if x_range is None:
        r = figure(x_axis_type="datetime", logo=None,
                   x_range=Range1d(min(data.index.values),
                                   max(data.index.values)),
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")
    else:
        r = figure(x_axis_type="datetime", x_range=x_range, logo=None,
                   tools="resize,hover,save,pan,box_zoom,wheel_zoom,reset")

    # Getting the appropiate list of colors
    colors = palette(len(instruments))
    i = 0
    # Preparing a set of data to convert into a source for the hover tool
    d = data.copy(deep=True)
    d['Time'] = [str(x) for x in pd.to_datetime(data.index.values)]
    # Inserting the lines in the plot
    for ins in instruments:
        r.line(data.index.values, data[ins], color=colors[i],
               legend=ins, line_width=3)
        # I don't know why, but if this source is not rebuilt every single
        # time, it doesn't plot correctly
        source = ColumnDataSource(d)
        # WARNING: THIS IS A HACK
        # Hover tool doesn't work over lines show I have created points
        r.scatter(data.index.values, data[ins], color=colors[i], source=source,
                  fill_color=None, size=8)
        i += 1

    r.title = "Power"
    r.grid.grid_line_alpha = 0.3

    # Adding the hover tool to see info when putting the mouse over the plot
    hover = r.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([("Time", "@Time")] +
                                 [(ins, "@" + ins) for ins in instruments])

    return r
