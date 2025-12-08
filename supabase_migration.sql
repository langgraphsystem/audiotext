-- Supabase Migration for Bot Memory System
-- Run this in Supabase SQL Editor (https://app.supabase.com/project/YOUR_PROJECT/sql)

-- 1. Enable pgvector extension for embeddings
create extension if not exists vector;

-- 2. Create the bot_memory table
create table if not exists bot_memory (
    id uuid default gen_random_uuid() primary key,
    user_id bigint not null,
    content_hash varchar(16) not null,
    content_type varchar(50) default 'tiktok',
    source_url text,
    content text not null,
    analysis text not null,
    summary text,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    created_at timestamp with time zone default now()
);

-- 3. Create indexes for better performance
create index if not exists idx_bot_memory_user_id on bot_memory(user_id);
create index if not exists idx_bot_memory_content_hash on bot_memory(content_hash);
create index if not exists idx_bot_memory_created_at on bot_memory(created_at);
create index if not exists idx_bot_memory_user_hash on bot_memory(user_id, content_hash);

-- 4. Create HNSW index for fast vector similarity search
create index if not exists idx_bot_memory_embedding on bot_memory
using hnsw (embedding vector_cosine_ops);

-- 5. Create function for semantic search
create or replace function match_memories(
    query_embedding vector(1536),
    match_user_id bigint,
    match_threshold float default 0.5,
    match_count int default 3
)
returns table (
    id uuid,
    user_id bigint,
    content text,
    analysis text,
    summary text,
    source_url text,
    created_at timestamp with time zone,
    similarity float
)
language sql stable
as $$
    select
        bot_memory.id,
        bot_memory.user_id,
        bot_memory.content,
        bot_memory.analysis,
        bot_memory.summary,
        bot_memory.source_url,
        bot_memory.created_at,
        1 - (bot_memory.embedding <=> query_embedding) as similarity
    from bot_memory
    where
        bot_memory.user_id = match_user_id
        and bot_memory.embedding is not null
        and 1 - (bot_memory.embedding <=> query_embedding) > match_threshold
    order by bot_memory.embedding <=> query_embedding
    limit match_count;
$$;

-- 6. Enable Row Level Security (RLS) - optional but recommended
alter table bot_memory enable row level security;

-- 7. Create policy to allow all operations (adjust as needed)
create policy "Allow all operations" on bot_memory
    for all
    using (true)
    with check (true);

-- 8. Grant permissions
grant all on bot_memory to anon, authenticated;
grant execute on function match_memories to anon, authenticated;
