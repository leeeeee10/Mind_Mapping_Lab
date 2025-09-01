# thought_graph.py
from typing import List, Dict

class Node:
    def __init__(self, name: str, ntype: str = "concept"):
        self.name = name
        self.ntype = ntype
    def __repr__(self):
        return f"Node({self.name}, type={self.ntype})"

class Edge:
    def __init__(self, source: Node, relation: str, target: Node):
        self.source = source
        self.relation = relation
        self.target = target
    def __repr__(self):
        return f"Edge({self.source.name} -[{self.relation}]-> {self.target.name})"

class ThoughtGraph:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

    def add_node(self, name: str, ntype: str = "concept") -> Node:
        if name not in self.nodes:
            self.nodes[name] = Node(name, ntype)
        return self.nodes[name]

    def add_edge(self, source: str, relation: str, target: str):
        src = self.add_node(source)
        tgt = self.add_node(target)
        edge = Edge(src, relation, tgt)
        self.edges.append(edge)

    def query_related(self, concept: str) -> List[Edge]:
        return [e for e in self.edges if e.source.name == concept or e.target.name == concept]

    def __repr__(self):
        return "\n".join([repr(e) for e in self.edges])
