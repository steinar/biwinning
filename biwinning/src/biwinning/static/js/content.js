var more = function (e, context) {
    $(context).find("#more a").click(function (e, item) {
        $.get(e.target.href, {}, function (data) {
            $body = $(data);

            $content = $("<div><div>").append($body.find("#content").children());
            $("#content").append($content);

            $more = $("<div></div>").append($body.find("#more"));
            $("#more").replaceWith($more);

            $(document).trigger('content', $content);
            $(document).trigger('content', $more);
        });
        return false;
    });
}

var endlessScroll = function(buttonSelector) {
    var isHandlingScroll = false;
    var handleScroll = function() {
        if (!isHandlingScroll && $(window).scrollTop() > ($(document).height() - $(window).height() - 500)) {
            isHandlingScroll = true;
            $(buttonSelector).click();
            $(document).ajaxComplete(function () {
                setTimeout(function() { isHandlingScroll = false; handleScroll(); }, 50);
            });
        }
    };
    $(window).scroll(handleScroll);
    $(window).load(handleScroll);
};

$(function () {
    $(document).bind('content', more);
    endlessScroll("#more a");
});