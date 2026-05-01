#! python 3
# Orientar pieza por puntos en los Sprues ("Analogía del Agua")
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

def orient_piece_by_points():
    # 1. Seleccionar la pieza completa
    obj_id = rs.GetObject("1. Selecciona la pieza (Anillo/Dije)", rs.filter.mesh | rs.filter.polysurface)
    if not obj_id: return

    # 2. Seleccionar los puntos que representan las bases de los sprues
    point_ids = rs.GetObjects("2. Selecciona los PUNTOS en las bases de los sprues (minimo 3)", rs.filter.point)
    if not point_ids or len(point_ids) < 3:
        print("Operación cancelada: Se requieren al menos 3 puntos para formar un plano estable.")
        return

    print("Calculando el plano del agua... (por favor espera)")
    rs.EnableRedraw(False)

    # Extraer las coordenadas 3D de los puntos seleccionados
    points = [rs.PointCoordinates(pid) for pid in point_ids]

# 3. Matemática: Calcular el plano que mejor atraviesa todos esos puntos a la vez
    # Rhino en Python devuelve 2 valores: el estado de éxito y el plano en sí.
    resultado = Rhino.Geometry.Plane.FitPlaneToPoints(points)
    
    # Extraemos los dos valores de la tupla
    success = resultado[0]
    fit_plane = resultado[1]
    
    if success != Rhino.Geometry.PlaneFitResult.Success:
        print("Error: Los puntos seleccionados no forman un plano válido (están todos en una sola línea).")
        rs.EnableRedraw(True)
        return

    # 4. Crear la matriz para alinear el plano calculado con el suelo universal de Rhino (Z=0)
    world_xy_plane = Rhino.Geometry.Plane.WorldXY
    xform_orient = Rhino.Geometry.Transform.PlaneToPlane(fit_plane, world_xy_plane)

    # Aplicar el movimiento a la pieza y a los puntos para que viajen juntos
    rs.TransformObject(obj_id, xform_orient)
    rs.TransformObjects(point_ids, xform_orient)

    # --- 5. Validación de Gravedad (El test del corcho) ---
    # Revisamos si la pieza quedó flotando hacia arriba o colgando hacia abajo
    geo_final = rs.coercegeometry(obj_id)
    bbox = geo_final.GetBoundingBox(True)
    
    # Calculamos dónde está el centro de masa de la caja
    z_center = (bbox.Max.Z + bbox.Min.Z) / 2.0
    
    # Si el centro está en los números positivos (+Z), la pieza está boca arriba
    if z_center > 0:
        print("La pieza quedó boca arriba. Volteando 180 grados para sumergirla...")
        # La rotamos como a un pollo en un asador, usando el eje X
        axis_x = Rhino.Geometry.Vector3d.XAxis
        xform_flip = Rhino.Geometry.Transform.Rotation(System.Math.PI, axis_x, Rhino.Geometry.Point3d(0,0,0))
        rs.TransformObject(obj_id, xform_flip)
        rs.TransformObjects(point_ids, xform_flip)

    # 6. Micro-Ajuste final: Asegurar que los puntos toquen exactamente el Z=0
    # Al calcular planos promedio puede quedar una diferencia microscópica, esto la elimina.
    pts_z_avg = sum([rs.PointCoordinates(pid).Z for pid in point_ids]) / len(point_ids)
    if abs(pts_z_avg) > 0.0001:
        rs.MoveObject(obj_id, (0, 0, -pts_z_avg))
        rs.MoveObjects(point_ids, (0, 0, -pts_z_avg))

    # Limpiar y mostrar resultado
    rs.UnselectAllObjects()
    rs.SelectObject(obj_id)
    rs.EnableRedraw(True)
    
    print("Éxito: La pieza ha sido sumergida y alineada horizontalmente por sus sprues.")

# Ejecutar
if __name__ == "__main__":
    orient_piece_by_points()