$("img").each(function (index, img) {
    $(this).replaceWith('<iframe class="iframeimg '+ $(this).attr("class")+'" id="iframe' + index + '" frameborder="0" scrolling="no" allowfullscreen><iframe>');
    var img = '<img class="'+ $(this).attr("class")+'" src="'+ $(this).attr("src")+'?'+Math.random()+'" style="" onload="parent.document.getElementById(\'iframe'+ index +'\').width=this.width; parent.document.getElementById(\'iframe'+ index +'\').height=this.height" />';
    $('#iframe' + index).contents().find('body').html(img);
    $('#iframe' + index).width("100%");
    iframecss = '<style type="text/css">body{margin:0;padding:0;}.avatar{width: 20px;height: 20px;border-radius: 2px;margin:5px 0 0;}img{max-width: 100%;} p img {vertical-align: middle;max-width: 100%;margin: 10px 0;}</style>';
    $('#iframe' + index).contents().find('head').append(iframecss);
});