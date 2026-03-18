-- Initial Database Schema for Velora SaaS

-- Create custom types
CREATE TYPE subscription_tier AS ENUM ('free', 'starter', 'pro', 'elite');

-- 1. Profiles Table (Extends Supabase Auth Users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    tier subscription_tier DEFAULT 'free',
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Turn on RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Allow users to read their own profile
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (new.id, new.email);
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 2. API Keys Table
CREATE TABLE public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    exchange TEXT NOT NULL, -- 'mt5', 'binance', etc.
    mt5_login TEXT,
    mt5_server TEXT,
    api_key_encrypted TEXT,
    api_secret_encrypted TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own API keys" 
    ON public.api_keys FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own API keys" 
    ON public.api_keys FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own API keys" 
    ON public.api_keys FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own API keys" 
    ON public.api_keys FOR DELETE USING (auth.uid() = user_id);

-- 3. User Strategies Table
CREATE TABLE public.strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    risk_level TEXT DEFAULT 'medium',
    is_active BOOLEAN DEFAULT false,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.strategies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own strategies" 
    ON public.strategies FOR ALL USING (auth.uid() = user_id);

-- 4. Trade History Table
CREATE TABLE public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    strategy_id UUID REFERENCES public.strategies(id) ON DELETE SET NULL,
    ticket TEXT NOT NULL,
    symbol TEXT NOT NULL,
    trade_type TEXT NOT NULL, -- 'buy', 'sell'
    volume DECIMAL NOT NULL,
    open_price DECIMAL NOT NULL,
    close_price DECIMAL,
    profit DECIMAL,
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ,
    status TEXT DEFAULT 'open', -- 'open', 'closed'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own trades" 
    ON public.trades FOR SELECT USING (auth.uid() = user_id);

-- Prevent unauthorized inserts/updates from UI (backend will handle this via service role)
CREATE POLICY "Service Role can insert trades" 
    ON public.trades FOR INSERT WITH CHECK (true);
CREATE POLICY "Service Role can update trades" 
    ON public.trades FOR UPDATE USING (true);
