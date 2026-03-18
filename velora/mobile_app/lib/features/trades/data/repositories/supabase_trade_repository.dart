import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:velora_trade_terminal/features/trades/domain/entities/trade.dart';
import 'package:velora_trade_terminal/features/trades/domain/repositories/trade_repository.dart';

class SupabaseTradeRepository implements TradeRepository {
  SupabaseTradeRepository(this._client);

  final SupabaseClient _client;

  @override
  Future<void> createTrade(Trade trade) async {
    await _client.from('trades').insert({
      'symbol': trade.symbol,
      'side': trade.side,
      'quantity': trade.quantity,
      'entry_price': trade.entryPrice,
      'exit_price': trade.exitPrice,
      'pnl': trade.pnl,
    });
  }

  @override
  Future<List<Trade>> fetchRecentTrades() async {
    final data = await _client
        .from('trades')
        .select('id, symbol, side, quantity, entry_price, exit_price, pnl')
        .order('opened_at', ascending: false)
        .limit(20);

    return (data as List<dynamic>)
        .map(
          (row) => Trade(
            id: row['id'] as String,
            symbol: row['symbol'] as String,
            side: row['side'] as String,
            quantity: (row['quantity'] as num).toDouble(),
            entryPrice: (row['entry_price'] as num).toDouble(),
            exitPrice: row['exit_price'] == null ? null : (row['exit_price'] as num).toDouble(),
            pnl: row['pnl'] == null ? null : (row['pnl'] as num).toDouble(),
          ),
        )
        .toList();
  }
}
