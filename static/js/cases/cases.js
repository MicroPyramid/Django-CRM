
function close_case(x, url){
  var stat = $("#status_id"+x).text()
  if(stat==="Closed"){
    alert("Case Already Closed")
  }
  else{
    $.post(url, {
     "case_id": x
    }, function(data) {
     $("#status_id"+data.cid).text(data.status)
    })
  }
}

function remove_case(x, url){
  if (!confirm('Are you sure you want to Remove?'))
    return;
  window.location = url
    $.post(url, {
     "case_id": x
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
