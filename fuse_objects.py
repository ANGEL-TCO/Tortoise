#! python 3
# PREPROCESSING OBJECTS (WRAPPER)
#! python 3
# Selección por ventana/múltiple + ShrinkWrap directo
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

def create_shrinkwrap_from_selection():
    # Validar versión de Rhino
    if Rhino.RhinoApp.Version.Major < 8:
        print("El comando ShrinkWrap requiere Rhino 8 o superior.")
        return

    # Pedir al usuario que seleccione objetos (permite selección por ventana o múltiples clics)
    obj_ids = rs.GetObjects("Selecciona la(s) pieza(s) con una ventana", 
                            rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    
    if not obj_ids:
        print("Operación cancelada: No se seleccionó ningún objeto.")
        return

    # Recolectar todas las geometrías en una lista tipada para la API
    geometries = System.Collections.Generic.List[Rhino.Geometry.GeometryBase]()
    
    for obj_id in obj_ids:
        geo = rs.coercegeometry(obj_id)
        if geo:
            # Si es una Extrusión Ligera, convertirla a Brep para mayor compatibilidad
            if isinstance(geo, Rhino.Geometry.Extrusion):
                geo = geo.ToBrep(False)
            geometries.Add(geo)

    if geometries.Count == 0:
        print("No se encontró geometría válida para procesar.")
        return

    print("Calculando ShrinkWrap unificado para {} objetos...".format(geometries.Count))
    
    # Apagar el redibujado para evitar parpadeos y acelerar el proceso
    rs.EnableRedraw(False)

    # --- APLICAR SHRINKWRAP CON PARÁMETROS FIJOS ---
    sw_params = Rhino.Geometry.ShrinkWrapParameters()
    sw_params.TargetEdgeLength = 0.1
    sw_params.Offset = 0.0
    sw_params.SmoothingIterations = 0
    sw_params.PolygonOptimization = 0
    sw_params.FillHoles = False
    sw_params.InflateVerticesAndPoints = False

    mesh_params = Rhino.Geometry.MeshingParameters.Default
    
    # Generar la malla envolvente de todos los objetos seleccionados
    sw_mesh = Rhino.Geometry.Mesh.ShrinkWrap(geometries, sw_params, mesh_params)

    if sw_mesh:
        # Deseleccionar los objetos originales
        rs.UnselectAllObjects()
        
        # Añadir el nuevo sólido al documento y seleccionarlo
        sw_id = sc.doc.Objects.AddMesh(sw_mesh)
        rs.SelectObject(sw_id)
        print("ShrinkWrap completado con éxito.")
    else:
        print("Error al generar el ShrinkWrap.")

    # Restaurar la interfaz
    rs.EnableRedraw(True)

# Ejecutar
if __name__ == "__main__":
    create_shrinkwrap_from_selection()
