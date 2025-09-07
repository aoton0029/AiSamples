# コンテクスト設計テンプレート（Context Engineering）  
(マークダウン / プレースホルダは jinja2)

---

## メタ情報
- プロジェクト名: `{{ project_name }}`
- バージョン: `{{ version | default("1.0") }}`
- 作成日: `{{ created_at | default("{{ now() }}") }}`
- 作成者: `{{ author | default("unknown") }}`

---

## 1. 目的と適用範囲
- 目的: {{ objective }}
- 適用範囲:
  - システム / モジュール: {{ scope.module }}
  - 利用シナリオ: 
    {% for s in scope.scenarios %}
    - {{ s }}
    {% endfor %}

---

## 2. ステークホルダー
- プライマリ: {{ stakeholders.primary }}
- セカンダリ:
  {% for p in stakeholders.secondary %}
  - {{ p }}
  {% endfor %}

---

## 3. コンテクスト概要 (要約)
- コンテクストID: `{{ context.id }}`
- 短い説明: {{ context.summary }}
- 期待する振る舞い / 成果: {{ context.expected_outcome }}

---

## 4. データソース / トリガー
- 入力ソース:
  {% for src in data_sources %}
  - 名称: {{ src.name }}  
    種類: {{ src.type }}  
    更新頻度: {{ src.frequency }}  
    信頼度: {{ src.trust | default("unknown") }}  
  {% endfor %}
- トリガー条件:
  {% for t in triggers %}
  - {{ t }}
  {% endfor %}

---

## 5. エンティティ設計（スキーマ）
- エンティティ名: `{{ entity.name }}`
  - 説明: {{ entity.description }}
  - 主キー: `{{ entity.pk }}`
  - 属性:
    {% for attr in entity.attributes %}
    - {{ attr.name }} (型: {{ attr.type }}) - 必須: {{ "Yes" if attr.required else "No" }} - 説明: {{ attr.desc | default("-") }}
      {% if attr.constraints %}
      - 制約:
        {% for c in attr.constraints %}
        - {{ c }}
        {% endfor %}
      {% endif %}
    {% endfor %}
  - 関連:
    {% for rel in entity.relations %}
    - {{ rel.type }} -> {{ rel.target }} (注: {{ rel.note | default("-") }})
    {% endfor %}

---

## 6. 制約と検証ルール
- 全体制約:
  {% for c in constraints.global %}
  - {{ c }}
  {% endfor %}
- 属性レベル検証:
  {% for v in constraints.attribute_level %}
  - {{ v.attribute }}: {{ v.rule }} (エラーコード: {{ v.code | default("N/A") }})
  {% endfor %}

---

## 7. プロンプト設計（テンプレート）
- ベース説明（システム指示）:
  ```jinja2
  {{ system_instruction | default("You are a helpful assistant specialized in {{ domain }}.") }}
  ```
- 入力プロンプトテンプレート:
  ```jinja2
  背景: {{ background }}
  タスク: {{ task_description }}

  入力データ:
  {% for item in input_items %}
  - {{ item.name }}: {{ "{{ " }}{{ item.placeholder }}{{ " }}" }}
  {% endfor %}

  出力形式: {{ output_format }}

  制約:
  {% for c in prompt_constraints %}
  - {{ c }}
  {% endfor %}
  ```
- 出力スキーマ（検査用）:
  ```json
  {
    "type": "object",
    "properties": {
      {% for p in output_schema %}
      "{{ p.name }}": { "type": "{{ p.type }}" }{% if not loop.last %},{% endif %}
      {% endfor %}
    },
    "required": [{% for r in output_schema if r.required %}"{{ r.name }}"{% if not loop.last %}, {% endif %}{% endfor %}]
  }
  ```

---

## 8. 例（テンプレートに値を埋めたサンプル）
- 入力（Jinja2を適用した例）:
  ```jinja2
  {% set user = {"name":"佐藤","age":30} %}
  依頼: {{ user.name }}の年齢は{{ user.age }}歳です。適切な応答を作成してください。
  ```
- 期待出力例:
  - 「佐藤さんは30歳です。何か他にお手伝いできますか？」

---

## 9. フォールバック / エラーハンドリング
- デフォルト応答: {{ fallback.default_response | default("申し訳ありませんが回答できません。") }}
- 再試行ポリシー:
  - 再試行回数: {{ fallback.retries | default(1) }}
  - 再試行間隔(秒): {{ fallback.retry_delay | default(2) }}

---

## 10. 更新とライフサイクル管理
- 更新頻度: {{ lifecycle.update_frequency }}
- バージョン管理: {{ lifecycle.versioning | default("semantic") }}
- テストカバレッジ要件: {{ lifecycle.test_coverage | default(">=80%") }}

---

## 11. プライバシーとセキュリティ
- 保護すべき属性: 
  {% for a in privacy.sensitive_attributes %}
  - {{ a }}
  {% endfor %}
- マスキングルール:
  {% for m in privacy.masking %}
  - {{ m.attribute }} -> {{ m.rule }}
  {% endfor %}

---

## 12. モニタリングと評価指標 (KPI)
- レイテンシ目標: {{ monitoring.latency_target }}
- 正確度指標: {{ monitoring.accuracy_metric }}
- ログ項目:
  {% for l in monitoring.log_fields %}
  - {{ l }}
  {% endfor %}

---

## 13. テストケース（主要）
- ユニット/統合テストの例:
  {% for tc in tests %}
  - id: {{ tc.id }}  
    説明: {{ tc.desc }}  
    入力: {{ tc.input_summary }}  
    期待出力: {{ tc.expected }}
  {% endfor %}

---

## 14. 導入ガイド（簡易）
1. テンプレートに値を埋める（jinja2レンダリング）  
2. 入力バリデーションを実行  
3. モデル/サービスへ送信  
4. 出力スキーマ検証とマスキング  
5. ログとメトリクス収集

---

## 15. ノートと拡張ポイント
- 拡張: 新しいエンティティやデータソースを追加する際のチェックリストを準備すること。  
- 備考: 実運用ではテンプレートのバージョン管理と A/B テストを推奨。

---
