#! python 3
# Configurar documento a milímetros (sin escalar) + Crear bloque base
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino

def setup_units_and_create_block():
    # 1. Cambiar las unidades del documento a Milímetros
    # El segundo parámetro 'False' equivale a "Change unit system only"
    sc.doc.AdjustModelUnitSystem(Rhino.UnitSystem.Millimeters, False)
    
    print("Unidades del documento actualizadas a Milímetros (sin escalar objetos).")

    # 2. Medidas absolutas (1 unidad = 1 mm) para un bloque de 2" x 6" x 1"
    w = 2.0 * 25.4   # 50.8 mm
    l = 6.0 * 25.4   # 152.4 mm
    h = 1.0 * 25.4   # 25.4 mm

    # 3. Construir la caja
    plane = Rhino.Geometry.Plane.WorldXY
    x_interval = Rhino.Geometry.Interval(0, w)
    y_interval = Rhino.Geometry.Interval(0, l)
    z_interval = Rhino.Geometry.Interval(0, h)
    
    box = Rhino.Geometry.Box(plane, x_interval, y_interval, z_interval)

    # 4. Convertir a sólido y añadir al documento
    brep = box.ToBrep()
    if brep:
        obj_id = sc.doc.Objects.AddBrep(brep)
        rs.UnselectAllObjects()
        rs.SelectObject(obj_id)
        sc.doc.Views.Redraw()
        print("Bloque base creado: 50.8 x 152.4 x 25.4 mm.")
    else:
        print("Error al intentar crear el bloque.")

# Ejecutar
if __name__ == "__main__":
    setup_units_and_create_block()