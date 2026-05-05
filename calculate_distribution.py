#! python 3
# Automated Fixture Array (Corrected Translation)
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import math

def automated_fixture_array():
    # 1. Select objects
    block_id = rs.GetObject("Selecciona el bloque de fixture (2x6x1)", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not block_id: return

    piece_id = rs.GetObject("Selecciona la pieza a distribuir", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not piece_id: return

    # 2. Margins and gaps
    margin = rs.GetReal("Margen desde el borde del bloque", 5.0, 0.0)
    gap = rs.GetReal("Espacio entre piezas (distancia de seguridad)", 4.0, 0.0)
    
    if margin is None or gap is None: return

    # 3. Bounding Boxes
    block_geo = rs.coercegeometry(block_id)
    piece_geo = rs.coercegeometry(piece_id)
    
    block_bbox = block_geo.GetBoundingBox(True)
    piece_bbox = piece_geo.GetBoundingBox(True)

    # Block dimensions
    bw = block_bbox.Max.X - block_bbox.Min.X
    bl = block_bbox.Max.Y - block_bbox.Min.Y
    
    # Piece dimensions
    pw = piece_bbox.Max.X - piece_bbox.Min.X
    pl = piece_bbox.Max.Y - piece_bbox.Min.Y

    # 4. Calculate Max Pieces
    count_x = int(math.floor((bw - (2 * margin) + gap) / (pw + gap)))
    count_y = int(math.floor((bl - (2 * margin) + gap) / (pl + gap)))

    if count_x < 1 or count_y < 1:
        print("Error: La pieza es demasiado grande para el bloque con los márgenes especificados.")
        return

    print("Calculando distribución: {} piezas en X, {} piezas en Y. Total: {}".format(count_x, count_y, count_x * count_y))

    # 5. Centering
    total_array_w = (count_x * pw) + ((count_x - 1) * gap)
    total_array_l = (count_y * pl) + ((count_y - 1) * gap)
    
    start_x = block_bbox.Min.X + (bw - total_array_w) / 2
    start_y = block_bbox.Min.Y + (bl - total_array_l) / 2
    start_z = block_bbox.Max.Z

    # 6. Execute Array
    rs.EnableRedraw(False)
    
    new_pieces = []
    
    # Original reference point
    ref_point = Rhino.Geometry.Point3d(piece_bbox.Min.X, piece_bbox.Min.Y, piece_bbox.Min.Z)
    
    # Target point for the first piece [0,0]
    target_pt_00 = Rhino.Geometry.Point3d(start_x, start_y, start_z)
    
    # Move the original piece to the start position FIRST
    translation_00 = target_pt_00 - ref_point
    rs.MoveObject(piece_id, translation_00)
    new_pieces.append(piece_id)

    # Now create copies based on the relative array offsets
    for i in range(count_x):
        for j in range(count_y):
            # Skip the first one since we just moved it there
            if i == 0 and j == 0:
                continue
            
            # Purely relative translation vector from the new position
            offset_vec = Rhino.Geometry.Vector3d(i * (pw + gap), j * (pl + gap), 0)
            
            # Copy using the relative vector
            new_obj = rs.CopyObject(piece_id, offset_vec)
            if new_obj:
                new_pieces.append(new_obj)

    rs.UnselectAllObjects()
    rs.SelectObjects(new_pieces)
    rs.EnableRedraw(True)
    
    print("Distribución completada. Se han organizado {} piezas.".format(len(new_pieces)))

if __name__ == "__main__":
    automated_fixture_array()
