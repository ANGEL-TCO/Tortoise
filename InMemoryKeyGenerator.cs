#! csharp
using System;
using System.Collections.Generic;
using Rhino;
using Rhino.Geometry;
using Rhino.Geometry.Intersect;
using Rhino.Input;
using Rhino.Input.Custom;
using Rhino.DocObjects;
using Rhino.Commands;

// Slice + Extrude + ShrinkWrap — 100% In-Memory, C# optimized
// Requires Rhino 8+

var doc = RhinoDoc.ActiveDoc;
var tol  = doc.ModelAbsoluteTolerance;

// ── 0. Version guard ──────────────────────────────────────────────────
if (RhinoApp.Version.Major < 8)
{
    RhinoApp.WriteLine("ShrinkWrap requires Rhino 8 or higher.");
    return;
}

// ── 1. Pick object ────────────────────────────────────────────────────
var getObj = new GetObject();
getObj.SetCommandPrompt("Select the piece");
getObj.GeometryFilter = ObjectType.Brep | ObjectType.Surface | ObjectType.Mesh;
getObj.Get();
if (getObj.CommandResult() != Result.Success) return;

GeometryBase geo = getObj.Object(0).Geometry();
if (geo == null) return;

// Promote Extrusion → Brep so intersection works uniformly
if (geo is Extrusion ext)
    geo = ext.ToBrep(false);

// ── 2. Layer height ───────────────────────────────────────────────────
var getNum = new GetNumber();
getNum.SetCommandPrompt("Layer height");
getNum.SetDefaultNumber(5.0);
getNum.SetLowerLimit(0.1, false);
getNum.Get();
if (getNum.CommandResult() != Result.Success) return;
double layerHeight = getNum.Number();

// ── 3. Setup ──────────────────────────────────────────────────────────
var bbox  = geo.GetBoundingBox(true);
double zMin = bbox.Min.Z;
double zMax = bbox.Max.Z;

bool isMesh = geo is Mesh;
bool isBrep = geo is Brep;

var geoForSW = new List<GeometryBase>();

RhinoApp.WriteLine("Processing in memory — please wait...");

// ── 4. Main slice loop (zero document writes) ─────────────────────────
for (double z = zMin; z <= zMax; z += layerHeight)
{
    var plane  = new Plane(new Point3d(0, 0, z), Vector3d.ZAxis);
    double height = zMax - z;
    if (height <= 0) continue;

    var curves = new List<Curve>();

    if (isMesh)
    {
        var plines = Intersection.MeshPlane((Mesh)geo, plane);
        if (plines != null)
            foreach (var pl in plines)
                curves.Add(new PolylineCurve(pl));
    }
    else if (isBrep)
    {
        bool ok = Intersection.BrepPlane(
            (Brep)geo, plane, tol,
            out Curve[] crvs, out Point3d[] _);
        if (ok && crvs != null)
            curves.AddRange(crvs);
    }

    foreach (var crv in curves)
    {
        if (!crv.IsClosed) continue;

        // Prefer lightweight Extrusion object (faster + less RAM)
        var extrusion = Extrusion.Create(crv, height, true);
        if (extrusion != null)
        {
            geoForSW.Add(extrusion);
            continue;
        }

        // Fallback: full Brep extrusion for geometrically complex curves
        var srf = Surface.CreateExtrusion(crv, new Vector3d(0, 0, height));
        if (srf == null) continue;
        var brep = srf.ToBrep();
        if (brep == null) continue;
        brep = brep.CapPlanarHoles(tol);
        if (brep != null)
            geoForSW.Add(brep);
    }
}

if (geoForSW.Count == 0)
{
    RhinoApp.WriteLine("Error: no geometry generated — check object validity and layer height.");
    return;
}

RhinoApp.WriteLine($"Virtual solids: {geoForSW.Count}. Running ShrinkWrap...");

// ── 5. ShrinkWrap ─────────────────────────────────────────────────────
var swParams = new ShrinkWrapParameters
{
    TargetEdgeLength         = 0.1,
    Offset                   = 0.0,
    SmoothingIterations      = 0,
    FillHoles                = false,
    InflateVerticesAndPoints = false,
};

var swMesh = Mesh.ShrinkWrap(geoForSW, swParams, MeshingParameters.Default);

// ── 6. Single document write ──────────────────────────────────────────
if (swMesh != null)
{
    var id = doc.Objects.AddMesh(swMesh);
    doc.Objects.Select(id);
    doc.Views.Redraw();
    RhinoApp.WriteLine("Done.");
}
else
{
    RhinoApp.WriteLine("ShrinkWrap failed — try increasing TargetEdgeLength.");
}