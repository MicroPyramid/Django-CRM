$("body").on("click", ".setstatus", function (e) {
    e.preventDefault();
    eventID = $(this).closest("tr")[0].id;
    event = eventID.match(/\d+/)[0];
    status = $(this).text().replace("Set ", "");
    $.post(
        "/planner/event/set/status/",
        {id: event, status: status},
        function (data, status, xhr) {
            if (status == "success") {
                if (data["success"] == "Event Updated") {
                    $("#" + eventID.match(/\D+/)[0] + data["id"] + "status").fadeOut(function () {
                        $(this).text(data["status"]);
                    }).fadeIn();
                }
                else if (data["AUTH"] == "NO") {
                    window.location = "/accounts/login/";
                    //login REDIRECT URL
                }
                else if (data["INVALID"] == "METHOD") {
                    window.location = "/logout/";
                }
                else if (data["METHOD"] == "INVALID") {
                    window.location = "/logout/";
                }
                else {
                    if (data["Event"] != "DoesNotExist") {
                        window.location = "/logout/";
                    }
                }
            }
            else if (status == "error") {
                console.log(jqXhr);
                if (data["error"] == "Something Went Wrong!!!") {
                    window.location = "/";
                }
            }
            else {
                console.log(status);
            }
        });
});

$("body").on("click", "#selectparent", function (e) {
    e.preventDefault();
    $("#selectparentmodel").modal("show");
    $("#selectparentmodel").find(".modal-title").text("Select " + $("#parent_type").val());
    if ($("#parent_type").val() == "Account") {
        gURL = "/accounts/get/list/";
    }
    if ($("#parent_type").val() == "Contact") {
        gURL = "/contacts/get/list/";
    }
    else if ($("#parent_type").val() == "Lead") {
        gURL = "/leads/get/list/";
    }
    else if ($("#parent_type").val() == "Opportunity") {
        gURL = "/opportunities/get/list/";
    }
    else if ($("#parent_type").val() == "Case") {
        gURL = "/cases/get/list/";
    }
    $.get(
        gURL,
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#selectcontact-modal-body").html(data);
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

});
$("body").on("click", ".parentname", function (e) {
    e.preventDefault();
    console.log($(this));

    $(".parent_id").val($(this).attr("id"));
    $(".parent_name").val($(this).text().trim());
    $("#selectparentmodel").modal("hide");
});

$("body").on("click", "#closeselectparentmodel", function (e) {
    e.preventDefault();
    $("#selectparentmodel").modal("hide");
    $(".parent_name").val("");
    $(".parent_id").val("");
});
$("body").on("click", "#clearparent", function (e) {
    e.preventDefault();
    console.log($(this));
    $(this).parent().parent().id;
    $(".parent_name").val("");
    $(".parent_id").val("");
});
$("body").on("click", ".glyphicon-trash", function (e) {
    if ($($(this).siblings()[2]).prop("checked") == false) {
        $($(this).siblings()[2]).prop("checked", true);
        $(this).css({"color": "red"});
        $($(this).siblings()[0]).attr("disabled", "");
        $($(this).siblings()[1]).attr("disabled", "");
    }
    else {
        $($(this).siblings()[2]).prop("checked", false);
        $($(this).siblings()[0]).removeAttr("disabled", "");
        $($(this).siblings()[1]).removeAttr("disabled", "");
        $(this).removeAttr("style");
    }
})
$("body").on("click", ".pagination li a", function (e) {
    e.preventDefault();
    URL = window.location.pathname + $(this).context.search;
    $(".for-pagination").animate({width: "20px"});
    $.get(
        URL,
        function (data, status, xhr) {
            if (status == "success") {
                $(".for-pagination").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $(".for-pagination").html("Something Went Wrong Try Again Later...");
            }
        });
});

/////////////////////SELECT ATTENDEE USERS//////////////////////////////////////////////////
$("body").on("click", "#selectusers", function (e) {
    e.preventDefault();
    $("#selectusersmodel").modal("show");
    $.get(
        "/planner/get/users/",
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#selectusers-modal-body").html(data);
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

});
$("body").on("click", "#clearuser", function (e) {
    e.preventDefault();
    $(".attendees-users-user_name").val("");
    $(".assigned_users").val("");
});

$("body").on("click", "#selectusers-modal-body .paginate-me-users", function (e) {
    e.preventDefault();
    $("#selectusers-modal-body").animate({width: "20px"});
    $.get(
        "/planner/get/users/" + $(this).context.search,
        function (data, status, xhr) {
            if (status == "success") {
                $("#selectusers-modal-body").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $(".for-pagination").html("Something Went Wrong Try Again Later...");
            }
        });
});
var $uids = {}
$("body").on("click", "#selectusers-modal-body .checkuser", function (e) {
    // console.log($(this).prop("checked") == true)
    if ($(this).prop("checked") == true) {
        if (!($(this).val() in $uids))
            $uids[$(this).val()] = $(this).parent().next().text().trim();
    }
    else {
        delete $uids[$(this).val()];
    }
    // console.log($uids)
})

$("body").on("click", "#closeselectusersmodel", function (e) {
    if ($(".selectedusers").length < 1) {
        $(".attendees-users-user_name").parent().after("<div class="selectedusers"></div>");
        $(".selectedusers").html("");
    }
    $(".selectedusers").html("");
    // $(".attendees-users-user_name").parent().after("<div class="selectedusers"></div>")
    for (a in $uids) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_user" type="hidden" name="attendees_user" value="' + a + '"/>';
            str = '<div class="input-group"><input placeholder="user" readonly value="' + $uids[a] + '" name="attendees_username" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthisuser"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $(".selectedusers").append(str);
        }
    }
})
$("body").on("click", ".clearthisuser", function (e) {
    e.preventDefault();
    $(this).closest(".input-group").remove();
    delete $uids[$(this).parent().next().val()];
    // console.log($uids)
})

//CONTACTS START //////////////////////////////////////////////////////////////
$("body").on("click", "#select-attendee-contacts", function (e) {
    e.preventDefault();
    $("#select-contacts-model").modal("show");
    $.get(
        "/planner/get/contacts/",
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#select-contacts-modal-body").html(data);
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

});
// $("body").on("click", ".username", function (e) {
//     e.preventDefault()
//     console.log($(this))
//     $("#assigned_users").val($(this).attr("id"))
//     $("#user_name").val($(this).text())
//     $("#selectusersmodel").modal("hide");
// });
// $("body").on("click", "#clearcontacts", function (e) {
//     e.preventDefault()
//     $("#attendees_contacts").val(")
// });

$("body").on("click", ".paginate-me-contacts", function (e) {
    e.preventDefault();
    $("#attendees_contacts-modal-body").animate({width: "20px"});
    $.get(
        "/planner/get/contacts/" + $(this).context.search,
        function (data, status, xhr) {
            if (status == "success") {
                $("#attendees_contacts-modal-body").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $(".for-pagination-contacts").html("Something Went Wrong Try Again Later...");
            }
        });
});
var $cids = {}
$("body").on("click", ".checkcontact", function (e) {
    // console.log($(this).prop("checked") == true)
    if ($(this).prop("checked") == true) {
        if (!($(this).val() in $cids));
            $cids[$(this).val()] = $(this).parent().next().text().trim();
    }
    else {
        delete $cids[$(this).val()];
    }
    // console.log($cids)
})
$("body").on("click", "#close-attendees-contacts-model", function (e) {
    // console.log($cids)
    $(".selectedcontacts").html("");
    // $('#contact_name').parent().after('<div class="selectedcontacts"></div>')
    for (a in $cids) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_contacts" type="hidden" name="attendees_contacts" value="' + a + '"/>';
            str = '<div class="input-group"><input placeholder="Contacts" readonly value="' + $cids[a] + '" name="attendees_contactname" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthiscontact"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $(".selectedcontacts").append(str);
        }
    }
})
$("body").on("click", ".clearthiscontact", function (e) {
    e.preventDefault();
    $(this).closest(".input-group").remove();
    delete $cids[$(this).parent().next().val()];
    // console.log($cids)
})

//LEADS START //////////////////////////////////////////////////////////////
$("body").on("click", "#select-attendee-leads", function (e) {
    e.preventDefault();
    $("#select-leads-model").modal("show");
    $.get(
        "/planner/get/leads/",
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#select-leads-modal-body").html(data);
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

});
// $("body").on("click", "#assigned-user-modal-body .username", function (e) {
//     e.preventDefault()
//     console.log($(this))
//     $("#assigned_users").val($(this).attr("id"))
//     $("#user_name").val($(this).text())
//     $("#select-assigned-user-model").modal("hide");
// });
// $("body").on("click", "#clearcontacts", function (e) {
//     e.preventDefault()
//     $("#attendees_contacts").val(")
// });

$("body").on("click", ".paginate-me-leads", function (e) {
    e.preventDefault();
    $("#attendees_leads-modal-body").animate({width: "20px"});
    $.get(
        "/planner/get/leads/" + $(this).context.search,
        function (data, status, xhr) {
            if (status == "success") {
                $("#attendees_leads-modal-body").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $(".for-pagination-contacts").html("Something Went Wrong Try Again Later...");
            }
        });
});
var $lids = {};
$("body").on("click", ".checklead", function (e) {
    // console.log($(this).prop("checked") == true)
    if ($(this).prop("checked") == true) {
        if (!($(this).val() in $lids))
            $lids[$(this).val()] = $(this).parent().next().text().trim();
    }
    else {
        delete $lids[$(this).val()];
    }
    // console.log($lids)
})
$("body").on("click", "#close-attendees-leads-model", function (e) {
    // console.log($lids)
    $("#selectedleads").html("");
    $("#leads_name").parent().after("<div id="selectedleads"></div>");
    for (a in $lids) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_leads" type="hidden" name="attendees_leads" value="' + a + '"/>';
            str = '<div class="input-group"><input placeholder="Leads" readonly value="' + $lids[a] + '" name="attendees_leadname" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthislead"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $("#selectedleads").append(str);
        }
    }
})
$("body").on("click", ".clearthislead", function (e) {
    e.preventDefault();
    $(this).closest(".input-group").remove();
    delete $lids[$(this).parent().next().val()];
    // console.log($lids)
})
/////////////////////SELECT ASSIGNED USERS//////////////////////////////////////////////////
$("body").on("click", "#assign-user", function (e) {
    e.preventDefault();
    $("#select-assigned-user-model").modal("show");
    $.get(
        "/planner/get/users/",
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#assigned-user-modal-body").html(data);
                $("#assigned-user-modal-body .checkuser").remove();
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
                }
            }
            else {
                console.log(status)
            }
        });

});

$("body").on("click", "#select-assigned-user-model .cell .username", function (e) {
    e.preventDefault();
    $(".selected-assigned-users").html("");
    $("#select-assigned-user-model").modal("hide");
    strr = '<input class="assigned_users" type="hidden" name="assigned_users" value="' + $(this).context.id + '"/>';
    str = '<div class="input-group"><input readonly value="' + $(this).text() + '" name="assigned_username" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthis-assigned-user"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
    $(".selected-assigned-users").append(str);
})

$("body").on("click", "#close-assigned-user-model", function (e) {
    $(".selected-assigned-users").html("");
});
$("body").on("click", "#modeldialogclosed", function (e) {
    $(".selected-assigned-users").html("");
    $(".selectedcontacts").html("");
    $(".selectedusers").html("");
    $("#selectedleads").html("");
});
$("body").on("click", ".clearthis-assigned-user", function (e) {
    e.preventDefault();
    $(this).closest(".input-group").remove();
    delete $aids[$(this).parent().next().val()];
})

$("body").on("click", "#assigned-user-modal-body .paginate-me-users", function (e) {
    e.preventDefault();
    $("#assigned-user-modal-body").animate({width: "20px"});
    $.get(
        "/planner/get/users/" + $(this).context.search,
        function (data, status, xhr) {
            if (status == "success") {
                $("#assigned-user-modal-body").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $("#assigned-user-modal-body .paginate-me-users").html("Something Went Wrong Try Again Later...");
            }
        });
});

function getOtherFields(data) {
    ///////////////////ASSGNED USERS////////////////////////////////////////////
    $(".selected-assigned-users").html("");
    $(".assigned_users_error").before("<div class="selected-assigned-users"></div>");
    for (a in data["assigned_users"]) {
        if ($.isNumeric(a)) {
            strr = '<input class="assigned_users" type="hidden" name="assigned_users" value="' + a + '"/>';
            // $('#user_name').after(str)
            str = '<div class="input-group"><input placeholder="Assign user" readonly value="' + data['assigned_users'][a] + '" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthis-assigned-user"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $(".selected-assigned-users").append(str);
        }
    }
    ///////////////////END  ASSGNED USERS////////////////////////////////////////////
    /////////////////// ATTENDEES LEADS////////////////////////////////////////////
    $("#selectedleads").html("");
    $("#leads_name").parent().after("<div id="selectedleads"></div>");
    for (a in data["attendees_leads"]) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_leads" type="hidden" name="attendees_leads" value="' + a + '"/>';
            str = '<div class="input-group"><input placeholder="Leads" readonly value="' + data['attendees_leads'][a] + '" name="attendees_leadname" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthislead"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $("#selectedleads").append(str);
        }
    }
    ///////////////////END  ATTENDEES LEADS////////////////////////////////////////////
    ///////////////////ATTENDEES CONTACTA////////////////////////////////////////////
    $(".selectedcontacts").html("");
    // $("#contact_name").parent().after("<div class="selectedcontacts"></div>")
    for (a in data["attendees_contacts"]) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_contacts" type="hidden" name="attendees_contacts" value="' + a + '"/>';
            str = '<div class="input-group"><input placeholder="Contacts" readonly value="' + data['attendees_contacts'][a] + '" name="attendees_contactname" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthiscontact"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $(".selectedcontacts").append(str);
        }
    }
    /////////////////// END ATTENDEES CONTACTA////////////////////////////////////////////
    /////////////////// ATTENDEES USERS////////////////////////////////////////////
    $(".selectedusers").html("");
    $(".attendees-users-user_name").parent().after("<div class="selectedusers"></div>");
    for (a in data["attendees_user"]) {
        if ($.isNumeric(a)) {
            strr = '<input id="attendees_user" type="hidden" name="attendees_user" value="' + a + '"/>';
            // $('#user_name').after(str)
            str = '<div class="input-group"><input placeholder="user" readonly value="' + data['attendees_user'][a] + '" name="attendees_username" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthisuser"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
            $(".selectedusers").append(str);
        }
    }
    /////////////////// END ATTENDEES USERS////////////////////////////////////////////
}

$("body").on("click", ".filterfield", function (e, afield) {
    e.preventDefault();
    $("." + $($(this).children()[0]).context.classList[0]).toggle();
})
$("body").on("click", ".remove-this-filter", function (e) {
    e.preventDefault();
    // console.log($(this))
    $addedFilterItem = $($(this).closest("div .input-group")[0]);
    $className = $addedFilterItem.context.classList[$addedFilterItem.context.classList.length - 1];
    $("." + $className).toggle();
});
$("body").on("click", ".reset-filters", function (e) {
    e.preventDefault();
    $(".addedFilters").children().hide();

    $(".filter-list .filterfield a").show();
})

$("body").on("click", ".searchmeetings", function (e) {
    e.preventDefault();
    // console.log($("#filter-form").serialize())
    $.get(
        "/planner/search/events/",
        data = $("#filter-form").serialize(),
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                if (data["Event"] == "DoesNotExist") {
                    $(".for-pagination").html("<div class="heading text-center"> No Meetings Found </div>");
                } else {
                    $(".for-pagination").html(data);
                }
                if (data["auth"] == "NO") {
                    alert("Not Authenticated!!");
                    window.location = "/login/";
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
});
//////////////////////////////////created user/////////////////////////////////////////////////////////////////////
$("body").on("click", "#created-user", function (e) {
    e.preventDefault();
    $("#select-created-user-model").modal("show");
    $.get(
        "/planner/get/users/",
        data = {},
        function (data, status, xhr) {
            if (status == "success") {
                // console.log(data)
                $("#created-user-modal-body").html(data);
                $("#created-user-modal-body .checkuser").remove();
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
});
$("body").on("click", "#select-created-user-model .cell .username", function (e) {
    e.preventDefault();
    $(".selected-created-user").html("");
    $("#select-created-user-model").modal("hide");
    strr = '<input class="created_user" type="hidden" name="created_user" value="' + $(this).context.id + '"/>';
    str = '<div class="input-group"><input readonly value="' + $(this).text() + '" class="main-element form-control input-sm" type="text"><span class="input-group-btn"><button tabindex="-1" type="button" class="btn btn-default input-sm clearthis-created-user"><i class="glyphicon glyphicon-remove"></i></button></span>' + strr + '</div>';
    $(".selected-created-user").append(str);
})

$("body").on("click", "#close-created-user-model", function (e) {
    $(".selected-created-user").html("");
});
$("body").on("click", "#modeldialogclosed", function (e) {
    $(".selected-created-user").html("");
});
$("body").on("click", ".clearthis-created-user", function (e) {
    e.preventDefault();
    $(this).closest(".input-group").remove();
    delete $aids[$(this).parent().next().val()];
})

$("body").on("click", "#created-user-modal-body .paginate-me-users", function (e) {
    e.preventDefault();
    $("#created-user-modal-body").animate({width: "20px"});
    $.get(
        "/planner/get/users/" + $(this).context.search,
        function (data, status, xhr) {
            if (status == "success") {
                $("#created-user-modal-body").html(data).animate({width: "100%"});
            }
            else if (status == "error") {
                $("#created-user-modal-body .paginate-me-users").html("Something Went Wrong Try Again Later...");
            }
        });
});
//////////////////////////////////end created user/////////////////////////////////////////////////////////////////////
