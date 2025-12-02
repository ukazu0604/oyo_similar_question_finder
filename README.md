# 応用情報 類似問題検索プロジェクト (oyo_similar_question_finder)

このプロジェクトは、応用情報技術者試験の過去問データを収集し、テキストのベクトル化技術を用いて類似した問題を見つけ出すことを目的としています。

## データ同期システム

このアプリケーションには、Google Apps Script (GAS) を利用して、学習データ（問題のチェック状態、リアクション、お気に入りなど）をクラウドに保存・同期する機能が含まれています。これにより、異なるデバイス間でも同じ学習環境を共有することができます。

### 主な機能

-   **ユーザー認証**: ユーザーIDとパスワードによる簡単な認証システム。
-   **データ同期**: 学習データを手動または自動でクラウドと同期。
-   **マルチデバイス対応**: 一度設定すれば、どのデバイスからでも同じデータにアクセス可能。

### 設定方法

1.  **バックエンドの準備**: `GAS_SETUP.md` の手順に従って、ご自身のGoogleアカウントにバックエンドとなるGoogle Apps Scriptのウェブアプリケーションをデプロイしてください。
2.  **アプリへの設定**:
    -   アプリ画面右上の「👤（人型）」アイコンからユーザー登録とログインを行います。
    -   アプリ画面右上の「⚙️（歯車）」アイコンをクリックして同期設定モーダルを開きます。
    -   デプロイ時に取得したGASの**ウェブアプリURL**を設定欄に入力し、保存します。

以上で設定は完了です。設定後は、手動でのアップロード/ダウンロードや、必要に応じた自動同期が行われます。

## テスト環境の設定

このプロジェクトでは、テスト実行時にGoogle Apps Script (GAS) のURLが必要となります。
セキュリティと管理の容易さを考慮し、GAS URLをリポジトリにコミットせずに設定できる仕組みを導入しました。

### 設定手順

新しい開発者がプロジェクトをクローンした場合、以下の手順でテスト環境を設定してください。

1.  **テスト設定ファイルの作成:**
    テストを実行する前に、まずプロジェクトのルートディレクトリで以下のコマンドを実行します。

    ```bash
    py create_test_config.py
    ```

    このコマンドは、テスト用の設定ファイルである `.test_settings.local` を作成し、同時にそのファイルがGitリポジトリにコミットされないよう、自動的に `.gitignore` へ追記します。

2.  **テスト用GAS URLの設定:**
    作成された `.test_settings.local` ファイルを開き、`TEST_GAS_URL`変数に**テスト用のGAS Web Apps URL**を設定してください。

    ```python
    # .test_settings.local
    # このファイルは.gitignoreで無視されます。
    # テスト用のGAS URLをここに設定してください。
    # 例: TEST_GAS_URL = "https://script.google.com/macros/s/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/exec"
    TEST_GAS_URL = "https://script.google.com/macros/s/YOUR_TEST_GAS_URL_HERE/exec"
    ```
    `YOUR_TEST_GAS_URL_HERE`の部分を、ご自身でデプロイしたテスト用のGAS Web Apps URLに置き換えてください。**本番環境のGAS URLを使用しないことを強く推奨します。**

3.  **テストの実行:**
    設定が完了したら、通常通りテストを実行できます。

    ```bash
    py run_all_tests.py
    ```

    テストフレームワークは、`.test_settings.local`から`TEST_GAS_URL`を自動的に読み込み、テスト時にブラウザの`localStorage`に設定して使用します。

## 開発ワークフロー

### GASコードの管理とデプロイ

GASコードは`gas/`ディレクトリで管理されており、claspを使用してデプロイできます。

#### 初回セットアップ

1. **claspのインストール**:
   ```bash
   npm install -g @google/clasp
   ```

2. **Googleアカウントでログイン**:
   ```bash
   clasp login
   ```

3. **Apps Script APIを有効化**:
   - https://script.google.com/home/usersettings にアクセス
   - 「Google Apps Script API」をオンにする
   - 数分待つ（APIの有効化が反映されるまで）

4. **スクリプトIDの設定**:
   - GASエディタで「プロジェクトの設定」→「スクリプトID」をコピー
   - `gas/.clasp.json`を開き、`<YOUR_SCRIPT_ID>`を実際のスクリプトIDに置き換え

#### デプロイ

```bash
py deploy_gas.py
```

または、コマンドラインから：

```bash
cd gas
clasp push
```

#### GASから最新コードを取得

```bash
py pull_gas.py
```

詳細は`GAS_SETUP.md`を参照してください。

### テストの実行

```bash
py run_all_tests.py
```

すべてのテストを実行します。
