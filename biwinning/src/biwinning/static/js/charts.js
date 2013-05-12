var renderChart = function (item) {
    var $item = $(item);
    if ($item.data('chart')) return;

    var makeChart = function(categories, series) {
        var chart = new Highcharts.Chart({
            chart:{
                renderTo:item,
                type:'bar'
            },
            title:{
                text:null
            },
            xAxis:{
                categories: categories,
                title:{
                    text:null
                }
            },
            yAxis:{
                min:0,
                title:{ text:'Distance in km' }
            },
            tooltip:{
                formatter:function () {
                    return this.y + ' km';
                }
            },
            plotOptions:{
                bar:{
                    dataLabels:{
                        enabled:true
                    }
                }
            },
            legend:{
                enabled:false
            },
            credits:{
                enabled:false
            },
            series: series
        });
    };

    $.getJSON($item.data('ajax-url'), {}, function (data) {
        if (!data.length) {
            return $item.hide();
        }
        var categories = $.map(data, function (item, i) {
            return item.label
        });
        var values = $.map(data, function (item, i) {
            return item.value
        });

        $item.height(50+39*values.length)

        $item.data('chart', makeChart(categories, [{'name': 'Km', data: values}]));
    });
};


var applyCharts = function (e, context) {
    $(context).find(".barchart").each(function (i, item) {
        renderChart(item)
    });
};

var applyTooltip = function (e, context) {
    $(context).find("a[data-toggle=popover]")
        .popover()
        .click(function (e) {
            e.preventDefault()
        });

    $(context).find("a[data-toggle=tooltip]")
        .tooltip()
        .click(function (e) {
            e.preventDefault()
        });
};

$(function () {
    $(document).bind('content', applyCharts);
    $(document).bind('content', applyTooltip);
});