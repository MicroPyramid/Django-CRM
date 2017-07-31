
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

 $('#comment_submit').click(function(e) {
       e.preventDefault();
       $.ajax({
              url: '/leads/create_comment/',
              type: 'POST',
              dataType: 'html',
              data: $('#comment_form').serialize(),
              success: function(response) {
                window.location = ""
                  console.log(response);
              },
              error: function(e) {
                  console.log(e);
              }
        });
    });


 function edit_comment(x){
    $('#myModal').modal('show');
    comment = $("#comment_name"+x).text()
     $("#commentid").val(x)
     $("#id_editcomment").val(comment)
}
$("#comment_edit").click(function(e){
    e.preventDefault()
    $.get('/leads/create_comment/', $("#comment_edit_form").serialize(), function(data){
        if(data.error)
        {
            $('#id_editcomment').attr('placeholder',data.error);
        }
        else{
        $("#comment_name"+data.commentid).text(data.comment)
            $('#myModal').modal('hide');
}

    })
     })






function HideError(e){
    $("#CommentError").hide()
}

function remove_comment(x){
    var csrftoken = getCookie('csrftoken');
    $.post('/leads/remove_comment/', {"comment_id":x, "csrfmiddlewaretoken": csrftoken,}, function(data){
        $("#comment"+data.cid).remove()
    })
}

             $(function () {
                 $('#start_date').datetimepicker();
             });