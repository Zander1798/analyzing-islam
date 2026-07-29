-- ============================================================
-- Narrow, direct-Postgres credential for retrieval evaluation.
--
-- Safe to re-run. This file creates no data and contains NO PASSWORD.
-- Set the live password out of band from a protected operator secret.
--
-- The role may:
--   * connect to postgres and use public
--   * select kb_docs and kb_chunks through explicit read-only RLS policies
--   * execute match_corpus(...) and kb_find_ref(text)
--
-- It may not inherit another role, create permanent or temporary objects,
-- use auth/storage, write any table, or execute another application function.
-- ============================================================

begin;

do $$
begin
  if current_database() <> 'postgres' then
    raise exception 'kb_reader must be installed in the postgres database, not %',
      current_database();
  end if;

  if not exists (select 1 from pg_roles where rolname = 'kb_reader') then
    create role kb_reader
      login noinherit nosuperuser nocreatedb nocreaterole
      noreplication nobypassrls;
  end if;
end
$$;

-- Converge an existing role to the same non-administrative attributes without
-- replacing its out-of-band password.
alter role kb_reader
  login noinherit nosuperuser nocreatedb nocreaterole
  noreplication nobypassrls;

-- NOINHERIT does not prevent SET ROLE into every membership on all supported
-- PostgreSQL versions, so remove any membership rather than trusting the flag.
do $$
declare
  parent_role record;
begin
  for parent_role in
    select parent.rolname
    from pg_auth_members member_of
    join pg_roles parent on parent.oid = member_of.roleid
    join pg_roles child on child.oid = member_of.member
    where child.rolname = 'kb_reader'
  loop
    execute format('revoke %I from kb_reader', parent_role.rolname);
  end loop;
end
$$;

-- TEMPORARY is granted to PUBLIC by PostgreSQL by default. A per-role REVOKE
-- cannot override PUBLIC, and CREATE TEMP TABLE would violate the no-object-
-- creation boundary. Preserve the current effective TEMP privilege explicitly
-- for every existing role except kb_reader, then remove the PUBLIC grant.
do $$
declare
  existing_role record;
begin
  for existing_role in
    select rolname
    from pg_roles
    where rolname <> 'kb_reader'
      and has_database_privilege(rolname, current_database(), 'TEMPORARY')
  loop
    execute format(
      'grant temporary on database %I to %I',
      current_database(),
      existing_role.rolname
    );
  end loop;

  execute format(
    'revoke temporary on database %I from public',
    current_database()
  );
end
$$;

revoke all on database postgres from kb_reader;
grant connect on database postgres to kb_reader;

revoke all on schema public from kb_reader;
grant usage on schema public to kb_reader;

revoke all on schema auth, storage from kb_reader;
revoke all on all tables in schema auth, storage from kb_reader;
revoke all on all sequences in schema auth, storage from kb_reader;
revoke all on all functions in schema auth, storage from kb_reader;

revoke all on all tables in schema public from kb_reader;
revoke all on all sequences in schema public from kb_reader;
revoke all on all functions in schema public from kb_reader;

grant select on table public.kb_docs, public.kb_chunks to kb_reader;

-- RLS is enabled on both KB tables with no general read policy. Table SELECT
-- alone would therefore return no rows. Recreate two role-specific SELECT-only
-- policies inside this transaction so the migration converges atomically.
drop policy if exists kb_docs_select_kb_reader on public.kb_docs;
create policy kb_docs_select_kb_reader
  on public.kb_docs for select to kb_reader using (true);

drop policy if exists kb_chunks_select_kb_reader on public.kb_chunks;
create policy kb_chunks_select_kb_reader
  on public.kb_chunks for select to kb_reader using (true);

-- PostgreSQL grants EXECUTE on new functions to PUBLIC unless the owner's
-- default privileges say otherwise. The live database still had legacy PUBLIC
-- EXECUTE on application functions, including unrelated SECURITY DEFINER
-- functions. A direct REVOKE from kb_reader cannot override that inheritance.
--
-- Preserve the three existing Supabase API roles' access, then remove PUBLIC
-- from every non-extension function in public. The catalog-derived signature
-- is used only by this superuser-run migration; neither retrieval function
-- contains dynamic SQL.
do $$
declare
  app_function record;
begin
  for app_function in
    select p.oid::regprocedure::text as signature
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and not exists (
        select 1
        from pg_depend dependency
        where dependency.classid = 'pg_proc'::regclass
          and dependency.objid = p.oid
          and dependency.deptype = 'e'
      )
      and exists (
        select 1
        from aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) acl
        where acl.grantee = 0
          and acl.privilege_type = 'EXECUTE'
      )
  loop
    execute format(
      'grant execute on function %s to anon, authenticated, service_role',
      app_function.signature
    );
    execute format(
      'revoke execute on function %s from public',
      app_function.signature
    );
  end loop;
end
$$;

-- Keep functions created later by the two schema-owning roles closed to
-- PUBLIC. Supabase's explicit anon/authenticated/service_role defaults remain.
alter default privileges for role supabase_admin in schema public
  revoke execute on functions from public;
alter default privileges for role postgres in schema public
  revoke execute on functions from public;

grant execute on function
  public.match_corpus(text, vector, integer, jsonb, text[], text[])
  to kb_reader;
grant execute on function public.kb_find_ref(text) to kb_reader;

commit;
