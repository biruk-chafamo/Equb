function changeTabTo(current_tab) {
    var element = document.getElementById(current_tab);
    element.style.background = "rgba(204, 204, 204,0.5)";
    element.style.borderRadius = "7px"
};


$('.accept-invite').click( function(event) {
    var equb_id = $(this).parent()[0].classList[0];

    var data = {csrfmiddlewaretoken: "{{ csrf_token }}", 'equb_id': Number(equb_id)};


  event.preventDefault();
  $.ajax({
    type : "POST",
    url : "{% url 'moneypool:accept_invite' %}",
    csrfmiddlewaretoken: "{{ csrf_token }}",
    data : data,
    success: function(){
        $(`li.invites.${equb_id}`).remove();
      },
    error: function(XMLHttpRequest, textStatus, errorThrown) {
      alert("some error " + String(errorThrown) + String(textStatus) + String(XMLHttpRequest.responseText));
      }
   });
});

$('.invite_to_equb' ).click(function() {
  $( this ).toggleClass( 'invite_yes' );
});

$('.invite_button').click( function(event) {
    var equb_id = this.classList[0];
    var invitees = $(`.invite_to_equb.${equb_id}.invite_yes`);
    var data = {csrfmiddlewaretoken: "{{ csrf_token }}", 'equb_id': Number(equb_id), 'invited':[]};
    for (let invitee of invitees) {
        data['invited'].push(invitee.innerText);
    }

  event.preventDefault();
  $.ajax({
    type : "POST",
    url : "http://127.0.0.1:8000/moneypool/invite",
    csrfmiddlewaretoken: "{{ csrf_token }}",
    data : data,
    error: function(XMLHttpRequest, textStatus, errorThrown) {
      alert("some error " + String(errorThrown) + String(textStatus) + String(XMLHttpRequest.responseText));
      }
  });
});


$('.live-equb').change( function () {
   var pinnedEqub = $('.live-equb option:selected')[0].value;
   $('.test-live').append(pinnedEqub);
   event.preventDefault();
  $.ajax({
    type : "POST",
    url : "{% url 'moneypool:pin_equb' %}",
    csrfmiddlewaretoken: "{{ csrf_token }}",
    data : {csrfmiddlewaretoken: "{{ csrf_token }}",'pinnedEqub': Number(pinnedEqub)},
    error: function(XMLHttpRequest, textStatus, errorThrown) {
      alert("some error " + String(errorThrown) + String(textStatus) + String(XMLHttpRequest.responseText));
      }
    });
  });
