
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

$("#comment_form").submit(function(e){
    e.preventDefault()
    var formData = new FormData($("#comment_form")[0]);
    $.ajax({
                url : "/cases/create_comment/", // the endpoint,commonly same url
                type : "POST", // http method
                data : formData,
                cache: false,
                contentType: false,
                processData: false,
             success: function(data){
            if(data.error){
                $("#CommentError").html(data.error).show()
            }
            else{
            $("#comments_div").prepend("<li class='list-group-item list-row' id='comment"+data.com_id+"'>"+
                                 "<div class='pull-right right-container'>"+
                                 "<div class='list-row-buttons btn-group pull-right'>"+
                                 "<button class='btn btn-link btn-sm dropdown-toggle' data-toggle='dropdown' type='button'><span class='caret'></span></button>"+
                                 "<ul class='dropdown-menu pull-right'>"+
                                 "<li><a class='action' onclick='edit_comment("+data.com_id+")'>Edit</a></li>"+
                                 "<li><a class='action' onclick='remove_comment("+data.com_id+")''>Remove</a></li></ul></div></div>"+
                                 "<div class='stream-head-container'> "+data.com_user+" Commented</div>"+
                                 "<div class='stream-post-container' id='comment_name"+data.com_id+"'>"+data.comment+"</div>"+
                                 "<div class='stream-date-container"+data.com_id+"'>"+data.comment_time+"</div></div><div class='stream-date-container' id='comment_file_div"+data.com_id+"'><div id='new_comment"+data.com_id+"'</div></div></li>"
                                 )
            for (var key in data.file){
                      $("#new_comment"+data.com_id).append(
                        "<div class='gray-box' id='comment_file_span"+key+"' style='background-color:#cccccc; "+
                    "padding:5px;display: inline-block;margin:4px; width: 100%; max-width: 400px;'>"+
                    "<span class='preview'><a href='/cases/"+key+"download'>"+data.file[key]+"</a></span>"+
                    "<a class='remove-attachment pull-right' onclick='remove_file("+key+")'>"+
                 "<span class='glyphicon glyphicon-remove'></span></a></div>")
                              }
            $("#id_comments").val("")
            $("#comments_file").replaceWith($("#comments_file").val('').clone(true));
            $("#selected_files").html("")
            alert("Comment Submitted")
                }
            }
        })
})

$("#comments_file").change(function(){
    var v = document.getElementById('comments_file')
    $("#selected_files").html("")
    for (var i = 0; i < v.files.length; ++i) {
     $("#selected_files").append('<li>' + v.files.item(i).name + '</li>')
  }
})
function edit_comment(x){
    $('#myModal').modal('show');
    comment = $("#comment_name"+x).text()
     $("#commentid").val(x)
     $("#id_editcomment").val(comment)
     $("#edit_file_field").html($("#comment_file_div"+x).clone())
}
$("#comment_edit").click(function(e){
    e.preventDefault()
    var formData = new FormData($("#comment_edit_form")[0]);
    $.ajax({
                url : "/cases/edit_comment/", // the endpoint,commonly same url
                type : "POST", // http method
                data : formData,
                cache: false,
                contentType: false,
                processData: false,
                success:function(data){
        if(data.error)
        {
            // $('#id_editcomment').attr('placeholder',data.error);
            alert(data.error)
            // $('#id_editcomment').addClass("input-focus");
        }
        else{
        $("#comment_name"+data.commentid).text(data.comment)
             for (var key in data.file){
                      $("#comment_file_div"+data.commentid).append(
                        "<div class='gray-box' id='comment_file_span"+key+"' style='background-color:#cccccc; "+
                    "padding:5px;display: inline-block;margin:4px; width: 100%; max-width: 400px;'>"+
                    "<span class='preview'><a href='/cases/"+key+"download/'>"+data.file[key]+"</a></span>"+
                    "<a class='remove-attachment pull-right' onclick='remove_file("+key+")'>"+
                 "<span class='glyphicon glyphicon-remove'></span></a></div>")
                              }
            $('#myModal').modal('hide');
            $("#id_editcomment").val("")
            $("#comments_file_edit").replaceWith($("#comments_file_edit").val('').clone(true));
        }
    }
})
})

// $("#comment_form").submit(function(){
//     alert("helloo")
// })
function HideError(e){
    $("#CommentError").hide()
}

function remove_file(x){
    var csrftoken = getCookie('csrftoken');
    var con = confirm("Sure, You want to delete")
    if (con == true){
    $.post('/cases/remove_comment_file/', {"file_id":x, "csrfmiddlewaretoken": csrftoken,}, function(data){
        if(data.error){
            alert(data.error)
        }
        else{
        $("#comment_file_span"+data.file_id).remove()
        $("#comment_file_span"+data.file_id).closest('div').remove();}
    })}
}

function remove_comment(x){
    var csrftoken = getCookie('csrftoken');
    var con = confirm("Sure, You want to delete")
    if (con == true){
    $.post('/cases/remove_comment/', {"comment_id":x, "csrfmiddlewaretoken": csrftoken,}, function(data){
        if(data.error){
         alert(data.error)
        }
        else{
        $("#comment"+data.cid).remove()
    }
    })}
}

function editFun(x) {
    var csrftoken = getCookie('csrftoken');
    $.ajax({
        type: "POST",
        url: "/cases/editdetails/", // the endpoint,commonly same url
        data: {
            csrfmiddlewaretoken: csrftoken,
            tid: x
        },
        success: function(data) {
            $("#maincontainer").hide()
            $("#editdiv").show()
            $("#id_name").val(data.name)
            $("#id_status").val(data.status)
            $("#id_account").val(data.account)
            $("#id_priority").val(data.priority)
            $("#hiddenval").val(data.eid)
            $("#id_case_type").val(data['case-type'])
            $("#id_description").val(data.description)
            contacts = data.contacts.replace("b'", "")
            contacts = contacts.replace(/\\n/g, '')
            contacts = contacts.replace(/\\t/g, '')
            contacts = contacts.replace(/'/g, '')
            contacts = contacts.replace(/}/g, '')
            $("#id_contacts").html(contacts)
        }
    })


    $('#id_account').change(function() {
        var acc = $("#id_account").val()
        var csrftoken = getCookie('csrftoken');
        $.get("/cases/select_contacts/", {
            "acc": acc,
            "csrfmiddlewaretoken": csrftoken
        }, function(data) {
            $("#id_contacts").html("")
            $.each(data, function(index, value) {
                // console.log(index, value)
                $("#id_contacts").append("<option value=" + index + ">" + value + "</option>")
            });
        })
    });

}
$('#edit_update').click(function(e) {
    if($("#id_name").val() == ""){
        e.preventDefault();
         $("#NameError").show()
        }
    })
$('body').on('click', '.status_set', function (e) {
    e.preventDefault();
     eventID = $(this).closest('ul').attr('id')
     event = eventID.match(/\d+/)[0]
     status = $(this).text().replace('Set ', '')
     var token = getCookie('csrftoken');
     window.location = ""
    $.post(
        '/planner/event/set/status/',
        {id: event, status: status, csrfmiddlewaretoken: token},
        function (data) {
            console.log("success")
        })
 })

$('body').on('click', '.remove_event', function (e) {
    e.preventDefault();
     eventID = $(this).closest('ul').attr('id')
     event = eventID.match(/\d+/)[0]
     var token = getCookie('csrftoken');
     window.location = ""
      $.post(
        '/planner/meeting/delete/',
        {meetingID: event, csrfmiddlewaretoken: token},
        function (data) {
            console.log("removed")
        })
  })

$('body').on('click', '.display_event', function (e) {
    e.preventDefault();
    eventID = $(this).closest('ul').attr('id')
     event = eventID.match(/\d+/)[0]
     var token = getCookie('csrftoken');
      $.post(
        '/planner/get/meeting/',
        {meetingID: event, csrfmiddlewaretoken: token},
        function (data, status, xhr) {
          $("#meeting-dispaly-model").modal("show")        })
  })