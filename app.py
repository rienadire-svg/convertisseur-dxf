import io
import xml.etree.ElementTree as ET
import ezdxf
import ezdxf.path
from ezdxf.path import Path, render_lwpolylines
import streamlit as st

st.set_page_config(page_title="Convertisseur SVG vers DXF", page_icon="✂️")

st.title("Convertisseur Découpe Cuir — SVG vers DXF")
st.write(
    "Déposez votre fichier vectoriel SVG (exporté depuis Illustrator) pour"
    " obtenir un DXF compatible Mozart."
)


# Détection dynamique du parseur SVG selon la version d'ezdxf
def parse_d_string(d_str):
  if hasattr(ezdxf.path, "parse_svg_path"):
    return ezdxf.path.parse_svg_path(d_str)
  elif hasattr(ezdxf.path, "from_svg_path"):
    return ezdxf.path.from_svg_path(d_str)
  elif hasattr(ezdxf.path, "svg") and hasattr(
      ezdxf.path.svg, "parse_svg_path"
  ):
    return ezdxf.path.svg.parse_svg_path(d_str)
  else:
    raise AttributeError("Parseur SVG non trouvé dans ezdxf.path")


# Conversion des formes basiques SVG en tracés vectoriels (d-string)
def elem_to_d(elem):
  tag = elem.tag.split("}")[-1].lower()
  attr = elem.attrib

  if tag == "path" and "d" in attr:
    return attr["d"]
  elif tag == "rect":
    x, y = float(attr.get("x", 0)), float(attr.get("y", 0))
    w, h = float(attr.get("width", 0)), float(attr.get("height", 0))
    if w > 0 and h > 0:
      return f"M {x},{y} h {w} v {h} h {-w} Z"
  elif tag == "line":
    x1, y1 = attr.get("x1", 0), attr.get("y1", 0)
    x2, y2 = attr.get("x2", 0), attr.get("y2", 0)
    return f"M {x1},{y1} L {x2},{y2}"
  elif tag == "polyline":
    pts = attr.get("points", "").strip()
    if pts:
      return f"M {pts}"
  elif tag == "polygon":
    pts = attr.get("points", "").strip()
    if pts:
      return f"M {pts} Z"
  elif tag == "circle":
    cx, cy, r = (
        float(attr.get("cx", 0)),
        float(attr.get("cy", 0)),
        float(attr.get("r", 0)),
    )
    if r > 0:
      return (
          f"M {cx - r},{cy} A {r},{r} 0 1,0 {cx + r},{cy} A {r},{r} 0 1,0"
          f" {cx - r},{cy}"
      )
  return None


uploaded_file = st.file_uploader("Choisissez un fichier SVG", type=["svg"])

if uploaded_file is not None:
  try:
    svg_content = uploaded_file.read().decode("utf-8")

    doc = ezdxf.new(dxfversion="R2000")
    msp = doc.modelspace()

    root = ET.fromstring(svg_content)
    paths = []

    for elem in root.iter():
      d_attr = elem_to_d(elem)
      if d_attr:
        d_attr = d_attr.strip()
        if d_attr:
          try:
            res = parse_d_string(d_attr)
            if isinstance(res, Path):
              paths.append(res)
            elif res:
              for p in res:
                paths.append(p)
          except Exception:
            continue

    if paths:
      # Conversion des courbes en polylignes DXF
      render_lwpolylines(msp, paths, distance=0.1)

      out_stream = io.StringIO()
      doc.write(out_stream)
      dxf_bytes = out_stream.getvalue().encode("utf-8")

      output_filename = uploaded_file.name.rsplit(".", 1)[0] + "_Mozart.dxf"

      st.success("Conversion réussie !")
      st.download_button(
          label="Télécharger le fichier DXF",
          data=dxf_bytes,
          file_name=output_filename,
          mime="application/dxf",
      )
    else:
      st.error(
          "Aucun tracé vectoriel valide n'a été trouvé dans le fichier SVG."
      )

  except Exception as e:
    st.error(f"Erreur lors de la conversion : {str(e)}")
