import 'package:flutter/material.dart';
import 'ticket_form_screen.dart';

/// Wrapper that uses TicketFormScreen in create mode.
class TicketCreateScreen extends StatelessWidget {
  const TicketCreateScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const TicketFormScreen();
  }
}
