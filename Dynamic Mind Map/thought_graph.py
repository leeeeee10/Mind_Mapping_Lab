# thought_graph.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json
import re

ALLOWED_NODE_TYPES = {
    "人物画像", "技能", "岗位", "行业", "约束", "趋势", "资源", "行动", "成果"
}

ALLOWED_RELATIONS = {
    "需要", "提升", "导致", "促进", "抑制", "迁移到", "适配", "依赖于", "位于", "推荐"
}

@dataclass
class Node:
    id: str
    name: str
    ntype: str
    attrs: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Edge:
    id: str
    source: str
    relation: str
    target: str
    weight: float = 0.5
    conditions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

@dataclass
class ThoughtGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, Edge] = field(default_factory=dict)

    # --------- 构建/修改 ----------
    def add_node(self, node: Node):
        if node.id in self.nodes:
            raise ValueError(f"节点重复: {node.id}")
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        if edge.id in self.edges:
            raise ValueError(f"关系重复: {edge.id}")
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise ValueError(f"关系引用不存在的节点: {edge.source}->{edge.target}")
        self.edges[edge.id] = edge

    # --------- 查询/序列化 ----------
    def to_min_triples(self) -> List[str]:
        """紧凑三元组文本，用于喂给第二次API"""
        triples = []
        for e in self.edges.values():
            s = self.nodes[e.source].name
            t = self.nodes[e.target].name
            triples.append(f"({e.id}) {s} -[{e.relation}, w={e.weight}]-> {t}")
        return triples

    def to_json(self) -> str:
        data = {
            "nodes": [vars(n) for n in self.nodes.values()],
            "edges": [vars(e) for e in self.edges.values()],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json_str(s: str) -> "ThoughtGraph":
        data = json.loads(s)
        tg = ThoughtGraph()
        for n in data.get("nodes", []):
            tg.add_node(Node(
                id=n["id"], name=n["name"], ntype=n.get("ntype", "概念"),
                attrs=n.get("attrs", {})
            ))
        for e in data.get("edges", []):
            edge = Edge(
                id=e["id"],
                source=e["source"],
                relation=e["relation"],
                target=e["target"],
                weight=float(e.get("weight", 0.5)),
                conditions=e.get("conditions", []) or [],
                evidence=e.get("evidence", []) or [],
            )
            tg.add_edge(edge)
        return tg

    # --------- 校验 ----------
    def validate(self) -> Dict[str, Any]:
        problems: List[str] = []
        # 节点类型/ID 唯一性检查
        seen_ids = set()
        for n in self.nodes.values():
            if n.id in seen_ids:
                problems.append(f"节点ID重复: {n.id}")
            seen_ids.add(n.id)
            if n.ntype not in ALLOWED_NODE_TYPES:
                problems.append(f"不允许的节点类型: {n.id}({n.name}) -> {n.ntype}")

        # 关系检查
        seen_eids = set()
        for e in self.edges.values():
            if e.id in seen_eids:
                problems.append(f"关系ID重复: {e.id}")
            seen_eids.add(e.id)

            if e.relation not in ALLOWED_RELATIONS:
                problems.append(f"不允许的关系类型: {e.id} -> {e.relation}")

            if e.source not in self.nodes or e.target not in self.nodes:
                problems.append(f"关系引用不存在的节点: {e.id} {e.source}->{e.target}")

            if not (0.0 <= e.weight <= 1.0):
                problems.append(f"关系权重范围错误(0~1): {e.id} -> {e.weight}")

        return {
            "valid": len(problems) == 0,
            "problems": problems,
            "summary": {
                "节点数": len(self.nodes),
                "关系数": len(self.edges),
            }
        }

# --------- 工具函数：从大模型输出中提取 JSON ---------
_JSON_RE = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

def extract_first_json(text: str) -> Optional[str]:
    """
    从模型返回中提取第一个 JSON 对象（避免模型加了解释性文字）。
    """
    m = _JSON_RE.search(text)
    if m:
        return m.group(0)
    return None
