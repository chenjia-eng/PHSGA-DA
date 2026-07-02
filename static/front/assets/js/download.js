(function ($) {



    $("#download").click(function (event) {
        event.preventDefault();
        var uuid = $('#table').attr('data-id');
        window.location = "/detail/download/"+uuid;

    });




})(jQuery);


