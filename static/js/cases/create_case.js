
$('#id_account').change(function(){
    var account = $("#id_account").val()
    $.get("/cases/select_contacts/", {"account":account}, function(data){
      $("#id_contacts").html("")
      $.each(data, function (index, value) {
        $("#id_contacts").append("<option value="+index+">"+value+"</option>")
      });
    })
});
