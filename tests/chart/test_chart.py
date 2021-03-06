# encoding: utf-8

"""
Test suite for pptx.chart.chart module
"""

from __future__ import absolute_import, print_function

import pytest

from pptx.chart.axis import CategoryAxis, DateAxis, ValueAxis
from pptx.chart.chart import Chart, Legend, _Plots
from pptx.chart.data import ChartData
from pptx.chart.plot import _BasePlot
from pptx.chart.series import SeriesCollection
from pptx.chart.xmlwriter import _BaseSeriesXmlRewriter
from pptx.enum.chart import XL_CHART_TYPE
from pptx.parts.chart import ChartWorkbook

from ..unitutil.cxml import element, xml
from ..unitutil.mock import (
    call, class_mock, function_mock, instance_mock, property_mock
)


class DescribeChart(object):

    def it_provides_access_to_the_category_axis(self, category_axis_fixture):
        chart, category_axis_, AxisCls_, xAx = category_axis_fixture
        category_axis = chart.category_axis
        AxisCls_.assert_called_once_with(xAx)
        assert category_axis is category_axis_

    def it_raises_when_no_category_axis(self, cat_ax_raise_fixture):
        chart = cat_ax_raise_fixture
        with pytest.raises(ValueError):
            chart.category_axis

    def it_provides_access_to_the_value_axis(self, val_ax_fixture):
        chart, ValueAxis_, valAx, value_axis_ = val_ax_fixture
        value_axis = chart.value_axis
        ValueAxis_.assert_called_once_with(valAx)
        assert value_axis is value_axis_

    def it_raises_when_no_value_axis(self, val_ax_raise_fixture):
        chart = val_ax_raise_fixture
        with pytest.raises(ValueError):
            chart.value_axis

    def it_provides_access_to_its_series(self, series_fixture):
        chart, SeriesCollection_, plotArea, series_ = series_fixture
        series = chart.series
        SeriesCollection_.assert_called_once_with(plotArea)
        assert series is series_

    def it_provides_access_to_its_plots(self, plots_fixture):
        chart, plots_, _Plots_, plotArea = plots_fixture
        plots = chart.plots
        _Plots_.assert_called_once_with(plotArea, chart)
        assert plots is plots_

    def it_knows_whether_it_has_a_legend(self, has_legend_get_fixture):
        chart, expected_value = has_legend_get_fixture
        assert chart.has_legend == expected_value

    def it_can_change_whether_it_has_a_legend(self, has_legend_set_fixture):
        chart, new_value, expected_xml = has_legend_set_fixture
        chart.has_legend = new_value
        assert chart._chartSpace.xml == expected_xml

    def it_provides_access_to_its_legend(self, legend_fixture):
        chart, Legend_, expected_calls, expected_value = legend_fixture
        legend = chart.legend
        assert Legend_.call_args_list == expected_calls
        assert legend is expected_value

    def it_knows_its_chart_type(self, chart_type_fixture):
        chart, PlotTypeInspector_, plot_, chart_type = chart_type_fixture
        _chart_type = chart.chart_type
        PlotTypeInspector_.chart_type.assert_called_once_with(plot_)
        assert _chart_type is chart_type

    def it_knows_its_style(self, style_get_fixture):
        chart, expected_value = style_get_fixture
        assert chart.chart_style == expected_value

    def it_can_change_its_style(self, style_set_fixture):
        chart, new_value, expected_xml = style_set_fixture
        chart.chart_style = new_value
        assert chart._chartSpace.xml == expected_xml

    def it_can_replace_the_chart_data(self, replace_fixture):
        (chart, chart_data_, SeriesXmlRewriterFactory_, chart_type,
         rewriter_, chartSpace, workbook_, xlsx_blob) = replace_fixture

        chart.replace_data(chart_data_)

        SeriesXmlRewriterFactory_.assert_called_once_with(
            chart_type, chart_data_
        )
        rewriter_.replace_series_data.assert_called_once_with(chartSpace)
        workbook_.update_from_xlsx_blob.assert_called_once_with(xlsx_blob)

    # fixtures -------------------------------------------------------

    @pytest.fixture(params=['c:catAx', 'c:dateAx', 'c:valAx'])
    def category_axis_fixture(self, request, CategoryAxis_, DateAxis_,
                              ValueAxis_):
        ax_tag = request.param
        chartSpace_cxml = 'c:chartSpace/c:chart/c:plotArea/%s' % ax_tag
        chartSpace = element(chartSpace_cxml)
        chart = Chart(chartSpace, None)
        AxisCls_ = {
            'c:catAx':  CategoryAxis_,
            'c:dateAx': DateAxis_,
            'c:valAx':  ValueAxis_
        }[ax_tag]
        axis_ = AxisCls_.return_value
        xAx = chartSpace.xpath('.//%s' % ax_tag)[0]
        return chart, axis_, AxisCls_, xAx

    @pytest.fixture
    def cat_ax_raise_fixture(self):
        chart = Chart(element('c:chartSpace/c:chart/c:plotArea'), None)
        return chart

    @pytest.fixture
    def chart_type_fixture(self, PlotTypeInspector_, plot_):
        chart = Chart(None, None)
        chart._plots = [plot_]
        chart_type = XL_CHART_TYPE.PIE
        PlotTypeInspector_.chart_type.return_value = chart_type
        return chart, PlotTypeInspector_, plot_, chart_type

    @pytest.fixture(params=[
        ('c:chartSpace/c:chart',          False),
        ('c:chartSpace/c:chart/c:legend', True),
    ])
    def has_legend_get_fixture(self, request):
        chartSpace_cxml, expected_value = request.param
        chart = Chart(element(chartSpace_cxml), None)
        return chart, expected_value

    @pytest.fixture(params=[
        ('c:chartSpace/c:chart', True,
         'c:chartSpace/c:chart/c:legend'),
    ])
    def has_legend_set_fixture(self, request):
        chartSpace_cxml, new_value, expected_chartSpace_cxml = request.param
        chart = Chart(element(chartSpace_cxml), None)
        expected_xml = xml(expected_chartSpace_cxml)
        return chart, new_value, expected_xml

    @pytest.fixture(params=[
        ('c:chartSpace/c:chart',          False),
        ('c:chartSpace/c:chart/c:legend', True),
    ])
    def legend_fixture(self, request, Legend_, legend_):
        chartSpace_cxml, has_legend = request.param
        chartSpace = element(chartSpace_cxml)
        chart = Chart(chartSpace, None)
        expected_value, expected_calls = None, []
        if has_legend:
            expected_value = legend_
            legend_elm = chartSpace.chart.legend
            expected_calls.append(call(legend_elm))
        return chart, Legend_, expected_calls, expected_value

    @pytest.fixture
    def plots_fixture(self, _Plots_, plots_):
        chartSpace = element('c:chartSpace/c:chart/c:plotArea')
        plotArea = chartSpace.xpath('./c:chart/c:plotArea')[0]
        chart = Chart(chartSpace, None)
        return chart, plots_, _Plots_, plotArea

    @pytest.fixture
    def replace_fixture(
            self, chart_data_, SeriesXmlRewriterFactory_, series_rewriter_,
            workbook_, workbook_prop_):
        chartSpace = element('c:chartSpace/c:chart/c:plotArea/c:pieChart')
        chart = Chart(chartSpace, None)
        chart_type = XL_CHART_TYPE.PIE
        xlsx_blob = 'fooblob'
        chart_data_.xlsx_blob = xlsx_blob
        return (
            chart, chart_data_, SeriesXmlRewriterFactory_, chart_type,
            series_rewriter_, chartSpace, workbook_, xlsx_blob
        )

    @pytest.fixture
    def series_fixture(self, SeriesCollection_, series_collection_):
        chartSpace = element('c:chartSpace/c:chart/c:plotArea')
        plotArea = chartSpace.xpath('.//c:plotArea')[0]
        chart = Chart(chartSpace, None)
        return chart, SeriesCollection_, plotArea, series_collection_

    @pytest.fixture(params=[
        ('c:chartSpace/c:style{val=42}', 42),
        ('c:chartSpace',                 None),
    ])
    def style_get_fixture(self, request):
        chartSpace_cxml, expected_value = request.param
        chart = Chart(element(chartSpace_cxml), None)
        return chart, expected_value

    @pytest.fixture(params=[
        ('c:chartSpace',                4,    'c:chartSpace/c:style{val=4}'),
        ('c:chartSpace',                None, 'c:chartSpace'),
        ('c:chartSpace/c:style{val=4}', 2,    'c:chartSpace/c:style{val=2}'),
        ('c:chartSpace/c:style{val=4}', None, 'c:chartSpace'),
    ])
    def style_set_fixture(self, request):
        chartSpace_cxml, new_value, expected_chartSpace_cxml = request.param
        chart = Chart(element(chartSpace_cxml), None)
        expected_xml = xml(expected_chartSpace_cxml)
        return chart, new_value, expected_xml

    @pytest.fixture(params=[
        ('c:chartSpace/c:chart/c:plotArea/(c:catAx,c:valAx)', 0),
        ('c:chartSpace/c:chart/c:plotArea/(c:valAx,c:valAx)', 1),
    ])
    def val_ax_fixture(self, request, ValueAxis_, value_axis_):
        chartSpace_xml, idx = request.param
        chartSpace = element(chartSpace_xml)
        chart = Chart(chartSpace, None)
        valAx = chartSpace.xpath('.//c:valAx')[idx]
        return chart, ValueAxis_, valAx, value_axis_

    @pytest.fixture
    def val_ax_raise_fixture(self):
        chart = Chart(element('c:chartSpace/c:chart/c:plotArea'), None)
        return chart

    # fixture components ---------------------------------------------

    @pytest.fixture
    def CategoryAxis_(self, request, category_axis_):
        return class_mock(
            request, 'pptx.chart.chart.CategoryAxis',
            return_value=category_axis_
        )

    @pytest.fixture
    def category_axis_(self, request):
        return instance_mock(request, CategoryAxis)

    @pytest.fixture
    def chart_data_(self, request):
        return instance_mock(request, ChartData)

    @pytest.fixture
    def DateAxis_(self, request, date_axis_):
        return class_mock(
            request, 'pptx.chart.chart.DateAxis', return_value=date_axis_
        )

    @pytest.fixture
    def date_axis_(self, request):
        return instance_mock(request, DateAxis)

    @pytest.fixture
    def Legend_(self, request, legend_):
        return class_mock(
            request, 'pptx.chart.chart.Legend', return_value=legend_
        )

    @pytest.fixture
    def legend_(self, request):
        return instance_mock(request, Legend)

    @pytest.fixture
    def PlotTypeInspector_(self, request):
        return class_mock(request, 'pptx.chart.chart.PlotTypeInspector')

    @pytest.fixture
    def _Plots_(self, request, plots_):
        return class_mock(
            request, 'pptx.chart.chart._Plots', return_value=plots_
        )

    @pytest.fixture
    def plot_(self, request):
        return instance_mock(request, _BasePlot)

    @pytest.fixture
    def plots_(self, request):
        return instance_mock(request, _Plots)

    @pytest.fixture
    def SeriesCollection_(self, request, series_collection_):
        return class_mock(
            request, 'pptx.chart.chart.SeriesCollection',
            return_value=series_collection_
        )

    @pytest.fixture
    def SeriesXmlRewriterFactory_(self, request, series_rewriter_):
        return function_mock(
            request, 'pptx.chart.chart.SeriesXmlRewriterFactory',
            return_value=series_rewriter_, autospec=True
        )

    @pytest.fixture
    def series_collection_(self, request):
        return instance_mock(request, SeriesCollection)

    @pytest.fixture
    def series_rewriter_(self, request):
        return instance_mock(request, _BaseSeriesXmlRewriter)

    @pytest.fixture
    def ValueAxis_(self, request, value_axis_):
        return class_mock(
            request, 'pptx.chart.chart.ValueAxis',
            return_value=value_axis_
        )

    @pytest.fixture
    def value_axis_(self, request):
        return instance_mock(request, ValueAxis)

    @pytest.fixture
    def workbook_(self, request):
        return instance_mock(request, ChartWorkbook)

    @pytest.fixture
    def workbook_prop_(self, request, workbook_):
        return property_mock(
            request, Chart, '_workbook', return_value=workbook_
        )


class Describe_Plots(object):

    def it_supports_indexed_access(self, getitem_fixture):
        plots, idx, PlotFactory_, plot_elm, chart_, plot_ = getitem_fixture
        plot = plots[idx]
        PlotFactory_.assert_called_once_with(plot_elm, chart_)
        assert plot is plot_

    def it_supports_len(self, len_fixture):
        plots, expected_len = len_fixture
        assert len(plots) == expected_len

    # fixtures -------------------------------------------------------

    @pytest.fixture(params=[
        ('c:plotArea/c:barChart', 0),
        ('c:plotArea/(c:radarChart,c:barChart)', 1),
    ])
    def getitem_fixture(self, request, PlotFactory_, chart_, plot_):
        plotArea_cxml, idx = request.param
        plotArea = element(plotArea_cxml)
        plot_elm = plotArea[idx]
        plots = _Plots(plotArea, chart_)
        return plots, idx, PlotFactory_, plot_elm, chart_, plot_

    @pytest.fixture(params=[
        ('c:plotArea',                          0),
        ('c:plotArea/c:barChart',               1),
        ('c:plotArea/(c:barChart,c:lineChart)', 2),
    ])
    def len_fixture(self, request):
        plotArea_cxml, expected_len = request.param
        plots = _Plots(element(plotArea_cxml), None)
        return plots, expected_len

    # fixture components ---------------------------------------------

    @pytest.fixture
    def chart_(self, request):
        return instance_mock(request, Chart)

    @pytest.fixture
    def PlotFactory_(self, request, plot_):
        return function_mock(
            request, 'pptx.chart.chart.PlotFactory', return_value=plot_
        )

    @pytest.fixture
    def plot_(self, request):
        return instance_mock(request, _BasePlot)
