function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$('#id_account').change(function(){
    var csrftoken = getCookie('csrftoken');
    var Account= $("#id_account").val()
        $.get("/opportunities/contacts/", {"Account":Account, "csrfmiddlewaretoken": csrftoken}, function(data){
          $("#id_contacts").html("")
          $.each(data, function (index, value) {
                $("#id_contacts").append("<option value="+index+">"+value+"</option>")
          });
        })
});

$("#comment_form").submit(function(e){
    e.preventDefault()
    var formData = new FormData($("#comment_form")[0]);
    $.ajax({
        url : "/opportunities/comment_add/",
        type : "POST",
        data : formData,
        cache: false,
        contentType: false,
        processData: false,
        success: function(data){
            if(data.error){
                $("#CommentError").html(data.error).show()
            }
            else {
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
                $("#id_comments").val("")
                alert("Comment Submitted")
            }
        }
    });
});


function edit_comment(x){
    $('#myModal_comment').modal('show');
    comment = $("#comment_name"+x).text()
    $("#commentid").val(x)
    $("#id_editcomment").val(comment)
}

$("#comment_edit").click(function(e){
    alert("Heyyyyyyyyyyy")
    e.preventDefault()
    var formData = new FormData($("#comment_edit_form")[0]);
    $.ajax({
        url : "/opportunities/comment_edit/",
        type : "POST",
        data : formData,
        cache: false,
        contentType: false,
        processData: false,
        success:function(data){
            if(data.error) {
                alert(data.error)
            } else {
                $("#comment_name"+data.commentid).text(data.comment)
                $('#myModal_comment').modal('hide');
                $("#id_editcomment").val("")
            }
        }
    })
});

function remove_comment(x){
  var csrftoken = getCookie('csrftoken');
  var warn = confirm("Are You Sure, you Want to Delete this Comment!?")
  if (warn == true){
    $.post('/opportunities/comment_remove/', {"comment_id":x, "csrfmiddlewaretoken": csrftoken, }, function(data){
      if(data.error){
        alert(data.error)
      } else {
        $("#comment"+data.oid).remove()
      }
    })
  }
}

function editFun(x) {
    var csrftoken = getCookie('csrftoken');
    alert("Heloooooooooooooo")
    $.ajax({
        type: "POST",
        url: "/opportunities/editdetails/",
        data: {
            csrfmiddlewaretoken: csrftoken,
            tid: x
        },
        success: function(data) {
            $("#viewdiv").hide()
            $("#editdiv").show()
            $("#id_name").val(data.name)
            $("#id_stage").val(data.stage)
            $("#id_amount").val(data.amount)
            $("#id_account").val(data.account)
            $("#id_probability").val(data.probability)
            $("#id_close_date").val(data.close_date)
            $("#hiddenval").val(data.eid)
            $("#id_lead_source").val(data.sources)
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
        var Account = $("#id_account").val()
        var csrftoken = getCookie('csrftoken');
        $.get("/opportunities/contacts/", {
            "Account": Account,
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
