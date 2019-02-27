$(document).ready(function () {
    $(".addedFilters .input-group").toggle()
    $("#addreminder").click(function (e) {
        e.preventDefault()
        forms_count = $(".reminderslist").length
        //console.log(forms_count)
        if (forms_count == 0) {
            getreminders()
        } else {
            $temp_reminder = $(".reminderslist").first().clone();
            copied_html = $temp_reminder.html();
            processed_html = copied_html.replace(/form-\d-/g, "form-" + (forms_count) + "-")
            // processed_html=copied_html.replace(/form-\d-id/g, "form-" + (forms_count) + "-")
            $temp_reminder.html(processed_html)
            $(".reminderslist").last().after($temp_reminder)
            $(".reminderslist").last().show()
            // console.log($(".reminderslist").last())
            $("#" + $(".reminderslist").last().children()[0].id).removeAttr("disabled")
            $("#" + $(".reminderslist").last().children()[1].id).removeAttr("disabled")
            $("#" + $(".reminderslist").last().children()[2].id).removeAttr("checked")
            $("#" + $(".reminderslist").last().children()[3].id).removeAttr("style")
            $("#" + $(".reminderslist").last().children()[4].id).removeAttr("value")
            $("#id_form-TOTAL_FORMS").val($(".reminderslist").length)
        }
    });
    $(function () {
        $(".startdatepicker").datetimepicker(
            {
                format: "MM/DD/YYYY HH:MM:ss"
            }
        );
        $(".enddatepicker").datetimepicker({
            useCurrent: false,
            format: "MM/DD/YYYY HH:MM:ss"
        });
        $(".startdatepicker").on("dp.change", function (e) {
            $(".enddatepicker").data("DateTimePicker").minDate(e.date);
        });
        $(".enddatepicker").on("dp.change", function (e) {
            $(".startdatepicker ").data("DateTimePicker").maxDate(e.date);
        });
    });
});
$("body").on("click", "#modeldialogclosed", function () {
    $("i[id$=_error]").text("")
    $("#meeting-create-model").modal("hide");
    $("#update-form").attr({"id": "model-form"})
    $("#model-form").find("input[type=text], textarea").val("");
    $(".parent_name").val("")
    $(".parent_id").val("")
    $("#update").attr("id", "gocreatemeeting").text("Create");
    getreminders()
    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"})


});
$("body").on("click", "#successmodeldialogclosed", function () {
    $("#meeting-success-model").modal("hide");
    $(".parent_name").val("")

});
$("body").on("submit", "#model-form", function (e) {
    e.preventDefault();
    // console.log($("#model-form").serialize())
    $.post(
        "/planner/meeting/create/",
        $("#model-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Meeting Created") {
                    $("#meetingslist").prepend('<tr id="meeting' + data["id"] + '">' +
                        '<td><a id="meeting' + data["id"] + 'name" name" href="#">' + data["name"] + '</a></td>' +
                        '<td id="meeting' + data["id"] + 'parent">' + data["parent"] + '</td>' +
                        '<td id="meeting' + data["id"] + 'status" >' + data["status"] + '</td>' +
                        '<td id="meeting' + data["id"] + 'startdate">' + data["startdate"] + '</td>' +
                        '<td>' +
                        '<div class="dropdown">' +
                        '<button class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">Action ' +
                        '<span class="caret"></span></button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a id="meeting' + data["id"] + 'view" class="viewthis" href="#">View</a></li>' +
                        '<li><a id="meeting' + data["id"] + 'edit" class="editthis" href="#">Edit</a></li>' +
                        '<li><a id="meeting' + data["id"] + 'remove" class="removethis" href="#">Remove</a></li>' +
                        '<li><a class="setstatus" href="#">Set Held</a></li>' +
                        '<li><a class="setstatus" href="#">Set Not Held</a></li>' +
                        '</ul>' +
                        '</div>' +
                        '</td>' +
                        '</tr>');
                    $("i[id$=_error]").text("")
                    $("#meeting-create-model").modal("hide");
                    $("#meeting-success-model").modal("show");
                    $("#model-form").find("input[type=text], textarea").val("");
                    $("#selectedleads").html("")
                    $(".selectedcontacts").html("")
                    $(".selectedusers").html("")
                    $("#assignaed_user").html("")
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!")

                    //login REDIRECT URL
                }
                else {
                    // console.log("Meeting Not Created")
                    // resp = JSON.parse(data);
                    if (data["success"] != "Meeting Created") {
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
                    console.log("Something Went Wrong!!!")
                }
            }
            else {
                console.log(status)
            }
        });
});
$("body").on("click", "#reminders input[type=checkbox]", function (e) {
    is_match = $(this).attr("name").match(/form-\d+-DELETE/)
    if (is_match) {
        // $(this).closest(".reminderslist").hide();
        $(this).attr("checked", "checked")
    }
});
$("body").on("click", ".removethis", function (e) {
    e.preventDefault()
    meetingID = $(this).closest("tr")[0].id
    $("#meeting-delete-model").modal("show");
});
$("body").on("click", "#deletemeeting", function () {
    $("#meeting-delete-model").modal("hide");
    $.post(
        "/planner/meeting/delete/",
        {meetingID: meetingID.match(/\d+/)[0]},
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Meeting Deleted") {
                    $("#" + meetingID).css({
                        "background": "#e6f9ff",
                    }).animate({opacity: "0"}, 2000, function () {
                        $(this).remove();
                    });
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!")
                    //login REDIRECT URL
                }
                else if (data["failed" == "ERROR"]) {
                    alert("ERROR OCCURED!!!\nTry Later.")
                }
            }

            else if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {
                    window.location = "/";
                    console.log("Something Went Wrong!!!")
                }

                else {
                    console.log(status)
                }
            }
        });
});
$("body").on("click", ".viewthis", function (e, from_edit_this) {
    e.preventDefault()
    $("#selectedleads").html("")
    $(".selectedcontacts").html("")
    $(".selected-assignee-users").html("")
    $(".selectedusers").html("")
    meetingID = $(this).closest("tr")[0].id
    meet = meetingID.match(/\d+/)[0]
    $("#model-form").append('<input type="hidden" name="meetingID" value="' + meet + '">');
    $("#gocreatemeeting").attr("id", "editmeeting").text("Edit");
    $.post(
        "/planner/get/meeting/",
        {meetingID: meetingID.match(/\d+/)[0]},
        function (data, status, xhr) {
            // console.log(data)
            if (status == "success") {
                if (data["meeting"]["event_type"] == "Meeting") {
                    $("#name").val(data["meeting"]["name"])
                    $("#status").val(data["meeting"]["status"])
                    $("#start_date").val(data["meeting"]["start_date"])
                    $("#close_date").val(data["meeting"]["close_date"])
                    $("#duration").val(data["meeting"]["duration"])
                    $("#description").val(data["meeting"]["description"])
                    $("#meeting-create-model .parent_name").val(data["parent_name"])
                    $("#meeting-create-model .parent_id").val(data["parent_id"])
                    $("#meeting-create-model .parent_type").val(data["parent_type"])
                    getOtherFields(data)

                    remindersHTML = data.remindersHTML.replace("b'", "")
                    remindersHTML.replace("</div>'", "</div>")
                    remindersHTML = remindersHTML.replace(/\\n/g, '')
                    remindersHTML = remindersHTML.replace(/'/g, '')
                    $("#reminder1").replaceWith(remindersHTML)
                    $("#reminder1").show()
                    if (from_edit_this != true) {
                        $(".reminderslist select").attr("disabled", true)
                        $(".glyphicon-plus").hide()
                        $(".glyphicon-trash").hide()
                    }
                }
                else if (data["failed"] == "ERROR") {
                    alert(data["failed"])

                    //login REDIRECT URL
                }
                else if (data["AUTH"] == "NO") {
                    alert("Not Authanticated")
                    //login redirect
                }
            }
            else if (status == "error") {
                console.log(jqXhr);

            }
            else {
                console.log(status)
            }
        });
    $("#meeting-create-model").modal("show");
    $(".modal-body :input").attr("disabled", true);
});

$("body").on("click", "#editmeeting", function (e) {
    e.preventDefault();
    $(".modal-body :input").removeAttr("disabled")
    $(".reminderslist select").removeAttr("disabled")
    $(".glyphicon-plus").show()
    $(".glyphicon-trash").show()
    $("#model-form").attr({"id": "update-form", "type": "submit"});
    $("#editmeeting").attr({"id": "update", "type": "submit"}).text("Update");
    $("#modeldialogclosed").attr({"id": "modeldialogclosed"});
    $("#modelbody").append("<input type='hidden' value='" + meetingID + "'>")
});
$("body").on("click", "#updatemodeldialogclosed", function (e) {
    e.preventDefault();
    $("i[id$=_error]").text("")
    $("#meeting-create-model").modal("hide");
    $("#update").attr({"id": "create", "type": "submit"}).text("Create");
    $("#model-form").find("input[type=text], textarea").val("");
    $("#update-form").attr({"id": "model-form"})
    $("#updatemodeldialogclosed").attr({"id": "model-form"})
    $(".reminderslist[style='display:inline-flex']").remove();

});
$("body").on("click", "#createmeeting", function (e) {
    $(".modal-body :input").removeAttr("disabled")
    $("#gocreatemeeting").attr("id", "gocreatemeeting").text("Create");
    $("#editmeeting").attr("id", "gocreatemeeting").text("Create");
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("")
    $("#parent_id").val("")
    $("#selectedleads").html("")
    $(".selectedcontacts").html("")
    $(".selected-assignee-users").html("")
    $(".selectedusers").html("")
    // $("#update").attr("id", "gocreatemeeting").text("Create");
    getreminders()


});

$("body").on("submit", "#update-form", function (e) {
    e.preventDefault();
    $.post(
        "/planner/meeting/update/",
        $("#update-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Meeting Updated") {
                    $("#meeting" + data["id"] + "name").text(data["name"]);
                    $("#meeting" + data["id"] + "parent").text(data["parent"]);
                    $("#meeting" + data["id"] + "startdate").text(data["startdate"]);
                    $("i[id$=_error]").text("")
                    $("#meeting-create-model").modal("hide");
                    $("#update").attr({"id": "gocreatemeeting", "type": "submit"}).text("Create");

                    $("#update-form").attr({"id": "model-form"})
                    $("#model-form").find("input[type=text], textarea").val("");
                    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"})
                    $(".reminderslist[style='display:inline-flex']").remove();
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!")

                    //login REDIRECT URL
                }
                else {
                    // console.log("Meeting Not Created")
                    // resp = JSON.parse(data);
                    if (data["success"] != "Meeting Updated") {
                        for (a in data) {
                            if (data[a] == "Please correct the duplicate values below.") {
                                data[a] = "Please remove duplicate Reminders."
                            }
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
                    console.log("Something Went Wrong!!!")
                }
            }
            else {
                console.log(status)
            }
        });
});
$("body").on("click", ".editthis", function (e) {
    e.preventDefault()
    $($(this).parent().siblings()[0]).children().trigger("click", true)
    $("#editmeeting").trigger("click")
    $("#selectedleads").html("")
    $(".selectedcontacts").html("")
    $(".selectedusers").html("")
    $("#assignaed_user").html("")
});
function getreminders() {
    $.get(
        "/planner/get/reminders/",
        $("#update-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#reminder1").replaceWith(data)
                if (data["auth"] == "NO") {
                    alert("Not Authanticated!!")
                    //login REDIRECT URL
                }

            }
            if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {
                    alert("We Regret, there is an issue!! Try again.")
                    window.location = "/";
                    console.log("Something Went Wrong!!!")
                }
            }
            else {
                console.log(status)
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
