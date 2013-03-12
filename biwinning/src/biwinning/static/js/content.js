var more = function(e, context) {
    $(context).find("#more a").click(function(e, item) {
        $.get(e.target.href, {}, function (data){
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

$(function () {
    $(document).bind('content', more);
});