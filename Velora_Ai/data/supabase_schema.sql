-- Run this in your Supabase SQL editor before first launch

create table if not exists velora_trades (
  id bigserial primary key,
  ticket bigint,
  symbol text,
  direction text,
  lots float,
  entry float,
  sl float,
  tp float,
  pnl float,
  strategy_id text,
  strategy_name text,
  confluence_score int,
  status text default 'open',
  close_reason text,
  created_at timestamptz default now(),
  closed_at timestamptz
);

create table if not exists velora_signals_rejected (
  id bigserial primary key,
  symbol text,
  direction text,
  reason text,
  confluence_score int,
  created_at timestamptz default now()
);

create table if not exists velora_events (
  id bigserial primary key,
  type text,
  action text,
  payload text,
  created_at timestamptz default now()
);

create table if not exists velora_errors (
  id bigserial primary key,
  symbol text,
  direction text,
  error text,
  context text,
  created_at timestamptz default now()
);

-- Enable Realtime for dashboard
alter publication supabase_realtime add table velora_trades;
alter publication supabase_realtime add table velora_events;
