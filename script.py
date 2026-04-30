#! python 3
# Cortar en capas + extrusión hasta tope + ShrinkWrap (100% In-Memory API)
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

def slice_and_shrinkwrap_optimized():
    # Validar versión de Rhino
    if Rhino.RhinoApp.Version.Major < 8:
        print("El comando ShrinkWrap requiere Rhino 8 o superior.")
        return

    obj_id = rs.GetObject("Selecciona la pieza", rs.filter.polysurface | rs.filter.surface | rs.filter.mesh)
    if not obj_id:
        return

    layer_height = rs.GetReal("Altura de capa", 5.0, 0.1)
    if not layer_height:
        return

    # Extraer la geometría pura sin depender de la base de datos del documento
    geo = rs.coercegeometry(obj_id)
    if not geo: return

    bbox = geo.GetBoundingBox(True)
    z_min = bbox.Min.Z
    z_max = bbox.Max.Z
    tol = sc.doc.ModelAbsoluteTolerance

    # Determinar tipo de geometría
    is_mesh = isinstance(geo, Rhino.Geometry.Mesh)
    is_brep = isinstance(geo, Rhino.Geometry.Brep)
    if not is_brep and isinstance(geo, Rhino.Geometry.Extrusion):
        geo = geo.ToBrep(False)
        is_brep = True

    # Esta lista almacenará los sólidos virtuales en la RAM
    geometries_for_sw = System.Collections.Generic.List[Rhino.Geometry.GeometryBase]()

    print("Procesando en memoria... (Calculando matemáticas, por favor espera)")
    rs.EnableRedraw(False)

    current_z = z_min

    # BUCLE PRINCIPAL (Sin tocar el documento de Rhino)
    while current_z <= z_max:
        plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(0, 0, current_z), Rhino.Geometry.Vector3d.ZAxis)
        height = z_max - current_z
        curves_to_extrude = []

        # 1. Intersección Matemática Pura
        if is_mesh:
            plines = Rhino.Geometry.Intersect.Intersection.MeshPlane(geo, plane)
            if plines:
                for pline in plines:
                    curves_to_extrude.append(Rhino.Geometry.PolylineCurve(pline))
        elif is_brep:
            success, crvs, pts = Rhino.Geometry.Intersect.Intersection.BrepPlane(geo, plane, tol)
            if success and crvs:
                curves_to_extrude.extend(crvs)

        # 2. Extrusión Ligera Virtual
        for crv in curves_to_extrude:
            if crv.IsClosed and height > 0:
                # Intentar crear una Extrusión Ligera (mucho más rápida y consume menos RAM)
                extrusion = Rhino.Geometry.Extrusion.Create(crv, height, True)
                if extrusion:
                    geometries_for_sw.Add(extrusion)
                else:
                    # Fallback de seguridad: Si la curva es demasiado extraña, usar Brep
                    vector = Rhino.Geometry.Vector3d(0, 0, height)
                    srf = Rhino.Geometry.Surface.CreateExtrusion(crv, vector)
                    if srf:
                        brep = srf.ToBrep()
                        if brep:
                            brep = brep.CapPlanarHoles(tol)
                            if brep:
                                geometries_for_sw.Add(brep)

        current_z += layer_height

    if geometries_for_sw.Count == 0:
        print("Error: No se generó geometría para procesar.")
        rs.EnableRedraw(True)
        return

    print("Sólidos virtuales generados: {}. Aplicando ShrinkWrap...".format(geometries_for_sw.Count))

    # --- 3. APLICAR SHRINKWRAP ---
    sw_params = Rhino.Geometry.ShrinkWrapParameters()
    sw_params.TargetEdgeLength = 0.1
    sw_params.Offset = 0.0
    sw_params.SmoothingIterations = 0
    sw_params.PolygonOptimization = 0
    sw_params.FillHoles = False
    sw_params.InflateVerticesAndPoints = False

    mesh_params = Rhino.Geometry.MeshingParameters.Default
    sw_mesh = Rhino.Geometry.Mesh.ShrinkWrap(geometries_for_sw, sw_params, mesh_params)

    # 4. Volcar el resultado final al documento (Única escritura en disco/archivo)
    if sw_mesh:
        sw_id = sc.doc.Objects.AddMesh(sw_mesh)
        rs.SelectObject(sw_id)
        print("Operación completada a máxima velocidad.")
    else:
        print("Error al generar el ShrinkWrap.")

    rs.EnableRedraw(True)

# Ejecutar
if __name__ == "__main__":
    slice_and_shrinkwrap_optimized()
