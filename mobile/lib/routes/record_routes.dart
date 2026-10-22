import '../config/api_config.dart';
import 'app_routes.dart';

/// Where a linked record opens: a built-in kind by name, a custom object as
/// `obj:<key>`. `null` for anything else, so callers render it as plain text.
String? linkedRecordRoute(String target, String id) {
  switch (target) {
    case 'lead':
      return AppRoutes.leadDetail.replaceFirst(':id', id);
    case 'contact':
      return AppRoutes.contactDetail.replaceFirst(':id', id);
    case 'account':
      return AppRoutes.accountDetail.replaceFirst(':id', id);
    case 'deal':
      return AppRoutes.dealDetail.replaceFirst(':id', id);
    case 'ticket':
      return AppRoutes.ticketDetail.replaceFirst(':id', id);
    case 'task':
      return AppRoutes.taskDetail.replaceFirst(':id', id);
  }
  if (target.startsWith('obj:')) {
    final key = target.substring(4);
    return ApiConfig.isObjectKey(key) ? AppRoutes.objectRecord(key, id) : null;
  }
  return null;
}
