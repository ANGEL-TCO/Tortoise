#aplanar y alinear
import rhinoscriptsyntax as rs

# -------------------------
# CONFIG
# -------------------------
ANGLE = 45
TOL = 1e-6

# -------------------------
# SELECCIÓN
# -------------------------
obj = rs.GetObject("Selecciona el objeto")

# -------------------------
# FUNCIONES BASE
# -------------------------
def get_center(obj):
    bbox = rs.BoundingBox(obj)
    return rs.PointDivide(rs.PointAdd(bbox[0], bbox[6]), 2)

def rotate(obj, angle, axis):
    center = get_center(obj)
    rs.RotateObject(obj, center, angle, axis)

def get_height(obj):
    bbox = rs.BoundingBox(obj)
    min_x = min(pt.X for pt in bbox)
    left_face_pts = [pt for pt in bbox if abs(pt.X - min_x) < TOL]
    z_values = [pt.Z for pt in left_face_pts]
    return max(z_values) - min(z_values)

# 🔹 NUEVA: ancho de la cara superior
def get_top_width(obj):
    bbox = rs.BoundingBox(obj)

    max_z = max(pt.Z for pt in bbox)
    top_pts = [pt for pt in bbox if abs(pt.Z - max_z) < TOL]

    x_vals = [pt.X for pt in top_pts]
    return max(x_vals) - min(x_vals)

# -------------------------
# OPTIMIZACIÓN POR EJE (ALTURA)
# -------------------------
def optimize_axis(obj, axis):
    current_height = get_height(obj)

    # + dirección
    rotate(obj, ANGLE, axis)
    new_height = get_height(obj)

    if new_height < current_height:
        current_height = new_height
        while True:
            rotate(obj, ANGLE, axis)
            new_height = get_height(obj)
            if new_height < current_height:
                current_height = new_height
            else:
                rotate(obj, -ANGLE, axis)
                break
        return True

    rotate(obj, -ANGLE, axis)

    # - dirección
    rotate(obj, -ANGLE, axis)
    new_height = get_height(obj)

    if new_height < current_height:
        current_height = new_height
        while True:
            rotate(obj, -ANGLE, axis)
            new_height = get_height(obj)
            if new_height < current_height:
                current_height = new_height
            else:
                rotate(obj, ANGLE, axis)
                break
        return True

    rotate(obj, ANGLE, axis)
    return False

# -------------------------
# NUEVA OPTIMIZACIÓN EN Z (ANCHO)
# -------------------------
def optimize_z_width(obj):
    print("\nOptimizando rotación en Z (ancho superior)")

    current_width = get_top_width(obj)

    # +Z
    rotate(obj, ANGLE, (0,0,1))
    new_width = get_top_width(obj)

    if new_width < current_width:
        current_width = new_width
        while True:
            rotate(obj, ANGLE, (0,0,1))
            new_width = get_top_width(obj)
            if new_width < current_width:
                current_width = new_width
                print("   ↓ ancho:", current_width)
            else:
                rotate(obj, -ANGLE, (0,0,1))
                break
        return

    rotate(obj, -ANGLE, (0,0,1))

    # -Z
    rotate(obj, -ANGLE, (0,0,1))
    new_width = get_top_width(obj)

    if new_width < current_width:
        current_width = new_width
        while True:
            rotate(obj, -ANGLE, (0,0,1))
            new_width = get_top_width(obj)
            if new_width < current_width:
                current_width = new_width
                print("   ↓ ancho:", current_width)
            else:
                rotate(obj, ANGLE, (0,0,1))
                break
        return

    rotate(obj, ANGLE, (0,0,1))
    print("→ No mejora en Z (ancho)")

# -------------------------
# LOOP GLOBAL
# -------------------------
iteration = 0

while True:
    ANGLE = 45
    iteration += 1
    print("\nIteración global:", iteration)

    improved = False

    if optimize_axis(obj, (1,0,0)):
        improved = True

    if optimize_axis(obj, (0,1,0)):
        improved = True

    if optimize_axis(obj, (0,0,1)):
        improved = True

    if not improved:
        print("Convergencia alcanzada (altura)")
        print(ANGLE)
        break

while True:
    ANGLE = 15
    iteration += 1
    print("\nIteración global:", iteration)

    improved = False

    if optimize_axis(obj, (1,0,0)):
        improved = True

    if optimize_axis(obj, (0,1,0)):
        improved = True

    if optimize_axis(obj, (0,0,1)):
        improved = True

    if not improved:
        print("Convergencia alcanzada (altura)")
        print(ANGLE)
        ANGLE = ANGLE/3

        break

while True:
    ANGLE = 1
    iteration += 1
    print("\nIteración global:", iteration)

    improved = False

    if optimize_axis(obj, (1,0,0)):
        improved = True

    if optimize_axis(obj, (0,1,0)):
        improved = True

    if optimize_axis(obj, (0,0,1)):
        improved = True

    if not improved:
        print("Convergencia alcanzada (altura)")
        print(ANGLE)
        ANGLE = ANGLE/3

        break

# 🔥 NUEVO PASO FINAL
optimize_z_width(obj)

print("\nOptimización completa (altura + alineación horizontal)")