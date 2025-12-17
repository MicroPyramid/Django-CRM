import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../data/models/task.dart';
import '../services/api_service.dart';

/// Tasks list state
class TasksState {
  final List<Task> tasks;
  final bool isLoading;
  final String? error;
  final int totalCount;
  final bool hasMore;
  final int currentOffset;

  const TasksState({
    this.tasks = const [],
    this.isLoading = false,
    this.error,
    this.totalCount = 0,
    this.hasMore = true,
    this.currentOffset = 0,
  });

  const TasksState.initial()
      : tasks = const [],
        isLoading = false,
        error = null,
        totalCount = 0,
        hasMore = true,
        currentOffset = 0;

  TasksState copyWith({
    List<Task>? tasks,
    bool? isLoading,
    String? error,
    int? totalCount,
    bool? hasMore,
    int? currentOffset,
    bool clearError = false,
  }) {
    return TasksState(
      tasks: tasks ?? this.tasks,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      totalCount: totalCount ?? this.totalCount,
      hasMore: hasMore ?? this.hasMore,
      currentOffset: currentOffset ?? this.currentOffset,
    );
  }
}

/// Tasks notifier for managing tasks state
class TasksNotifier extends StateNotifier<TasksState> {
  TasksNotifier() : super(const TasksState.initial());

  final ApiService _apiService = ApiService();
  static const int _pageSize = 20;

  /// Fetch tasks from API
  Future<void> fetchTasks({
    String? search,
    String? status,
    String? priority,
    bool refresh = false,
  }) async {
    if (state.isLoading) return;

    if (refresh) {
      state = state.copyWith(
        currentOffset: 0,
        hasMore: true,
        clearError: true,
      );
    }

    debugPrint('TasksNotifier: Fetching tasks (offset: ${state.currentOffset})...');
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      // Build query parameters
      final queryParams = <String, String>{
        'limit': _pageSize.toString(),
        'offset': state.currentOffset.toString(),
      };

      if (search != null && search.isNotEmpty) {
        queryParams['search'] = search;
      }
      if (status != null && status.isNotEmpty) {
        queryParams['status'] = status;
      }
      if (priority != null && priority.isNotEmpty) {
        queryParams['priority'] = priority;
      }

      final url = Uri.parse(ApiConfig.tasks).replace(queryParameters: queryParams).toString();
      final response = await _apiService.get(url);

      if (response.success && response.data != null) {
        final data = response.data!;

        debugPrint('TasksNotifier: API response keys: ${data.keys.toList()}');

        // Parse tasks - handle different response formats
        List<dynamic> tasksList = [];
        int tasksCount = 0;

        if (data['tasks'] != null) {
          tasksList = data['tasks'] as List<dynamic>? ?? [];
          tasksCount = data['tasks_count'] as int? ?? tasksList.length;
        } else if (data['results'] != null) {
          // Handle paginated response format
          tasksList = data['results'] as List<dynamic>? ?? [];
          tasksCount = data['count'] as int? ?? tasksList.length;
        }

        debugPrint('TasksNotifier: Found ${tasksList.length} tasks in response');

        final newTasks = <Task>[];
        for (final item in tasksList) {
          try {
            if (item is Map<String, dynamic>) {
              newTasks.add(Task.fromJson(item));
            } else {
              debugPrint('TasksNotifier: Skipping non-map item: ${item.runtimeType}');
            }
          } catch (e) {
            debugPrint('TasksNotifier: Error parsing task: $e');
            debugPrint('TasksNotifier: Task data: $item');
          }
        }

        // Update state
        final updatedTasks = refresh ? newTasks : [...state.tasks, ...newTasks];

        state = state.copyWith(
          tasks: updatedTasks,
          isLoading: false,
          totalCount: tasksCount,
          hasMore: newTasks.length >= _pageSize,
          currentOffset: state.currentOffset + newTasks.length,
        );

        debugPrint('TasksNotifier: Loaded ${newTasks.length} tasks (total: ${updatedTasks.length})');
      } else {
        state = state.copyWith(
          isLoading: false,
          error: response.message ?? 'Failed to load tasks',
        );
        debugPrint('TasksNotifier: API error - ${response.message}');
      }
    } catch (e) {
      debugPrint('TasksNotifier: Exception - $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to load tasks: ${e.toString()}',
      );
    }
  }

  /// Refresh tasks (reset and fetch first page)
  Future<void> refresh() async {
    state = const TasksState.initial();
    await fetchTasks(refresh: true);
  }

  /// Load more tasks
  Future<void> loadMore() async {
    if (!state.hasMore || state.isLoading) return;
    await fetchTasks();
  }

  /// Clear tasks data
  void clear() {
    state = const TasksState.initial();
  }
}

/// Tasks provider
final tasksProvider = StateNotifierProvider<TasksNotifier, TasksState>((ref) {
  return TasksNotifier();
});

/// Convenience providers
final tasksListProvider = Provider<List<Task>>((ref) {
  return ref.watch(tasksProvider).tasks;
});

final tasksLoadingProvider = Provider<bool>((ref) {
  return ref.watch(tasksProvider).isLoading;
});

final tasksErrorProvider = Provider<String?>((ref) {
  return ref.watch(tasksProvider).error;
});

/// Grouped tasks providers
final overdueTasksProvider = Provider<List<Task>>((ref) {
  final tasks = ref.watch(tasksListProvider);
  return tasks.where((t) => t.isOverdue).toList()
    ..sort((a, b) {
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
  return tasks.where((t) => t.isUpcoming).toList()
    ..sort((a, b) {
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
