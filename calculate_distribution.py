#! python 3
# Distribución Automática de Piezas (Array) en Fixture
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import math

def automated_fixture_array():
    # 1. Selección de objetos
    block_id = rs.GetObject("Selecciona el bloque de fixture (2x6x1)", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not block_id: return

    piece_id = rs.GetObject("Selecciona la pieza a distribuir", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not piece_id: return

    # 2. Configuración de márgenes y espacios (en unidades del documento, asumiendo mm)
    # Margen: Espacio desde el borde del bloque a la primera pieza
    # Gap: Espacio entre piezas para que pase la herramienta (fresa)
    margin = rs.GetReal("Margen desde el borde del bloque", 5.0, 0.0)
    gap = rs.GetReal("Espacio entre piezas (distancia de seguridad)", 4.0, 0.0)
    
    if margin is None or gap is None: return

    # 3. Obtener dimensiones mediante BoundingBoxes
    block_geo = rs.coercegeometry(block_id)
    piece_geo = rs.coercegeometry(piece_id)
    
    block_bbox = block_geo.GetBoundingBox(True)
    piece_bbox = piece_geo.GetBoundingBox(True)

    # Dimensiones del Bloque
    bw = block_bbox.Max.X - block_bbox.Min.X
    bl = block_bbox.Max.Y - block_bbox.Min.Y
    
    # Dimensiones de la Pieza
    pw = piece_bbox.Max.X - piece_bbox.Min.X
    pl = piece_bbox.Max.Y - piece_bbox.Min.Y

    # 4. Cálculo matemático del máximo de piezas (Nesting Lineal)
    # Formula: (LargoBloque - 2*Margen + Gap) / (LargoPieza + Gap)
    count_x = int(math.floor((bw - (2 * margin) + gap) / (pw + gap)))
    count_y = int(math.floor((bl - (2 * margin) + gap) / (pl + gap)))

    if count_x < 1 or count_y < 1:
        print("Error: La pieza es demasiado grande para el bloque con los márgenes especificados.")
        return

    print("Calculando distribución: {} piezas en X, {} piezas en Y. Total: {}".format(count_x, count_y, count_x * count_y))

    # 5. Calcular el centrado automático
    # Calculamos cuánto mide el "bloque" de piezas total
    total_array_w = (count_x * pw) + ((count_x - 1) * gap)
    total_array_l = (count_y * pl) + ((count_y - 1) * gap)
    
    # Punto de inicio para que el array quede centrado en el bloque
    start_x = block_bbox.Min.X + (bw - total_array_w) / 2
    start_y = block_bbox.Min.Y + (bl - total_array_l) / 2
    
    # Altura Z: Colocamos la base de la pieza (Z=0 del bbox) en la cara superior del bloque
    # Asumimos que la cara superior del bloque es block_bbox.Max.Z
    start_z = block_bbox.Max.Z

    # 6. Ejecutar la distribución (Array)
    rs.EnableRedraw(False)
    
    new_pieces = []
    
    # Punto de referencia original de la pieza (esquina min de su bbox)
    ref_point = Rhino.Geometry.Point3d(piece_bbox.Min.X, piece_bbox.Min.Y, piece_bbox.Min.Z)

    for i in range(count_x):
        for j in range(count_y):
            # No duplicamos la pieza original en la posición (0,0)
            if i == 0 and j == 0:
                # Mover la pieza original a la primera posición
                target_pt = Rhino.Geometry.Point3d(start_x, start_y, start_z)
                translation = target_pt - ref_point
                rs.MoveObject(piece_id, translation)
                new_pieces.append(piece_id)
                continue
            
            # Calcular posición de destino para las copias
            offset_x = i * (pw + gap)
            offset_y = j * (pl + gap)
            
            target_pt = Rhino.Geometry.Point3d(start_x + offset_x, start_y + offset_y, start_z)
            translation = target_pt - ref_point
            
            # Copiar y mover
            new_obj = rs.CopyObject(piece_id, translation)
            new_pieces.append(new_obj)

    rs.UnselectAllObjects()
    rs.SelectObjects(new_pieces)
    rs.EnableRedraw(True)
    
    print("Distribución completada. Se han organizado {} piezas.".format(len(new_pieces)))

if __name__ == "__main__":
    automated_fixture_array()
