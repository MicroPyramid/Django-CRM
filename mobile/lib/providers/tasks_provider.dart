import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/lead.dart' show Priority;
import '../data/models/task.dart';
import '../services/api_service.dart';

export '../services/api_service.dart' show ApiResponse;

/// Paginated tasks snapshot — wrapped by AsyncValue.
class TasksListData {
  final List<Task> tasks;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const TasksListData({
    this.tasks = const [],
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  TasksListData copyWith({
    List<Task>? tasks,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
  }) {
    return TasksListData(
      tasks: tasks ?? this.tasks,
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

class TasksNotifier extends AsyncNotifier<TasksListData> {
  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  @override
  Future<TasksListData> build() => _fetchPage(offset: 0);

  Future<void> refresh({
    String? search,
    String? status,
    String? priority,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => _fetchPage(
        offset: 0,
        search: search,
        status: status,
        priority: priority,
      ),
    );
  }

  Future<void> loadMore({
    String? search,
    String? status,
    String? priority,
  }) async {
    final current = state.value;
    if (current == null || !current.hasMore) return;
    if (state.isLoading) return;

    state = await AsyncValue.guard(() async {
      final next = await _fetchPage(
        offset: current.currentOffset,
        search: search,
        status: status,
        priority: priority,
      );
      return current.copyWith(
        tasks: [...current.tasks, ...next.tasks],
        totalCount: next.totalCount,
        hasMore: next.hasMore,
        currentOffset: next.currentOffset,
      );
    });
  }

  Future<TasksListData> _fetchPage({
    required int offset,
    String? search,
    String? status,
    String? priority,
  }) async {
    final queryParams = <String, String>{
      'limit': _pageSize.toString(),
      'offset': offset.toString(),
    };
    if (search != null && search.isNotEmpty) queryParams['search'] = search;
    if (status != null && status.isNotEmpty) queryParams['status'] = status;
    if (priority != null && priority.isNotEmpty) {
      queryParams['priority'] = priority;
    }

    final url = Uri.parse(
      ApiConfig.tasks,
    ).replace(queryParameters: queryParams).toString();
    debugPrint('TasksNotifier: Fetching tasks (offset: $offset)...');
    final response = await _apiService.get(url);

    if (!response.success || response.data == null) {
      throw Exception(response.message ?? 'Failed to load tasks');
    }

    final data = response.data!;
    debugPrint('TasksNotifier: API response keys: ${data.keys.toList()}');

    List<dynamic> tasksList = [];
    int tasksCount = 0;

    if (data['tasks'] != null) {
      tasksList = data['tasks'] as List<dynamic>? ?? [];
      tasksCount = data['tasks_count'] as int? ?? tasksList.length;
    } else if (data['results'] != null) {
      tasksList = data['results'] as List<dynamic>? ?? [];
      tasksCount = data['count'] as int? ?? tasksList.length;
    }

    final newTasks = <Task>[];
    for (final item in tasksList) {
      try {
        if (item is Map<String, dynamic>) {
          newTasks.add(Task.fromJson(item));
        }
      } catch (e) {
        debugPrint('TasksNotifier: Error parsing task: $e');
      }
    }

    debugPrint('TasksNotifier: loaded ${newTasks.length} tasks');

    return TasksListData(
      tasks: newTasks,
      totalCount: tasksCount,
      hasMore: newTasks.length >= _pageSize,
      currentOffset: offset + newTasks.length,
    );
  }

  /// Fetch a single task from the API.
  Future<Task?> getTaskById(String taskId) async {
    try {
      final url = '${ApiConfig.tasks}$taskId/';
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final taskData = response.data!['task_obj'] as Map<String, dynamic>?;
        if (taskData != null) {
          return Task.fromJson(taskData);
        }
      }
      return null;
    } catch (e) {
      debugPrint('TasksNotifier: Exception getting task - $e');
      return null;
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> createTask(
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _apiService.post(ApiConfig.tasks, data);
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> updateTask(
    String taskId,
    Map<String, dynamic> data,
  ) async {
    try {
      final url = '${ApiConfig.tasks}$taskId/';
      final response = await _apiService.put(url, data);
      if (response.success) await refresh();
      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  Future<ApiResponse<Map<String, dynamic>>> deleteTask(String taskId) async {
    try {
      final url = '${ApiConfig.tasks}$taskId/';
      final response = await _apiService.delete(url);

      if (response.success || response.statusCode == 204) {
        final current = state.value;
        if (current != null) {
          state = AsyncValue.data(
            current.copyWith(
              tasks: current.tasks.where((t) => t.id != taskId).toList(),
              totalCount: current.totalCount - 1,
            ),
          );
        }
        return ApiResponse(success: true, statusCode: 204);
      }

      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Toggle a task's completion (helper for the UI checkbox).
  Future<ApiResponse<Map<String, dynamic>>> toggleTaskStatus(Task task) async {
    final newStatus = task.completed ? 'New' : 'Completed';
    return patchTask(task.id, {'status': newStatus});
  }

  /// Partially update a task — optimistically applies changes locally.
  Future<ApiResponse<Map<String, dynamic>>> patchTask(
    String taskId,
    Map<String, dynamic> data,
  ) async {
    try {
      final url = '${ApiConfig.tasks}$taskId/';
      final response = await _apiService.patch(url, data);

      if (response.success) {
        final current = state.value;
        if (current != null) {
          state = AsyncValue.data(
            current.copyWith(
              tasks: current.tasks.map((t) {
                if (t.id == taskId) {
                  return t.copyWith(
                    status: data.containsKey('status')
                        ? TaskStatus.fromString(data['status'] as String?)
                        : null,
                    priority: data.containsKey('priority')
                        ? Priority.fromString(data['priority'] as String?)
                        : null,
                    title: data['title'] as String?,
                    description: data['description'] as String?,
                  );
                }
                return t;
              }).toList(),
            ),
          );
        }
      }

      return response;
    } catch (e) {
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }
}

final tasksProvider = AsyncNotifierProvider<TasksNotifier, TasksListData>(
  TasksNotifier.new,
);

/// Convenience providers — read from the AsyncValue.
final tasksListProvider = Provider<List<Task>>((ref) {
  return ref.watch(tasksProvider).value?.tasks ?? const [];
});

final tasksLoadingProvider = Provider<bool>((ref) {
  return ref.watch(tasksProvider).isLoading;
});

final tasksErrorProvider = Provider<String?>((ref) {
  return ref.watch(tasksProvider).error?.toString();
});

/// Grouped tasks providers (filters / sorters on top of the loaded list).
final overdueTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => t.isOverdue).toList()..sort((a, b) {
    if (a.dueDate == null) return 1;
    if (b.dueDate == null) return -1;
    return a.dueDate!.compareTo(b.dueDate!);
  });
});

final todayTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => !t.completed && t.isDueToday).toList()
    ..sort((a, b) {
      if (a.dueDate == null) return 1;
      if (b.dueDate == null) return -1;
      return a.dueDate!.compareTo(b.dueDate!);
    });
});

final upcomingTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => t.isUpcoming).toList()..sort((a, b) {
    if (a.dueDate == null) return 1;
    if (b.dueDate == null) return -1;
    return a.dueDate!.compareTo(b.dueDate!);
  });
});

final completedTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => t.completed).toList();
});

final noDueDateTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => !t.completed && t.dueDate == null).toList();
});
