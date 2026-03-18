class Trade {
  const Trade({
    required this.id,
    required this.symbol,
    required this.side,
    required this.quantity,
    required this.entryPrice,
    this.exitPrice,
    this.pnl,
  });

  final String id;
  final String symbol;
  final String side;
  final double quantity;
  final double entryPrice;
  final double? exitPrice;
  final double? pnl;
}
