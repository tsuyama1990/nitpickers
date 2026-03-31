nitpickers ワークフロー 「5フェーズ構成」リファクタリング詳細要件定義書

1. 概要

本要件定義書は、LangGraphを用いた現在のAIエージェントワークフローを、安定性と役割分担を強化した「5フェーズ構成」へリファクタリングするための具体的な実装仕様を定義する。

1.1 目標とする5フェーズ

Phase 0: Init Phase (CLIによる静的セットアップ)

Phase 1: Architect Graph (要件分割と計画レビュー)

Phase 2: Coder Graph (並列実装、直列Audit、リファクタリングループ)

Phase 3: Integration Phase (3-Way Diff統合、Global Sandbox)

Phase 4: UAT & QA Graph (統合環境での動的E2Eテスト)

2. 状態管理（State）の改修要件

LangGraph間で持ち回る状態（TypedDict等）に、直列制御およびリファクタリング制御のための変数を追加する。

対象ファイル: src/state.py

CycleState クラスに以下のフィールドを追加・初期化する。

is_refactoring: bool (初期値: False)

用途: Sandboxテストを通過した際、次に「Auditorへ行くか（実装段階）」「FinalCriticへ行くか（リファクタ段階）」を判定するためのフラグ。

current_auditor_index: int (初期値: 1)

用途: 直列Auditにおいて、現在何番目のAuditor（1〜3）がレビュー中かを管理する。

audit_attempt_count: int (初期値: 0)

用途: 同一Auditorからの指摘（Reject）による修正往復回数をカウントする（無限ループ防止、最大2回を想定）。

3. グラフ定義（Graph）の改修要件

LangGraphのエッジ（遷移）を5フェーズ仕様に再配線する。

対象ファイル: src/graph.py

3.1 _create_coder_graph (Phase 2) の再配線

既存の committee_manager や uat_evaluate を削除し、直列ループを構築する。

【追加・使用するノード】

coder_session

self_critic (新規、または既存流用。初回実装のみ通す想定)

sandbox_evaluate (Localでの静的テスト・単体テスト)

auditor_node (OpenRouter。直列で1〜3を順に実行)

refactor_node (新規。固定プロンプトによるリファクタ指示)

final_critic_node (新規。自己最終レビュー)

【エッジ定義 (Edges & Conditional Edges)】

START: START → coder_session

Coderからの分岐: coder_session → self_critic (初回のみ) → sandbox_evaluate。または2回目以降は直接 sandbox_evaluate。

Sandboxからの分岐: sandbox_evaluate → route_sandbox_evaluate (Conditional)

"failed" → coder_session (差し戻し)

"auditor" (成功 & is_refactoring == False) → auditor_node

"final_critic" (成功 & is_refactoring == True) → final_critic_node

Auditorからの分岐: auditor_node → route_auditor (Conditional)

"reject" → coder_session (修正指示)

"next_auditor" → auditor_node (ループ、次のAuditorへ)

"pass_all" → refactor_node

Refactorから: refactor_node → sandbox_evaluate

※ refactor_node の中で state["is_refactoring"] = True に更新すること。

Final Criticからの分岐: final_critic_node → route_final_critic (Conditional)

"reject" → coder_session

"approve" → END

3.2 _create_integration_graph (Phase 3) の新設

すべての並列サイクルが完了した後に実行される、統合用の新しいグラフ。

【ノード構成】

git_merge_node: int ブランチ等への標準的なGit Mergeを試行。

master_integrator_node: JULESによる3-Way Diff競合解消。

global_sandbox_node: 統合後の全体静的解析（Linter/Pytest）。

【エッジ定義】

START → git_merge_node

git_merge_node → route_merge (Conditional)

"conflict" → master_integrator_node

"success" → global_sandbox_node

master_integrator_node → git_merge_node (再試行)

global_sandbox_node → route_global_sandbox (Conditional)

"failed" → master_integrator_node (統合によるエンバグ修正)

"pass" → END

3.3 _create_qa_graph (Phase 4) の調整

Phase 3が成功した後に独立して呼ばれる。現状の実装（UAT実行 → エラーならQA Auditor → JULESで修正）を維持。

4. ルーティング関数（Routers）の実装要件

グラフの条件分岐エッジで使用される関数を定義する。

対象ファイル: src/nodes/routers.py

route_sandbox_evaluate(state: CycleState) -> str:

state.get("sandbox_status") == "failed" なら "failed" を返す。

成功時、state.get("is_refactoring") == True なら "final_critic" を返す。

それ以外は "auditor" を返す。

route_auditor(state: CycleState) -> str: (新規作成)

現在のAuditorのレビュー結果が「Reject（指摘あり）」なら、audit_attempt_count を+1し "reject" を返す（試行上限を超えた場合のフォールバック処理も考慮）。

結果が「Approve（承認）」なら、current_auditor_index を+1する。

current_auditor_index > 3 (最大数超過) になれば、全承認とみなし "pass_all" を返す。

それ以外は "next_auditor" を返す。

route_final_critic(state: CycleState) -> str: (新規作成)

自己評価がNGなら "reject"、OKなら "approve" を返す。

5. ユースケース（Services / Usecases）の改修要件

5.1 3-Way Diff 統合ロジックの実装

コンフリクトマーカー（<<<<<<<）を含むファイル全体を渡すのではなく、Baseと両者のDiffを分離してLLMに渡す。

対象ファイル: src/services/conflict_manager.py

scan_conflicts メソッドは維持。

build_conflict_package メソッドの改修:
Gitコマンドを使用して、コンフリクトファイルの3つの状態を取得し、プロンプトを構築する。

Baseコード取得コマンド例: git show :1:{file_path}

Local (Cycle A) 取得: git show :2:{file_path}

Remote (Cycle B) 取得: git show :3:{file_path}

構築するプロンプトの構成案:

あなた（Master Integrator）の任務は、Gitのコンフリクトを安全に解消することです。
以下の共通祖先（Base）のコードに対して、Branch AとBranch Bの変更意図を両立させた、最終的な完全なコードを生成してください。

### Base (元のコード)
```python
{base_code}
```

### Branch A の変更 (Local)
```python
{local_code}
```

### Branch B の変更 (Remote)
```python
{remote_code}
```



5.2 UATフェーズの分離

対象ファイル: src/services/uat_usecase.py

Phase 2 (Coder Phase) から呼ばれていたトリガーを排除。

Phase 3の統合が完了した後の Phase 4 (QA Graph) 専用のユースケース として振る舞うように、入力状態（State）の受け取り方を調整する。

6. オーケストレーション（CLI / WorkflowService）の改修要件

システム全体の実行順序を制御する。

対象ファイル: src/cli.py および src/services/workflow.py

run_cycle コマンド（または全体実行コマンド）のフローを以下のように変更する。

並列実行: 各Cycleの build_coder_graph を並列（非同期）で実行し、すべてが END に到達するのを待機する。

統合フェーズ呼出: すべてのPRが揃ったら、新設した build_integration_graph を単一プロセスで実行する。

UATフェーズ呼出: 統合グラフが成功裡に終了した場合のみ、build_qa_graph を実行し、最終的なE2Eテストを行う。


最終的なフローは下記を想定している

flowchart TD
    %% フェーズ0: 初期セットアップ (CLI)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
        GenTemplates[".env.sample / .gitignore, strict ruff, mypy settings (Local)"]
        UpdateDocker["add .env path on docker-compose.yml (User)"]
        PrepareSpec["define ALL_SPEC.md (User)"]

        InitCmd --> GenTemplates --> UpdateDocker --> PrepareSpec
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])

        subgraph Architect_Phase ["JULES: Architect Phase"]
            ArchSession["architect_session\n(要件をN個のサイクルに分割)"]
            ArchCritic{"self-critic review\n(固定プロンプトで計画レビュー)"}
        end

        OutputSpecs[/"各サイクルの SPEC.md\n全体 UAT_SCENARIO.md"/]

        PrepareSpec --> InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
        ArchCritic -- "Approve" --> OutputSpecs
    end

    %% フェーズ2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (並列実行: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(実装 & PR作成)"]
        SelfCritic["JULES: SelfCriticReview\n(初期実装のレビュー)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}

        AuditorNode{"OpenRouter: auditor_node\n(直列: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(固定プロンプトでリファクタ)"]
        FinalCritic{"JULES: Final Self-critic\n(自己最終レビュー)"}

        OutputSpecs -->|サイクルNとして開始| CoderSession

        CoderSession -- "1回目" --> SelfCritic --> SandboxEval
        CoderSession -- "2回目以降" --> SandboxEval

        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (実装中)" --> AuditorNode
        SandboxEval -- "Pass (リファクタ済)" --> FinalCritic

        AuditorNode -- "Reject (各最大2回)" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode

        RefactorNode --> SandboxEval

        FinalCritic -- "Reject" --> CoderSession
    end

    %% フェーズ3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge\n(intブランチへ統合)"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diffで競合解消)"]
        GlobalSandbox{"LOCAL: global_sandbox\n(統合後の全体Linter/Pytest)"}
    end

    %% フェーズ4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate\n(Playwright E2Eテスト等)"}
        QaAuditor["OpenRouter: qa_auditor\n(エラーログ/画像解析)"]
        QaSession["JULES: qa_session\n(統合環境での修正)"]
        EndNode(((END: 開発完了)))
    end

    %% ==========================================
    %% フェーズ間の接続（エラー防止のため外側に記述）
    %% ==========================================

    FinalCritic -- "Approve\n(全PR出揃う)" --> MergeTry

    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry

    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Fail (統合による破壊)" --> MasterIntegrator

    GlobalSandbox -- "Pass" --> UatEval

    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval

    UatEval -- "Pass" --> EndNode

    %% ==========================================
    %% スタイリング
    %% ==========================================
    classDef graphNode fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef conditional fill:#fff3cd,stroke:#ffeeba,stroke-width:2px;
    classDef success fill:#d4edda,stroke:#c3e6cb,stroke-width:2px;
    classDef highlight fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;

    class ArchCritic,SandboxEval,AuditorNode,FinalCritic,MergeTry,GlobalSandbox,UatEval conditional;
    class EndNode success;
    class GlobalSandbox highlight;
