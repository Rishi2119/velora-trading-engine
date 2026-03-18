import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../services/ai_agent_service.dart';
import '../theme.dart';

class AiAgentScreen extends StatefulWidget {
  const AiAgentScreen({super.key});

  @override
  State<AiAgentScreen> createState() => _AiAgentScreenState();
}

class _AiAgentScreenState extends State<AiAgentScreen> {
  Map<String, dynamic>? _agent;
  final List<Map<String, dynamic>> _history = [];
  bool _loading = true;
  Timer? _timer;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _fetchData();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchData() async {
    try {
      final api = Provider.of<AiAgentService>(context, listen: false);
      final agentData = await api.getAgentStatus();
      
      if (mounted && agentData['latest_thought'] != null) {
        setState(() {
          _agent = agentData;
          _loading = false;
          
          // Add to history if unique
          if (_history.isEmpty || _history.last['thought'] != agentData['latest_thought']) {
            _history.add({
              'time': TimeOfDay.now().format(context),
              'thought': agentData['latest_thought'],
              'decision': agentData['latest_decision'] ?? 'HOLD'
            });
            // Keep history length manageable
            if (_history.length > 50) _history.removeAt(0);

            // Auto-scroll to text
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (_scrollController.hasClients) {
                _scrollController.animateTo(
                  _scrollController.position.maxScrollExtent,
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOut,
                );
              }
            });
          }
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggleAgent() async {
    setState(() => _loading = true);
    try {
      final api = Provider.of<AiAgentService>(context, listen: false);
      if (_agent?['is_running'] == true) {
        await api.stopAgent();
      } else {
        await api.startAgent();
      }
      await _fetchData();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading && _agent == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final isRunning = _agent?['is_running'] == true;
    final confidence = ((_agent?['confidence'] ?? 0) * 100).toInt();

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Agent Control'),
        actions: [
          IconButton(
            icon: Icon(isRunning ? LucideIcons.square : LucideIcons.play),
            color: isRunning ? VeloraTheme.error : VeloraTheme.success,
            onPressed: () => showDialog(
              context: context,
              builder: (ctx) => AlertDialog(
                backgroundColor: VeloraTheme.bgSurface,
                title: Text(isRunning ? 'Stop AI Agent?' : 'Start AI Agent?'),
                content: Text(isRunning 
                  ? 'The NIM reasoning engine will pause trading signals immediately.'
                  : 'The Kimi K2.5 agent will spin up and take over autonomous trading decisions.'
                ),
                actions: [
                   TextButton(child: const Text('Cancel'), onPressed: () => Navigator.pop(ctx)),
                   ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: isRunning ? VeloraTheme.error : VeloraTheme.success),
                      onPressed: () { 
                        Navigator.pop(ctx); 
                        _toggleAgent(); 
                      }, 
                      child: Text(isRunning ? 'STOP' : 'START')
                    )
                ],
              )
            )
          )
        ],
      ),
      body: Column(
        children: [
          // Header Stats
          Container(
            padding: const EdgeInsets.all(16),
            color: VeloraTheme.bgSurface,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                Column(
                  children: [
                    Text('Status', style: TextStyle(color: VeloraTheme.textMuted, fontSize: 12)),
                    const SizedBox(height: 4),
                    Text(isRunning ? 'RUNNING' : 'OFFLINE', style: TextStyle(color: isRunning ? VeloraTheme.success : VeloraTheme.warning, fontWeight: FontWeight.bold)),
                  ],
                ),
                Column(
                  children: [
                    Text('Confidence', style: TextStyle(color: VeloraTheme.textMuted, fontSize: 12)),
                    const SizedBox(height: 4),
                    Text('$confidence%', style: const TextStyle(color: VeloraTheme.primary, fontWeight: FontWeight.bold)),
                  ],
                ),
              ],
            ),
          ),
          
          // Log output
          Expanded(
            child: Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black, // true terminal aesthetic
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white10),
              ),
              child: _history.isEmpty 
                  ? const Center(child: Text('Waiting for agent telemetry...', style: TextStyle(color: Colors.white30, fontFamily: 'monospace')))
                  : ListView.builder(
                      controller: _scrollController,
                      itemCount: _history.length,
                      itemBuilder: (context, index) {
                        final log = _history[index];
                        final Color decisionColor = log['decision'].contains('BUY') || log['decision'].contains('TRADE')
                            ? VeloraTheme.success 
                            : log['decision'].contains('SELL') ? VeloraTheme.error
                            : VeloraTheme.accent;

                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text('[${log['time']}] ', style: const TextStyle(color: Colors.white30, fontSize: 11, fontFamily: 'monospace')),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                    decoration: BoxDecoration(color: decisionColor.withOpacity(0.2), borderRadius: BorderRadius.circular(2)),
                                    child: Text(log['decision'], style: TextStyle(color: decisionColor, fontSize: 10, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
                                  )
                                ],
                              ),
                              const SizedBox(height: 4),
                              Text(log['thought'], style: const TextStyle(color: Colors.white70, fontSize: 13, fontFamily: 'monospace', height: 1.4)),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          )
        ],
      ),
    );
  }
}
