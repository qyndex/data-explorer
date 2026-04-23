-- Initial schema for Data Explorer
-- Tables: profiles, datasets, saved_queries, query_results

-- ==========================================================================
-- profiles — auto-created on signup via trigger
-- ==========================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT,
    full_name   TEXT,
    plan        TEXT NOT NULL DEFAULT 'free',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Auto-create profile on new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ==========================================================================
-- datasets — uploaded data files with schema metadata
-- ==========================================================================
CREATE TABLE IF NOT EXISTS public.datasets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    schema      JSONB NOT NULL DEFAULT '{}',
    row_count   INTEGER NOT NULL DEFAULT 0,
    source      TEXT NOT NULL DEFAULT 'upload',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_datasets_owner ON public.datasets(owner_id);
CREATE INDEX IF NOT EXISTS idx_datasets_name ON public.datasets(owner_id, name);

ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own datasets"
    ON public.datasets FOR SELECT
    USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own datasets"
    ON public.datasets FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own datasets"
    ON public.datasets FOR UPDATE
    USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own datasets"
    ON public.datasets FOR DELETE
    USING (auth.uid() = owner_id);


-- ==========================================================================
-- saved_queries — user-saved SQL/analysis queries
-- ==========================================================================
CREATE TABLE IF NOT EXISTS public.saved_queries (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    dataset_id  UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    sql_query   TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_queries_owner ON public.saved_queries(owner_id);
CREATE INDEX IF NOT EXISTS idx_saved_queries_dataset ON public.saved_queries(dataset_id);

ALTER TABLE public.saved_queries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own queries"
    ON public.saved_queries FOR SELECT
    USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own queries"
    ON public.saved_queries FOR INSERT
    WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own queries"
    ON public.saved_queries FOR UPDATE
    USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own queries"
    ON public.saved_queries FOR DELETE
    USING (auth.uid() = owner_id);


-- ==========================================================================
-- query_results — cached execution results
-- ==========================================================================
CREATE TABLE IF NOT EXISTS public.query_results (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id          UUID NOT NULL REFERENCES public.saved_queries(id) ON DELETE CASCADE,
    result_data       JSONB NOT NULL DEFAULT '[]',
    row_count         INTEGER NOT NULL DEFAULT 0,
    execution_time_ms INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_query_results_query ON public.query_results(query_id);

ALTER TABLE public.query_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own query results"
    ON public.query_results FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.saved_queries sq
            WHERE sq.id = query_results.query_id
              AND sq.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own query results"
    ON public.query_results FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.saved_queries sq
            WHERE sq.id = query_results.query_id
              AND sq.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own query results"
    ON public.query_results FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.saved_queries sq
            WHERE sq.id = query_results.query_id
              AND sq.owner_id = auth.uid()
        )
    );


-- ==========================================================================
-- updated_at trigger for datasets
-- ==========================================================================
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS datasets_updated_at ON public.datasets;
CREATE TRIGGER datasets_updated_at
    BEFORE UPDATE ON public.datasets
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
