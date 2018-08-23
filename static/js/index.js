$("body").on("click", "#home", function (e) {
    e.preventDefault();
    window.location = "/";
});
//
// $('body').on('click', '#loadmeetings', function (e) {
//     //Loads Meetings Tab
//     e.preventDefault()
//     $.get(
//         '/planner/meetings/list/',
//         function (data, textStatus, jQxhr) {
//             if (textStatus == 'success') {
//                 $("#mainbody").html(data);
//             }
//             else {
//                 alert(data)
//             }
//         });
//     $(function () {
//         $('#startdatepicker').datetimepicker(
//             {
//                 format: 'MM/DD/YYYY HH:MM:SS'
//             }
//         );
//         $('#enddatepicker').datetimepicker({
//             useCurrent: false,
//             format: 'MM/DD/YYYY HH:MM:SS'
//         });
//         $("#startdatepicker").on("dp.change", function (e) {
//             $('#enddatepicker').data("DateTimePicker").minDate(e.date);
//         });
//         $("#enddatepicker").on("dp.change", function (e) {
//             $('#startdatepicker ').data("DateTimePicker").maxDate(e.date);
//         });
//     });
// });
// //end loads meetings tab
// $('body').on('click', '#loadtasks', function (e) {
//     e.preventDefault()
//     //Loads tasks Tab
//     $.get(
//         '/planner/tasks/list/',
//         function (data, textStatus, jQxhr) {
//             if (textStatus == 'success') {
//                 $("#mainbody").html(data);
//             }
//             else {
//                 alert(data)
//             }
//         });
//
// });
// //end loads tasks tab
// //Loads calls Tab
// $('body').on('click', '#loadmcalls', function (e) {
//     e.preventDefault()
//     $.get(
//         '/planner/calls/list/',
//         function (data, textStatus, jQxhr) {
//             if (textStatus == 'success') {
//                 $("#mainbody").html(data);
//             }
//             else {
//                 alert(data)
//             }
//         });
//
// });
// //end loads calls tab
