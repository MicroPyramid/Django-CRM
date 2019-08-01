$("#comment_form").submit(function(e) {
  e.preventDefault();
  var formData = new FormData($("#comment_form")[0]);
  $.ajax({
    url: "/cases/comment/add/",
    type: "POST",
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function(data) {
      if (data.error) {
        $("#CommentError")
          .html(data.error)
          .show();
      } else {
        d = new Date(data.commented_on);
        let options = {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit"
        };
        d = d.toLocaleString("en-us", options);
        $("#comments_div").prepend(
          "<li class='list-group-item list-row' id='comment" +
            data.comment_id +
            "'>" +
            "<div class='float-right right-container'>" +
            "<div class='list-row-buttons btn-group float-right'>" +
            "<button class='btn primary_btn btn-sm dropdown-toggle' data-toggle='dropdown' type='button'><span class='caret'></span>Actions</button>" +
            "<ul style='width: fit-content; min-width: -webkit-fill-available;' class='dropdown-menu text-center'>" +
            "<li><a style='padding: 0.5em; background: #17a2b8; color:white; font-weight: 600;' class='action' onclick='edit_comment(" +
            data.comment_id +
            ")'>Edit</a></li>" +
            "<li><a style='padding: 0.5em; background: #17a2b8; color:white; font-weight: 600;' class='action' onclick='remove_comment(" +
            data.comment_id +
            ")''>Remove</a></li></ul></div></div>" +
            "<div class='stream-post-container' id='comment_name" +
            data.comment_id +
            "'><pre>" +
            data.comment +
            "</pre></div>" +
            "<div class='stream-container'><pre class='float-left'>" +
            data.commented_by +
            "</pre><pre class='float-right' title='" +
            d.toLocaleString("en-US", { hour12: true }) +
            "'>" +
            data.commented_on_arrow +
            "</pre></div>"
        );
        $("#id_comments").val("");
        alert("Comment Submitted");
        $("#CommentError").html("");
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

$("#comment_edit").click(function(e) {
  e.preventDefault();
  var formData = new FormData($("#comment_edit_form")[0]);
  $.ajax({
    url: "/cases/comment/edit/",
    type: "POST",
    data: formData,
    cache: false,
    contentType: false,
    processData: false,
    success: function(data) {
      if (data.error) {
        $("#CommentEditError")
          .html(data.error)
          .show();
      } else {
        $("#comment_name" + data.comment_id).html(
          "<pre>" + data.comment + "</pre>"
        );
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
    $.post(
      "/cases/comment/remove/",
      {
        comment_id: x
      },
      function(data) {
        if (data.error) {
          alert(data.error);
        } else {
          $("#comment" + data.cid).remove();
        }
      }
    );
  }
}
