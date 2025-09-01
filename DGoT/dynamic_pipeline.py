# -*- coding: utf-8 -*-
import requests
from dynamic_thought_graph import DynamicThoughtGraph

# ⚠️ 直接写死 API Key
API_KEY = "sk-edfsimejxizigdometxmimnpmnbrttzfgfykflbmbxguxvob"
API_URL = "https://api.siliconflow.cn/v1/chat/completions"

class LLMWrapper:
    def __init__(self, api_key: str = API_KEY, url: str = API_URL, model: str = "Qwen/QwQ-32B"):
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

class DynamicPipeline:
    """动态思维图谱两阶段推理"""
    def __init__(self, llm: LLMWrapper):
        self.graph = DynamicThoughtGraph()
        self.llm = llm

    def generate_graph(self, question: str):
        system_prompt = (
            "你是就业顾问AI，请基于问题生成一个结构化的就业思维图谱。\n"
            "节点包括：职业目标、核心技能、学习资源、就业机会等；\n"
            "关系包括：requires, leads_to, supports, mitigates。\n"
            "输出格式：每行 source -[relation]-> target"
        )
        graph_text = self.llm.generate(system_prompt, question)
        # 解析图谱文本
        for line in graph_text.split("\n"):
            if "-[" in line and "]->" in line:
                src = line.split("-[")[0].strip()
                rel = line.split("-[")[1].split("]->")[0].strip()
                tgt = line.split("]->")[1].strip()
                self.graph.add_edge(src, rel, tgt)
        return self.graph

    def answer_with_graph(self, question: str):
        # 构建上下文
        if self.graph.edges:
            context = "\n".join([f"{e.source.name} -[{e.relation}]-> {e.target.name}" for e in self.graph.edges])
            system_prompt = f"你必须基于以下动态思维图谱回答问题，不能编造额外关系：\n{context}"
        else:
            system_prompt = "思维图谱为空，请直接回答不知道。"

        answer = self.llm.generate(system_prompt, question)
        return answer

    def check_consistency(self, answer: str):
        missing = []
        for e in self.graph.edges:
            if e.source.name.lower() not in answer.lower() or e.target.name.lower() not in answer.lower():
                missing.append(f"{e.source.name} -[{e.relation}]-> {e.target.name}")
        return {
            "consistent": len(missing) == 0,
            "missing": missing,
            "relations_checked": [f"{e.source.name} -[{e.relation}]-> {e.target.name}" for e in self.graph.edges]
        }

def main():
    llm = LLMWrapper()
    pipeline = DynamicPipeline(llm)

    question = "我想成为数据科学领域的专业人才，应该如何规划学习和就业？"

    print("=== 阶段 1: 生成动态思维图谱 ===")
    graph = pipeline.generate_graph(question)
    print(graph)

    print("\n=== 阶段 2: 基于图谱回答问题 ===")
    answer = pipeline.answer_with_graph(question)
    print(answer)

    print("\n=== 一致性校验 ===")
    check = pipeline.check_consistency(answer)
    print(check)

if __name__ == "__main__":
    main()
