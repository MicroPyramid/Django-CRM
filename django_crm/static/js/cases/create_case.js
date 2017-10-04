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

$('#id_account').change(function(){
    var csrftoken = getCookie('csrftoken');
    var acc= $("#id_account").val()
        $.get("/cases/select_contacts/", {"acc":acc, "csrfmiddlewaretoken": csrftoken}, function(data){
          $("#id_contacts").html("")
          $.each(data, function (index, value) {
            // console.log(index, value)
                $("#id_contacts").append("<option value="+index+">"+value+"</option>")
            });
        })
      });

$('#formsubmit').click(function(e) {
    if($("#id_name").val() == ""){
        e.preventDefault();
         $("#NameError").show()
        }
    })