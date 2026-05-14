import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../../core/theme/theme.dart';
import '../../data/models/ticket.dart';
import '../../providers/analytics_provider.dart';

/// Analytics dashboard for tickets (Tier 2). Read-only — no CSV export on
/// mobile; users go to the web for that.
class TicketAnalyticsScreen extends ConsumerStatefulWidget {
  const TicketAnalyticsScreen({super.key});

  @override
  ConsumerState<TicketAnalyticsScreen> createState() =>
      _TicketAnalyticsScreenState();
}

class _TicketAnalyticsScreenState extends ConsumerState<TicketAnalyticsScreen> {
  DateTimeRange _range = DateTimeRange(
    start: DateTime.now().subtract(const Duration(days: 30)),
    end: DateTime.now(),
  );
  TicketPriority? _priority;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _apply());
  }

  void _apply() {
    ref.read(analyticsProvider.notifier).setQuery(
          AnalyticsQuery(
            from: _range.start,
            to: _range.end,
            priority: _priority?.value,
          ),
        );
  }

  Future<void> _pickRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 1)),
      initialDateRange: _range,
    );
    if (picked != null) {
      setState(() => _range = picked);
      _apply();
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = ref.watch(analyticsProvider);

    return Scaffold(
      backgroundColor: AppColors.surfaceDim,
      appBar: AppBar(
        title: const Text('Analytics'),
        backgroundColor: AppColors.surface,
        elevation: 0,
        scrolledUnderElevation: 1,
        leading: IconButton(
          icon: const Icon(LucideIcons.chevronLeft),
          onPressed: () => context.pop(),
        ),
      ),
      body: Column(
        children: [
          _filterBar(),
          Expanded(child: _body(data)),
        ],
      ),
    );
  }

  Widget _filterBar() {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: _pickRange,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.gray100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(LucideIcons.calendar, size: 16),
                  const SizedBox(width: 8),
                  Text(
                    '${_fmt(_range.start)} — ${_fmt(_range.end)}',
                    style: AppTypography.body,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                for (final p in [null, ...TicketPriority.values])
                  Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: Text(p == null ? 'All priorities' : p.label),
                      selected: _priority == p,
                      onSelected: (_) {
                        setState(() => _priority = p);
                        _apply();
                      },
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _fmt(DateTime d) =>
      '${d.year}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Widget _body(AnalyticsDashboard data) {
    if (data.isLoading && data.frt == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (data.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(LucideIcons.alertCircle, size: 48, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(data.error!, style: AppTypography.body),
            const SizedBox(height: 16),
            TextButton(onPressed: _apply, child: const Text('Retry')),
          ],
        ),
      );
    }

    final frt = data.frt;
    final mttr = data.mttr;
    final backlog = data.backlog;
    final sla = data.sla;

    return RefreshIndicator(
      onRefresh: () async => _apply(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 80),
        children: [
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.55,
            children: [
              _MetricTile(
                title: 'First Response',
                value: _hours(frt?['median_hours']),
                subtitle:
                    'p90 ${_hours(frt?['p90_hours'])} · ${frt?['count'] ?? 0} tickets',
                breachLabel: '${frt?['breach_count'] ?? 0} breached',
                icon: LucideIcons.zap,
                color: AppColors.primary600,
              ),
              _MetricTile(
                title: 'Resolution',
                value: _hours(mttr?['median_hours']),
                subtitle:
                    'p90 ${_hours(mttr?['p90_hours'])} · ${mttr?['count'] ?? 0} resolved',
                icon: LucideIcons.checkCircle,
                color: AppColors.success600,
              ),
              _MetricTile(
                title: 'Backlog (today)',
                value: _backlogCurrent(backlog).toString(),
                subtitle:
                    'Peak urgent ${_backlogPeakUrgent(backlog)} in window',
                icon: LucideIcons.inbox,
                color: AppColors.warning600,
              ),
              _MetricTile(
                title: 'SLA breach rate',
                value: _rate(sla?['frt_breach_rate']),
                subtitle: 'Resolution ${_rate(sla?['resolution_breach_rate'])}',
                icon: LucideIcons.alertTriangle,
                color: AppColors.danger600,
              ),
            ],
          ),
          const SizedBox(height: 16),
          _AgentsSection(agents: data.agents),
        ],
      ),
    );
  }

  String _hours(dynamic v) {
    if (v == null) return '—';
    final d = (v as num).toDouble();
    if (d < 1) return '${(d * 60).round()}m';
    if (d < 10) return '${d.toStringAsFixed(1)}h';
    return '${d.round()}h';
  }

  String _rate(dynamic v) {
    if (v == null) return '—';
    final d = (v as num).toDouble();
    return '${(d * 100).toStringAsFixed(1)}%';
  }

  int _backlogCurrent(Map<String, dynamic>? backlog) {
    if (backlog == null) return 0;
    final series = backlog['series'] as List<dynamic>? ?? const [];
    if (series.isEmpty) return 0;
    final last = series.last as Map<String, dynamic>;
    return last['open_count'] as int? ?? 0;
  }

  int _backlogPeakUrgent(Map<String, dynamic>? backlog) {
    if (backlog == null) return 0;
    final series = backlog['series'] as List<dynamic>? ?? const [];
    int peak = 0;
    for (final p in series) {
      if (p is Map<String, dynamic>) {
        final u = p['urgent_count'] as int? ?? 0;
        if (u > peak) peak = u;
      }
    }
    return peak;
  }
}

class _MetricTile extends StatelessWidget {
  final String title;
  final String value;
  final String subtitle;
  final String? breachLabel;
  final IconData icon;
  final Color color;

  const _MetricTile({
    required this.title,
    required this.value,
    required this.subtitle,
    required this.icon,
    required this.color,
    this.breachLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: color),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  title.toUpperCase(),
                  style: AppTypography.overline.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: AppTypography.h2.copyWith(
              color: color,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: AppTypography.caption.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          if (breachLabel != null) ...[
            const SizedBox(height: 4),
            Text(
              breachLabel!,
              style: AppTypography.caption.copyWith(
                color: AppColors.danger600,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _AgentsSection extends StatelessWidget {
  final List<Map<String, dynamic>> agents;
  const _AgentsSection({required this.agents});

  @override
  Widget build(BuildContext context) {
    if (agents.isEmpty) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: AppLayout.borderRadiusLg,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'PER-AGENT',
            style: AppTypography.overline.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          for (final a in agents.take(20)) _agentRow(a),
        ],
      ),
    );
  }

  Widget _agentRow(Map<String, dynamic> a) {
    final email = a['email'] as String? ?? a['name'] as String? ?? '—';
    final handled = a['handled'] as int? ?? 0;
    final avgFrt = a['avg_frt_hours'];
    final breachRate = a['breach_rate'];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(
              email,
              style: AppTypography.body.copyWith(fontWeight: FontWeight.w500),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          _stat('$handled', 'cases'),
          const SizedBox(width: 12),
          _stat(_formatFrt(avgFrt), 'FRT'),
          const SizedBox(width: 12),
          _stat(_formatRate(breachRate), 'breach'),
        ],
      ),
    );
  }

  Widget _stat(String value, String label) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Text(
          value,
          style: AppTypography.caption.copyWith(fontWeight: FontWeight.w600),
        ),
        Text(
          label,
          style: AppTypography.caption.copyWith(
            color: AppColors.textTertiary,
            fontSize: 10,
          ),
        ),
      ],
    );
  }

  String _formatFrt(dynamic v) {
    if (v == null) return '—';
    final d = (v as num).toDouble();
    if (d < 1) return '${(d * 60).round()}m';
    return '${d.toStringAsFixed(1)}h';
  }

  String _formatRate(dynamic v) {
    if (v == null) return '—';
    final d = (v as num).toDouble();
    return '${(d * 100).toStringAsFixed(0)}%';
  }
}
