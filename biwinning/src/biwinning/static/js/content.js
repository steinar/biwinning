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
            $(document).trigger('content-loaded');
        });
        return false;
    });
}

var endlessScroll = function (buttonSelector) {
    var isHandlingScroll = false;

    var isNearBottom = function edge() {
        return $(window).scrollTop() > ($(document).height() - $(window).height() - 500);
    }

    var requestContentIfNeeded = function requestContentIfNeeded() {
        if (!isHandlingScroll && isNearBottom()) {
            isHandlingScroll = true;
            $(buttonSelector).click();
        }
    };

    var releaseLock = function releaseLock() {
        setTimeout(function () {
            isHandlingScroll = false;
            requestContentIfNeeded();
        }, 100);
    };

    $(window).scroll(requestContentIfNeeded);
    $(window).load(requestContentIfNeeded);
    $(document).bind('content-loaded', releaseLock);
};

$(function () {
    $(document).bind('content', more);
    endlessScroll("#more a");
});