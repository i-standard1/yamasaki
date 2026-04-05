---
paths:
  - "supabase/**"
---

# Supabase Auth 実装ルール（Next.js + @supabase/ssr）

<!-- AI: このルールは supabase/ ディレクトリ操作時にロードされる。
src/, app/, lib/ でSupabase関連コードを書く場合も、このルールの内容を適用すること。
CLAUDE.md の auth が supabase-auth でないプロジェクトでは無視してよい -->

Supabase認証を実装する場合、以下を厳守すること。

1. **site_url はユーザーの実際のアクセスドメインに合わせる**
   - `localhost` でアクセスするなら `site_url = "http://localhost:3000"`
   - `127.0.0.1` でアクセスするなら `site_url = "http://127.0.0.1:3000"`
   - `localhost` と `127.0.0.1` はブラウザのcookieでは別ドメイン扱い。不一致するとPKCE認証が失敗する
2. **ログインは Server Action で実装する**（クライアントサイドの `signInWithOAuth` は使わない）
3. **コールバックは `/auth/callback` に配置する**（`/api/auth/callback` ではない）
4. **コールバックでは `createClient()`（server.ts）+ `redirect()`（next/navigation）を使う**
5. **ミドルウェア（またはproxy）で `/auth/callback` をスキップする**（PKCEクッキーの干渉を防ぐ）
   - Next.js 15以前: `middleware.ts` を使用
   - Next.js 16以降: `middleware.ts` は非推奨。`proxy.ts`（proxy pattern）を使用すること。関数名も `middleware` → `proxy` に変更が必要
6. **server.ts の `setAll` は try/catch で囲む**（Server Componentから呼ばれた場合のエラーを無視する）
7. **CI で `supabase status -o env` から環境変数を取得する際の変数名に注意**
   - URL は `API_URL`（`SUPABASE_URL` ではない）
   - 例: `NEXT_PUBLIC_SUPABASE_URL=$(supabase status -o env | grep API_URL | cut -d= -f2- | tr -d '"')`
   - `ANON_KEY`, `SERVICE_ROLE_KEY` はそのままマッチする
   - 出力値がダブルクォート付きのため `tr -d '"'` で除去必須
8. **認証ガードは proxy.ts（またはmiddleware.ts）に一元化する**
   - 未認証→`/login` リダイレクトは proxy.ts だけが行う
   - `layout.tsx` や `page.tsx` に `if (!user) redirect("/login")` を書かない
   - `layout.tsx` のリダイレクトはビジネスロジック（例: プロジェクト未参加→新規作成）のみ許可
   - 認証ガードが複数レイヤーに分散すると、互いに矛盾してリダイレクトループの原因になる
9. **Route Group 使用時、`app/page.tsx` をルート直下に作成しない**
   - `app/(dashboard)/page.tsx` は URL `/` にマッチする。`app/page.tsx` が存在すると優先されて Route Group の page.tsx が到達不能になる
   - 認証後のデフォルト遷移先は `/` とする（Route Group 名をURLに含めない。例: `(dashboard)` を使っていても `/dashboard` ではなく `/`）

# Supabase RLS（Row Level Security）実装の注意点

RLSポリシーを実装する場合、PostgreSQL固有の以下2つの落とし穴に注意すること。

1. **メンバーシップテーブル（`_members`系）の自己参照は無限再帰になる**
   - ポリシー内で自テーブルをSELECTすると、そのSELECTにも同じポリシーが適用され無限ループになる
   - 回避策: `SECURITY DEFINER` 関数（関数オーナー権限で実行されRLSをバイパスする）にメンバーシップ判定を切り出し、ポリシーから呼ぶ
   ```sql
   -- NG: ポリシーが自テーブルを参照 → 無限再帰
   USING (EXISTS (SELECT 1 FROM members WHERE org_id = org_id AND user_id = auth.uid()))

   -- OK: SECURITY DEFINER 関数経由で回避
   USING (public.is_org_member(organization_id))
   ```
2. **親テーブルの `INSERT..RETURNING` が SELECT ポリシーで失敗する**
   - Supabaseクライアントの `.insert().select()` は内部的に `INSERT ... RETURNING` を使い、PostgreSQLはRETURNINGの結果にもSELECTポリシーを適用する
   - 例: `organizations` にINSERT直後、まだ `organization_members` にレコードがないため「メンバーのみ閲覧可」のSELECTポリシーが通らずINSERT全体が失敗する
   - 回避策（いずれか）:
     - **トリガーで即時メンバー追加**: INSERTトリガーで作成者を自動的にメンバーテーブルに追加し、RETURNING時点でSELECTポリシーが通るようにする
     - **SELECTポリシーに作成者チェックを追加**: 親テーブルに `created_by` カラムを持たせ、`OR created_by = auth.uid()` をSELECTポリシーに追加する
     - **上位権限のフォールバック**: 親テーブルのSELECTポリシーに `OR is_org_owner_or_admin(organization_id)` など、既に確立済みの権限チェックを追加する
3. **ユーザー参照の FK は `public.users(id)` にする（`auth.users(id)` は不可）**
   - `public.users` プロフィールテーブルがある場合、他テーブルのユーザー FK は必ず `REFERENCES public.users(id)` にすること
   - PostgREST は公開スキーマ（`public`）内の FK しか辿れない。`auth.users(id)` への FK だと `.select("assignee:users(display_name)")` のような embedded resource クエリが「relationship not found」で失敗する
   - `public.users` の RLS は認証済みユーザー全員に SELECT を許可する（`display_name` / `avatar_url` はメンバー一覧表示に必要）
   ```sql
   -- NG: PostgREST が auth スキーマの FK を辿れない
   assignee_id uuid REFERENCES auth.users(id)

   -- OK: public スキーマ内で FK が完結する
   assignee_id uuid REFERENCES public.users(id)
   ```
