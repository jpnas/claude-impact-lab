import struct
import shapely.geometry as sg
from pathlib import Path


def _read_dbf(dbf_path: Path) -> list[dict]:
    with open(dbf_path, "rb") as f:
        header = f.read(32)
        num_records = struct.unpack("<I", header[4:8])[0]
        header_size = struct.unpack("<H", header[8:10])[0]
        record_size = struct.unpack("<H", header[10:12])[0]
        field_data = f.read(header_size - 32 - 1)
        f.read(1)  # terminator
        fields = []
        for i in range(0, len(field_data), 32):
            chunk = field_data[i : i + 32]
            if len(chunk) < 32:
                break
            name = chunk[:11].replace(b"\x00", b"").decode("utf-8", errors="replace")
            typ = chr(chunk[11])
            length = chunk[16]
            fields.append((name, typ, length))
        records = []
        for _ in range(num_records):
            raw = f.read(record_size)
            if raw[0] == 0x2A:
                continue  # deleted record
            vals = {}
            offset = 1
            for name, typ, length in fields:
                vals[name] = raw[offset : offset + length].decode("utf-8", errors="replace").strip()
                offset += length
            records.append(vals)
    return records


def _read_shp_polygons(shp_path: Path) -> list[sg.Polygon]:
    """Read polygon geometries from .shp file (shape type 5 = Polygon)."""
    import shapefile as sf
    reader = sf.Reader(str(shp_path))
    polygons = []
    for shape in reader.shapes():
        if shape.shapeType == 5:
            parts = list(shape.parts) + [len(shape.points)]
            rings = []
            for i in range(len(parts) - 1):
                ring = shape.points[parts[i] : parts[i + 1]]
                rings.append(ring)
            if rings:
                exterior = rings[0]
                holes = rings[1:]
                polygons.append(sg.Polygon(exterior, holes))
            else:
                polygons.append(sg.Polygon())
        else:
            polygons.append(sg.Polygon())
    return polygons


def load_areas(shapefile_base: Path) -> dict[str, sg.Polygon]:
    """Returns {nome_subar: Polygon} for all 8 FM areas."""
    records = _read_dbf(Path(str(shapefile_base) + ".dbf"))
    polygons = _read_shp_polygons(Path(str(shapefile_base) + ".shp"))
    assert len(records) == len(polygons), f"DBF/SHP mismatch: {len(records)} vs {len(polygons)}"
    return {rec["nome_subar"]: poly for rec, poly in zip(records, polygons)}
