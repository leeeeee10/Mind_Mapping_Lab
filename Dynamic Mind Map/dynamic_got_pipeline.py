# dynamic_got_pipeline.py
import os
import json
import requests
from typing import Dict, Any, List

from thought_graph import ThoughtGraph, extract_first_json
import prompts as P

API_URL = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_MODEL = "Qwen/QwQ-32B"  # 你也可以换成别的兼容模型

class LLM:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, url: str = API_URL, timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.url = url
        self.timeout = timeout

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        resp = requests.post(self.url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

# ---------------- 核心流程 ----------------

def generate_graph(llm: LLM, question: str) -> ThoughtGraph:
    """
    第一次 API：请模型生成“思维图 JSON”，并解析+校验。
    """
    user_prompt = P.GRAPH_GEN_USER_TEMPLATE.format(question=question)
    raw = llm.chat(P.GRAPH_GEN_SYSTEM, user_prompt)

    json_str = extract_first_json(raw)
    if not json_str:
        raise ValueError("未能从大模型输出中提取JSON，请检查提示词或模型输出。")

    tg = ThoughtGraph.from_json_str(json_str)
    report = tg.validate()
    if not report["valid"]:
        print("⚠️ 图谱校验问题：")
        for p in report["problems"]:
            print(" -", p)
    print("📈 图谱摘要：", report["summary"])
    return tg

def answer_with_graph(llm: LLM, question: str, tg: ThoughtGraph) -> Dict[str, Any]:
    """
    第二次 API：把“紧凑三元组”喂给模型，要求严格基于图进行回答。
    """
    triples = tg.to_min_triples()
    triples_text = "\n".join(f"- {t}" for t in triples)

    user_prompt = P.ANSWER_USER_TEMPLATE.format(
        question=question,
        triples_text=triples_text
    )
    raw = llm.chat(P.ANSWER_SYSTEM, user_prompt)

    json_str = extract_first_json(raw)
    if not json_str:
        raise ValueError("未能从回答中提取JSON。")

    result = json.loads(json_str)
    return result

# ---------------- 一致性校验 ----------------

def coverage_check(tg: ThoughtGraph, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    校验点：
    1) used_nodes/used_edges 是否存在于图中
    2) 覆盖度：回答是否覆盖权重Top-K的边（通过名字包含来粗检）
    """
    problems: List[str] = []
    used_nodes = set(result.get("used_nodes", []))
    used_edges = set(result.get("used_edges", []))

    # 1) 引用存在性
    for nid in used_nodes:
        if nid not in tg.nodes:
            problems.append(f"引用了不存在的节点ID: {nid}")
    for eid in used_edges:
        if eid not in tg.edges:
            problems.append(f"引用了不存在的关系ID: {eid}")

    # 2) 覆盖Top-K 边（K=3）
    top_edges = sorted(tg.edges.values(), key=lambda e: e.weight, reverse=True)[:3]
    final_answer: str = result.get("final_answer", "")
    missed_important = []
    for e in top_edges:
        s = tg.nodes[e.source].name
        t = tg.nodes[e.target].name
        # 粗略：答案里至少出现任一端点名称
        if (s not in final_answer) and (t not in final_answer):
            missed_important.append(f"{e.id}:{s}-[{e.relation}]->{t}")

    return {
        "是否通过": "是" if not problems and not missed_important else "否",
        "结构问题": problems or "无",
        "高权重关系未覆盖": missed_important or "无",
        "建议": "若存在未覆盖高权重关系，考虑在答案中补充与其相关的建议或行动项。"
    }

# ---------------- 运行入口 ----------------

def main():
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("请先设置环境变量 SILICONFLOW_API_KEY")

    llm = LLM(api_key=api_key)

    # 你可以换成自己的真实画像/约束/目标
    question = (
        "我有3年Python数据分析经验，本科非CS。想在新能源行业（优先光伏/风电）找数据分析/数据工程岗位，"
        "期望在上海或杭州，愿意每周投入10小时学习。请给出技能补齐、证书建议、项目组合和3个月行动计划。"
    )

    print("== 第一步：生成思维图 ==")
    tg = generate_graph(llm, question)
    print(tg.to_json())

    print("\n== 第二步：基于图回答 ==")
    result = answer_with_graph(llm, question, tg)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n== 第三步：一致性校验 ==")
    report = coverage_check(tg, result)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
