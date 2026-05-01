# GENERATE KEY
#! python 3 extrusion por capas by Gemini, idea by NGL
#! python 3
# Cortar en capas + extrusión hasta el tope + ShrinkWrap API RhinoCommon
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

def add_centered_plane(origin, width, height):
    plane = Rhino.Geometry.Plane(
        Rhino.Geometry.Point3d(origin[0], origin[1], origin[2]),
        Rhino.Geometry.Vector3d(0,0,1)
    )

    x_interval = Rhino.Geometry.Interval(-width/2.0, width/2.0)
    y_interval = Rhino.Geometry.Interval(-height/2.0, height/2.0)

    plane_srf = Rhino.Geometry.PlaneSurface(plane, x_interval, y_interval)

    return sc.doc.Objects.AddSurface(plane_srf)


def extrude_curve_solid(crv_id, height):
    crv = rs.coercecurve(crv_id)
    if not crv:
        return None

    # Vector siempre hacia arriba
    vector = Rhino.Geometry.Vector3d(0, 0, height)

    # Crear superficie de extrusión
    srf = Rhino.Geometry.Surface.CreateExtrusion(crv, vector)
    if not srf:
        return None

    # Convertir a Brep
    brep = srf.ToBrep()

    # Tapar (convertir a sólido)
    if brep and brep.IsSolid == False:
        tol = sc.doc.ModelAbsoluteTolerance
        brep = brep.CapPlanarHoles(tol)

    if brep:
        return sc.doc.Objects.AddBrep(brep)

    return None


def slice_and_shrinkwrap():
    # Validar versión de Rhino (ShrinkWrap requiere Rhino 8)
    if Rhino.RhinoApp.Version.Major < 8:
        print("El comando ShrinkWrap requiere Rhino 8 o superior.")
        return

    obj = rs.GetObject("Selecciona la pieza", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not obj:
        return

    layer_height = rs.GetReal("Altura de capa", 5.0, 0.1)
    if not layer_height:
        return

    bbox = rs.BoundingBox(obj)

    x_vals = [pt.X for pt in bbox]
    y_vals = [pt.Y for pt in bbox]
    z_vals = [pt.Z for pt in bbox]

    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)
    z_min, z_max = min(z_vals), max(z_vals)

    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0

    x_size = (x_max - x_min) * 1.1
    y_size = (y_max - y_min) * 1.1

    current_z = z_min
    solids = []

    # Apagar el redibujado de la interfaz para acelerar el cálculo
    rs.EnableRedraw(False)

    while current_z <= z_max:
        curves = []
        
        # --- NUEVA LÓGICA: Detección automática de tipo de geometría ---
        if rs.IsMesh(obj):
            # Intersección matemática optimizada para Mallas (Meshes/STLs)
            mesh = rs.coercemesh(obj)
            plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0, 0, current_z), Rhino.Geometry.Vector3d(0,0,1))
            plines = Rhino.Geometry.Intersect.Intersection.MeshPlane(mesh, plane)
            
            if plines:
                for pline in plines:
                    # Convertir la polilínea resultante a una curva en el documento
                    crv = Rhino.Geometry.PolylineCurve(pline)
                    crv_id = sc.doc.Objects.AddCurve(crv)
                    curves.append(crv_id)
        else:
            # Intersección original para Superficies y Polisuperficies (Breps)
            plane_id = add_centered_plane(
                (center_x, center_y, current_z),
                x_size,
                y_size
            )
            intersect_result = rs.IntersectBreps(obj, plane_id)
            if intersect_result:
                curves = intersect_result
            rs.DeleteObject(plane_id)
        # ---------------------------------------------------------------

        if curves:
            for crv in curves:
                if rs.IsCurveClosed(crv):
                    
                    # Extruir hasta arriba del bounding box
                    height = z_max - current_z

                    if height > 0:
                        solid_id = extrude_curve_solid(crv, height)
                        if solid_id:
                            solids.append(solid_id)
            
            # Borrar las curvas de intersección inmediatamente
            rs.DeleteObjects(curves)

        current_z += layer_height

    if not solids:
        print("No se pudieron generar los sólidos.")
        rs.EnableRedraw(True)
        return

    print("Sólidos generados: {}. Calculando ShrinkWrap vía RhinoCommon...".format(len(solids)))

    # --- APLICAR SHRINKWRAP VÍA API ---
    
    # 1. Recolectar las geometrías en una lista fuertemente tipada de .NET
    # Esto evita problemas de sobrecarga al llamar métodos de C# desde Python
    geometries = System.Collections.Generic.List[Rhino.Geometry.GeometryBase]()
    for sid in solids:
        geo = rs.coercegeometry(sid)
        if geo:
            geometries.Add(geo)
            
    # 2. Configurar los parámetros exactos
    sw_params = Rhino.Geometry.ShrinkWrapParameters()
    sw_params.TargetEdgeLength = 0.1
    sw_params.Offset = 0.0
    sw_params.SmoothingIterations = 0
    sw_params.PolygonOptimization = 0
    sw_params.FillHoles = False
    sw_params.InflateVerticesAndPoints = False

    # 3. Configurar parámetros de mallado (Requerido por la API al pasar Breps/GeometryBase)
    mesh_params = Rhino.Geometry.MeshingParameters.Default

    # 4. Llamar al método estático ShrinkWrap correcto
    sw_mesh = Rhino.Geometry.Mesh.ShrinkWrap(geometries, sw_params, mesh_params)

    if sw_mesh:
        sw_id = sc.doc.Objects.AddMesh(sw_mesh)
        rs.SelectObject(sw_id)
        rs.DeleteObjects(solids)
        print("ShrinkWrap completado con éxito.")
    else:
        print("Error: No se pudo generar el ShrinkWrap.")

    rs.EnableRedraw(True)

# Ejecutar
if __name__ == "__main__":
    slice_and_shrinkwrap()