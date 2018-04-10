$('body').on('click', '.setstatus', function (e) {
    e.preventDefault();
    eventID = $(this).closest("tr")[0].id
    event = eventID.match(/\d+/)[0]
    status = $(this).text().replace('Set ', '')
    $.post(
        '/planner/event/set/status/',
        {id: event, status: status},
        function (data, status, xhr) {
            if (status == 'success') {
                if (data['success'] == 'Event Updated') {
                    $('#' + eventID.match(/\D+/)[0] + data["id"] + 'status').fadeOut(function () {
                        $(this).text(data["status"]);
                    }).fadeIn();
                }
                else if (data['AUTH'] == 'NO') {
                    window.location = '/accounts/login/';
                    //login REDIRECT URL
                }
                else if (data['INVALID'] == 'METHOD') {
                    window.location = '/logout/'
                }
                else if (data['METHOD'] == 'INVALID') {
                    window.location = '/logout/'
                }
                else {
                    if (data['Event'] != 'DoesNotExist') {
                        window.location = '/logout/'
                    }
                }
            }
            else if (status == 'error') {
                console.log(jqXhr);
                if (data['error'] == 'Something Went Wrong!!!') {
                    window.location = '/';
                    console.log('Something Went Wrong!!!')
                }
            }
            else {
                console.log(status)
            }
        });
});

$('body').on('click', '#selectparent', function (e) {
    e.preventDefault()
    $('#selectparentmodel').modal("show");
    $('#selectparentmodel').find('.modal-title').text('Select ' + $('#parent_type').val())
    if ($('#parent_type').val() == 'Account') {
        gURL = '/accounts/get/list/'
    }
    if ($('#parent_type').val() == 'Contact') {
        gURL = '/contacts/get/list/'
    }
    else if ($('#parent_type').val() == 'Lead') {
        gURL = '/leads/get/list/'
    }
    else if ($('#parent_type').val() == 'Opportunity') {
        gURL = '/opportunities/get/list/'
    }
    else if ($('#parent_type').val() == 'Case') {
        gURL = '/cases/get/list/'
    }
    $.get(
        gURL,
        data = {},
        function (data, status, xhr) {
            if (status == 'success') {
                // console.log(data)
                $("#selectcontact-modal-body").html(data)
                if (data['auth'] == 'NO') {
                    alert('Not Authanticated!!')
                    //login REDIRECT URL
                }

            }
            if (status == 'error') {
                console.log(jqXhr);
                if (data['error'] == 'Something Went Wrong!!!') {
                    alert('We Regret, there is an issue!! Try again.')
                    window.location = '/';
                    console.log('Something Went Wrong!!!')
                }
            }
            else {
                console.log(status)
            }
        });

});
$('body').on('click', '.parentname', function (e) {
    e.preventDefault()
    console.log($(this))
    $('#parent_id').val($(this).attr('id'))
    $('#parent_name').val($(this).text().trim())
    $('#selectparentmodel').modal("hide");
});

$('body').on('click', '#closeselectparentmodel', function (e) {
    e.preventDefault()
    $('#selectparentmodel').modal("hide");
    $('#parent_name').val('')
    $('#parent_id').val('')
});
$('body').on('click', '#clearparent', function (e) {
    e.preventDefault()
    $('#parent_name').val('')
    $('#parent_id').val('')
});
$("body").on("click", '.glyphicon-trash', function (e) {
    if ($($(this).siblings()[2]).prop("checked") == false) {
        $($(this).siblings()[2]).prop('checked', true)
        $(this).css({'color': 'red'})
        $($(this).siblings()[0]).attr('disabled', '')
        $($(this).siblings()[1]).attr('disabled', '')
    }
    else {
        $($(this).siblings()[2]).prop('checked', false)
        $($(this).siblings()[0]).removeAttr('disabled', '')
        $($(this).siblings()[1]).removeAttr('disabled', '')
        $(this).removeAttr('style')
    }
})
$('body').on('click', '.paginate-me', function (e) {
    e.preventDefault();
    URL = window.location.pathname + $(this).context.search
    $('.for-pagination').animate({width: '20px'})
    $.get(
        URL,
        function (data, status, xhr) {
            if (status == 'success') {
                $('.for-pagination').html(data).animate({width: '100%'})
            }
            else if (status == 'error') {
                $('.for-pagination').html('Something Went Wrong Try Again Later...')
            }
        });
});
$('body').on('click', '#selectusers', function (e) {
    e.preventDefault()
    $('#selectusersmodel').modal("show");
    $.get(
        '/planner/get/users/',
        data = {},
        function (data, status, xhr) {
            if (status == 'success') {
                // console.log(data)
                $("#selectusers-modal-body").html(data)
                if (data['auth'] == 'NO') {
                    alert('Not Authanticated!!')
                    //login REDIRECT URL
                }
            }
            if (status == 'error') {
                console.log(jqXhr);
                if (data['error'] == 'Something Went Wrong!!!') {
                    alert('We Regret, there is an issue!! Try again.')
                    window.location = '/';
                    console.log('Something Went Wrong!!!')
                }
            }
            else {
                console.log(status)
            }
        });

});
$('body').on('click', '.username', function (e) {
    e.preventDefault()
    console.log($(this))
    $('#assigned_users').val($(this).attr('id'))
    $('#user_name').val($(this).text())
    $('#selectusersmodel').modal("hide");
});
$('body').on('click', '#clearuser', function (e) {
    e.preventDefault()
    $('#user_name').val('')
    $('#assigned_users').val('')
});

$('body').on('click', '.paginate-me-users', function (e) {
    e.preventDefault();
    $('#selectusers-modal-body').animate({width: '20px'})
    $.get(
        '/planner/get/users/' + $(this).context.search,
        function (data, status, xhr) {
            if (status == 'success') {
                $('#selectusers-modal-body').html(data).animate({width: '100%'})
            }
            else if (status == 'error') {
                $('.for-pagination').html('Something Went Wrong Try Again Later...')
            }
        });
});

var $uids = []
$('body').on('click', '.checkuser', function (e) {
    console.log($(this).prop("checked") == true)
    if ($(this).prop("checked") == true) {
        $uids.push($(this).val())
    }
    else {
        $uids.remove($(this).val())
    }
    var unique = $uids.filter(function (itm, i, $uids) {
        return i == $uids.indexOf(itm);
    });
    $uids = unique
    console.log($uids)
})
$('body').on('click', '#closeselectusersmodel', function (e) {
    console.log($uids)
    for (a in $uids) {
        if ($.isNumeric(a)) {
            str = '<input id="assigned_users" type="hidden" name="assigned_users" value="' + $uids[a] + '"/>'
            $('#user_name').after(str)
        }
    }
})


Array.prototype.remove = function () {
    var what, a = arguments, L = a.length, ax;
    while (L && this.length) {
        what = a[--L];
        while ((ax = this.indexOf(what)) !== -1) {
            this.splice(ax, 1);
        }
    }
    return this;
};
