  $("#form_opp").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    $.post("/oppurtunities/create/", $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_opp,
            function(field_name, error){
              err_opp = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_opp); })
            }
        else {
          window.location = "";
        }
    })
  });

  $(".form_opp_edit").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    url = $this.attr('action')
    $.post(url , $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_opp,
            function(field_name, error){
              err_opp = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_opp); })
            }
        else {
          window.location = "";
        }
    })
  });

  $("body").on("click",".opp_remove",function(e){
    href=$(this).attr("data-href")
    id=$(this).attr("id")
    $.get(href,{}, function(data){
      window.location = "";
    },'json');
  });

  $("#form_con").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    $.post("/contacts/create/", $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_con,
            function(field_name, error){
              err_con = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_con); })
            }
        else {
          window.location = "";
        }
    })
  });

  $(".form_con_edit").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    url = $this.attr('action')
    $.post(url , $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_con,
            function(field_name, error){
              err_con = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_con); })
            }
        else {
          window.location = "";
        }
    })
  });

  $("body").on("click",".con_remove",function(e){
    href=$(this).attr("data-href")
    id=$(this).attr("id")
    $.get(href,{}, function(data){
      window.location = "";
    },'json');
  });

  $("#form_case").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    $.post("/cases/create/", $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_case,
            function(field_name, error){
              err_case = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_case); })
            }
        else {
          window.location = "";
        }
    })
  });

  $(".form_case_edit").submit(function(e) {
    e.preventDefault();
    $this = $(this)
    url = $this.attr('action')
    $.post(url , $this.serialize(), function(response){
        if(response.error){
          $(".error").remove();
          $.each(response.errors_case,
            function(field_name, error){
              err_case = '<span class="error" style="color:red;">' + error + '</span>'
              $this.find("[name=" + field_name + "]").after(err_case); })
            }
        else {
          window.location = "";
        }
    })
  });

  $("body").on("click",".case_remove",function(e){
    href=$(this).attr("data-href")
    id=$(this).attr("id")
      window.location = "";
    $.get(href,{}, function(data){
    },'json');
  });

  $(function () {
    $('#datetimepicker1, #datetimepicker2').datetimepicker({
      'format': 'YYYY-MM-DD'
    });
  });

  $('#remove_account').click(function(e){
    var result = confirm("Are You Sure You Want to delete?");
    if (result==false) {
      e.preventDefault()
    }
  });

  function oppForm() {
    $('.error').hide()
    document.getElementById("form_opp").reset();
  }

  function conForm() {
    $('.error').hide()
    document.getElementById("form_con").reset();
  }

  function caseForm() {
    $('.error').hide()
    document.getElementById("form_case").reset();
  }