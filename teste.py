<<<<<<< HEAD
from quad_tree import Rectangle
from quad_tree import QuadTreeNode

def main():

    # Definindo a área total do quadtree: centro (500, 500), largura total 1000x1000 => hw=500, hh=500
    boundary = Rectangle(cx=500, cy=500, hw=500, hh=500)
    root = QuadTreeNode(boundary, capacity=2)

    # Criando alguns retângulos a serem inseridos
    rects = [
        Rectangle(cx=450, cy=450, hw=30, hh=30),  # Dentro do NW
        Rectangle(cx=550, cy=450, hw=30, hh=30),  # Dentro do NE
        Rectangle(cx=450, cy=550, hw=30, hh=30),  # Dentro do SW
        Rectangle(cx=550, cy=550, hw=30, hh=30),  # Dentro do SE
        Rectangle(cx=500, cy=500, hw=50, hh=50),  # No centro
        Rectangle(cx=1001, cy=1001, hw=1, hh=1),  # Fora do quadtree
    ]

    # Inserir todos os retângulos
    for i, r in enumerate(rects):
        result = root.insert(r)
        print(f"Retângulo {i} inserido? {result}")

    root.print()

if __name__ == "__main__":
    main()

=======
metricas = {
    "metrica1": 1,
    "metrica2": 2,
    "metrica3": 3,
}

for metrica in metricas:
    print(f"{metrica}: {metricas[metrica]}")
>>>>>>> 6ba8b2eec27248a7e0c2ce25c95e1594d0d947bf
