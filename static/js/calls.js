$(document).ready(function () {
    $(".addedFilters .input-group").toggle();
    $(function () {
        $(".startdatepicker").datetimepicker(
            {
                format: "MM/DD/YYYY HH:MM:ss"
            }
        );
    });
    $("#addreminder").click(function (e) {
        e.preventDefault();
        forms_count = $(".reminderslist").length;
        // console.log(forms_count)
        if (forms_count == 0) {
            getreminders();
        } else {
            $temp_reminder = $(".reminderslist").first().clone();
            copied_html = $temp_reminder.html();
            processed_html = copied_html.replace(/form-\d-/g, "form-" + (forms_count) + "-");
            // processed_html=copied_html.replace(/form-\d-id/g, "form-" + (forms_count) + "-")
            $temp_reminder.html(processed_html);
            $(".reminderslist").last().after($temp_reminder);
            $(".reminderslist").last().show();
            // console.log($(".reminderslist").last())
            $($(".reminderslist").last().children()[0]).removeAttr("disabled");
            $($(".reminderslist").last().children()[1]).removeAttr("disabled");
            $($(".reminderslist").last().children()[2]).removeAttr("checked");
            $($(".reminderslist").last().children()[3]).removeAttr("style");
            $($(".reminderslist").last().children()[4]).removeAttr("value");
            $("#id_form-TOTAL_FORMS").val($(".reminderslist").length);
        }
    });
});
$("body").on("click", "button[id=remove]", function (e) {
    if ($(".reminderslist").length != 1) {
        $(this).closest(".reminderslist").remove();
        $("#id_form-TOTAL_FORMS").val($(".reminderslist").length);
    }
});
$("body").on("click", "#modeldialogclosed", function () {
    $("i[id$=_error]").text("");
    $("#call-create-model").modal("hide");
    $("#update-form").attr({"id": "model-form"});
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("");
    $("#parent_id").val("");
    $("#update").attr("id", "gocreatecall").text("Create");
    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"});

});
$("body").on("click", "#successmodeldialogclosed", function () {
    $("#call-success-model").modal("hide");
});
$("body").on("submit", "#model-form", function (e) {
    e.preventDefault();
    $.post(
        "/planner/call/create/",
        $("#model-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Call Created") {
                    $("#callslist").prepend('<tr id="call' + data['id'] + '">' +
                        '<td><a id="call' + data["id"] + 'name" name" href="#">' + data["name"] + '</a></td>' +
                        '<td id="call' + data["id"] + 'parent" >' + data["parent"] + '</td>' +
                        '<td id="call' + data["id"] + 'status" >' + data["status"] + '</td>' +
                        '<td id="call' + data["id"] + 'start_date">' + data["start_date"] + '</td>' +
                        '<td>' +
                        '<div class="dropdown">' +
                        '<button class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">Action' +
                        '<span class="caret"></span></button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a class="viewthis" href="#">View</a></li>' +
                        '<li><a class="editthis" href="#">Edit</a></li>' +
                        '<li><a class="removethis" href="#">Remove</a></li>' +
                        '<li><a class="setstatus" href="#">Set Held</a></li>' +
                        '<li><a class="setstatus" href="#">Set Not Held</a></li>' +
                        '</ul>' +
                        '</div>' +
                        '</td>' +
                        '</tr>');
                    $("i[id$=_error]").text("");
                    $("#call-create-model").modal("hide");
                    $("#call-success-model").modal("show");
                    $("#model-form").find("input[type=text], textarea").val("");
                    $(".selected-assigned-users").html("");
                    $(".selectedcontacts").html("");
                    $(".selectedusers").html("");
                    $("#selectedleads").html("");
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");
                    //login REDIRECT URL
                }
                else {
                    if (data["success"] != "Call Created") {
                        for (a in data) {
                            $("#" + a + "_error").text(data[a]);
                            $("#" + a + "_error").css("color", "red");
                        }
                    }
                }
            }
            else if (status == "success") {
                console.log(status);
            }
        }
    );
});
$("body").on("click", "select input[type=checkbox]", function (e) {
    is_match = $(this).attr("name").match(/form-\d+-DELETE/);
    if (is_match) {
        // $(this).closest(".reminderslist").hide();
        $(this).attr("checked", "checked");
    }
});
$("body").on("click", ".removethis", function (e) {
    e.preventDefault();
    callID = $(this).closest("tr")[0].id;
    $("#call-delete-model").modal("show");
});
$("body").on("click", "#deletecall", function () {
    $("#call-delete-model").modal("hide");
    $.post(
        "/planner/call/delete/",
        {callID: callID.match(/\d+/)[0]},
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Call Deleted") {
                    $("#" + callID).css({
                        "background": "#e6f9ff",
                    }).animate({opacity: "0"}, 2000, function () {
                        $(this).remove();
                    });
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");
                    //login REDIRECT URL
                }
                else if (data["failed" == "ERROR"]) {
                    alert("ERROR OCCURED!!!\nTry Later.");
                }
            }

            else if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {
                    window.location = "/";
                }

                else {
                    console.log(status);
                }
            }
        });
});
$("body").on("click", ".viewthis", function (e, from_edit_this) {
    e.preventDefault();
    callID = $(this).closest("tr")[0].id;
    call = callID.match(/\d+/)[0];
    $("#model-form").append('<input type="hidden" name="callID" value="' + call + '">');
    $("#gocreatecall").attr("id", "editcall").text("Edit");
    $("#selectedleads").html("");
    $("#selectedcontacts").html("");
    $("#selected-assignee-users").html("");
    $("#selectedusers").html("");
    $.post(
        "/planner/get/call/",
        {callID: callID.match(/\d+/)[0]},
        function (data, status, xhr) {
            // console.log(data)
            if (status == "success") {
                if (data["call"]["event_type"] == "Call") {
                    $("#name").val(data["call"]["name"]);
                    $("#parent").val(data["call"]["parent"]);
                    $("#status").val(data["call"]["status"]);
                    $("#start_date").val(data["call"]["start_date"]);
                    $("#close_date").val(data["call"]["close_date"]);
                    $("#duration").val(data["call"]["duration"]);
                    $("#description").val(data["call"]["description"]);
                    $("#parent_name").val(data["parent_name"]);
                    $("#parent_id").val(data["parent_id"]);
                    $("#parent_type").val(data["parent_type"]);
                    getOtherFields(data);
                    // reminders = JSON.parse(data['reminders'])
                    remindersHTML = data.remindersHTML.replace("b'", "");
                    remindersHTML.replace("</div>'", "</div>");
                    remindersHTML = remindersHTML.replace(/\\n/g, '');
                    remindersHTML = remindersHTML.replace(/'/g, '');
                    $("#reminder1").replaceWith(remindersHTML);
                    $("#reminder1").show();
                    if (from_edit_this != true) {
                        // alert(from_edit_this)
                        $(".reminderslist select").attr("disabled", true);
                        $(".glyphicon-plus").hide();
                        $(".glyphicon-trash").hide();
                    }
                }
                else if (data["failed"] == "ERROR") {
                    alert(data["failed"]);

                    //login REDIRECT URL
                }
                else if (data["AUTH"] == "NO") {
                    alert("Not Authanticated");
                    //login redirect
                }
            }
            else if (status == "error") {
                console.log(jqXhr);

            }
            else {
                console.log(status);
            }
        });
    $("#call-create-model").modal("show");
    $(".modal-body :input").attr("disabled", true);


});

$("body").on("click", "#editcall", function (e) {
    e.preventDefault();
    $(".modal-body :input").removeAttr("disabled");
    $(".reminderslist select").removeAttr("disabled");
    $(".glyphicon-plus").show();
    $(".glyphicon-trash").show();
    $("#model-form").attr({"id": "update-form", "type": "submit"});
    $("#editcall").attr({"id": "update", "type": "submit"}).text("Update");
    $("#modeldialogclosed").attr({"id": "modeldialogclosed"});
    $("#modelbody").append('<input type="hidden" value="' + callID + '">');
});
$("body").on("click", "#updatemodeldialogclosed", function (e) {
    e.preventDefault();
    $("i[id$=_error]").text("")
    $("#call-create-model").modal("hide");
    $("#update").attr({"id": "create", "type": "submit"}).text("Create");
    $("#model-form").find("input[type=text], textarea").val("");
    $("#update-form").attr({"id": "model-form"});
    $("#updatemodeldialogclosed").attr({"id": "model-form"});
    $(".reminderslist[style='display:inline-flex']").remove();

});
$("body").on("click", "#createcall", function (e) {
    $(".modal-body :input").removeAttr("disabled");
    $("#gocreatecall").attr("id", "gocreatecall").text("Create");
    $("#editcall").attr("id", "gocreatecall").text("Create");
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("");
    $("#parent_id").val("");
    $("#selectedleads").html("");
    $("#selectedcontacts").html("");
    $("#selected-assignee-users").html("");
    $("#selectedusers").html("");
    getreminders()
});

$("body").on("submit", "#update-form", function (e) {
    e.preventDefault();
    $.post(
        "/planner/call/update/",
        $("#update-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Call Updated") {
                    $("#call" + data["id"] + "name").text(data["name"]);
                    $("#call" + data["id"] + "parent").text(data["parent"]);
                    $("#call" + data["id"] + "status").text(data["status"]);
                    $("#call" + data["id"] + "startdate").text(data["startdate"]);
                    $("i[id$=_error]").text("");
                    $("#call-create-model").modal("hide");
                    $("#update").attr({"id": "gocreatecall", "type": "submit"}).text("Create");
                    $("#update-form").attr({"id": "model-form"});
                    $("#model-form").find("input[type=text], textarea").val("");
                    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"});
                    $(".reminderslist[style='display:inline-flex']").remove();
                    $(".selected-assigned-users").html("");
                    $(".selectedcontacts").html("");
                    $(".selectedusers").html("");
                    $("#selectedleads").html("");
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");
                    window.location="/";
                    //login REDIRECT URL
                }
                else {
                    // resp = JSON.parse(data);
                    if (data["success"] != "Meeting Updated") {
                        for (a in data) {
                            $("#" + a + "_error").text(data[a]);
                            $("#" + a + "_error").css("color", "red");
                        }
                    }
                }
            }
            else if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {

                    window.location = "/";
                    console.log("Something Went Wrong!!!");
                }
            }
            else {
                console.log(status);
            }
        });
});
$("body").on("click", ".editthis", function (e) {
    $($(this).parent().siblings()[0]).children().trigger("click", true);
    $("#editcall").trigger("click");
});

function getreminders() {
    $.get(
        "/planner/get/reminders/",
        $("#update-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#reminder1").replaceWith(data);
                if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");
                    //login REDIRECT URL
                }
            }
            if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {
                    alert("We Regret, there is an issue!! Try again.");
                    window.location = "/";
                    console.log("Something Went Wrong!!!");
                }
            }
            else {
                console.log(status);
            }
        });
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (settings.type == "POST" || settings.type == "PUT" || settings.type == "DELETE") {

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            }
        }
    }
});
