import 'dart:convert';

import 'package:bottle_crm/data/models/lead.dart';
import 'package:bottle_crm/data/models/task.dart';
import 'package:bottle_crm/providers/leads_provider.dart';
import 'package:bottle_crm/providers/tasks_provider.dart';
import 'package:bottle_crm/services/api_service.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

/// The four "Needs Attention" badges on the dashboard now open a list.
///
/// The risk in linking them is a list whose length disagrees with the number
/// that opened it, which is worse than a dead badge: it looks like an answer.
/// Each count comes from `ApiHomeView`, so these tests pin the client filter
/// against the server's definition, field by field:
///
///   overdue_tasks    status__in=["New","In Progress"], due_date__lt=today
///   tasks_due_today  status__in=["New","In Progress"], due_date=today
///   followups_today  next_follow_up=today
///   hot_leads        rating="HOT", status__in=["assigned","in process"]
///
/// The second half asserts what reaches the wire, because a `Set` of statuses
/// only becomes a repeated `?status=` through `Uri.replace`, which is a detail
/// of dart:core rather than something this code controls.
class _RecordingClient extends http.BaseClient {
  _RecordingClient(this.body);

  final String body;
  final List<Uri> urls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    urls.add(request.url);
    return http.StreamedResponse(
      Stream.value(utf8.encode(body)),
      200,
      request: request,
    );
  }
}

const _emptyTasks = '{"tasks": [], "tasks_count": 0}';
const _emptyLeads =
    '{"open_leads": {"open_leads": [], "leads_count": 0}, '
    '"close_leads": {"close_leads": []}}';

void main() {
  // A Thursday, so "the day before" crosses nothing interesting, and a
  // single-digit month and day so the zero padding is actually exercised.
  final day = DateTime(2026, 8, 7);

  group('what each badge means', () {
    test('Overdue is still-open tasks due before today', () {
      final f = TaskFilters.overdue(day);

      expect(f.statuses, {TaskStatus.newTask, TaskStatus.inProgress});
      // The server says `due_date__lt=today`; on a date column the day before,
      // inclusive, is the same set, and `__lte` is what the list endpoint takes.
      expect(f.dueDateLte, '2026-08-06');
      expect(f.dueDateGte, isNull);
    });

    test('Due Today is still-open tasks on exactly that day', () {
      final f = TaskFilters.dueOn(day);

      expect(f.statuses, {TaskStatus.newTask, TaskStatus.inProgress});
      expect(f.dueDateGte, '2026-08-07');
      expect(f.dueDateLte, '2026-08-07');
    });

    test('a single-digit month and day are zero padded', () {
      // '2026-1-5' is not a date the API parses, and it now answers 400 rather
      // than 500, so an unpadded day would be a visible failure.
      expect(TaskFilters.dueOn(DateTime(2026, 1, 5)).dueDateGte, '2026-01-05');
      expect(
        LeadFilters.followUpsOn(DateTime(2026, 1, 5)).nextFollowUp,
        '2026-01-05',
      );
    });

    test('Hot Leads is rated hot AND still being worked', () {
      final f = LeadFilters.hot();

      expect(f.rating, LeadRating.hot);
      // Without the statuses this would also list recycled leads, which the
      // badge does not count, so the list would be longer than the number.
      expect(f.statuses, {LeadStatus.assigned, LeadStatus.inProcess});
    });

    test('Follow-ups is one exact day', () {
      expect(LeadFilters.followUpsOn(day).nextFollowUp, '2026-08-07');
    });
  });

  group('what goes on the wire', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() => container.dispose());

    test('two statuses become two status parameters', () async {
      final client = _RecordingClient(_emptyTasks);
      ApiService().setClientForTesting(client);

      await container.read(tasksProvider.future);
      await container
          .read(tasksProvider.notifier)
          .setFilters(TaskFilters.overdue(day));

      final query = client.urls.last.queryParametersAll;
      expect(query['status'], containsAll(['New', 'In Progress']));
      expect(query['due_date__lte'], ['2026-08-06']);
    });

    test('one status is still one parameter', () async {
      final client = _RecordingClient(_emptyTasks);
      ApiService().setClientForTesting(client);

      await container.read(tasksProvider.future);
      await container
          .read(tasksProvider.notifier)
          .setFilters(const TaskFilters(statuses: {TaskStatus.completed}));

      expect(client.urls.last.queryParametersAll['status'], ['Completed']);
    });

    test('no status means no status parameter at all', () async {
      final client = _RecordingClient(_emptyTasks);
      ApiService().setClientForTesting(client);

      await container.read(tasksProvider.future);
      await container
          .read(tasksProvider.notifier)
          .setFilters(const TaskFilters());

      expect(client.urls.last.queryParameters.containsKey('status'), isFalse);
    });

    test('the hot-leads view sends the rating and both statuses', () async {
      final client = _RecordingClient(_emptyLeads);
      ApiService().setClientForTesting(client);

      await container.read(leadsProvider.future);
      await container
          .read(leadsProvider.notifier)
          .setFilters(LeadFilters.hot());

      final query = client.urls.last.queryParametersAll;
      expect(query['rating'], ['HOT']);
      expect(query['status'], containsAll(['assigned', 'in process']));
    });

    test('the follow-ups view sends the day', () async {
      final client = _RecordingClient(_emptyLeads);
      ApiService().setClientForTesting(client);

      await container.read(leadsProvider.future);
      await container
          .read(leadsProvider.notifier)
          .setFilters(LeadFilters.followUpsOn(day));

      expect(client.urls.last.queryParametersAll['next_follow_up'], [
        '2026-08-07',
      ]);
    });
  });

  group('the chip a filtered list shows', () {
    test('one status has a label to print, several do not', () {
      // The chip prints `statuses.first` only when there is exactly one.
      // Printing one of two would name a filter narrower than the list is.
      expect(
        const TaskFilters(statuses: {TaskStatus.newTask}).status,
        TaskStatus.newTask,
      );
      expect(TaskFilters.overdue(day).status, isNull);
      expect(
        const LeadFilters(statuses: {LeadStatus.assigned}).status,
        LeadStatus.assigned,
      );
      expect(LeadFilters.hot().status, isNull);
    });

    test('a badge-opened list counts as filtered, so Clear is offered', () {
      // `isActive` drives the clear-all control. A list the user did not
      // narrow themselves is exactly the one they need a way out of.
      expect(TaskFilters.overdue(day).isActive, isTrue);
      expect(TaskFilters.dueOn(day).isActive, isTrue);
      expect(LeadFilters.hot().isActive, isTrue);
      expect(LeadFilters.followUpsOn(day).isActive, isTrue);
      expect(const TaskFilters().isActive, isFalse);
      expect(const LeadFilters().isActive, isFalse);
    });

    test('clearing the status empties the set rather than leaving one', () {
      expect(TaskFilters.overdue(day).cleared(status: true).statuses, isEmpty);
      expect(LeadFilters.hot().cleared(status: true).statuses, isEmpty);
    });

    test('the single-select sheet still overwrites the whole set', () {
      // The sheet offers one status at a time. Coming from a two-status badge,
      // picking "Completed" has to replace both, not add a third.
      final next = TaskFilters.overdue(
        day,
      ).copyWith(status: TaskStatus.completed);

      expect(next.statuses, {TaskStatus.completed});
    });

    test('the lead sheet does the same', () {
      expect(LeadFilters.hot().withStatus(LeadStatus.recycled).statuses, {
        LeadStatus.recycled,
      });
      expect(LeadFilters.hot().withStatus(null).statuses, isEmpty);
    });
  });
}
