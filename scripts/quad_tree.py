from dataclasses import dataclass
from typing import List, Optional

# Nova lasse Rectangle com centro como referência e largura/altura sendo "meia"
@dataclass
class Rectangle:
    id: int
    cx: float  # centro x
    cy: float  # centro y
    hw: float  # meia largura (half-width)
    hh: float  # meia altura (half-height)

    def __init__(self, cx, cy, hw, hh, id=-1):
        self.cx = cx
        self.cy = cy
        self.hw = hw
        self.hh = hh
        self.id = id

    def intersects(self, other: 'Rectangle') -> bool:
        return not (
            self.cx + self.hw <= other.cx - other.hw or
            self.cx - self.hw >= other.cx + other.hw or
            self.cy + self.hh <= other.cy - other.hh or
            self.cy - self.hh >= other.cy + other.hh
        )

# Adaptar QuadTreeNode para usar o novo modelo
class QuadTreeNode:

    def __init__(self, boundary: Rectangle, minSize, capacity: int = 4):
        self.boundary = boundary
        self.capacity = capacity
        self.objects: List[Rectangle] = []
        self.divided = False
        self.minSize = minSize
        self.children: List[Optional[QuadTreeNode]] = [None, None, None, None]  # NW, NE, SW, SE

    def print(self, level: int = 0):
        indent = '  ' * level
        print(f"{indent}Node(center=({self.boundary.cx}, {self.boundary.cy}), "
              f"hw={self.boundary.hw}, hh={self.boundary.hh}, objects={len(self.objects)})")

        # Exibir os retângulos armazenados nesse nó (se houver)
        for i, rect in enumerate(self.objects):
            print(f"{indent}  Rect {i}: center=({rect.cx}, {rect.cy}), hw={rect.hw}, hh={rect.hh}, id={rect.id}")

        # Recursivamente imprimir os filhos (se houver)
        if self.divided:
            for i, child in enumerate(self.children):
                quadrant = ["NW", "NE", "SW", "SE"][i]
                print(f"{indent}  -> {quadrant}")
                if child:
                    child.print(level + 2)

    def subdivide(self):

        hw = self.boundary.hw // 2
        hh = self.boundary.hh // 2

        if hw < self.minSize or hh < self.minSize:
            return

        cx = self.boundary.cx
        cy = self.boundary.cy

        self.children[0] = QuadTreeNode(Rectangle(cx - hw, cy - hh, hw, hh), self.minSize)  # NW
        self.children[1] = QuadTreeNode(Rectangle(cx + hw, cy - hh, hw, hh), self.minSize)  # NE
        self.children[2] = QuadTreeNode(Rectangle(cx - hw, cy + hh, hw, hh), self.minSize)  # SW
        self.children[3] = QuadTreeNode(Rectangle(cx + hw, cy + hh, hw, hh), self.minSize)  # SE

        self.divided = True

        inserted = False
        for rect in self.objects:

            for child in self.children:
                if child:
                    inserted |= child.insert(rect)

            if not inserted:
                print("Capacity must be greater than 0")

        self.objects = []

    def insert(self, rect: Rectangle) -> bool:

        if not self.boundary.intersects(rect):
            return False

        hw = self.boundary.hw // 2
        hh = self.boundary.hh // 2

        if not self.divided and len(self.objects) < self.capacity:
            self.objects.append(rect)
            return True

        #NOTE: If the node can't be subdivided anymore it should not have an object limit
        elif hw < self.minSize * 2 or hh < self.minSize * 2:
            self.objects.append(rect)
            return True

        if not self.divided:
            self.subdivide()

        inserted = False
        for child in self.children:
            if child:
                inserted |= child.insert(rect)

        return inserted

    def search(self, rect: Rectangle) -> List[Rectangle]:
        """
        Encontra a folha da quadtree que contém (ou intersecta) o retângulo dado
        e retorna os objetos armazenados nesse nó folha.
        """
        if not self.boundary.intersects(rect):
            return []  # Fora da área da quadtree

        if not self.divided:
            return self.objects

        results = []

        for child in self.children:
            #NOTE: Nesse caso o bounds checking é necessário
            if child and child.boundary.intersects(rect):
                results += child.search(rect)

        return results  # Não foi possível encontrar (raro)
