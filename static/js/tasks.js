$(document).ready(function () {
    $(".addedFilters .input-group").toggle();
    $(function () {
        $('.startdatepicker').datetimepicker(
            {
                format: "MM/DD/YYYY HH:MM:ss"
            }
        );
        $('.enddatepicker').datetimepicker({
            useCurrent: false, //Important! See issue #1075
            format: "MM/DD/YYYY HH:MM:ss"
        });
        $(".startdatepicker").on("dp.change", function (e) {
            $('.enddatepicker').data("DateTimePicker").minDate(e.date);
        });
        $(".enddatepicker").on("dp.change", function (e) {
            $('.startdatepicker ').data("DateTimePicker").maxDate(e.date);
        });
    });
});
$('body').on('submit', '#model-form', function (e) {
    e.preventDefault();
    $.post(
        '/planner/task/create/',
        $('#model-form').serialize(),
        function (data, textStatus, jQxhr) {
            // console.log("Success");
            if (textStatus == 'success') {
                if (data['success'] == 'Task Created') {
                    $("#taskslist").prepend('<tr id="task' + data['id'] + '">' +
                        '<td><a id="task' + data["id"] + 'name" name" href="#">' + data["name"] + '</a></td>' +
                        '<td id="task' + data["id"] + 'status" >' + data["status"] + '</td>' +
                        '<td id="task' + data["id"] + 'priority" >' + data["priority"] + '</td>' +
                        '<td id="task' + data["id"] + 'startdate">' + data["startdate"] + '</td>' +
                        '<td>' +
                        '<div class="dropdown">' +
                        '<button class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown">Action ' +
                        '<span class="caret"></span></button>' +
                        '<ul class="dropdown-menu">' +
                        '<li><a class="viewthis" href="">View</a></li>' +
                        '<li><a class="editthis" href="#">Edit</a></li>' +
                        '<li><a class="removethis" href="#">Remove</a></li>' +
                        // '<li><a class="completethis" href="#">Complete</a></li>' +
                        '</ul>' +
                        '</div>' +
                        '</td>' +
                        '</tr>');
                    $("i[id$=_error]").text("");
                    $("#task-create-model").modal("hide");
                    $("#task-success-model").modal("show");
                    $("#model-form").find("input[type=text], textarea").val("");
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");
                    //login REDIRECT URL
                }
                else {
                    if (data["success"] != "Task Created") {
                        for (a in data) {
                            $("#" + a + "_error").text(data[a]);
                            $("#" + a + "_error").css("color", "red");
                        }
                    }
                }
            }
            else if (textStatus == "error") {
                console.log(textStatus);
            }
        });
});
$("body").on("click", "#modeldialogclosed", function () {
    $("i[id$=_error]").text("");
    $("#task-create-model").modal("hide");
    $("#update-form").attr({"id": "model-form"});
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("");
    $("#parent_id").val("");
    $("#update").attr("id", "gocreatetask").text("Create");
    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"});


});
$("body").on("click", "#successmodeldialogclosed", function () {
    $("#task-success-model").modal("hide");
});

$("body").on("click", ".removethis", function (e) {
    e.preventDefault();
    taskID = $(this).closest("tr")[0].id;
    $.post(
        "/planner/task/delete/",
        {taskID: taskID.match(/\d+/)[0]},
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Task Deleted") {
                    $("#" + taskID).css({
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
                    console.log("Something Went Wrong!!!");
                }

                else {
                    console.log(status);
                }
            }
        });
});
$("body").on("click", ".viewthis", function (e) {
    e.preventDefault();
    taskID = $(this).closest("tr")[0].id;
    task = taskID.match(/\d+/)[0];
    $("#model-form").append("<input type="hidden" name="taskID" value="" + task + "">");
    $("#gocreatetask").attr("id", "edittask").text("Edit");
    $.post(
        "/planner/get/task/",
        {taskID: taskID.match(/\d+/)[0]},
        function (data, status, xhr) {
            // console.log(data)
            if (status == "success") {
                if (data["task"]["event_type"] == "Task") {
                    $("#name").val(data["task"]["name"]);
                    $("#parent").val(data["task"]["parent"]);
                    $("#status").val(data["task"]["status"]);
                    $("#priority").val(data["task"]["priority"]);
                    $("#start_date").val(data["task"]["start_date"]);
                    $("#close_date").val(data["task"]["close_date"]);
                    $("#description").val(data["task"]["description"]);
                    $("#parent_name").val(data["parent_name"]);
                    $("#parent_id").val(data["parent_id"]);
                    $("#parent_type").val(data["parent_type"]);
                    ///////////////////ASSGNED USERS////////////////////////////////////////////
                    $("#selected-assignee-users").html("");
                    $("#assigned_user_error").before("<div id="selected-assignee-users"></div>");
                    for (a in data["assigned_users"]) {
                        if ($.isNumeric(a)) {
                            strr = "<input id="assigned_user" type="hidden" name="assigned_users" value="" + a + ""/>";
                            // $("#user_name").after(str)
                            str = "<div class="input-group"><input placeholder="Assign user" readonly value="" + data["assigned_users"][a] + "" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthis-assigned-user"><i class="glyphicon glyphicon-remove"></i></button></span>" + strr + "</div>";
                            $("#selected-assignee-users").append(str);
                        }
                    }
                    ///////////////////END  ASSGNED USERS////////////////////////////////////////////
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
    $("#task-create-model").modal("show");
    $(".modal-body :input").attr("disabled", true);


});
$("body").on("click", "#edittask", function (e) {
    e.preventDefault();
    $(".modal-body :input").removeAttr("disabled");
    $("#model-form").attr({"id": "update-form", "type": "submit"});
    $("#edittask").attr({"id": "update", "type": "submit"}).text("Update");
    $("#modeldialogclosed").attr({"id": "modeldialogclosed"});
    $("#modelbody").append("<input type="hidden" value="" + taskID + "">");
});
$("body").on("click", "#updatemodeldialogclosed", function (e) {
    e.preventDefault();
    $("i[id$=_error]").text("");
    $("#task-create-model").modal("hide");
    $("#update").attr({"id": "gocreatetask", "type": "submit"}).text("Create");
    $("#update-form").attr({"id": "model-form"});
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("");
    $("#parent_id").val("");
    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"});

});
$("body").on("click", "#createtask", function (e) {
    $(".modal-body :input").removeAttr("disabled");
    $("#gocreatetask").attr("id", "gocreatetask").text("Create");
    $("#edittask").attr("id", "gocreatetask").text("Create");
    $("#model-form").find("input[type=text], textarea").val("");
    $("#parent_name").val("");
    $("#parent_id").val("");
    $("#selected-assignee-users").html("");
});
$("body").on("submit", "#update-form", function (e) {
    e.preventDefault();
    $.post(
        "/planner/task/update/",
        $("#update-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Task Updated") {
                    $("#task" + data["id"] + "name").text(data["name"]);
                    $("#task" + data["id"] + "status").text(data["status"]);
                    $("#task" + data["id"] + "priority").text(data["priority"]);
                    $("#task" + data["id"] + "start_date").text(data["startdate"]);
                    $("i[id$=_error]").text("");
                    $("#task-create-model").modal("hide");
                    $("#update").attr({"id": "gocreatetask", "type": "submit"}).text("Create");

                    $("#update-form").attr({"id": "model-form"});
                    $("#model-form").find("input[type=text], textarea").val("");
                    $("#updatemodeldialogclosed").attr({"id": "modeldialogclosed"});
                }
                else if (data["auth"] == "NO") {
                    alert("Not Authanticated!!");

                    //login REDIRECT URL
                }
                else {

                    if (data["success"] != "Task Updated") {
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
    $(".viewthis").click();
    $("#edittask").click();
});

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (settings.type == "POST" || settings.type == "PUT" || settings.type == "DELETE") {

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            }
        }
    }
});
