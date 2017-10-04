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

function close_case(x){
  var csrftoken = getCookie('csrftoken');
     stat = $("#status_id"+x).text()
     if(stat=="Closed"){
      alert("Case Already Closed")
     }
     else{
      $.post("/cases/close_case/", {
       "case_id": x,
       "csrfmiddlewaretoken": csrftoken
      }, function(data) {
       $("#status_id"+data.cid).text(data.status)
      })}
    }

function remove_case(x){
  var csrftoken = getCookie('csrftoken');
      $.post("/cases/"+x+"/delete/", {
       "case_id": x,
       "csrfmiddlewaretoken": csrftoken
      }, function(data) {
       $(".case_row" + data.case_id).remove()
       $(".total_count").html("Total "+data.count)
      })
     }

  $(document).ready(function() {
     $("#bulk_select").change(function() {
      var $input = $(this);
      if ($input.is(":checked")) {
       $("#multiselect input[type=checkbox]").prop('checked', true);
      } else {
       $("#multiselect input[type=checkbox]").prop('checked', false);
      }
     });
    function grab_selected() {
    var tasks = [];
    $('#multiselect input:checked').each(function() {
        tasks.push($(this).val());
    });
    return tasks;
    }
     $("#mass_remove").click(function(e) {
      e.preventDefault()
      var csrftoken = getCookie('csrftoken');
      var tasks= grab_selected()
      var len = $.map(tasks, function(n, i) { return i; }).length;
      if(tasks==0){
        alert("No case selected")
      }
      else{
      $.post("/cases/remove_multicases/",data= {'tasks[]': tasks, "csrfmiddlewaretoken": csrftoken}, function(data) {
        var con = data.cid
            for (let i = 0, l = con.length; i < l; i++) {
                $(".case_row" + con[i]).remove()
              }
        $(".total_count").html("Total "+data.count)
      })}
     });

      $('input[type=checkbox]').each(function(){
        if ($(this).is(':checked')){
        $('#dropaction').removeAttr('disabled');
       }else{
         $('#dropaction').attr('disabled','disabled');
       }})
      $('input[type=checkbox]').change(function(){
        $('input[type=checkbox]').each(function(){
        if ($(this).is(':checked'))
          { bo=true
            return false}
        else{ bo=false}
         })
        if(bo==true){
        $('#dropaction').removeAttr('disabled');
       }else{
         $('#dropaction').attr('disabled','disabled');
       }
      })
    /* $("#massupdate_submit").click(function(e) {
      var tasks= grab_selected()
      var csrftoken = getCookie('csrftoken');
      var data = $('#mass_update').serializeArray();
      data.push({name: 'tasks', value: tasks});
      $.post("/cases/mass_update/",data, function(data) {
      alert(data)
      }
        )
   });*/
   })

$("#page_field").change(function(e){
e.preventDefault();
$("#per_page_field").val($("#page_field").val())
$('#filter_form').attr("action", $(this).attr("href"));
$('#filter_form').submit();
});

$("a[rel='page']").click(function(e){
e.preventDefault();
$('#filter_form').attr("action", $(this).attr("href"));
$('#filter_form').submit();
});
