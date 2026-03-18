-- VELORA TRADE TERMINAL - Supabase Production Schema
-- Run in Supabase SQL Editor or via migration tooling.

create extension if not exists "pgcrypto";

create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.profiles (
  id uuid primary key references public.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  discipline_score int not null default 50 check (discipline_score between 0 and 100),
  daily_streak int not null default 0,
  quote_of_day text not null default 'Discipline beats emotion.',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  plan text not null check (plan in ('free', 'pro', 'premium')),
  status text not null default 'active' check (status in ('active', 'canceled', 'past_due')),
  started_at timestamptz not null default now(),
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.trades (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  symbol text not null,
  side text not null check (side in ('buy', 'sell')),
  quantity numeric(18,8) not null,
  entry_price numeric(18,8) not null,
  exit_price numeric(18,8),
  pnl numeric(18,8),
  opened_at timestamptz not null default now(),
  closed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.journals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  trade_id uuid references public.trades(id) on delete set null,
  emotion text not null,
  notes text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.achievements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  badge_code text not null,
  badge_name text not null,
  unlocked_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique(user_id, badge_code)
);

create index if not exists idx_subscriptions_user_id on public.subscriptions(user_id);
create index if not exists idx_trades_user_id_opened_at on public.trades(user_id, opened_at desc);
create index if not exists idx_journals_user_id_created_at on public.journals(user_id, created_at desc);
create index if not exists idx_achievements_user_id on public.achievements(user_id);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_users_touch_updated_at
before update on public.users
for each row execute function public.touch_updated_at();

create trigger trg_profiles_touch_updated_at
before update on public.profiles
for each row execute function public.touch_updated_at();

create trigger trg_subscriptions_touch_updated_at
before update on public.subscriptions
for each row execute function public.touch_updated_at();

create trigger trg_trades_touch_updated_at
before update on public.trades
for each row execute function public.touch_updated_at();

create trigger trg_journals_touch_updated_at
before update on public.journals
for each row execute function public.touch_updated_at();

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;

  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name', 'Trader'))
  on conflict (id) do nothing;

  insert into public.subscriptions (user_id, plan, status)
  values (new.id, 'free', 'active')
  on conflict do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_auth_user();

create or replace function public.upsert_subscription_plan(p_plan text)
returns public.subscriptions
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_result public.subscriptions;
begin
  v_user_id := auth.uid();
  if v_user_id is null then
    raise exception 'Not authenticated';
  end if;

  if p_plan not in ('free', 'pro', 'premium') then
    raise exception 'Invalid plan';
  end if;

  insert into public.subscriptions (user_id, plan, status, started_at)
  values (v_user_id, p_plan, 'active', now())
  on conflict (id) do nothing;

  update public.subscriptions
  set plan = p_plan,
      status = 'active',
      started_at = now(),
      expires_at = case when p_plan = 'free' then null else now() + interval '30 days' end
  where user_id = v_user_id
    and id = (
      select id from public.subscriptions
      where user_id = v_user_id
      order by created_at desc
      limit 1
    )
  returning * into v_result;

  return v_result;
end;
$$;

alter table public.users enable row level security;
alter table public.profiles enable row level security;
alter table public.subscriptions enable row level security;
alter table public.trades enable row level security;
alter table public.journals enable row level security;
alter table public.achievements enable row level security;

create policy "users_select_own" on public.users
for select using (auth.uid() = id);
create policy "users_insert_own" on public.users
for insert with check (auth.uid() = id);
create policy "users_update_own" on public.users
for update using (auth.uid() = id) with check (auth.uid() = id);
create policy "users_delete_own" on public.users
for delete using (auth.uid() = id);

create policy "profiles_select_own" on public.profiles
for select using (auth.uid() = id);
create policy "profiles_insert_own" on public.profiles
for insert with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles
for update using (auth.uid() = id) with check (auth.uid() = id);
create policy "profiles_delete_own" on public.profiles
for delete using (auth.uid() = id);

create policy "subscriptions_select_own" on public.subscriptions
for select using (auth.uid() = user_id);
create policy "subscriptions_insert_own" on public.subscriptions
for insert with check (auth.uid() = user_id);
create policy "subscriptions_update_own" on public.subscriptions
for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "subscriptions_delete_own" on public.subscriptions
for delete using (auth.uid() = user_id);

create policy "trades_select_own" on public.trades
for select using (auth.uid() = user_id);
create policy "trades_insert_own" on public.trades
for insert with check (auth.uid() = user_id);
create policy "trades_update_own" on public.trades
for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "trades_delete_own" on public.trades
for delete using (auth.uid() = user_id);

create policy "journals_select_own" on public.journals
for select using (auth.uid() = user_id);
create policy "journals_insert_own" on public.journals
for insert with check (auth.uid() = user_id);
create policy "journals_update_own" on public.journals
for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "journals_delete_own" on public.journals
for delete using (auth.uid() = user_id);

create policy "achievements_select_own" on public.achievements
for select using (auth.uid() = user_id);
create policy "achievements_insert_own" on public.achievements
for insert with check (auth.uid() = user_id);
create policy "achievements_update_own" on public.achievements
for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "achievements_delete_own" on public.achievements
for delete using (auth.uid() = user_id);

grant execute on function public.upsert_subscription_plan(text) to authenticated;
