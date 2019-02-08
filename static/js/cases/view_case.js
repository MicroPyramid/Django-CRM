
$("#comment_form").submit(function (e) {
  e.preventDefault();
  var formData = new FormData($("#comment_form")[0]);
  $.ajax({
    url: "/cases/comment/add/",
    type: "POST",
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function (data) {
      if (data.error) {
        $("#CommentError").html(data.error).show();
      } else {
        d = new Date(data.commented_on);
        $("#comments_div").prepend("<li class='list-group-item list-row' id='comment" + data.comment_id + "'>" +
          "<div class='float-right right-container'>" +
          "<div class='list-row-buttons btn-group float-right'>"+
          "<button class='btn primary_btn btn-sm dropdown-toggle' data-toggle='dropdown' type='button'><span class='caret'></span>Actions</button>"+          "<ul class='dropdown-menu text-center'>" +
          "<li><a class='action' onclick='edit_comment(" + data.comment_id + ")'>Edit</a></li>" +
          "<li><a class='action' onclick='remove_comment(" + data.comment_id + ")''>Remove</a></li></ul></div></div>" +
          "<div class='stream-post-container' id='comment_name"+data.comment_id+"'><pre>"+data.comment+"</pre></div>"+
          "<div class='stream-container'><pre class='float-left'>"+data.commented_by+"</pre><pre class='float-right'>"+d.toLocaleString('en-US', { hour12: true })+"</pre></div>"
        );
        $("#id_comments").val("");
        alert("Comment Submitted");
        $("#CommentError").html('');
      }
    }
  });
});


function edit_comment(x) {
  $("#Comments_Cases_Modal").modal("show");
  comment = $("#comment_name" + x).text();
  $("#commentid").val(x);
  $("#id_editcomment").val(comment);
}

$("#comment_edit").click(function (e) {
  e.preventDefault();
  var formData = new FormData($("#comment_edit_form")[0]);
  $.ajax({
    url: "/cases/comment/edit/",
    type: "POST",
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function (data) {
      if (data.error) {
        $("#CommentEditError").html(data.error).show();
      } else {
        $("#comment_name" + data.comment_id).html("<pre>" + data.comment + "</pre>");
        $("#Comments_Cases_Modal").modal("hide");
        $("#id_editcomment").val("");
        $("#CommentEditError").html("");
      }
    }
  });
});


function HideError(e) {
  $("#CommentError").hide();
}

function remove_comment(x) {
  var con = confirm("Do you want to Delete it for Sure!?");
  if (con == true) {
    $.post("/cases/comment/remove/", {
      "comment_id": x
    }, function (data) {
      if (data.error) {
        alert(data.error);
      } else {
        $("#comment" + data.cid).remove();
      }
    })
  }
}
