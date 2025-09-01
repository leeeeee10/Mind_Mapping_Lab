# prompts.py

# 第一次API：要求模型“生成思维图（JSON）”
GRAPH_GEN_SYSTEM = """你是就业领域的推理规划助手。\
请把你的推理过程表示成“思维图”，只输出JSON，不要输出其他解释。"""

GRAPH_GEN_USER_TEMPLATE = """\
请围绕下面的问题，构建一张就业规划的思维图：
问题：{question}

要求：
1) 严格输出 JSON，字段如下：
{{
  "nodes": [
    {{"id": "n1", "name": "数据分析师", "ntype": "岗位", "attrs": {{"level": "junior"}}}},
    {{"id": "n2", "name": "Python", "ntype": "技能", "attrs": {{"proficiency": "intermediate"}}}},
    {{"id": "n3", "name": "新能源行业", "ntype": "行业", "attrs": {{"subsector": "光伏"}}}},
    {{"id": "n4", "name": "在线课程", "ntype": "资源", "attrs": {{"provider": "Coursera"}}}},
    {{"id": "n5", "name": "城市：上海", "ntype": "约束", "attrs": {{"type": "location"}}}}
  ],
  "edges": [
    {{"id": "e1", "source": "n2", "relation": "需要", "target": "n1", "weight": 0.9,
      "conditions": ["岗位要求中必备"], "evidence": ["招聘JD常见要求"]}},
    {{"id": "e2", "source": "n4", "relation": "提升", "target": "n2", "weight": 0.7,
      "conditions": ["每周学习6小时"], "evidence": ["课程大纲"]}},
    {{"id": "e3", "source": "n3", "relation": "适配", "target": "n1", "weight": 0.6,
      "conditions": ["行业知识补齐"], "evidence": ["行业报告"]}}
  ]
}}

2) 约束：
- ntype 仅可从：["人物画像","技能","岗位","行业","约束","趋势","资源","行动","成果"] 中选取
- relation 仅可从：["需要","提升","导致","促进","抑制","迁移到","适配","依赖于","位于","推荐"] 中选取
- 节点数建议 8~14，关系 10~20；边必须引用已存在的节点ID；weight 在 0~1。
- 多给“行动/资源/技能/岗位/行业/约束”这些类型，尽量可执行。
- 严格只输出 JSON（不加反引号、不加解释）。
"""

# 第二次API：把图喂回去，要求“只基于图”回答
ANSWER_SYSTEM = """你是就业顾问。你将收到一张思维图（三元组列表），必须严格基于该图回答，\
不可编造图外关系。回答语言：中文，结构清晰，可执行步骤优先。"""

ANSWER_USER_TEMPLATE = """\
问题：{question}

思维图（紧凑三元组）：
{triples_text}

请输出 JSON，字段：
{{
  "final_answer": "给出面向该用户的具体建议，条目化；指出短板与补齐路径；给出3阶段行动计划；",
  "used_nodes": ["n1","n2","..."],
  "used_edges": ["e1","e3","..."],
  "risks": ["识别2-4个主要风险"],
  "missing_info": ["还缺的关键信息（如地区、期望薪资、时间约束等）"]
}}
严格只输出 JSON。
"""
