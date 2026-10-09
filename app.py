import io
import xml.etree.ElementTree as ET
import ezdxf
from ezdxf.path import from_svg_path, render_lwpolylines
import streamlit as st

st.set_page_config(page_title="Convertisseur SVG vers DXF", page_icon="✂️")

st.title("Convertisseur Découpe Cuir — SVG vers DXF")
st.write(
    "Déposez votre fichier vectoriel SVG (exporté depuis Illustrator) pour"
    " obtenir un DXF compatible Mozart."
)

uploaded_file = st.file_uploader("Choisissez un fichier SVG", type=["svg"])

if uploaded_file is not None:
  try:
    svg_content = uploaded_file.read().decode("utf-8")

    doc = ezdxf.new(dxfversion="R2000")
    msp = doc.modelspace()

    root = ET.fromstring(svg_content)
    paths = []

    for elem in root.iter():
      tag = elem.tag.split("}")[-1]
      if tag == "path" and "d" in elem.attrib:
        d_attr = elem.attrib["d"].strip()
        if d_attr:
          try:
            p = from_svg_path(d_attr)
            paths.append(p)
          except Exception:
            continue

    if paths:
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
