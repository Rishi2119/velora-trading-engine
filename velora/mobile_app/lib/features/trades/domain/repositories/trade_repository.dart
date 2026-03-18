import 'package:velora_trade_terminal/features/trades/domain/entities/trade.dart';

abstract class TradeRepository {
  Future<List<Trade>> fetchRecentTrades();
  Future<void> createTrade(Trade trade);
}
