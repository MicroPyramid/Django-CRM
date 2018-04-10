function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function close_case(x, url){
  var csrftoken = getCookie('csrftoken');
  var stat = $("#status_id"+x).text()
  if(stat==="Closed"){
    alert("Case Already Closed")
  }
  else{
    $.post(url, {
     "case_id": x,
     "csrfmiddlewaretoken": csrftoken
    }, function(data) {
     $("#status_id"+data.cid).text(data.status)
    })
  }
}

function remove_case(x, url){
  var csrftoken = getCookie('csrftoken');
  if (!confirm('Are you sure you want to Remove?'))
    return;
  window.location = url
    $.post(url, {
     "case_id": x,
     "csrfmiddlewaretoken": csrftoken
    }, function(data) {
     $(".case_row" + data.case_id).remove()
     $(".total_count").html("Total "+data.count)
    })
}

$("a[rel='page']").click(function(e){
  e.preventDefault();
  $('#cases_filter').attr("action", $(this).attr("href"));
  $('#cases_filter').submit();
});
