# demo_pipeline.py
import requests
from thought_graph import ThoughtGraph

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "xxxxxxxxxxxxxx"  # ⚠️ 建议用环境变量

class LLMWrapper:
    """封装 SiliconFlow API 调用"""
    def __init__(self, api_key: str, url: str = API_URL, model: str = "Qwen/QwQ-32B"):
        self.api_key = api_key
        self.url = url
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        resp = requests.post(self.url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

class Pipeline:
    def __init__(self, graph: ThoughtGraph, llm: LLMWrapper):
        self.graph = graph
        self.llm = llm

    def check_consistency(self, answer: str, edges):
        """
        简单一致性校验：
        - 检查回答中是否出现了相关节点
        - 检查是否提到关系（关键词匹配）
        """
        missing = []
        for e in edges:
            src, rel, tgt = e.source.name, e.relation, e.target.name
            if src.lower() not in answer.lower() or tgt.lower() not in answer.lower():
                missing.append(f"{src} -[{rel}]-> {tgt}")
        return {
            "是否一致": "是" if len(missing) == 0 else "否",
            "缺失关系": missing if missing else "无",
            "已检查关系": [f"{e.source.name} -[{e.relation}]-> {e.target.name}" for e in edges]
        }

    def answer(self, question: str) -> dict:
        # 1. 检索相关子图
        related_edges = []
        for node in self.graph.nodes:
            if node.lower() in question.lower():
                related_edges.extend(self.graph.query_related(node))

        # 2. 构造 system prompt
        if related_edges:
            context = "\n".join([f"{e.source.name} -[{e.relation}]-> {e.target.name}" for e in related_edges])
            system_prompt = f"你必须基于以下思维图谱回答问题，不能编造额外关系：\n{context}"
        else:
            system_prompt = "思维图谱中没有相关信息时，请直接回答不知道。"

        # 3. 调用 API
        answer = self.llm.generate(system_prompt, question)

        # 4. 一致性校验
        check = self.check_consistency(answer, related_edges)

        return {
            "问题": question,
            "回答": answer,
            "一致性校验": check
        }

if __name__ == "__main__":
    # 构建一个复杂的就业思维图谱
    g = ThoughtGraph()
    g.add_edge("就业市场", "受影响于", "经济环境")
    g.add_edge("就业市场", "受影响于", "技术发展")
    g.add_edge("就业市场", "提供", "就业机会")
    g.add_edge("大学毕业生", "进入", "就业市场")
    g.add_edge("技能匹配", "决定", "就业机会")
    g.add_edge("人工智能", "改变", "技能需求")
    g.add_edge("远程办公", "影响", "就业市场")
    g.add_edge("职业培训", "提高", "就业竞争力")
    g.add_edge("经济衰退", "减少", "就业机会")
    g.add_edge("绿色能源", "创造", "就业机会")

    # 初始化 LLM 接口
    llm = LLMWrapper(API_KEY)
    pipe = Pipeline(g, llm)

    # 提问示例
    q1 = "大学毕业生在进入就业市场时面临哪些挑战？"
    q2 = "人工智能会如何影响未来的就业机会？"
    q3 = "绿色能源行业能提供哪些就业机会？"

    for q in [q1, q2, q3]:
        result = pipe.answer(q)
        print("\n=== QA 结果 ===")
        print("问题:", result["问题"])
        print("回答:", result["回答"])
        print("一致性校验:", result["一致性校验"])
